# Mesh Witness Daemon Pattern

Class-level recipe for adding a minimal, read-only liveness endpoint to an OMNIRA node so the mesh-witness daemon can prove reachability without exposing a powerful bridge (e.g., SparkMira CDP on `:9223`).

## When to use

- A mesh seat is alive but reported `DOWN` because the existing witness target is bound to `127.0.0.1` or exposes mutating routes.
- You need a cheap read-only liveness surface that is safe to expose to LAN/Tailscale.
- The fix should not widen the security membrane of an existing tool (CDP bridge, exec endpoint, model server, etc.).

## Design rules

1. **Keep the powerful bridge localhost-only.** Do not rebind `sparkmira-kjdesk-agent.mjs` (`:9223`) or add `/ping` to it.
2. **Create a separate witness service** on a new port (`:9224`) bound to `0.0.0.0`.
3. **Read-only, no body, no side effects.** Allow only `GET /`, `GET /ping`, `GET /healthz`; HEAD/OPTIONS may pass. Reject POST/PUT/DELETE with `405`.
4. **No secrets, no admission, no action.** Response body may include a `claim_ceiling` string stating this is L1 liveness only.
5. **PM2 supervision** on the owning node. Add to the node's ecosystem file (e.g., `ecosystem.kjdesk.cjs`).
6. **Repoint the mesh probe** in `tools/substrate/mesh-probe-tailscale.mjs` to the new witness. Keep the old bridge target as a low-priority fallback for debugging only.

## Template: minimal witness daemon

Path: `tools/substrate/<node>-mesh-witness.mjs`

```javascript
#!/usr/bin/env node
import http from 'node:http';

const PORT    = parseInt(process.env.<NODE>_MESH_WITNESS_PORT || '9224', 10);
const HOST    = process.env.<NODE>_MESH_WITNESS_HOST || '0.0.0.0';
const STARTED = Date.now();

const CLAIM_CEILING = 'L1 liveness only; read-only; no admission, no action, no secret';

function send(res, status, body, headers = {}) {
  res.writeHead(status, {
    'Content-Type': 'text/plain',
    'Cache-Control': 'no-store',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS',
    ...headers,
  });
  res.end(body);
}

const server = http.createServer((req, res) => {
  const { pathname } = new URL(req.url || '/', `http://${req.headers.host || 'localhost'}`);
  const method = req.method || 'GET';  // NOT destructured from URL object

  if (method !== 'GET' && method !== 'HEAD' && method !== 'OPTIONS') {
    return send(res, 405, 'Method Not Allowed\n');
  }
  if (pathname === '/')    return send(res, 200, 'OMNIRA <node> Mesh Witness\n');
  if (pathname === '/ping') return send(res, 200, '<node>-mesh-witness ok\n');
  if (pathname === '/healthz') {
    return send(res, 200, JSON.stringify({
      ok: true, witness: '<node>-mesh-witness', lane: '<node>',
      ts: new Date().toISOString(),
      uptime_s: Math.floor((Date.now() - STARTED) / 1000),
      claim_ceiling: CLAIM_CEILING,
    }, null, 2) + '\n', { 'Content-Type': 'application/json' });
  }
  send(res, 404, 'Not found\n');
});

