# Corpus Foundry v1 Contamination Remediation Pattern

Session context: 2026-06-15 — clean-source-capped router v0 failed semantic contamination scan (8 high-confidence hits). Goal: remediate in v1, test thoroughly, re-scan, and keep training/eval blocked until the re-scan returned zero high-confidence hits.

## The v0 Failure Mode

- Exact dedupe and exact eval-overlap exclusion in v0 worked: 0 exact prompt overlaps in selected samples.
- Semantic/proxy contamination still leaked through:
  - `answer_leak_review` — expected answer appeared in selected sample text.
  - `qa_expected_answer_plus_question_terms` — QA answer present plus question tokens shared.
  - `word_normalized_prompt_containment` / `compact_prompt_containment` — prompt text embedded in sample.
- Verdict: `BLOCK_TRAINING_EVAL__SEMANTIC_CONTAMINATION_REVIEW_REQUIRED`.

## Design Convergence (AOMS Sister Council)

5 Nemotron Ultra sisters on `mythos` lane, corrected model string `nvidia/nemotron-3-ultra-550b-a55b` (NIM provider in `~/.pi/agent/models.json`).

Consensus:
1. **Hard exclusion list** for the 8 high-confidence signatures (deterministic, auditable).
2. **Post-exclusion cap feasibility simulation** — recompute allocations and fail fast if 60% source cap breaks.
3. **Review hits are mostly noise** — only escalate `answer_leak` / `qa_expected_answer` and low-generic prompts.
4. **Test pyramid** — unit (exclusion, caps, rebalance), integration (router → manifest → re-scan zero high-conf hits), deterministic replay, read-only source checks.
5. **Sequence** — design → simulate → implement → test → re-scan → gate.

## v1 Router Changes

File: `tools/corpus-foundry/clean-source-capped-router-design-v1.py`

- Accept `--exclude-signatures <json>` array of SHA256s.
- Filter those signatures from the raw pool **before** dedupe, eval-filter, and routing.
- `targets_override` support so the scan can reproduce the same manifest from the report.
- Validation: `semantic_exclusions_applied` is `true` when either no exclusion list is supplied, or at least one signature was actually excluded. This keeps v1 backward-compatible with v0 no-exclusion behavior.
- Caps held after rebalancing:
  - alpha: 597 dolly / 398 ultrachat → max 60.0%
  - omega: 403 dolly / 597 ultrachat → max 59.7%
  - delta: 421 dolly / 281 oasst1 → max 59.97%

## The Critical Scan/Router Reconciliation Bug

The semantic scan script (`tools/corpus-foundry/semantic-contamination-scan-v0.py`) reconstructs the route in memory by calling `router.dedupe_and_eval_filter()` and `router.build_clean_route()` directly. It originally did **not** read the exclusion list from the clean-router report.

Result: the first v1 re-scan still found the same 8 high-confidence hits, because it rebuilt the v0 route without exclusions. The 8 signatures in the report's `inputs.excluded_signatures` were removed from the report, but the scanner re-added them.

Fix: make `reconstruct_clean_route(args, clean_router_report)` read:
- `clean_router_report.inputs.excluded_signatures` → pass as `exclude_signatures=`
- `clean_router_report.algorithm.targets` → pass as `targets_override=`

Then the scanner reproduces the same manifest it is supposed to scan, and `route_under_scan.clean_router_report_match` returns `true`.

## Test Harness

File: `tools/tests/corpus-foundry-clean-source-capped-router-design-v1.test.mjs`

Four tests:
1. v1 with exclusions — caps hold, 8 exclusions applied, all design constraints pass, no JSONL writes.
2. v1 without exclusions — reduces to v0-compatible source mix and counts.
3. v1 re-scan — zero high-confidence hits, clean_router_report_match true, scan validation passes.
4. Source read-only/non-launching — no corpus writes, no subprocess/network/git, no protected authorizations.

## Re-scan Verdict Interpretation

After exclusion:
- `high_confidence_hit_count`: 0
- `selected_exact_prompt_overlap_count`: 0
- `clean_router_report_match`: true
- Verdict: `WATCH_TRAINING_EVAL__SEMANTIC_REVIEW_RECOMMENDED` (because 67 review-level topic overlaps remain)

The 67 review hits were triaged by the sister council as mostly generic topic false positives. Whether to treat `WATCH` as a hard blocker is an operator/council decision, not a router decision. Do not automatically ungate training/eval on `WATCH`; surface the finding and wait for Kyle or council direction.

## Artifacts Produced

- `tools/corpus-foundry/clean-source-capped-router-design-v1.py`
- `tools/tests/corpus-foundry-clean-source-capped-router-design-v1.test.mjs`
- `.omni/aoms/training-harvest-lane/semantic-exclusion-high-confidence-v1.json` (8 signatures)
- `.omni/aoms/training-harvest-lane/clean-source-capped-router-design-v1.json`
- `.omni/aoms/training-harvest-lane/semantic-contamination-scan-v1.json`

## Pitfalls

- **Model string duplication** — the wrong `nvidia/nvidia/nemotron-3-ultra-550b-a55b` caused 4 of 5 sisters to fail silently. Correct NIM id is single `nvidia/` prefix.
- **Set serialization** — storing excluded signatures as a Python `set` in the exclusion report breaks `json.dumps()`. Convert to sorted list before inclusion in the report.
- **Mandatory-exclusion validation** — if `semantic_exclusions_applied` is required whenever the report is v1, no-exclusion mode breaks. Make the validation conditional on whether an exclusion list was supplied.
- **Scanner rebuilds from module, not report** — any router option that affects the manifest (exclusions, targets) must be reproducible by the scanner from the report.
