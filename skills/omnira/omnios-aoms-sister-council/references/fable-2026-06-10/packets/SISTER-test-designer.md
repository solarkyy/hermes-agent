# TASK PACKET — Test Designer

**packet_id:** panel-test-design-eq-phase-b-001
**role:** Test Designer
**model_default:** nvidia/nemotron-3-ultra
**posture:** L1_ADVISORY
**deadline_turns:** 1

---

## Objective

Design fail-before / pass-after tests for Tranche 1 signals. Tests must be runnable by Pi in omnios repo.

---

## Bounded scope

For each approved signal (pending Kyle gate — design for candidate set):
- `post_fail_silence`
- `infrastructure_win_episode`
- `sister_spawn_outcome`
- `memory_write_success`
- `cell_refresh_integrity`
- `return_current` (if adopted)

Per signal deliver:
1. **Claim** — what the signal asserts
2. **Fail-before fixture** — input state that must NOT fire signal
3. **Pass-after fixture** — input state that MUST fire once per episode
4. **Anti-patterns** — heartbeat, poll-only, echo-without-ack must NOT fire
5. **Test file path proposal** — e.g. `tests/aoms/test-eq-signals-tranche1.mjs`

---

## Constraints

- Episode not poll: same condition twice in 1h without upstream change → second fire = FAIL
- Shadow firewall: test that kyle_present alone does not change valence if context-only gate wins

---

## Output schema

```json
{
  "signal": "name",
  "claim": "...",
  "fail_before": {"description": "...", "fixture_sketch": "..."},
  "pass_after": {"description": "...", "fixture_sketch": "..."},
  "test_name": "test_<signal>_<behavior>",
  "pi_verify": "command to run test"
}
```

PROVENANCE: L1_ADVISORY