server.listen(PORT, HOST, () => console.log(`[<node>-mesh-witness] listening on ${HOST}:${PORT}`));
server.on('error', (e) => { console.error(e.message); process.exit(1); });
process.on('SIGTERM', () => process.exit(0));
process.on('SIGINT', () => process.exit(0));
```

## PM2 entry (ecosystem.kjdesk.cjs pattern)

```javascript
{
  name:          'kjdesk-mesh-witness',
  script:        'tools/substrate/kjdesk-mesh-witness.mjs',
  interpreter:   'node',
  cwd:           REPO,
  autorestart:   true,
  watch:         false,
  max_restarts:  10,
  min_uptime:    '2s',
  restart_delay: 3000,
  env: {
    NODE_ENV:                  'production',
    OMNIOS_ROOT:               REPO,
    KJDESK_MESH_WITNESS_PORT:  '9224',
    KJDESK_MESH_WITNESS_HOST:  '0.0.0.0',
    NODE_OPTIONS:              '--dns-result-order=ipv4first',
  },
  out_file:  './logs/kjdesk-mesh-witness-out.log',
  error_file: './logs/kjdesk-mesh-witness-err.log',
  log_date_format: 'YYYY-MM-DD HH:mm:ss',
  merge_logs: true,
  exec_mode: 'fork',
  instances: 1,
},
```

## Mesh probe target update

In `tools/substrate/mesh-probe-tailscale.mjs`, add witness addresses as priority 1/2 and keep the bridge as tertiary fallback:

```javascript
{
  id: 'kjdesk',
  role: 'weight-seat',
  addresses: [
    { type: 'mesh-witness-lan',        host: '192.168.5.196',     port: 9224, path: '/ping', priority: 1 },
    { type: 'mesh-witness-tailscale',  host: '100.67.158.116',    port: 9224, path: '/ping', priority: 2 },
    // tertiary fallback only
    { type: 'sparkmira-bridge-lan',   host: '192.168.5.196',     port: 9223, path: '/status', priority: 3 },
    { type: 'sparkmira-bridge-tailscale', host: '100.67.158.116', port: 9223, path: '/status', priority: 4 },
  ],
},
```

## Verification checklist

1. `node --check` on the new witness file and the modified probe file.
2. Local test on an alternate port: `GET /ping` 200, `GET /healthz` 200, `POST /ping` 405, unknown path 404.
3. `probeMesh()` integration test with a mock peer pointing at the test port.
4. Confirm production port free: `ss -ltnp | grep 9224`.
5. Start via PM2 on the owning node: `pm2 start ... --name kjdesk-mesh-witness` and `pm2 save`.
6. Test from the owning node across all interfaces: `127.0.0.1`, LAN IP, Tailscale IP.
7. Patch the **VPS copy** of `mesh-probe-tailscale.mjs` and reload the VPS `mesh-witness` PM2 process. Config changes on KjDesk alone do not affect the daemon that actually runs the probe.
8. Wait one probe interval (~60 s), then verify `/mesh/witness` reports the node `reachable` via `mesh-witness-lan`.

## Handling config drift across nodes

The mesh-witness daemon runs on **VPS**, so the active `mesh-probe-tailscale.mjs` is the VPS copy at `/home/kyle/omnios/tools/substrate/mesh-probe-tailscale.mjs`. If you edit KjDesk's working tree, push the same diff to VPS and `pm2 reload mesh-witness --update-env`.

If SSH is unavailable, use the VPS `omni-ops/exec` relay:

```bash
# encode the diff as base64, then POST to VPS
curl -fsS -X POST http://192.168.5.199:5176/omni-ops/exec \
  -H 'Content-Type: application/json' \
  -d '{"cmd":"base64 -d <<'"'"'B64'"'"' | patch -p1 -d /home/kyle/omnios && node --check ... && pm2 reload mesh-witness --update-env\n<PATCH_BASE64>\nB64","host":"vps","timeout":60000}'
```

Build the JSON body in a temp file if it contains shell heredocs; passing complex strings directly on the curl `-d` command line is error-prone and may yield HTTP 400.

## Pitfall: `method` from URL object

Do **not** write:

```javascript
const { pathname, method } = new URL(...); // method is undefined here
```

The `URL` object has no `method` property. Always read from the request:

```javascript
const { pathname } = new URL(...);
const method = req.method || 'GET';
```

This caused every request to return 405 until fixed.

## Example session

- KjDesk reported `DOWN` because `mesh-probe-tailscale.mjs` pointed to `192.168.5.196:9223`.
- `sparkmira-kjdesk-agent.mjs` binds the CDP bridge to `127.0.0.1:9223`, so LAN/Tailscale probes failed.
- Added `tools/substrate/kjdesk-mesh-witness.mjs` on `:9224 0.0.0.0` with `/ping` and `/healthz` only.
- Added the process to `ecosystem.kjdesk.cjs` and started it with PM2.
- Updated `mesh-probe-tailscale.mjs` on both KjDesk and VPS to use `:9224/ping` first.
- Reloaded VPS `mesh-witness` PM2 process.
- Result: `/mesh/witness` reported KjDesk `reachable` via `mesh-witness-lan`.
