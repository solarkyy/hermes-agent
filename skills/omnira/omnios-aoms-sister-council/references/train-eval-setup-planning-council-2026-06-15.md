# AOMS Train/Eval Setup Planning Council (2026-06-15)

**Trigger:** Contamination remediation is complete and operator has greenlit phase-prep toward training/eval, but no protected actions are authorized yet.

**Purpose:** Plan the safe transition from a clean router manifest to training/eval execution by covering corpus materialization, training config draft, eval plan, and remaining operator gates.

**Scope:** Phase-prep only. No corpus writes, no training, no eval execution, no EVO/GPU touch, no provider/queue/git mutations, no checkpoint admission.

---

## When to convene

- Clean-router v1+ has passed tests and re-scan.
- Operator has cleared `WATCH` or accepted triage of review hits.
- User says: "set ourselves up for training/eval," "plan the next phase," "greenlight phase-prep."

---

## Required inputs before the council

| Input | Path | Why needed |
|-------|------|------------|
| Router v1+ report | `.omni/aoms/training-harvest-lane/clean-source-capped-router-design-v1.json` | Source of selected signatures, counts, source mix |
| Semantic scan v1+ report | `.omni/aoms/training-harvest-lane/semantic-contamination-scan-v1.json` | Confirms gate status and review-hit count |
| Exclusion list | `.omni/aoms/training-harvest-lane/semantic-exclusion-high-confidence-v1.json` | Audit trail for removed signatures |
| Transform module | `.omni/aoms/training-harvest-lane/transform-humai-unified-v0.py` | Maps signatures back to actual samples |
| Dry report | `.omni/aoms/training-harvest-lane/oasst-production-transform-dry-report-v0.json` | OASST atomicity policy + source paths |
| Eval battery | `.omni/aoms/training-harvest-lane/eval-battery-sister-v0.json` | Reserved prompts for later eval planning |
| Trainer status | `.omni/trainer/*.json` | Existing compute state per node/sister |

---

## Council questions

1. **Corpus materialization spec** — file layout, deterministic reconstruction, hashes, staging area.
2. **Training config draft per sister** — model targets, base checkpoints, LoRA vs full fine-tune, compute target, safety preflights.
3. **Eval plan draft** — reserved battery, metrics, pass/fail criteria, isolation from training corpus.
4. **Gates checklist + sequence** — order of operator gates from cleared contamination scan to first eval run.

---

## Convergence template

The council should converge on:

- **Recommended first sister** (usually the idle/quarantine-free one; Omega in the 2026-06-15 case).
- **Corpus staging directory** and naming convention.
- **Minimum trainer command shape** based on the most recent successful canary.
- **Explicit list of remaining operator gates** with exact authorization verbs.

---

## Operator gates remaining after contamination clearance

| Gate | Authorization verb | Typical blocker |
|------|-------------------|-----------------|
| Corpus materialization | `corpus_overwrite_allowed` | Writing JSONL/txt from signatures |
| EVO safety preflight | `evo_preflight_passed` | Boot ID, GPU baseline, quiet units |
| Delta quarantine clearance | `delta_quarantine_cleared` | Prior autopsy/EVO reboot history |
| WARM/HOT source policy | `warm_hot_sources_reviewed` | Sources flagged for extra scrutiny |
| Training compute | `training_allowed` | EVO availability, Vast.ai budget |
| Eval run | `eval_run_allowed` | Reserved battery isolation |
| Checkpoint admission | `checkpoint_admission_allowed` | Eval pass + operator sign-off |
| Promotion/deploy | `promotion_or_deploy_allowed` | Admission + integration tests |

---

## Output artifacts

- Setup plan markdown: `.omni/aoms/training-harvest-lane/train-eval-setup-plan-v1.md`
- Council prompt: `.omni/aoms/training-harvest-lane/train-eval-setup-planning-sister-council-prompt.md`
- Receipt: `docs/receipts/YYYY-MM-DD-aoms-train-eval-setup-plan-v1.md`
- Anchor update: `.omni/omnira-brain/SESSION-ANCHOR.md`

---

## Pitfalls

1. **Do not materialize corpora without the explicit `corpus_overwrite_allowed` gate.** Read-only dry-runs and hash verification come first.
2. **Do not treat "greenlight" as authorization for protected actions.** Ask which greenlight: planning (Option 1) vs execution (Option 2).
3. **Do not skip trainer-status inspection.** A sister with complete training (Alpha 1B) needs different decisions than an idle sister (Omega) or a quarantined sister (Delta).
4. **Do not edit the scan JSON verdict** to make `WATCH` disappear. Document operator clearance in receipt + anchor.
5. **Do not assume NIM Nemotron Ultra spawns will land.** If sister directories contain only `prompt.md` and no stdout/stderr, the spawn failed silently — fall back to existing council convergence + real data.

---

## NIM silent-failure signature (2026-06-15)

After spawning 5 Nemotron Ultra sisters for this council, all directories were created with `prompt.md` only — no `stdout.log`, no `stderr.log`, metadata wrapper missing. This means the Pi/NIM route failed before the worker could write output.

**Fallback:**
1. Check `~/.pi/agent/models.json` for the correct NIM model id.
2. Use the verified model string: `nvidia/nemotron-3-ultra-550b-a55b`.
3. If spawns still fail, synthesize the plan from the prior remediation council's convergence + real manifest/trainer data.
4. Council-post that the spawn failed and the fallback was used.

---

## Example plan excerpt

```markdown
## Recommended sequence
1. Approve corpus materialization → write per-sister `.txt`/`.slice.jsonl`/`.meta.json` to staging area
2. Verify materialized corpora against router v1 manifest (hash, counts, source mix)
3. Approve EVO safety preflight for Omega (idle, no quarantine history)
4. Run Omega v1 training on EVO with watcher, isolated output dir, spend/time caps
5. Run eval on Omega checkpoint against reserved eval battery
6. Iterate Alpha/Delta based on Omega results and separate gates
7. Admit checkpoints only after eval pass + operator gate
```

---

## Related

- `omnira/omnios-aoms-sister-council` §Contamination Remediation Council Pattern
- `mlops/corpus-foundry-contamination-gate`
- `organism/session-registry`
- `references/aoms-operating-manual.md`
