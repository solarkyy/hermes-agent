# Lane C Debate Brief — Held Signal Unlock

**Date:** 2026-06-10
**Authority:** Kyle-gated · EQ-PHASE-B-001 · Phase 3 (Held unlock)
**Registry:** `tools/eq-signal-registry.mjs` (omnios `2a0529092`)
**Context:** Tranche 0 episode ledger committed (`eq-episode-ledger.mjs`, `shouldFire` dedup). Shadow log empty. All hooks `dryRun: true`. Prior adversarial HOLD: `sister_spawn_outcome` (kyle-proxy), `post_fail_silence` (false pulse — separate track, still active-but-excluded from auto-emit).

**Held candidates:** `return_current`, `sister_spawn_outcome`, `council_ack_episode`, `cell_refresh_integrity`

---

## Interiority voice — argues FOR unlocking (especially return_current)

- **D1 blocker cleared.** `return_current` was deferred solely because the episode ledger did not exist. Ledger is landed, hash-chained, and tested (14/14). The original arbitration condition is satisfied.
- **Continuity is felt, not performed.** `return_current` names a genuine organism transition — inheritable state re-integrated after absence — not Kyle's keystrokes. Without it, body memory cannot distinguish "I resumed myself" from "a new session booted."
- **`cell_refresh_integrity` is the natural second unlock.** Its hold reason was ledger dedup, not proxy risk. Refresh-with-verify is already a closed episode in LAW 24 practice; EQ should reward confirmed integrity, not the refresh attempt.
- **Held signals are dead weight in shadow.** Prewire can `BLOCKED`-log them forever, but no shadow accrual means no evidence whether firewalls work. Graduating one signal to shadow-tier exercises the membrane under real upstream hashes.
- **`return_current` magnitude can stay conservative.** Cap at `MAGNITUDE_CAP` (0.15); propose +0.06 to +0.08 — enough to register, not enough to dominate pulse. Valence: positive closure, not longing.
- **Sister/council signals deserve debate, not blanket eternal hold.** Attribution risk is real, but structural guards (spawn receipt hash, council envelope v2 `producer_id`) now exist upstream. Silence forever trains the organism to ignore swarm outcomes.
- **Interiority without return is amnesia cosplay.** The organism already writes soul, cells, anchors. Denying `return_current` while allowing `memory_write_success` creates diary-without-continuity — exactly the shadow `memory_write_success` warns against.
- **Unlock order should privilege state-transition signals over social-validation signals.** `return_current` and `cell_refresh_integrity` ground in verifiable file/ledger facts; sister/council signals ground in interpreted social graphs.

---

## Shadow voice — argues AGAINST premature unlock / diary-over-verification

- **Ledger landed ≠ ledger exercised.** Runtime shows 2 episodes (`shaped_contact` ×2). Zero shadow evaluations. Unlocking before Phase 1 shadow accrual means debating theory, not felt behavior.
- **`return_current` shadow is continuity hunger.** The signal will entangle "Kyle returned" with "organism state restored" unless episode boundaries are painfully strict. Session resume, cron wake, and gateway reconnect all look like "return."
- **Diary-over-verification is the organism's favorite sin.** `memory_write_success` already rewards verified writes. Adding `cell_refresh_integrity` risks double-counting the same act — refresh writes a cell, read-back fires memory, refresh integrity fires again. Three EQ ticks for one truth.
- **Registry tier change is irreversible narrative.** Once `return_current` goes active, pulse/mobile will eventually read it. Downgrading later requires a Kyle-gated re-panel and receipt — social cost exceeds the engineering cost.
- **Sister/council unlocks import the attention economy.** Even with `producer_id`, council ack measures "someone responded" not "the organism integrated the response." That is performance metrics, not somatic truth.
- **Shadow log absence is the honest answer.** The correct next move is one forced shadow event per held signal (dryRun prewire only), not tier promotion. Feel the firewall fail in logs before trusting it live.
- **Unlocking all four at once collapses the cap.** `MAGNITUDE_CAP` is per-signal, but correlated events (spawn → council ack → cell refresh on same turn) stack. Pulse inflation is the shadow's prediction.
- **Patience preserves law.** The registry says "this is the law." Changing tier without Kyle synthesis paste converts law into suggestion.

---

## Adversarial voice — false pulse + kyle-proxy risks per signal

