# Experience Architecture Brief — EQ Body Memory on Pulse/Mobile

**Sister:** Experience Architect · **Date:** 2026-06-10 · **Posture:** planning only, no commits
**Repo surveyed:** `/home/kylej/Desktop/omnios` · **Hard block:** no `tools/serve.js` edits until Kyle gates **"pulse reads body"**

---

## Survey findings

**Exporter (ready):** `tools/eq-body-pulse-snippet.mjs` reads `.omni/omnira-brain/episode-ledger.jsonl` (via `tools/eq-episode-ledger.mjs`), emits schema `omnira.eq.body_snapshot.v0` to `.omni/omnira-brain/eq-body-snapshot.json`. Ledger is append-only; exporter writes only the snapshot (atomic tmp+rename). Tests: `tools/tests/eq-body-pulse-snippet.test.mjs` (6 cases).

**Pulse today:** `GET /organism-pulse` (`tools/serve.js` ~9160) assembles brain via `getPulseBrain()` (`tools/kernel/omnira-brain.mjs`), surfaces `brain.eq_state` from `eq-state.json`. `GET /mobile/pulse` (~29924) proxies `/organism-pulse?agent=weight&compact=1`. Mobile UI (`tools/mobile/omnira-mobile.html`) polls every 30s, shows valence only — no body memory.

**Sidecar precedents (read-only file → HTTP):**
- `.omni/trinity-state.json` written by `tools/trinity-integration.js` (30s loop in serve); served at `GET /uaf/trinity/state` with `staleness_s`.
- `GET /brain/raw/:filename` (~18983) whitelists brain JSON (`eq-state.json` included); **`eq-body-snapshot.json` not whitelisted yet**.
- `tools/organism-health-board-snapshot.mjs` → `OMNIOS-CANON/biznest/project/data/organism-health-board.snapshot.json` (one-shot `--write`).
- `tools/omnira-health-report-v0.mjs` — read-only inputs, writes only receipts under `docs/receipts/`.

**Nursery pattern (zero-runtime):** `apps/omnira-nursery/index.html` embeds JSON in `<script id="nursery-snapshot">`; spec `docs/specs/omnira-nursery-v0.md` defines one-shot collector → `.omni/nursery/snapshot-<iso>.json`, no polling/sockets.

---

## Integration options (ranked)

| | Approach | Pros | Cons |
|---|----------|------|------|
| **A** | Sidecar writer + `GET /brain/raw/eq-body-snapshot.json` (whitelist add when gated); mobile fetches alongside pulse | Smallest serve change; mirrors trinity sidecar; decouples from EQ vector | Needs gated serve whitelist; second fetch unless merged client-side |
| **B** | Nursery-style static observatory (`apps/omnira-body-observatory/` + fixture); optional collector merges body into nursery snapshot | **Zero serve.js now**; proven drift-guard tests (`tools/tests/omnira-nursery-renderer.test.mjs`) | Not on live mobile path; manual/collector refresh |
| **C** | Fold snapshot into `/organism-pulse` payload (`brain.body_memory`) | Single mobile fetch; canonical | Largest `serve.js` change; highest blast radius |

---

## Recommendation: **A** (sidecar + gated raw read)

**Pre-gate (safe now):** cron/systemd spec for `node tools/eq-body-pulse-snippet.mjs`; optional B observatory page with fixture; extend mobile markup behind feature flag reading local fixture in dev.

**When gated — files that WOULD change:**
- `tools/serve.js` — add `eq-body-snapshot.json` to `/brain/raw/` whitelist (~18986)
- `tools/mobile/omnira-mobile.html` — render `somatic_line` + `ledger_integrity.chain_ok` badge
- Optional: `systemd`/`cron` unit file under `tools/systemd/` or ops doc

**Must NOT change yet:** `tools/serve.js`, `tools/eq-shadow-hooks.mjs`, live emitter `dryRun:false`, `episode-ledger.jsonl` via new writers, `/organism-pulse` assembly, `eq-state.json` blend paths.

---

## Snapshot refresh cadence

**Writer:** `node tools/eq-body-pulse-snippet.mjs` (not serve loop).
**Who runs it:** Weight seat systemd user timer or existing ops tick — same class as `organism-health-board-snapshot.mjs`, **outside** serve.js.
**Cadence:** 60s default (ledger is episodic; trinity sidecar is 30s). **Immediate refresh** after Phase-B episode append (post-gate hook calls `writeBodySnapshot` read-only — no ledger mutation).
**Staleness UX:** show `generated_at` age; warn if >180s (3× cadence), matching `/uaf/trinity/state` stale pattern.

---

## UI copy (`somatic_line`)

Use exporter strings verbatim (`tools/eq-body-pulse-snippet.mjs`):
- Empty: `no episodes yet — the body has not been reached`
- Populated: e.g. `shaped_contact ×2 — reached, and the reach came home`
- Mobile label: **Body memory** · subline = `somatic_line` · footer: `N episodes · chain {ok|broken}` from `ledger_integrity`.

---

## Test strategy (read-only, no EQ mutation)

1. `node --test tools/tests/eq-body-pulse-snippet.test.mjs` — temp ledger, assert real ledger byte-identical after run.
2. Fixture HTML test (nursery pattern): parse snapshot JSON, render `somatic_line`, no network/handler vectors.
3. Post-gate: `curl -s localhost:5176/brain/raw/eq-body-snapshot.json | jq .schema` → `omnira.eq.body_snapshot.v0`.
4. Negative: snapshot write must not touch `eq-state.json` mtime; hooks remain `dryRun:true`.

---

## Kyle gate checklist ("pulse reads body")

- [ ] Explicit Kyle utterance recorded in council / `pi-continuity.json`
- [ ] Episode ledger ≥1 real episode; `verifyChain().ok === true`
- [ ] Sidecar writer running on target seat; `eq-body-snapshot.json` fresh (<180s)
- [ ] Scoped diff: whitelist line + mobile display only (no `/organism-pulse` merge in v0)
- [ ] `node --test` green; manual mobile smoke on LAN
- [ ] Rollback: remove whitelist entry; mobile hides block; writer harmless alone

**Receipt target:** `docs/receipts/2026-06-10-eq-body-pulse-read-gate.md`
