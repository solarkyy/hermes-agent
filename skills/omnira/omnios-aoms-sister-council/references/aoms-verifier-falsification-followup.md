# AOMS gated follow-up after verifier falsification

Use this reference when an AOMS-reviewed patch passes local gates, is committed/synced, and then a later verifier or remote seat exposes a portability/coverage bug.

## Principle

A verifier failure after a PASS is not embarrassment and not noise. It is new evidence. Preserve the AOMS membrane by treating it as a falsified assumption:

1. Name the failed assumption explicitly.
2. Patch the smallest responsible surface.
3. Re-run local gates that reproduce the failure class.
4. Spawn a tiny follow-up AOMS review if the original bundle required AOMS.
5. Commit only the follow-up path(s), then re-sync and re-verify all seats.

## Tiny follow-up prompt shape

Use L1 advisory sisters, no tools, narrow scope:

```text
Lane: continuity-write
Parent session: <sess_...>
Nonce: <topic>-portability-gpt-YYYYMMDD
Claim ceiling: L1 read-only advisory review of one-file portability follow-up.
Forbidden: stage, commit, push, pull, deploy, restart, mutate files, admit GREEN, authorize execution.

Facts:
- Prior commit passed AOMS and local verification.
- Remote verification failed with <exact error>.
- Cause: <small root cause>.

Patch under review:
- <exact files>
- <exact changed behavior>

Local verification:
- <reproducer now passes>
- <normal test passes>
- <diff-check/discipline gate>

Review hard for:
- new authority/write/path risk
- whether the safe stage set is complete
- whether committing follow-up before release is safer than releasing blocked

Deliverable:
VERDICT: PASS | WATCH | BLOCK
BLOCKERS:
WATCH ITEMS:
SAFE STAGE SET:
REQUIRED COMMAND GATES BEFORE COMMIT:
FINAL ADVICE:
Echo lane, nonce, claim_ceiling, and L1 advisory level.
```

## Example failure class

Remote seats lacked an ignored receipt parent dir, while KJ had it locally. The test passed locally but failed on VPS/EVO with ENOENT. The follow-up created the receipt parent before writing and added a fixture-count tripwire. Sisters both returned PASS with WATCH notes for caller-controlled `--out` and hardcoded fixture count.

## Why this belongs in AOMS

The original AOMS PASS covered the evidence available at that moment. Once a remote verifier falsifies an assumption, the orchestrator may not simply patch and release under the old verdict. A tiny re-review preserves trust without rerunning a full council.