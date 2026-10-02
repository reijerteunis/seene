import { BadRequestException, Body, Controller, HttpCode, Inject, Post } from '@nestjs/common';

import { isPostmarkInbound, toAppendInput } from '../mail/postmark';
import { type AppendInput, THREAD_STORE, type ThreadStore } from '../mail/threads';

/**
 * Where forwarded mail enters. In the local environment a fixture is replayed
 * against it (`pnpm replay:inbound`); in a pilot Postmark posts to it through the
 * Cloudflare Tunnel. Both are the same route, so what is tested is what runs.
 *
 * It accepts and stores; it does not match to an order or a claim, which is
 * SEEN-062's work against the real schema.
 */
@Controller('webhooks/postmark')
export class PostmarkController {
  constructor(@Inject(THREAD_STORE) private readonly threads: ThreadStore) {}

  @Post('inbound')
  // 202, not 200: the mail is accepted and put on a thread, and what happens to it
  // after that is a job. Postmark retries anything that is not a 2xx.
  @HttpCode(202)
  async inbound(@Body() body: unknown): Promise<{ threadId: string; created: boolean }> {
    if (!isPostmarkInbound(body)) {
      throw new BadRequestException('Not a Postmark inbound payload.');
    }

    let input: AppendInput;
    try {
      input = toAppendInput(body);
    } catch (error) {
      throw new BadRequestException(String(error instanceof Error ? error.message : error));
    }

    const { thread, created } = await this.threads.append(input);

    return { threadId: thread.id, created };
  }
}
