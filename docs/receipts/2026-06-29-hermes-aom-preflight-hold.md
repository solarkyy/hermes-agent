# Receipt: Hermes/AOM preflight HOLD

Date: 2026-06-29

## Subject

Read-only preflight across Hermes context-budget gates and AOM BDI admission posture.

## Status

HOLD for AOM training/admission. Hermes Gate 4/5 remains acceptable only as warn-only documentation/instrumentation, not enforcement.

## Evidence

- Pi verification: `py_compile` passed for Hermes budget/prompt/CLI files.
- Pi verification: targeted Hermes tests passed: `23 passed, 1 warning`.
- SparkMira was consulted in a fresh thread, not Kyle's protected `6a401ebd...` thread. Fresh conversation id prefix: `6a427796...`.
- SparkMira L1 advisory: treat BDI `bdi_valid: true` / `bdi_score: 1` as HOLD unless calibration/admission fields and authority chain are settled.
- Pi sister falsifier L1 advisory: spawn `sister-b5216b36`; output path `/home/kylej/Desktop/omnios/.omni/sister-spawn/2026-06-29T13-51-29-480Z-sister-b5216b36/stdout.log`.
- AOM latest pointer inspected: `/home/kylej/Desktop/omnios/.omni/aom/bdi-calibration/latest.json` has `bdi_valid: true`, `bdi_score: 1`, and `training_eligible: false`, but no settled `calibration_valid`, `verdict`, or admission receipt path.

## Decision

- Do not launch training.
- Do not admit/promote a body.
- Do not mutate AOM/AOMS state from this preflight.
- Do not treat BDI score success as training authority.
- Keep Hermes Gate 4/5 claims limited to warn-only instrumentation and receipts.

## Next safe action

If continuing, add a read-only AOM admission truth-table check that resolves missing `calibration_valid`, missing `verdict`, or missing admission receipt to `training_eligible: false / HOLD` before any training/admission path can consume BDI fields.