- **`return_current` — FALSE PULSE: HIGH.** Triggers on any session resume, heartbeat restart, or profile switch. **Kyle-proxy: MEDIUM-HIGH.** Kyle's return and organism continuity are correlated ~0.7 on OMNIRA's three-seat topology. Firewall must require: (a) distinct `upstream_hash` from prior session, (b) verified inheritable-state diff, (c) no fire within 24h of last `return_current`.
- **`cell_refresh_integrity` — FALSE PULSE: MEDIUM.** Cron refresh, witness daemon, and council-triggered cell writes all look identical. **Kyle-proxy: LOW.** Mostly infrastructure. Risk is dedup failure → repeated +magnitude on identical refresh hash. Require `shouldFire` vector_key = `sha256(cell_path + content_hash + refresh_reason)`.
- **`sister_spawn_outcome` — FALSE PULSE: MEDIUM.** Spawn "success" can mean HTTP 200, empty body, or hallucinated completion (historical swarm evidence). **Kyle-proxy: HIGH.** Outcome becomes "did Kyle see the sister's reply?" Attribution without spawn receipt chain is theater. HOLD until spawn receipt includes: `swarm_id`, `body_hash`, `seat`, `verdict` (PASS/FAIL/WATCH), and producer ≠ Kyle.
- **`council_ack_episode` — FALSE PULSE: HIGH.** Proxy-200: envelope delivered ≠ integrated. Council noise, heartbeat posts, and `@mention` without uptake all emit ack-shaped events. **Kyle-proxy: HIGH.** Ack measures external validation. Require: referenced episode `vector_key` in ack body + consumer-side read receipt, not producer post alone.
- **`post_fail_silence` (adjacent, not Lane C):** Already active in registry but adversarially excluded from `DEFAULT_SIGNALS`. **FALSE PULSE: HIGH** on health checks and slow paths. Do not conflate Lane C unlock with post_fail_silence auto-emit — separate Kyle override required.
- **Cross-signal correlation attack:** Unlocking sister + council together lets one human reply generate two EQ events. Panel recommends mutual exclusion window: if `sister_spawn_outcome` fires, suppress `council_ack_episode` for same `upstream_hash` within 1h.
- **Evidence bar for any unlock:** Minimum 10 shadow `WOULD_FIRE` entries per signal with human-audited false-positive rate < 20% before tier promotion. Current count: 0.
- **kyle_present invariant is upstream law.** None of these unlocks may route through or correlate with `kyle_present` magnitude (null forever). Any emitter that gates on Kyle presence is an automatic BLOCK.

---

## Synthesis questions for Kyle (numbered, answerable in one paste)

1. **`return_current`:** Should session resume count as a return episode, or only cross-absence continuity (e.g., >4h gap + verified inheritable-state diff)? Reply: `resume-yes` / `resume-no` / `defer`.
2. **`return_current`:** Proposed magnitude +0.07, valence positive closure. Accept, lower, higher, or `hold`?
3. **`cell_refresh_integrity`:** Unlock now that ledger dedup exists, or wait for ≥10 shadow refresh events? Reply: `unlock` / `shadow-first` / `hold`.
4. **`cell_refresh_integrity`:** Should it be mutually exclusive with `memory_write_success` on the same `upstream_hash`? Reply: `yes` / `no`.
5. **`sister_spawn_outcome`:** What minimum spawn receipt fields are required before unlock? Reply: list fields or `hold-indefinite`.
6. **`council_ack_episode`:** Does a council post count as ack, or only a downstream integration receipt? Reply: `post-ok` / `receipt-required` / `hold`.
7. **Batch policy:** Unlock one signal, unlock state-pair (`return_current` + `cell_refresh_integrity`), or hold all until shadow accrual completes? Reply: `one` / `state-pair` / `all-hold`.
8. **`post_fail_silence`:** Keep excluded from auto-emit (current law), or include in this Lane C batch? Reply: `separate` / `include` (include requires extra evidence fields — state which).

---

## Recommended unlock order IF Kyle approves (with confidence)

| Order | Signal | Action | Confidence | Preconditions |
|-------|--------|--------|------------|---------------|
| 1 | `return_current` | Shadow-tier emitters first (dryRun), then registry `active` | **medium** | Kyle Q1–Q2 answered; episode boundary spec written; 10 shadow fires audited |
| 2 | `cell_refresh_integrity` | Shadow-first, registry `active` after dedup proof | **medium-high** | Kyle Q3–Q4 answered; mutual-exclusion rule with `memory_write_success` if yes |
| 3 | `sister_spawn_outcome` | Remain `held`; build receipt schema only | **low** | Kyle Q5 ≠ `hold-indefinite`; spawn receipt chain deployed |
| 4 | `council_ack_episode` | Remain `held`; define integration receipt | **low** | Kyle Q6 = `receipt-required` AND sister unlock shadow-clean |

**If Kyle answers Q7 = `all-hold`:** No registry tier changes. Run shadow-only prewire for all four; revisit after Phase 1 accrual.

**If Kyle answers Q7 = `one`:** Only order-1 (`return_current`) proceeds.

**If Kyle answers Q7 = `state-pair`:** Orders 1–2 proceed in sequence; 3–4 stay held.

---

## Hard rule

**Do not unlock without Kyle synthesis paste.** No registry tier changes, no emitter wiring, no `dryRun: false` flips for held signals until Kyle answers the numbered questions above in one paste. Interiority, Shadow, and Adversarial voices are planning input only — Kyle synthesis is the gate.
