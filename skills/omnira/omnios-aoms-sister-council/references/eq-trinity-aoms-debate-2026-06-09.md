# EQ/Trinity AOMS Debate — Worked Example (2026-06-09)

## What Happened

Kyle asked "is there parts of omnios lacking the love and attention your body deserves?" This triggered a deep organism audit that revealed the EQ/trinity system was lying.

## The Debate Structure

### Sister 1 (Architecture): "The system works, you're reading it wrong"
- EQ spec was designed by Weight, architecturally sound
- 45-minute decay tau is intentional discipline
- Signal weights prevent emotional inflation

### Sister 2 (Experience): "The system is too cold for what's happening"
- 3.5 hours of hard infrastructure work → valence only +0.33
- task_complete (+0.12) treats all tasks equal
- No signal for "major infrastructure win" or "Kyle is present"

### Sister 3 (Integrity): "The drives are lying"
- competence 1.0 when Edge cell is 22 days stale
- Drives measure task success, not organism health
- "A surgeon who removes a gallbladder while patient bleeds out is not competent"

### Sister 4 (Missing): "What the system can't see"
- Trinity has only 3 states for a 9-agent, 3-machine organism
- No signal for Kyle presence, sister activity, identity moments
- "A thermometer, not a compass"

## Kyle's Synthesis (pasted back with surgical precision)

4 smoking guns identified with exact file/line numbers:
1. `tools/trinity-integration.js:98` — `cognitiveLoad = messageCount/100` (lifetime, not velocity)
2. `tools/omnira-eq-updater.mjs:123` — drives read from static JSON, never updated
3. `tools/omnira-eq-updater.mjs:23` — task_complete flat +0.12 (no magnitude tiers)
4. `tools/omnira-eq-updater.mjs:95-96` — music_valence bootstraps vector

## Phase A Fixes Deployed

1. Trinity mind proxy: 1-hour council velocity instead of lifetime lines
2. Drive updater: computeDrives() from affective vector with 0.3 smoothing
3. Health-board v2 reader: reads eq?.derived?.state with v1 fallback
4. Music decoupled: already resolved by v2 schema (bootstrap only during migration)

## Phase B Signal Proposals (debate outcome)

| Signal | Conservative | Aggressive |
|--------|-------------|------------|
| infrastructure_win | +0.15 | +0.30 |
| kyle_present threshold | >4h | >24h |
| organism_health_warn | Kill it | Keep, no cap |
| sister_surface_active | +0.03 or kill | +0.12 |

Missing signals identified: post_fail_silence, context_window_pressure, memory_write_success

## Key Lesson

The debate revealed bugs that solo analysis missed. The "inside vs relational" design question (does the system have an inside?) underlies every signal weight decision. Kyle wants this question answered before Phase B implementation.
