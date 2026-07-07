# Contamination Remediation Council Pattern — 2026-06-15

**Context:** AOMS clean-source-capped router v0 selections failed a semantic-proxy contamination scan: 8 high-confidence answer-leak/prompt-containment hits and 67 review-level topic overlaps. The remediation required both a design council (what to exclude, how to preserve caps, how to test) and a build/test/re-scan cycle.

## Trigger

A semantic contamination scan returns `BLOCK_TRAINING_EVAL__SEMANTIC_CONTAMINATION_REVIEW_REQUIRED` before any training/eval is authorized.

## Council purpose

Converge on a v1+ remediation design:
1. Hard exclusion list vs semantic firewall
2. Cap feasibility after exclusion
3. Triage of review hits (real risk vs generic topic overlap)
4. Test pyramid for the new router
5. Safe sequence: design → dry-run simulation → implement → test → re-scan → operator gate

## Lens model assignment

| Sister | Model | Voice |
|--------|-------|-------|
| ε | Nemotron Ultra | hard-list / firewall balance |
| θ | Nemotron Ultra | build-safe, test-first |
| α | Nemotron Ultra | hard-list only (audit stance) |
| β | Nemotron Ultra | hard-list only (risk-averse) |
| γ | Nemotron Ultra | both layers |

All were no-tools, `--thinking xhigh`, `--lane mythos`.

## Convergence

- **Hard exclude** the high-confidence signatures (unanimous).
- **Post-exclusion cap simulation** is mandatory — removing samples can push a sister over the source cap; rebalancing must be deterministic and auditable.
- **Fail-fast** if targets can't be met cleanly after exclusion; don't silently undershoot.
- **Review hits** are mostly generic topic overlap; only `answer_leak_review` / `qa_expected_answer_plus_question_terms` outside the high-confidence set warrant promotion.
- **Test pyramid**: unit (exclusion, caps, rebalance), integration (mock scan → router → re-scan zero high-conf), deterministic replay, property-based cap checks.
- **Sequence**: design → dry-run simulation → implement → test → re-scan → operator gate.

## Dry-run simulation command

```python
import json
from pathlib import Path

scan_path = Path('.omni/aoms/training-harvest-lane/semantic-contamination-scan-v0.json')
router_path = Path('.omni/aoms/training-harvest-lane/clean-source-capped-router-design-v0.json')

with open(scan_path) as f:
    scan = json.load(f)
with open(router_path) as f:
    router = json.load(f)

exclude_sigs = {s['signature_sha256']
                for s in scan['proposed_next_router_actions']['auto_exclude_high_confidence_signatures_next_design']}

per_sister = {}
for sister, stats in router['route_stats'].items():
    per_sister[sister] = {
        'total': stats['samples'],
        'sources': dict(stats['source_mix']),
        'exclude_counts': {source: 0 for source in stats['source_mix']},
        'exclude_total': 0,
    }

for hit in scan['findings']['high_confidence_examples']:
    sig = hit['signature_sha256']
    sister = hit['sister']
    source = hit['source']
    if sig in exclude_sigs:
        per_sister[sister]['exclude_counts'][source] += 1
        per_sister[sister]['exclude_total'] += 1

for sister, data in per_sister.items():
    new_total = data['total'] - data['exclude_total']
    new_sources = {}
    for source, count in data['sources'].items():
        new_count = count - data['exclude_counts'].get(source, 0)
        new_sources[source] = new_count
    max_pct = max(new_sources.values()) / new_total if new_total else 0
    print(f"{sister}: after={new_total}, sources={new_sources}, max_pct={max_pct:.4f}")
```

## Implementation checklist

- [ ] Copy v0 router module and test to v1.
- [ ] Add `--exclude-signatures <json-array-file>` argument.
- [ ] Filter excluded signatures in `dedupe_and_eval_filter` before exact-eval exclusion and dedupe.
- [ ] Add `--targets` override for deterministic rebalancing experiments.
- [ ] Validate post-exclusion composition obeys source caps; fail fast if not.
- [ ] Write exclusion list JSON from prior scan report.
- [ ] Update tests for: exclusion applied, v0 backward compatibility, re-scan zero high-confidence hits.
- [ ] Patch the scan script to read `excluded_signatures` and `targets` from the clean-router report so re-scan reconstructs the exact same manifest.
- [ ] Run full router → re-scan pipeline and persist reports + receipt.
- [ ] Update `SESSION-ANCHOR.md` with verdict and gate status.
- [ ] Operator clears `WATCH` if review hits are accepted as false positives.

