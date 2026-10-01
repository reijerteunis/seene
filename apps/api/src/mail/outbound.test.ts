import { describe, expect, it } from 'vitest';
import { mailpit } from './mailpit';
import { createMailer } from './outbound';

/**
 * The outbound half of the local mailbox, against the real Mailpit container:
 * nothing is stubbed, so a green here means dev:up gave us a mail server a pilot
 * brand's correspondence can actually go through.
 *
 * It reads the mail back rather than trusting the send, because an SMTP server
 * that accepts a message and drops it is exactly the failure this is here to catch.
 */
describe('outbound mail', () => {
  it('arrives in Mailpit with the subject and recipient it was sent with', async () => {
    const subject = `Seen local check ${process.pid}-${Date.now()}`;
    const mailer = createMailer(process.env);

    await mailer.send({
      to: 'brand@example.test',
      subject,
      text: 'The local environment sent this. Nothing left the machine.',
    });

    const message = await mailpit(process.env).waitForSubject(subject, 10_000);

    expect(message.To.map((recipient) => recipient.Address)).toContain('brand@example.test');
    expect(message.From.Address).toBe('seen@localhost');
  });

  it('says which host it could not reach rather than failing anonymously', async () => {
    const mailer = createMailer({ ...process.env, SMTP_PORT: '1' });

    await expect(
      mailer.send({ to: 'brand@example.test', subject: 'no', text: 'no' }),
    ).rejects.toThrow(/127\.0\.0\.1:1/);
  });
});
