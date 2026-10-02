import { createTransport } from 'nodemailer';

/** What every outbound mail needs. Templates and threading arrive with SEEN-063. */
interface OutboundMail {
  to: string;
  subject: string;
  text: string;
  html?: string;
  replyTo?: string;
}

export interface Mailer {
  /** Returns the id the mail server gave the message. */
  send(mail: OutboundMail): Promise<{ messageId: string }>;
}

type Environment = Readonly<Record<string, string | undefined>>;

/**
 * Mailpit locally, a real relay after go-live. Only the host and port change, so
 * this reads both from the environment and defaults to what docker-compose.yml
 * publishes.
 */
export function createMailer(env: Environment = process.env): Mailer {
  const host = env.SMTP_HOST ?? '127.0.0.1';
  const port = Number(env.SMTP_PORT ?? 1025);
  const from = env.SEEN_MAIL_FROM ?? 'Seen <seen@localhost>';

  const transport = createTransport({
    host,
    port,
    // Mailpit speaks plain SMTP on 1025. After go-live the relay sets these.
    secure: env.SMTP_SECURE === 'true',
    auth: env.SMTP_USER ? { user: env.SMTP_USER, pass: env.SMTP_PASSWORD ?? '' } : undefined,
    // Without this a wrong port waits for a connection nobody will answer.
    connectionTimeout: 5_000,
  });

  return {
    async send(mail) {
      try {
        const sent = await transport.sendMail({ from, ...mail });
        return { messageId: sent.messageId };
      } catch (error) {
        // The default message names neither, and "connect ECONNREFUSED" on its own
        // has cost more than one person an afternoon.
        throw new Error(
          `Could not send mail through ${host}:${port}: ` +
            `${error instanceof Error ? error.message : String(error)}`,
        );
      }
    },
  };
}
