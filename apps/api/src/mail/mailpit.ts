/**
 * Mailpit's read API, for tests and for a person checking what the environment
 * actually sent. It is a development tool and has no place in a deployed service,
 * which is why it holds no state and is constructed from the environment each time.
 */
export interface MailpitMessage {
  ID: string;
  Subject: string;
  From: { Address: string; Name: string };
  To: { Address: string; Name: string }[];
}

type Environment = Readonly<Record<string, string | undefined>>;

export function mailpit(env: Environment = process.env) {
  const base = (env.MAILPIT_URL ?? 'http://127.0.0.1:8025').replace(/\/$/, '');

  const list = async (): Promise<MailpitMessage[]> => {
    const response = await fetch(`${base}/api/v1/messages?limit=200`);
    if (!response.ok) throw new Error(`Mailpit at ${base} answered ${response.status}.`);

    return ((await response.json()) as { messages?: MailpitMessage[] }).messages ?? [];
  };

  return {
    list,

    /**
     * Polls rather than sleeping once: SMTP delivery and the HTTP read are two
     * different races, and a fixed sleep either flakes or wastes the difference.
     */
    async waitForSubject(subject: string, timeoutMs = 10_000): Promise<MailpitMessage> {
      const deadline = Date.now() + timeoutMs;

      for (;;) {
        const found = (await list()).find((message) => message.Subject === subject);
        if (found) return found;

        if (Date.now() >= deadline) {
          throw new Error(`No mail with subject '${subject}' reached Mailpit within ${timeoutMs}ms.`);
        }
        await new Promise((resolve) => setTimeout(resolve, 100));
      }
    },

    async deleteAll(): Promise<void> {
      await fetch(`${base}/api/v1/messages`, { method: 'DELETE' });
    },
  };
}
