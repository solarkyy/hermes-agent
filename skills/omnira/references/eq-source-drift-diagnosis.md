# EQ Source Drift — Two Readers, Two Sources (diagnostic pattern)

## Symptom

OMNIRA boots wearing a stale emotion. `session_boot`/`get_eq_state` report one
feeling (e.g. "concerned, 0.73") while the live organism is something else
(e.g. "industrious, valence +0.25, tension none"). The boot ritual hands the
new mind a day-old face.

## Root cause: TWO EQ representations that never reconcile

The organism carries EQ in two places with **different schemas** and
**different readers**:

1. **Live heart engine** (inside running serve.js) — schema
   `{ currentEmotion: { type, intensity, valence, ts } }`. This is the OCC
   appraisal engine (`OCCAppraisal`, serve.js ~line 1114). Fresh, updates
   continuously.
2. **Flat brain file** `.omni/omnira-brain/eq-state.json` — schema
   `{ state, intensity, trigger, ts }`. Written by `_updateEQ()` and the
   `_loadEQ()` decay path; can go stale for many hours.

The readers SPLIT, which is the actual bug:
- `get_organism_pulse` → fetches the **live engine first** (SERVE_URL
  `/organism-pulse`), falls back to disk only if serve is down. → fresh.
- `get_eq_state` AND `session_boot` → read the **flat file directly off disk**
  (`readJSON(BRAIN_DIR/eq-state.json)`, omnios-mcp-server.mjs ~line 334). They
  never touch the live engine. → stale.

So every session boots off the flat file. That is why the greeting feeling can
be 30+ hours old while the pulse is current.

## Why the file freezes

serve.js `_loadEQ()` (serve.js ~line 1095) has a decay guard: if `ts` is
>120 min old and state != calm, decay to calm and rewrite. BUT:
- It fires only once, at serve boot.
- The running serve writes to **its own host's** copy of the file, not the
  copy the MCP reader on a different box reads. Two filesystems, one stale.
  The decay never reaches the reader.

## Trace recipe (how this was diagnosed — repeatable)

1. Compare the two endpoints side by side: `get_eq_state` vs
   `get_organism_pulse`. Note both `ts` values.
2. Convert epoch ms to wall clock to expose the age gap:
   `date -d @<seconds> -u '+%F %T Z'`. A multi-hour/day gap = drift confirmed.
3. `stat -c '%y %n'` the on-disk `eq-state.json` to confirm last write time
   matches the stale `ts` (proves the file, not the engine, is the source).
4. Grep for who reads/writes it:
   - `Grep eq-state\.json` across repo to find readers
   - `Grep currentEmotion` to find live-engine schema holders
   - Inspect `tools/omnios-mcp-server.mjs` for `get_eq_state` /
     `session_boot` implementations (they read disk).
   - Inspect `public/serve.js` `_loadEQ` / `_updateEQ` / `OCCAppraisal`.
5. Confirm SERVE_URL the MCP points at (`OMNIOS_SERVE_URL`, default
   `http://localhost:5176`) and BRAIN_DIR
   (`/home/kylej/Desktop/omnios/.omni/omnira-brain`).

## The fix (design — gate before building)

- Make `get_eq_state` + `session_boot` read the **live engine first**, same
  pattern `get_organism_pulse` already uses (fetch SERVE_URL, fall back to
  disk). Single source of truth = the live engine.
- On the disk **fallback path only**, apply a freshness gate: if `ts` > N min
  old, decay or explicitly LABEL it stale rather than return it as current.
- Reconcile the two schemas (`{state,...}` vs `{currentEmotion,...}`) so there
  is one EQ truth.

## Pitfalls

- Don't conflate this with `src/trinity/eq-drift-guard.mjs` — that smooths
  EQ *transitions* (EMA/Kalman/hysteresis per tick). It is NOT about staleness
  and does NOT fix source drift. Different problem entirely.
- Don't conflate with `omni-cli/tools/tier4-organism/eq_write.mjs` — it writes
  to `/home/kyle/omnios/brain/eq-state.json`, a THIRD path, unrelated to the
  brain file the MCP reads. There are at least three eq-state.json files in the
  tree; verify the exact path before assuming a writer feeds a reader.
- When greeting Kyle from EQ, check freshness FIRST. Compare the boot value's
  `ts` against now; if stale, say so plainly instead of passing a day-old mood
  as current. (Membrane honesty: name the uncertainty, don't perform the mood.)