## Train/eval setup planning follow-up

Once the contamination gate is cleared, the next AOMS council should plan the phase-prep toward training/eval. See `references/train-eval-setup-planning-council-2026-06-15.md` for the template, remaining gates, and NIM silent-failure fallback.

## Key pitfalls

1. **Set serialization in JSON report.** If the exclusion set is stored as a Python `set`, `json.dumps` fails. Store `sorted(exclude_set)` instead.
2. **Scan reconstructs from module, not from report.** The scan script calls `router.build_raw_pool` and `router.dedupe_and_eval_filter` directly. If it ignores the exclusion list, it will reproduce the old hits. Pass exclusions from the report into these functions.
3. **Validation should not make exclusion mandatory when not requested.** v1 must remain backward-compatible with v0 no-exclusion output.
4. **Do not edit the scan JSON verdict.** Document operator clearance of `WATCH` in the markdown receipt and `SESSION-ANCHOR.md`, not by mutating the scan report.
5. **NIM Nemotron Ultra spawns can fail silently.** If sister directories contain only `prompt.md` and no stdout/stderr, the route failed. Fall back to existing council convergence + real manifest/trainer data.
6. **`WATCH` vs `PASS`.** A scanner that flags generic topic overlap will keep returning `WATCH`. Document sister-council triage and require operator clearance; do not silently edit the scan JSON to say `PASS`.
7. **Planning councils must be grounded against real infrastructure.** Sisters may recommend Llama/Qwen/Axolotl or other frontier tooling. The orchestrator must probe EVO/VPS/KjDesk for the actual trainer, model presets, checkpoints, and eval runner before accepting recommendations. See `references/train-eval-setup-planning-grounded-infrastructure-2026-06-15.md`.

## Spawn command used

```bash
export PATH="/home/kylej/.npm-global/bin:/usr/bin:/bin:/usr/local/bin:$PATH"
cd /home/kylej/Desktop/omnios
node tools/pi-sister-spawn.mjs \
  --worker-model nvidia/nemotron-3-ultra-550b-a55b \
  --lane mythos \
  --task-file /tmp/clean-router-v1-sister-council-prompt.md \
  --no-tools --no-audit --no-findings --no-receipt-skeleton \
  --thinking xhigh \
  --timeout 240
```

Run 4–5 parallel background spawns with `terminal(background=true, notify_on_complete=true)`.

## Artifacts produced

- `tools/corpus-foundry/clean-source-capped-router-design-v1.py`
- `tools/tests/corpus-foundry-clean-source-capped-router-design-v1.test.mjs`
- `.omni/aoms/training-harvest-lane/semantic-exclusion-high-confidence-v1.json`
- `.omni/aoms/training-harvest-lane/clean-source-capped-router-design-v1.json`
- `.omni/aoms/training-harvest-lane/semantic-contamination-scan-v1.json`
- `docs/receipts/2026-06-15-aoms-clean-source-capped-router-v1.md`

## Verdict progression

| Stage | Verdict | High-conf hits | Review hits | Notes |
|-------|---------|----------------|-------------|-------|
| v0 scan | `BLOCK_TRAINING_EVAL__SEMANTIC_CONTAMINATION_REVIEW_REQUIRED` | 8 | 67 | 0 exact overlaps |
| v1 scan | `WATCH_TRAINING_EVAL__SEMANTIC_REVIEW_RECOMMENDED` | 0 | 67 | exclusion + cap rebalance |
| operator cleared | `PASS_SEMANTIC_PROXY_SCAN_SOURCE_ONLY__NO_SELECTED_RISKS` | 0 | 67 (triaged) | sister-council accepted as generic topic noise |

## Council synthesis

"Hard deny list for the 8 signatures + semantic firewall as v2 exploration. The router must simulate post-exclusion composition and fail fast if caps breach. The 67 review hits are generic prompt overlap; only answer-leak or expected-answer cases should be promoted to hard exclude. Test thoroughly, re-scan, then gate."

## Operator gate handling

When the re-scan still emits `WATCH` for review hits:
1. Collect sister-council triage of the review set.
2. Present top review cases to operator with reasons.
3. Ask operator to clear, tighten scanner, or manual review.
4. Only update the receipt/anchor to `PASS` after explicit operator clearance.
5. Never edit the scan report's verdict field directly.

## Related

- `references/aoms-operating-manual.md` — lanes, verbs, membrane
- `references/grounded-council-architecture.md` — audit + grounding layers
- `references/aoms-builder-execution-pattern-2026-06-11.md` — builder sister pattern
