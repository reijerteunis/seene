import type { AppendInput } from './threads';

/** The fields of Postmark's inbound webhook this ticket reads. */
export interface PostmarkInbound {
  From: string;
  To: string;
  Subject: string;
  MessageID: string;
  MailboxHash?: string;
  Date?: string;
  TextBody?: string;
  StrippedTextReply?: string;
  Headers?: { Name: string; Value: string }[];
  ToFull?: { Email: string }[];
}

/**
 * The marketplaces whose mail we can name from the sending domain alone. SEEN-062
 * does the real identification, including the order and case ids in the body; this
 * is the part that is true from the envelope and needs no parsing to be sure of.
 */
const MARKETPLACE_DOMAINS: ReadonlyArray<[string, string]> = [
  ['bol.com', 'bol'],
  ['amazon.', 'amazon'],
  ['ebay.', 'ebay'],
  ['kaufland.', 'kaufland'],
  ['otto.', 'otto'],
];

export function isPostmarkInbound(body: unknown): body is PostmarkInbound {
  if (typeof body !== 'object' || body === null) return false;
  const candidate = body as Record<string, unknown>;

  return (
    typeof candidate.From === 'string' &&
    typeof candidate.To === 'string' &&
    typeof candidate.Subject === 'string' &&
    typeof candidate.MessageID === 'string'
  );
}

export function header(mail: PostmarkInbound, name: string): string | null {
  const found = mail.Headers?.find(
    (candidate) => candidate.Name.toLowerCase() === name.toLowerCase(),
  );
  return found?.Value ?? null;
}

export function marketplaceOf(address: string): string | null {
  const domain = address.split('@').pop()?.toLowerCase() ?? '';
  return MARKETPLACE_DOMAINS.find(([match]) => domain.includes(match))?.[1] ?? null;
}

/**
 * Which tenant the mail is for. Postmark puts everything after the plus in
 * MailboxHash, so `inbox+demo-tenant@...` is tenant `demo-tenant`. A forwarded mail
 * with no hash belongs to nobody yet and is the ops queue's problem in SEEN-062.
 */
export function tenantOf(mail: PostmarkInbound): string | null {
  if (mail.MailboxHash) return mail.MailboxHash;

  const plus = /\+([^@]+)@/.exec(mail.ToFull?.[0]?.Email ?? mail.To);
  return plus?.[1] ?? null;
}

/**
 * Replies carry the mail they answer in In-Reply-To, and that is the only thread
 * key here that is the counterparty's own word rather than our guess. Failing that,
 * the subject with its reply prefixes stripped: crude, and honest about being so.
 */
export function threadKey(mail: PostmarkInbound): string {
  const references = header(mail, 'In-Reply-To') ?? header(mail, 'References');
  if (references) return references.split(/\s+/)[0] ?? references;

  const own = header(mail, 'Message-ID');
  if (own) return own;

  return `subject:${normaliseSubject(mail.Subject)}`;
}

export function normaliseSubject(subject: string): string {
  return subject
    .replace(/^((re|fw|fwd|aw|antw)\s*(\[\d+\])?\s*:\s*)+/i, '')
    .trim()
    .toLowerCase();
}

/** The webhook body as the thread store wants it. Pure, so the controller stays thin. */
export function toAppendInput(mail: PostmarkInbound): AppendInput {
  const tenantId = tenantOf(mail);
  if (tenantId === null) {
    throw new Error('The mail carries no mailbox hash, so it names no tenant.');
  }

  return {
    tenantId,
    marketplace: marketplaceOf(mail.From),
    key: threadKey(mail),
    message: {
      direction: 'inbound',
      from: mail.From,
      to: mail.ToFull?.map((recipient) => recipient.Email) ?? [mail.To],
      subject: mail.Subject,
      body: mail.StrippedTextReply || mail.TextBody || '',
      receivedAt: mail.Date ? new Date(mail.Date).toISOString() : new Date().toISOString(),
      externalRef: header(mail, 'Message-ID'),
    },
  };
}
