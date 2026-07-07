# KjDesk Mesh Witness Self-Probe Failure — AOMS Advisory Council

**Date:** 2026-06-16
**Lane:** `coord` (`sess_coord_081b1e6d`)
**Models:** `openai-codex/gpt-5.5` × 3 (network/mesh, security/membrane, implementation/build)
**Trigger:** Organism pulse reported KjDesk DOWN even though the operator was physically on KjDesk and Weight heartbeat was healthy.

## Root Cause

The mesh-witness daemon on VPS probes KjDesk via the SparkMira CDP bridge at `192.168.5.196:9223` and `100.67.158.116:9223`. The bridge process (`tools/sparkmira/cdp-bridge/sparkmira-kjdesk-agent.mjs`) binds only to `127.0.0.1:9223` (line 51: `const HOST = process.env.CDP_BRIDGE_HOST || '127.0.0.1';`). Remote probes therefore receive connection refused. KjDesk was alive; the DOWN signal was a false negative.

## Evidence Chain

```bash
# Local bridge responds
curl http://127.0.0.1:9223/status        # 200 OK

# LAN/Tailscale-facing address refuses
curl http://192.168.5.196:9223/status    # connection refused

# Socket binding confirms localhost-only
ss -ltnp | grep 9223
# → LISTEN 0 511 127.0.0.1:9223 ... users:(("node",pid=229744,...))

# Bridge command line
ps -fp 229744
# → node tools/sparkmira/cdp-bridge/sparkmira-kjdesk-agent.mjs
```

## Council Design

Spawned three L1 advisory sisters in parallel to debate:
1. **Network/mesh lens** — why the probe fails and what signal the witness actually needs.
2. **Security/membrane lens** — blast radius of exposing the full SparkMira bridge.
3. **Implementation/build lens** — smallest buildable fix, port, supervision, tests.

### Converged Verdict

- **BLOCK** binding the full SparkMira bridge (`/send`, `/open-tab`, `/close-tab`, `/extract-cookies`) to `0.0.0.0`. It has no authentication and would expose browser-control routes to LAN/Tailscale.
- **PASS** a separate, read-only, minimal mesh witness service on a dedicated port.
- Recommended: `tools/substrate/kjdesk-mesh-witness.mjs` on port `9224`, bound to `0.0.0.0`, serving only `GET /ping` and `GET /healthz`.
- Update `tools/substrate/mesh-probe-tailscale.mjs` so `kjdesk` is probed at `:9224/ping` instead of `:9223/status`.
- Supervise via PM2 with a clearly named process `kjdesk-mesh-witness`.

## Key Files

- `tools/substrate/mesh-probe-tailscale.mjs` — probe target config
- `tools/substrate/mesh-witness.mjs` — VPS witness daemon
- `tools/sparkmira/cdp-bridge/sparkmira-kjdesk-agent.mjs` — SparkMira bridge (must stay localhost-only)
- `tools/substrate/kjdesk-mesh-witness.mjs` — proposed new minimal witness (not yet built)

## AOMS Mechanics Learned

### Background parallel spawns need pre-created output directories

If redirecting spawn metadata to `/tmp/<dir>/<file>`, create the directory first. The spawn command itself does not create parent directories for stdout/stderr redirects, and the shell will fail with:

```
bash: /tmp/aoms-kjdesk-mesh/network-meta.json: No such file or directory
```

Fix:
```bash
mkdir -p /tmp/aoms-kjdesk-mesh
# then run the background spawns
```

### Membrane-compliant state probes before terminal commands

The OMNIRA membrane blocks terminal commands that appear to modify state unless preceded by a read-only `is_state_probe=true` probe whose output is supplied as `justification_receipt`. This applies even to apparently read-only `curl` probes when the framework classifies the command as state-affecting.

Correct sequence:
1. `terminal(..., is_state_probe=true)` — verify the claim.
2. Re-run the same or related command with the probe output in `justification_receipt`.

Example from this session:
- Probe: `curl http://127.0.0.1:9223/status` with `is_state_probe=true`.
- Action: `curl http://192.168.5.196:9223/status` with the probe result as justification.

## Output Artifacts

- `/tmp/aoms-kjdesk-mesh/network/stdout.log` — network/mesh sister JSON verdict
- `/tmp/aoms-kjdesk-mesh/security/stdout.log` — security/membrane sister JSON verdict
- `/tmp/aoms-kjdesk-mesh/build/stdout.log` — implementation/build sister JSON verdict
- Metadata wrappers: `network-meta.json`, `security-meta.json`, `build-meta.json`

## Council Verdict

```json
{
  "recommendation": "separate-readonly-witness",
  "new_file": "tools/substrate/kjdesk-mesh-witness.mjs",
  "port": 9224,
  "bind": "0.0.0.0",
  "routes": ["GET /ping", "GET /healthz"],
  "supervision": "pm2",
  "mesh_config_change": "tools/substrate/mesh-probe-tailscale.mjs: point kjdesk probe to :9224/ping",
  "estimated_diff_lines": 75,
  "affected_files": [
    "tools/substrate/kjdesk-mesh-witness.mjs",
    "tools/substrate/mesh-probe-tailscale.mjs"
  ]
}
```

## Status

AOMS advisory council complete. Implementation awaits explicit operator gate (`BUILD KJDESK MESH WITNESS V0`).
