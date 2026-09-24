import { randomUUID } from 'node:crypto';

/**
 * A conversation with one counterparty about one thing. The trade record will hold
 * these as `message_threads` with a tenant_id and an RLS policy (SEEN-008); until
 * then they live behind this interface so the code that puts mail on a thread does
 * not change when the table arrives.
 */
export interface MessageThread {
  id: string;
  tenantId: string;
  /** Mail now. Marketplace messaging APIs join it in SEEN-061. */
  channel: 'mail';
  /** The marketplace the counterparty is, when the address says so. */
  marketplace: string | null;
  subject: string;
  /** The key replies are matched on: the root mail id, or the normalised subject. */
  key: string;
  openedAt: string;
  messages: ThreadMessage[];
}

export interface ThreadMessage {
  id: string;
  direction: 'inbound' | 'outbound';
  from: string;
  to: string[];
  subject: string;
  body: string;
  receivedAt: string;
  /** The counterparty's own id for this mail, which is what makes a replay idempotent. */
  externalRef: string | null;
}

export interface AppendResult {
  thread: MessageThread;
  /** False when the mail joined a thread that already existed, or was a replay. */
  created: boolean;
}

export interface ThreadStore {
  /** Puts the message on its thread, opening one if this is the first of its kind. */
  append(input: AppendInput): Promise<AppendResult>;
  byId(id: string): Promise<MessageThread | undefined>;
  all(): Promise<MessageThread[]>;
}

export interface AppendInput {
  tenantId: string;
  marketplace: string | null;
  key: string;
  message: Omit<ThreadMessage, 'id'>;
}

/** The injection token, so SEEN-062 swaps the implementation and no caller changes. */
export const THREAD_STORE = Symbol.for('seen.ThreadStore');

/**
 * Process memory, which is the right lifetime for a development environment and
 * the wrong one for anything else. It is deliberately the only implementation in
 * this ticket: persisting here would write SEEN-008's schema and its RLS rules
 * inside an environment ticket.
 */
export class InMemoryThreadStore implements ThreadStore {
  private readonly threads = new Map<string, MessageThread>();

  async append(input: AppendInput): Promise<AppendResult> {
    const existing = [...this.threads.values()].find(
      (thread) => thread.tenantId === input.tenantId && thread.key === input.key,
    );

    if (existing) {
      const replay =
        input.message.externalRef !== null &&
        existing.messages.some((message) => message.externalRef === input.message.externalRef);

      if (!replay) existing.messages.push({ id: randomUUID(), ...input.message });

      return { thread: existing, created: false };
    }

    const thread: MessageThread = {
      id: randomUUID(),
      tenantId: input.tenantId,
      channel: 'mail',
      marketplace: input.marketplace,
      subject: input.message.subject,
      key: input.key,
      openedAt: input.message.receivedAt,
      messages: [{ id: randomUUID(), ...input.message }],
    };
    this.threads.set(thread.id, thread);

    return { thread, created: true };
  }

  async byId(id: string): Promise<MessageThread | undefined> {
    return this.threads.get(id);
  }

  async all(): Promise<MessageThread[]> {
    return [...this.threads.values()];
  }
}
