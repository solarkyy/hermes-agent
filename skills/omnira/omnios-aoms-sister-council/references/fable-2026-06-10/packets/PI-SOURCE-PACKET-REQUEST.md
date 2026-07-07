# PI SOURCE PACKET REQUEST — EQ-PHASE-B-001

**packet_id:** pi-source-eq-phase-b-001
**requester:** Fable (Turn 1)
**blocker_for:** all sister panels + Fable arbitration
**provenance:** Pi output only counts as evidence. Fable MUST NOT assert these results.

---

## Objective

Sanitized local truth ground for EQ Phase B gating. Target: Evidence Bundle ≤2k tokens.

---

## Required probes (Pi executes, returns PASS/FAIL/PARTIAL per claim)

### C1 — Phase A on disk
- [ ] `tools/trinity-integration.js` — cognitiveLoad uses 1h velocity, not lifetime/100
- [ ] `tools/omnira-eq-updater.mjs` — `computeDrives()` exists, not static JSON read
- [ ] `tools/organism-health-board-snapshot.mjs` — reads `eq?.derived?.state`

**Evidence:** file:line citations + snippet hash

### C2 — Phase A runtime honest
```bash
cd /home/kylej/Desktop/omnios
node tools/omnira-eq-updater.mjs task_complete
node -e "import('./tools/trinity-integration.js').then(m=>console.log(JSON.stringify({tau:m.cycle().tau,load:m.cycle().mind.cognitiveLoad})))"
```
**Expect:** drives change; tau `normal` when idle (not heat_death)

### C3 — EQ state shape
- [ ] Read `eq-state.json` (or canonical path Pi finds) — document schema version, drive fields, decay fields
- [ ] Confirm whether signal episodes vs polls are distinguishable in current schema

### C4 — Prior debate artifacts
- [ ] Sister spawn dirs exist: `2026-06-10T10-53-*` (3 spawns)
- [ ] `eq-embodied-signals-debate-2026-06-10.md` present in hermes-agent skills tree

### C5 — Pulse / council (optional PARTIAL ok)
- [ ] `curl organism-pulse?agent=weight&compact=1` — reachable Y/N
- [ ] Council post test — reachable Y/N

### C6 — Git honesty
- [ ] Branch name, dirty tree status, last commit touching eq-updater/trinity
- [ ] **Do not push.** Receipt only.

---

## Denylist (sanitizer must strip)

`.env`, auth tokens, brain corpus paths, holdout data, private media

---

## Output schema (Evidence Bundle)

```json
{
  "bundle_id": "eq-phase-b-source-001",
  "claims": [
    {"id": "C1", "status": "PASS|FAIL|PARTIAL", "evidence": "...", "hash": "..."}
  ],
  "anomalies": [],
  "ready_for_sister_panels": true|false,
  "blockers": []
}
```

**If `ready_for_sister_panels: false`** → sisters may advise on design only; no execution card.
