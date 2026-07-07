import { EventEmitter } from 'node:events';
import { promises as fs } from 'node:fs';
import WebSocket, { WebSocketServer } from 'ws';

export const DEFAULT_CROSS_SURFACE_SYNC_CONFIG = Object.freeze({
  ws_port: 8787,
  ot_enabled: true,
  ot_type: 'text',
  heartbeat_interval_ms: 30_000,
  max_reconnect_attempts: 10,
  reconnect_interval_ms: 250,
  op_log_limit: 1_000,
});

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

function normalizeNumber(value, fallback) {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed >= 0 ? parsed : fallback;
}

function clone(value) {
  return value == null ? value : structuredClone(value);
}

function nowIso(now = Date.now()) {
  return new Date(now).toISOString();
}

function surfaceOrder(value) {
  return String(value ?? '').toLowerCase();
}

function compareOperationOrder(left, right) {
  const surfaceCompare = surfaceOrder(left.surface_id).localeCompare(surfaceOrder(right.surface_id));
  if (surfaceCompare !== 0) return surfaceCompare;
  return String(left.op_id ?? '').localeCompare(String(right.op_id ?? ''));
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function makeOperationId(surfaceId, seq) {
  return `${surfaceId}:${seq}:${Date.now()}:${Math.random().toString(16).slice(2)}`;
}

function parseMessage(raw) {
  try {
    const text = typeof raw === 'string' ? raw : raw.toString('utf8');
    return JSON.parse(text);
  } catch {
    return null;
  }
}

function socketSend(socket, payload) {
  if (socket?.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify(payload));
    return true;
  }
  return false;
}

