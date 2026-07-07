import test from 'node:test';
import assert from 'node:assert/strict';
import { once } from 'node:events';
import {
  CrossSurfaceSync,
  loadCrossSurfaceSyncConfig,
} from '../src/sync/cross-surface.mjs';

function testConfig(overrides = {}) {
  return {
    ws_port: 0,
    ot_enabled: true,
    ot_type: 'text',
    heartbeat_interval_ms: 0,
    max_reconnect_attempts: 20,
    reconnect_interval_ms: 20,
    op_log_limit: 100,
    ...overrides,
  };
}

async function waitUntil(predicate, label, timeoutMs = 1_500) {
  const started = Date.now();
  while (Date.now() - started < timeoutMs) {
    if (predicate()) return;
    await new Promise((resolve) => setTimeout(resolve, 10));
  }
  assert.fail(`Timed out waiting for ${label}`);
}

async function cleanup(...syncs) {
  await Promise.allSettled(syncs.map((sync) => sync?.disconnect?.({ reconnect: false })));
  await Promise.allSettled(syncs.map((sync) => sync?.stopServer?.()));
}

test('loads cross-surface sync config', async () => {
  const config = await loadCrossSurfaceSyncConfig('config/cross-surface-sync.yaml');
  assert.equal(config.ws_port, 8787);
  assert.equal(config.ot_enabled, true);
  assert.equal(config.ot_type, 'text');
  assert.equal(config.heartbeat_interval_ms, 30_000);
  assert.equal(config.max_reconnect_attempts, 10);
});

test('validates WebSocket mesh replication from Hermes to Pi and Telegram', async () => {
  const hermes = new CrossSurfaceSync({ surface_id: 'hermes', role: 'primary', config: testConfig() });
  const pi = new CrossSurfaceSync({ surface_id: 'pi', role: 'replica', config: testConfig() });
  const telegram = new CrossSurfaceSync({ surface_id: 'telegram', role: 'replica', config: testConfig() });

  try {
    await hermes.startServer({ port: 0 });
    const url = `ws://127.0.0.1:${hermes.address().port}`;

    const piSnapshot = once(pi, 'snapshot');
    const telegramSnapshot = once(telegram, 'snapshot');
    await pi.connect(url);
    await telegram.connect(url);
    await piSnapshot;
    await telegramSnapshot;

    pi.insertWhisper('mesh-thread', 0, 'hello', { base_version: 0, op_id: 'pi-mesh-1' });

    await waitUntil(
      () => hermes.getWhisper('mesh-thread').text === 'hello' &&
        pi.getWhisper('mesh-thread').text === 'hello' &&
        telegram.getWhisper('mesh-thread').text === 'hello',
      'mesh replication',
    );

    assert.equal(hermes.snapshot().version, 1);
    assert.equal(telegram.getWhisper('mesh-thread').version, 1);
  } finally {
    await cleanup(pi, telegram, hermes);
  }
});

test('validates OT merge for concurrent whisper inserts', () => {
  const hermes = new CrossSurfaceSync({ surface_id: 'hermes', role: 'primary', config: testConfig() });

  hermes.applyWhisperOperation({
    whisper_id: 'ot-thread',
    action: 'insert',
    pos: 0,
    text: 'Pi',
    base_version: 0,
    surface_id: 'pi',
    op_id: 'pi-ot-1',
  });
  const telegramEntry = hermes.applyWhisperOperation({
    whisper_id: 'ot-thread',
    action: 'insert',
    pos: 0,
    text: '+Telegram',
    base_version: 0,
    surface_id: 'telegram',
    op_id: 'telegram-ot-1',
  });

  assert.equal(hermes.getWhisper('ot-thread').text, 'Pi+Telegram');
  assert.equal(telegramEntry.operation.pos, 2);
  assert.equal(hermes.getWhisper('ot-thread').version, 2);
});

test('validates reconnect after server restart', async () => {
  const config = testConfig({ reconnect_interval_ms: 15, max_reconnect_attempts: 50 });
  const hermes = new CrossSurfaceSync({ surface_id: 'hermes', role: 'primary', config });
  const pi = new CrossSurfaceSync({ surface_id: 'pi', role: 'replica', config });
  let replacement;

  try {
    await hermes.startServer({ port: 0 });
    const port = hermes.address().port;
    const url = `ws://127.0.0.1:${port}`;
    const initialSnapshot = once(pi, 'snapshot');
    await pi.connect(url);
    await initialSnapshot;

    const reconnected = once(pi, 'connected');
    await hermes.stopServer();
    replacement = new CrossSurfaceSync({ surface_id: 'hermes', role: 'primary', config });
    await replacement.startServer({ port });

    await reconnected;
    await waitUntil(() => pi.clientSocket?.readyState === 1, 'client reconnect');
    assert.equal(pi.reconnectAttempts, 0);
  } finally {
    await cleanup(pi, hermes, replacement);
  }
});

test('validates surface switch replay for missed whisper operations', async () => {
  const hermes = new CrossSurfaceSync({ surface_id: 'hermes', role: 'primary', config: testConfig() });
  const pi = new CrossSurfaceSync({ surface_id: 'pi', role: 'replica', config: testConfig() });

  try {
    await hermes.startServer({ port: 0 });
    const url = `ws://127.0.0.1:${hermes.address().port}`;
    const initialSnapshot = once(pi, 'snapshot');
    await pi.connect(url);
    await initialSnapshot;

    hermes.insertWhisper('replay-thread', 0, 'one', {
      base_version: 0,
      surface_id: 'hermes',
      op_id: 'hermes-replay-1',
    });
    await waitUntil(() => pi.getWhisper('replay-thread').text === 'one', 'first replay-thread op');
    assert.equal(pi.snapshot().version, 1);

    await pi.disconnect({ reconnect: false });
    hermes.insertWhisper('replay-thread', 3, 'two', {
      base_version: 1,
      surface_id: 'hermes',
      op_id: 'hermes-replay-2',
    });

    const replay = once(pi, 'replay');
    await pi.connect(url);
    const [message] = await replay;

    await waitUntil(() => pi.getWhisper('replay-thread').text === 'onetwo', 'surface switch replay');
    assert.equal(message.from_version, 1);
    assert.equal(message.to_version, 2);
    assert.equal(message.ops.length, 1);
  } finally {
    await cleanup(pi, hermes);
  }
});
