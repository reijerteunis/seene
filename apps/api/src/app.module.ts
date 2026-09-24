import { Module } from '@nestjs/common';

import { HealthController } from './health.controller';
import { InMemoryThreadStore, THREAD_STORE } from './mail/threads';
import { PostmarkController } from './webhooks/postmark.controller';

/**
 * The whole HTTP surface in one list. THREAD_STORE is a token rather than a class
 * so SEEN-062 can put the Postgres-backed store behind it without touching the
 * controller that uses it.
 */
@Module({
  controllers: [HealthController, PostmarkController],
  providers: [{ provide: THREAD_STORE, useClass: InMemoryThreadStore }],
})
export class AppModule {}
