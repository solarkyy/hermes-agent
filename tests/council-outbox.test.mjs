import test from 'node:test';
import assert from 'node:assert/strict';
import { promises as fs } from 'node:fs';
import os from 'node:os';
import path from 'node:path';

import {
  CouncilOutbox,
  createCouncilOutbox,
  loadCouncilOutboxConfig,
} from '../src/council/outbox.mjs';

async function tempPaths() {
  const dir = await fs.mkdtemp(path.join(os.tmpdir(), 'council-outbox-'));
  return {
    dir,
    outboxPath: path.join(dir, 'outbox.json'),
    deadLetterPath: path.join(dir, 'dead-letter.json'),
    configPath: path.join(dir, 'council-outbox.yaml'),
  };
}

test('outbox persists queued council posts across process reloads', async () => {
  const paths = await tempPaths();
  const outbox = await createCouncilOutbox({
    outboxPath: paths.outboxPath,
    deadLetterPath: paths.deadLetterPath,
    idFactory: () => 'msg-durable',
  });

  await outbox.enqueue({ to: 'council', text: 'persist me', priority: 'high' });

  const reloaded = await createCouncilOutbox({
    outboxPath: paths.outboxPath,
    deadLetterPath: paths.deadLetterPath,
  });

  assert.equal(reloaded.pending().length, 1);
  assert.equal(reloaded.pending()[0].id, 'msg-durable');
  assert.equal(reloaded.pending()[0].payload.text, 'persist me');
});

test('flush retries unacked deliveries with configured backoff and records ACK receipts', async () => {
  const paths = await tempPaths();
  let now = 1_000;
  let calls = 0;
  const outbox = await createCouncilOutbox({
    outboxPath: paths.outboxPath,
    deadLetterPath: paths.deadLetterPath,
    maxRetries: 3,
    retryBackoffMs: 100,
    now: () => now,
    idFactory: () => 'msg-retry',
  });
  await outbox.enqueue({ to: 'council', text: 'retry until ack' });

  let result = await outbox.flush(async () => {
    calls += 1;
    return { status: 'sent_without_ack' };
  });

  assert.equal(calls, 1);
  assert.equal(result.pending, 1);
  assert.equal(outbox.getMessage('msg-retry').attempts, 1);
  assert.equal(outbox.getMessage('msg-retry').next_attempt_at, 1_100);

  result = await outbox.flush(async () => {
    calls += 1;
    return { ack: true };
  });
  assert.equal(calls, 1, 'message is not retried before next_attempt_at');
  assert.equal(result.pending, 1);

  now = 1_100;
  result = await outbox.flush(async (message) => {
    calls += 1;
    return { ack: true, correlation_id: message.correlation_id, receipt_id: 'ack-1' };
  });

  assert.equal(calls, 2);
  assert.equal(result.pending, 0);
  assert.equal(result.acked, 1);
  const acked = outbox.getMessage('msg-retry');
  assert.equal(acked.status, 'acked');
  assert.equal(acked.receipts.length, 1);
  assert.equal(acked.receipts[0].receipt_id, 'ack-1');
});

test('external ACK receipts match by correlation id', async () => {
  const paths = await tempPaths();
  const outbox = await createCouncilOutbox({
    outboxPath: paths.outboxPath,
    deadLetterPath: paths.deadLetterPath,
    idFactory: () => 'msg-ack',
  });
  await outbox.enqueue({ to: 'council', text: 'await explicit ack', correlation_id: 'corr-ack' });

  await outbox.flush(async () => ({ delivered: true }));
  assert.equal(outbox.getMessage('msg-ack').status, 'awaiting_ack');

  const matched = await outbox.ack({ correlation_id: 'corr-ack', receipt_id: 'receipt-42' });

  assert.equal(matched.status, 'acked');
  assert.equal(outbox.getMessage('msg-ack').receipts[0].receipt_id, 'receipt-42');
});

test('messages exceeding max retries are moved to the dead-letter file', async () => {
  const paths = await tempPaths();
  let now = 10_000;
  const outbox = await createCouncilOutbox({
    outboxPath: paths.outboxPath,
    deadLetterPath: paths.deadLetterPath,
    maxRetries: 2,
    retryBackoffMs: 50,
    now: () => now,
    idFactory: () => 'msg-dead',
  });
  await outbox.enqueue({ to: 'council', text: 'dead letter me' });

  await outbox.flush(async () => {
    throw new Error('council offline');
  });
  now = 10_050;
  const result = await outbox.flush(async () => {
    throw new Error('council offline');
  });

  assert.equal(result.pending, 0);
  assert.equal(result.dead_lettered.length, 1);
  assert.equal(outbox.getMessage('msg-dead'), undefined);

  const deadFile = JSON.parse(await fs.readFile(paths.deadLetterPath, 'utf8'));
  assert.equal(deadFile.dead_letters.length, 1);
  assert.equal(deadFile.dead_letters[0].id, 'msg-dead');
  assert.equal(deadFile.dead_letters[0].dead_letter_reason, 'council offline');
});

test('config loader reads council outbox yaml keys', async () => {
  const paths = await tempPaths();
  await fs.writeFile(
    paths.configPath,
    'max_retries: 7\nretry_backoff_ms: 250\ndead_letter_path: "dead.json"\noutbox_flush_interval_ms: 2000\n',
    'utf8',
  );

  const config = await loadCouncilOutboxConfig(paths.configPath);

  assert.deepEqual(config, {
    max_retries: 7,
    retry_backoff_ms: 250,
    dead_letter_path: 'dead.json',
    outbox_flush_interval_ms: 2000,
  });
});