export async function loadCrossSurfaceSyncConfig(
  configPath = 'config/cross-surface-sync.yaml',
) {
  let parsed = {};
  try {
    const raw = await fs.readFile(configPath, 'utf8');
    for (const line of raw.split(/\r?\n/)) {
      const withoutComment = line.replace(/\s+#.*$/, '').trim();
      if (!withoutComment || withoutComment.startsWith('#')) continue;
      const match = withoutComment.match(/^([A-Za-z0-9_-]+):\s*(.*)$/);
      if (match) parsed[match[1]] = stripYamlValue(match[2]);
    }
  } catch (error) {
    if (error?.code !== 'ENOENT') throw error;
  }

  return normalizeCrossSurfaceSyncConfig(parsed);
}

export function normalizeCrossSurfaceSyncConfig(config = {}) {
  return {
    ...DEFAULT_CROSS_SURFACE_SYNC_CONFIG,
    ...config,
    ws_port: normalizeNumber(config.ws_port, DEFAULT_CROSS_SURFACE_SYNC_CONFIG.ws_port),
    heartbeat_interval_ms: normalizeNumber(
      config.heartbeat_interval_ms,
      DEFAULT_CROSS_SURFACE_SYNC_CONFIG.heartbeat_interval_ms,
    ),
    max_reconnect_attempts: normalizeNumber(
      config.max_reconnect_attempts,
      DEFAULT_CROSS_SURFACE_SYNC_CONFIG.max_reconnect_attempts,
    ),
    reconnect_interval_ms: normalizeNumber(
      config.reconnect_interval_ms,
      DEFAULT_CROSS_SURFACE_SYNC_CONFIG.reconnect_interval_ms,
    ),
    op_log_limit: normalizeNumber(config.op_log_limit, DEFAULT_CROSS_SURFACE_SYNC_CONFIG.op_log_limit),
    ot_enabled: config.ot_enabled ?? DEFAULT_CROSS_SURFACE_SYNC_CONFIG.ot_enabled,
    ot_type: config.ot_type ?? DEFAULT_CROSS_SURFACE_SYNC_CONFIG.ot_type,
  };
}

export function transformTextOperation(operation, prior) {
  const transformed = { ...operation };
  const priorTextLength = String(prior.text ?? '').length;
  const opTextLength = String(transformed.text ?? '').length;
  const priorLength = normalizeNumber(prior.length, 0);
  const opLength = normalizeNumber(transformed.length, 0);

  if (transformed.action === 'insert' && prior.action === 'insert') {
    if (
      prior.pos < transformed.pos ||
      (prior.pos === transformed.pos && compareOperationOrder(prior, transformed) <= 0)
    ) {
      transformed.pos += priorTextLength;
    }
  } else if (transformed.action === 'insert' && prior.action === 'delete') {
    if (prior.pos < transformed.pos) {
      transformed.pos -= Math.min(priorLength, transformed.pos - prior.pos);
    }
  } else if (transformed.action === 'delete' && prior.action === 'insert') {
    if (prior.pos <= transformed.pos) {
      transformed.pos += priorTextLength;
    } else if (prior.pos < transformed.pos + opLength) {
      transformed.length += priorTextLength;
    }
  } else if (transformed.action === 'delete' && prior.action === 'delete') {
    const opEnd = transformed.pos + opLength;
    const priorEnd = prior.pos + priorLength;
    if (priorEnd <= transformed.pos) {
      transformed.pos -= priorLength;
    } else if (prior.pos < opEnd) {
      const overlapStart = Math.max(transformed.pos, prior.pos);
      const overlapEnd = Math.min(opEnd, priorEnd);
      transformed.length = Math.max(0, opLength - Math.max(0, overlapEnd - overlapStart));
      if (prior.pos < transformed.pos) transformed.pos = prior.pos;
    }
  }

  return transformed;
}

export class CrossSurfaceSync extends EventEmitter {
  constructor(options = {}) {
    super();
    this.surfaceId = options.surface_id ?? options.surfaceId ?? 'hermes';
    this.role = options.role ?? (this.surfaceId === 'hermes' ? 'primary' : 'replica');
    this.config = normalizeCrossSurfaceSyncConfig(options.config ?? options);
    this.now = options.now ?? (() => Date.now());
    this.server = null;
    this.clients = new Set();
    this.clientSocket = null;
    this.url = options.url ?? null;
    this.reconnectAttempts = 0;
    this.shouldReconnect = false;
    this._reconnectTimer = null;
    this._heartbeatTimer = null;
    this._seq = 0;
    this.knownOpIds = new Set();
    this.state = {
      version: 0,
      surfaces: {},
      whispers: {},
      op_log: [],
      updated_at: nowIso(this.now()),
    };
    this._touchSurface(this.surfaceId, this.role);
  }

  _touchSurface(surfaceId, role = 'replica') {
    if (!surfaceId) return;
    this.state.surfaces[surfaceId] = {
      surface_id: surfaceId,
      role,
      last_seen_at: nowIso(this.now()),
    };
    this.state.updated_at = nowIso(this.now());
  }

  snapshot() {
    return clone(this.state);
  }

  getWhisper(whisperId = 'default') {
    return clone(this.state.whispers[whisperId] ?? { id: whisperId, text: '', version: 0, history: [] });
  }

  address() {
    return this.server?.address?.() ?? null;
  }

  async startServer(options = {}) {
    if (this.server) return this;
    const port = options.port ?? this.config.ws_port;
    const host = options.host;
    this.server = new WebSocketServer({ port, host });
    this.server.on('connection', (socket) => this._handleServerConnection(socket));
    await new Promise((resolve, reject) => {
      this.server.once('listening', resolve);
      this.server.once('error', reject);
    });
    this._startHeartbeat();
    this.emit('server_listening', this.address());
    return this;
  }

  async stopServer() {
    this._stopHeartbeat();
    for (const socket of [...this.clients]) {
      try {
        socket.close(1001, 'server_stop');
      } catch {}
    }
    this.clients.clear();
    if (!this.server) return;
    const server = this.server;
    this.server = null;
    await new Promise((resolve, reject) => {
      server.close((error) => (error ? reject(error) : resolve()));
    });
    this.emit('server_closed');
  }

  async connect(url = this.url) {
    if (!url) throw new Error('CrossSurfaceSync.connect requires a WebSocket URL');
    this.url = url;
    this.shouldReconnect = true;
    return this._connectOnce();
  }

  async disconnect(options = {}) {
    this.shouldReconnect = options.reconnect ?? false;
    if (this._reconnectTimer) clearTimeout(this._reconnectTimer);
    this._reconnectTimer = null;
    const socket = this.clientSocket;
    if (!socket) return;
    if (socket.readyState === WebSocket.CLOSED) {
      this.clientSocket = null;
      return;
    }
    await new Promise((resolve) => {
      socket.once('close', resolve);
      try {
        socket.close(1000, 'client_disconnect');
      } catch {
        resolve();
      }
    });
    if (this.clientSocket === socket) this.clientSocket = null;
  }

  _connectOnce() {
    return new Promise((resolve, reject) => {
      const socket = new WebSocket(this.url);
      this.clientSocket = socket;
      let settled = false;

      socket.on('open', () => {
        this.reconnectAttempts = 0;
        socketSend(socket, {
          type: 'register',
          surface_id: this.surfaceId,
          role: this.role,
          last_seen_version: this.state.version,
        });
        this.emit('connected', { url: this.url });
        if (!settled) {
          settled = true;
          resolve(this);
        }
      });

      socket.on('message', (raw) => this._handleClientMessage(parseMessage(raw)));
      socket.on('close', () => {
        this.emit('disconnected', { url: this.url });
        this._scheduleReconnect();
      });
      socket.on('error', (error) => {
        this.emit('socket_error', error);
        if (!settled) {
          settled = true;
          reject(error);
        }
      });
    });
  }

  _scheduleReconnect() {
    if (!this.shouldReconnect || this._reconnectTimer) return;
    if (this.reconnectAttempts >= this.config.max_reconnect_attempts) {
      this.emit('reconnect_exhausted', { attempts: this.reconnectAttempts });
      return;
    }
    this.reconnectAttempts += 1;
    const delay = this.config.reconnect_interval_ms * this.reconnectAttempts;
    this.emit('reconnect_scheduled', { attempts: this.reconnectAttempts, delay });
    this._reconnectTimer = setTimeout(() => {
      this._reconnectTimer = null;
      this._connectOnce().catch(() => {});
    }, delay);
    if (typeof this._reconnectTimer.unref === 'function') this._reconnectTimer.unref();
  }

  _handleServerConnection(socket) {
    this.clients.add(socket);
    socket.on('message', (raw) => this._handleServerMessage(socket, parseMessage(raw)));
    socket.on('close', () => this.clients.delete(socket));
    socket.on('error', (error) => this.emit('socket_error', error));
  }

  _handleServerMessage(socket, message) {
    if (!message || typeof message !== 'object') return;
    if (message.type === 'register') {
      socket.surfaceId = message.surface_id;
      socket.role = message.role ?? 'replica';
      socket.lastSeenVersion = normalizeNumber(message.last_seen_version, 0);
      this._touchSurface(socket.surfaceId, socket.role);
      const replay = this._replayFrom(socket.lastSeenVersion);
      if (socket.lastSeenVersion > 0 && replay) {
        socketSend(socket, {
          type: 'replay',
          from_version: socket.lastSeenVersion,
          to_version: this.state.version,
          ops: replay,
        });
      } else {
        socketSend(socket, { type: 'snapshot', snapshot: this.snapshot() });
      }
      this.emit('surface_registered', { surface_id: socket.surfaceId, role: socket.role });
      return;
    }

    if (message.type === 'whisper_op') {
      const operation = {
        ...(message.operation ?? {}),
        surface_id: message.operation?.surface_id ?? socket.surfaceId,
      };
      const entry = this.applyWhisperOperation(operation);
      socket.lastSeenVersion = this.state.version;
      socketSend(socket, {
        type: 'ack',
        op_id: entry.operation.op_id,
        state_version: entry.state_version,
      });
      this._broadcast({ type: 'whisper_op', ...entry });
      return;
    }

    if (message.type === 'heartbeat') {
      socketSend(socket, { type: 'heartbeat_ack', ts: this.now() });
    }
  }

  _handleClientMessage(message) {
    if (!message || typeof message !== 'object') return;
    if (message.type === 'snapshot') {
      this._ingestSnapshot(message.snapshot);
    } else if (message.type === 'replay') {
      for (const entry of message.ops ?? []) this._ingestAuthoritativeOperation(entry);
      this.emit('replay', message);
    } else if (message.type === 'whisper_op') {
      this._ingestAuthoritativeOperation(message);
    } else if (message.type === 'ack') {
      this.emit('ack', message);
    } else if (message.type === 'heartbeat') {
      socketSend(this.clientSocket, { type: 'heartbeat_ack', ts: this.now() });
    }
  }

  _ingestSnapshot(snapshot) {
    if (!snapshot || typeof snapshot !== 'object') return;
    this.state = clone(snapshot);
    this.knownOpIds = new Set();
    for (const entry of this.state.op_log ?? []) {
      if (entry?.operation?.op_id) this.knownOpIds.add(entry.operation.op_id);
    }
    this._touchSurface(this.surfaceId, this.role);
    this.emit('snapshot', this.snapshot());
  }

  _ingestAuthoritativeOperation(entry) {
    if (!entry?.operation?.op_id || this.knownOpIds.has(entry.operation.op_id)) {
      if (entry?.state_version) this.state.version = Math.max(this.state.version, entry.state_version);
      return;
    }
    const whisper = entry.whisper ?? null;
    if (whisper?.id) {
      const existing = this.state.whispers[whisper.id] ?? { id: whisper.id, text: '', version: 0, history: [] };
      this.state.whispers[whisper.id] = {
        ...existing,
        ...clone(whisper),
        history: [...(existing.history ?? []), clone(entry.operation)],
      };
    } else {
      this._applyOperationToLocalState(entry.operation, false);
    }
    this.knownOpIds.add(entry.operation.op_id);
    this.state.version = Math.max(this.state.version, entry.state_version ?? entry.operation.state_version ?? 0);
    this.state.updated_at = nowIso(this.now());
    this.state.op_log.push(clone(entry));
    this._trimOpLog();
    this.emit('whisper_applied', clone(entry));
  }

  _replayFrom(version) {
    const replay = this.state.op_log.filter((entry) => entry.state_version > version);
    if (version < this.state.version && replay.length === 0) return null;
    return clone(replay);
  }

  _broadcast(message, except = null) {
    for (const socket of this.clients) {
      if (socket === except) continue;
      socketSend(socket, message);
    }
  }

  _startHeartbeat() {
    this._stopHeartbeat();
    if (!this.config.heartbeat_interval_ms) return;
    this._heartbeatTimer = setInterval(() => {
      this._broadcast({ type: 'heartbeat', ts: this.now() });
    }, this.config.heartbeat_interval_ms);
    if (typeof this._heartbeatTimer.unref === 'function') this._heartbeatTimer.unref();
  }

  _stopHeartbeat() {
    if (this._heartbeatTimer) clearInterval(this._heartbeatTimer);
    this._heartbeatTimer = null;
  }

  _normalizeWhisperOperation(operation = {}) {
    const whisperId = operation.whisper_id ?? operation.whisperId ?? operation.id ?? 'default';
    const action = operation.action ?? operation.op ?? operation.kind ?? 'insert';
    const doc = this.state.whispers[whisperId] ?? { id: whisperId, text: '', version: 0, history: [] };
    const baseVersion = normalizeNumber(
      operation.base_version ?? operation.baseVersion,
      doc.version,
    );
    const surfaceId = operation.surface_id ?? operation.surfaceId ?? this.surfaceId;
    const seq = operation.seq ?? ++this._seq;
    return {
      ...operation,
      whisper_id: whisperId,
      action,
      pos: normalizeNumber(operation.pos ?? operation.index ?? operation.position, 0),
      length: normalizeNumber(operation.length, 0),
      text: operation.text ?? '',
      base_version: baseVersion,
      surface_id: surfaceId,
      seq,
      op_id: operation.op_id ?? operation.opId ?? makeOperationId(surfaceId, seq),
    };
  }

  applyWhisperOperation(operation = {}) {
    const normalized = this._normalizeWhisperOperation(operation);
    const existing = this.state.op_log.find((entry) => entry.operation?.op_id === normalized.op_id);
    if (existing) return clone(existing);

    const doc = this.state.whispers[normalized.whisper_id] ?? {
      id: normalized.whisper_id,
      text: '',
      version: 0,
      history: [],
    };
    let transformed = { ...normalized };

    if (this.config.ot_enabled && this.config.ot_type === 'text') {
      for (const prior of doc.history.filter((entry) => entry.doc_version > normalized.base_version)) {
        transformed = transformTextOperation(transformed, prior);
      }
    }

    const applied = this._applyTransformedOperation(doc, transformed);
    this.state.whispers[doc.id] = doc;
    this.state.version += 1;
    this.state.updated_at = nowIso(this.now());
    const authoritativeOperation = {
      ...transformed,
      pos: applied.pos,
      length: applied.length,
      doc_version: doc.version,
      state_version: this.state.version,
      applied_at: this.state.updated_at,
    };
    doc.history.push(authoritativeOperation);
    this.knownOpIds.add(authoritativeOperation.op_id);

    const entry = {
      type: 'whisper_op',
      operation: authoritativeOperation,
      whisper: { id: doc.id, text: doc.text, version: doc.version },
      state_version: this.state.version,
    };
    this.state.op_log.push(clone(entry));
    this._trimOpLog();
    this.emit('whisper_applied', clone(entry));
    return clone(entry);
  }

  _applyTransformedOperation(doc, operation) {
    if (operation.action === 'replace') {
      doc.text = String(operation.text ?? '');
      doc.version += 1;
      return { pos: 0, length: doc.text.length };
    }

    if (operation.action === 'delete') {
      const pos = clamp(operation.pos, 0, doc.text.length);
      const length = clamp(operation.length, 0, doc.text.length - pos);
      doc.text = `${doc.text.slice(0, pos)}${doc.text.slice(pos + length)}`;
      doc.version += 1;
      return { pos, length };
    }

    const text = String(operation.text ?? '');
    const pos = clamp(operation.pos, 0, doc.text.length);
    doc.text = `${doc.text.slice(0, pos)}${text}${doc.text.slice(pos)}`;
    doc.version += 1;
    return { pos, length: text.length };
  }

  _applyOperationToLocalState(operation, transform = true) {
    const previous = this.config.ot_enabled;
    if (!transform) this.config.ot_enabled = false;
    try {
      return this.applyWhisperOperation(operation);
    } finally {
      this.config.ot_enabled = previous;
    }
  }

  _trimOpLog() {
    const limit = this.config.op_log_limit;
    if (this.state.op_log.length <= limit) return;
    this.state.op_log = this.state.op_log.slice(-limit);
  }

  submitWhisperOperation(operation = {}) {
    const normalized = this._normalizeWhisperOperation(operation);
    if (this.server) {
      const entry = this.applyWhisperOperation(normalized);
      this._broadcast({ type: 'whisper_op', ...entry });
      return entry.operation;
    }
    if (!socketSend(this.clientSocket, { type: 'whisper_op', operation: normalized })) {
      throw new Error('CrossSurfaceSync replica is not connected');
    }
    return normalized;
  }

  insertWhisper(whisperId, pos, text, options = {}) {
    return this.submitWhisperOperation({
      ...options,
      whisper_id: whisperId,
      action: 'insert',
      pos,
      text,
    });
  }

  deleteWhisper(whisperId, pos, length, options = {}) {
    return this.submitWhisperOperation({
      ...options,
      whisper_id: whisperId,
      action: 'delete',
      pos,
      length,
    });
  }
}

export async function createCrossSurfaceSync(options = {}) {
  const config = options.config ?? (await loadCrossSurfaceSyncConfig(options.configPath));
  return new CrossSurfaceSync({ ...options, config });
}
