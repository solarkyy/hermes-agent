import { promises as fs } from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

export const DEFAULT_COUNCIL_OUTBOX_CONFIG = Object.freeze({
  max_retries: 5,
  retry_backoff_ms: 1000,
  dead_letter_path: '.omni/council-dead-letter.json',
  outbox_flush_interval_ms: 5000,
});

const DEFAULT_OUTBOX_PATH = '.omni/council-outbox.json';
const ACTIVE_STATUSES = new Set(['queued', 'awaiting_ack']);

function isoNow(now = Date.now()) {
  return new Date(now).toISOString();
}

function normalizeNumber(value, fallback) {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed >= 0 ? parsed : fallback;
}

function stripYamlValue(value) {
  const trimmed = value.trim();
  if (
    (trimmed.startsWith('"') && trimmed.endsWith('"')) ||
    (trimmed.startsWith("'") && trimmed.endsWith("'"))
  ) {
    return trimmed.slice(1, -1);
  }
  if (/^-?\d+(\.\d+)?$/.test(trimmed)) return Number(trimmed);
  if (trimmed === 'true') return true;
  if (trimmed === 'false') return false;
  return trimmed;
}

export async function loadCouncilOutboxConfig(configPath = 'config/council-outbox.yaml') {
  let parsed = {};
  try {
    const raw = await fs.readFile(configPath, 'utf8');
    for (const line of raw.split(/\r?\n/)) {
      const withoutComment = line.replace(/\s+#.*$/, '').trim();
      if (!withoutComment || withoutComment.startsWith('#')) continue;
      const match = withoutComment.match(/^([A-Za-z0-9_-]+):\s*(.*)$/);
      if (!match) continue;
      parsed[match[1]] = stripYamlValue(match[2]);
    }
  } catch (error) {
    if (error?.code !== 'ENOENT') throw error;
  }

  return {
    ...DEFAULT_COUNCIL_OUTBOX_CONFIG,
    ...parsed,
    max_retries: normalizeNumber(parsed.max_retries, DEFAULT_COUNCIL_OUTBOX_CONFIG.max_retries),
    retry_backoff_ms: normalizeNumber(
      parsed.retry_backoff_ms,
      DEFAULT_COUNCIL_OUTBOX_CONFIG.retry_backoff_ms,
    ),
    outbox_flush_interval_ms: normalizeNumber(
      parsed.outbox_flush_interval_ms,
      DEFAULT_COUNCIL_OUTBOX_CONFIG.outbox_flush_interval_ms,
    ),
  };
}

async function ensureParent(filePath) {
  await fs.mkdir(path.dirname(filePath), { recursive: true });
}

async function readJsonFile(filePath, fallback) {
  try {
    return JSON.parse(await fs.readFile(filePath, 'utf8'));
  } catch (error) {
    if (error?.code === 'ENOENT') return structuredClone(fallback);
    throw error;
  }
}

async function writeJsonFileAtomic(filePath, value) {
  await ensureParent(filePath);
  const tmpPath = `${filePath}.${process.pid}.${Date.now()}.tmp`;
  await fs.writeFile(tmpPath, `${JSON.stringify(value, null, 2)}\n`, 'utf8');
  await fs.rename(tmpPath, filePath);
}

function makeId() {
  if (typeof crypto.randomUUID === 'function') return crypto.randomUUID();
  return crypto.randomBytes(16).toString('hex');
}

function extractAckKeys(receipt = {}) {
  return new Set(
    [
      receipt.outbox_id,
      receipt.outboxId,
      receipt.message_id,
      receipt.messageId,
      receipt.correlation_id,
      receipt.correlationId,
      receipt.id,
    ].filter(Boolean),
  );
}

function resultContainsAck(result) {
  if (!result) return null;
  if (result === true) return { ack: true };
  if (result.ack === true || result.ok === true || result.status === 'ack' || result.status === 'acked') {
    return result.receipt && typeof result.receipt === 'object' ? result.receipt : result;
  }
  if (result.receipt && typeof result.receipt === 'object') return result.receipt;
  return null;
}

export class CouncilOutbox {
  constructor(options = {}) {
    this.outboxPath = options.outboxPath ?? options.outbox_path ?? DEFAULT_OUTBOX_PATH;
    this.deadLetterPath =
      options.deadLetterPath ??
      options.dead_letter_path ??
      DEFAULT_COUNCIL_OUTBOX_CONFIG.dead_letter_path;
    this.maxRetries = normalizeNumber(
      options.maxRetries ?? options.max_retries,
      DEFAULT_COUNCIL_OUTBOX_CONFIG.max_retries,
    );
    this.retryBackoffMs = normalizeNumber(
      options.retryBackoffMs ?? options.retry_backoff_ms,
      DEFAULT_COUNCIL_OUTBOX_CONFIG.retry_backoff_ms,
    );
    this.outboxFlushIntervalMs = normalizeNumber(
      options.outboxFlushIntervalMs ?? options.outbox_flush_interval_ms,
      DEFAULT_COUNCIL_OUTBOX_CONFIG.outbox_flush_interval_ms,
    );
    this.now = options.now ?? (() => Date.now());
    this.idFactory = options.idFactory ?? makeId;
    this._state = { version: 1, messages: [], receipts: [] };
    this._deadState = { version: 1, dead_letters: [] };
    this._timer = null;
  }

  async load() {
    const state = await readJsonFile(this.outboxPath, { version: 1, messages: [], receipts: [] });
    const deadState = await readJsonFile(this.deadLetterPath, { version: 1, dead_letters: [] });
    this._state = {
      version: 1,
      messages: Array.isArray(state.messages) ? state.messages : [],
      receipts: Array.isArray(state.receipts) ? state.receipts : [],
    };
    this._deadState = {
      version: 1,
      dead_letters: Array.isArray(deadState.dead_letters) ? deadState.dead_letters : [],
    };
    return this;
  }

  async save() {
    await writeJsonFileAtomic(this.outboxPath, this._state);
    await writeJsonFileAtomic(this.deadLetterPath, this._deadState);
  }

  snapshot() {
    return structuredClone(this._state);
  }

  deadLetterSnapshot() {
    return structuredClone(this._deadState);
  }

  pending() {
    return this._state.messages.filter((message) => ACTIVE_STATUSES.has(message.status));
  }

  acked() {
    return this._state.messages.filter((message) => message.status === 'acked');
  }

  deadLetters() {
    return this._deadState.dead_letters;
  }

  getMessage(idOrCorrelationId) {
    return this._state.messages.find(
      (message) => message.id === idOrCorrelationId || message.correlation_id === idOrCorrelationId,
    );
  }

  async enqueue(post, metadata = {}) {
    const now = this.now();
    const id = post.id ?? post.outbox_id ?? this.idFactory();
    const correlationId = post.correlation_id ?? post.correlationId ?? id;
    const message = {
      id,
      correlation_id: correlationId,
      created_at: isoNow(now),
      updated_at: isoNow(now),
      status: 'queued',
      attempts: 0,
      next_attempt_at: now,
      last_attempt_at: null,
      destination: post.to ?? post.destination ?? null,
      payload: post.payload ?? {
        to: post.to,
        text: post.text,
        priority: post.priority,
      },
      metadata: { ...(post.metadata ?? {}), ...metadata },
      receipts: [],
      last_error: null,
      last_delivery_result: null,
    };
    this._state.messages.push(message);
    await this.save();
    return structuredClone(message);
  }

  _findMessageForReceipt(receipt) {
    const keys = extractAckKeys(receipt);
    return this._state.messages.find(
      (message) => keys.has(message.id) || keys.has(message.correlation_id),
    );
  }

  async acknowledge(receipt) {
    const normalizedReceipt = {
      ...receipt,
      received_at: receipt?.received_at ?? isoNow(this.now()),
    };
    this._state.receipts.push(normalizedReceipt);
    const message = this._findMessageForReceipt(normalizedReceipt);
    if (!message) {
      await this.save();
      return null;
    }

    message.status = 'acked';
    message.updated_at = isoNow(this.now());
    message.receipts.push(normalizedReceipt);
    message.last_error = null;
    await this.save();
    return structuredClone(message);
  }

  async ack(receipt) {
    return this.acknowledge(receipt);
  }

  async recordAck(receipt) {
    return this.acknowledge(receipt);
  }

  _dueMessages(now) {
    return this._state.messages.filter(
      (message) => ACTIVE_STATUSES.has(message.status) && (message.next_attempt_at ?? 0) <= now,
    );
  }

  _backoffDelay(attempts) {
    return this.retryBackoffMs * Math.max(1, attempts);
  }

  async _deadLetter(message, reason) {
    const now = this.now();
    const deadLetter = {
      ...structuredClone(message),
      status: 'dead_lettered',
      dead_lettered_at: isoNow(now),
      dead_letter_reason: reason,
    };
    this._deadState.dead_letters.push(deadLetter);
    this._state.messages = this._state.messages.filter((candidate) => candidate.id !== message.id);
    return deadLetter;
  }

  async flush(deliver) {
    if (typeof deliver !== 'function') {
      throw new TypeError('CouncilOutbox.flush requires a delivery function');
    }

    const flushed = [];
    const dead_lettered = [];
    const now = this.now();

    for (const message of this._dueMessages(now)) {
      message.attempts += 1;
      message.last_attempt_at = now;
      message.updated_at = isoNow(now);
      message.status = 'awaiting_ack';
      message.last_error = null;

      try {
        const result = await deliver(structuredClone(message));
        message.last_delivery_result = result ?? null;
        const ackReceipt = resultContainsAck(result);
        if (ackReceipt) {
          await this.acknowledge({
            ...ackReceipt,
            outbox_id: ackReceipt.outbox_id ?? message.id,
            correlation_id: ackReceipt.correlation_id ?? message.correlation_id,
          });
          flushed.push({ id: message.id, status: 'acked', attempts: message.attempts });
          continue;
        }
        message.last_error = 'missing_ack';
      } catch (error) {
        message.last_error = error?.message ?? String(error);
      }

      if (message.attempts >= this.maxRetries) {
        const deadLetter = await this._deadLetter(message, message.last_error ?? 'max_retries_exhausted');
        dead_lettered.push(deadLetter);
        flushed.push({ id: message.id, status: 'dead_lettered', attempts: message.attempts });
      } else {
        message.next_attempt_at = now + this._backoffDelay(message.attempts);
        flushed.push({ id: message.id, status: message.status, attempts: message.attempts });
      }
    }

    await this.save();
    return { flushed, dead_lettered, pending: this.pending().length, acked: this.acked().length };
  }

  start(deliver) {
    if (this._timer) return this._timer;
    this._timer = setInterval(() => {
      this.flush(deliver).catch(() => {});
    }, this.outboxFlushIntervalMs);
    if (typeof this._timer.unref === 'function') this._timer.unref();
    return this._timer;
  }

  stop() {
    if (this._timer) clearInterval(this._timer);
    this._timer = null;
  }
}

export async function createCouncilOutbox(options = {}) {
  const outbox = new CouncilOutbox(options);
  await outbox.load();
  return outbox;
}

export async function enqueueCouncilPost(outbox, post, metadata) {
  return outbox.enqueue(post, metadata);
}

export async function flushCouncilOutbox(outbox, deliver) {
  return outbox.flush(deliver);
}

export async function ackCouncilOutbox(outbox, receipt) {
  return outbox.acknowledge(receipt);
}
