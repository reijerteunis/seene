import { Test } from '@nestjs/testing';
import type { INestApplication } from '@nestjs/common';
import request from 'supertest';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { AppModule } from '../app.module';
import { THREAD_STORE, type ThreadStore } from '../mail/threads';
import inbound from './fixtures/postmark-inbound.json';
import reply from './fixtures/postmark-inbound-reply.json';

/**
 * The local environment's inbound path, end to end over HTTP: the same webhook
 * body Postmark posts, through the same route a pilot brand's forwarded mail will
 * reach, into a thread.
 *
 * The thread lives in memory behind ThreadStore. SEEN-008 creates message_threads
 * with its tenant_id and RLS policy and SEEN-062 does the real matching against
 * orders and claims; this proves the environment carries the mail, not that the
 * matching is right.
 *
 * A fresh application per test, because the store is process state and a test that
 * depends on the one before it is a test that reports the wrong thing when it fails.
 */
describe('the Postmark inbound webhook', () => {
  let app: INestApplication;
  let store: ThreadStore;

  const post = (body: unknown) =>
    request(app.getHttpServer()).post('/webhooks/postmark/inbound').send(body);

  beforeEach(async () => {
    const moduleRef = await Test.createTestingModule({ imports: [AppModule] }).compile();
    app = moduleRef.createNestApplication();
    await app.init();
    store = app.get<ThreadStore>(THREAD_STORE);
  });

  afterEach(async () => {
    await app.close();
  });

  it('accepts the fixture and answers with the thread it created', async () => {
    const response = await post(inbound).expect(202);

    expect(response.body).toMatchObject({ threadId: expect.any(String), created: true });

    const thread = await store.byId(response.body.threadId);
    expect(thread?.tenantId).toBe('demo-tenant');
    expect(thread?.marketplace).toBe('bol');
    expect(thread?.subject).toBe('Vergoedingsverzoek 1234567890 ontvangen');
    expect(thread?.messages).toHaveLength(1);
    expect(thread?.messages[0]).toMatchObject({
      direction: 'inbound',
      from: 'partnerservice@bol.com',
      externalRef: '<case-1234567890@bol.com>',
    });
  });

  it('puts a reply on the thread it is a reply to rather than opening a second one', async () => {
    const first = await post(inbound).expect(202);
    const second = await post(reply).expect(202);

    expect(second.body.threadId).toBe(first.body.threadId);
    expect(second.body.created).toBe(false);

    expect((await store.byId(first.body.threadId))?.messages).toHaveLength(2);
    expect(await store.all()).toHaveLength(1);
  });

  it('is idempotent on the mail id, because Postmark retries a webhook it did not hear back from', async () => {
    const first = await post(inbound).expect(202);
    await post(inbound).expect(202);

    expect((await store.byId(first.body.threadId))?.messages).toHaveLength(1);
  });

  it('refuses a body that is not a Postmark inbound payload', async () => {
    await post({ hello: 'world' }).expect(400);

    expect(await store.all()).toHaveLength(0);
  });
});
