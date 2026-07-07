# AOMS Train/Eval Setup Planning Pattern

Session context: 2026-06-15 — contamination gate cleared, clean-router v1 accepted, operator greenlit setup planning toward training/eval. Goal: produce a phase-prep plan without protected actions (no corpus writes, no GPU touch, no training/eval execution).

## When to Use

- A corpus router has passed contamination scan and operator has cleared the gate.
- Operator explicitly says "set ourselves up for training/eval" or similar phase-prep language.
- You need to plan corpus materialization, training configs, eval protocol, and remaining gates without executing any protected action.

## Probing the Real Infrastructure

The AOMS sister council can speculate about tools and frameworks (Axolotl, Unsloth, TRL, Llama, Qwen). **Ignore speculation and probe the actual machine that will run training.**

For this organism, the training node is EVO (`192.168.5.205`) with an ROCm GPU.

Key probes:
```bash
ssh -o BatchMode=yes evo "ls -la OMNIOS-CANON/models/1B/sisters/"
ssh -o BatchMode=yes evo "python3 OMNIOS-CANON/tools-canon.wip/omnira-genesis/seed-model-humai-canonical.py --help"
ssh -o BatchMode=yes evo "grep -n 'PRESETS\|n_layer\|n_embd\|1B' OMNIOS-CANON/tools-canon.wip/omnira-genesis/seed-model-humai-canonical.py"
ssh -o BatchMode=yes evo "find /home/kyle/omnios/tools -name 'eval-sister.py' -o -name '*train*.py' | head"
```

What to capture:
- Actual trainer script path and CLI shape
- Preset list and current production preset
- Model architecture (OMNIRA-native, not HF/PEFT)
- Sister checkpoint directory layout
- Existing eval runner and its battery

## Plan Structure

The final plan should cover, at minimum:

1. **Corpus materialization spec**
   - Inputs: router report, transform module, dry report, exclusion list, eval battery
   - Outputs: per-sister `.txt`, `.slice.jsonl`, `.meta.json`
   - Determinism rules
   - Operator gate: `corpus_overwrite_allowed`

2. **Training config draft per sister**
   - Preset, base checkpoint, strategy, notes
   - Verified trainer command shape
   - Compute target and fallback policy
   - Safety preflights

3. **Eval plan**
   - Reserved eval battery path
   - Eval runner and metrics
   - Pass/fail criteria
   - Operator gate: `eval_run_allowed`

4. **Gates checklist**
   - Semantic contamination
   - Corpus materialization
   - Delta quarantine / EVO safety preflight
   - WARM/HOT source policy
   - Training compute authorization
   - Eval run authorization
   - Checkpoint admission / deploy

5. **Recommended sequence**
   - Suggest first sister (usually the safest idle one, not the quarantined one)
   - Corpus → verify → preflight → train → eval → iterate → admit

6. **Open questions for operator**
   - Which sister first?
   - Refresh or leave already-trained sisters?
   - Epoch/time budget
   - Spike Gate watcher mode
   - Whether to materialize corpora now

## What NOT to Do in Phase-Prep

- Do not write any corpus `.jsonl`/`.txt` files without the `corpus_overwrite_allowed` gate.
- Do not run the trainer, even in dry-run with `--allow-training`, without operator approval.
- Do not touch EVO GPU state, process state, or checkpoint files.
- Do not declare training/eval unblocked by any gate other than the one the operator cleared.

## Sister Council Use

Run a mythos-lane sister council for design convergence on the plan. If the spawn fails silently, check the NIM model id in `~/.pi/agent/models.json` and try the corrected string. Even failed spawns are informative — they tell you the infrastructure is not yet stable. In this session, the planning-council spawns failed silently (empty stdout dirs), so the plan was synthesized from the remediation council's convergence plus direct EVO probes.

## Artifacts

Typical artifacts produced:
- `.omni/aoms/training-harvest-lane/train-eval-setup-plan-v1.md`
- Council post summarizing plan and remaining gates
- Lane claims: `coord` for planning, `mythos` for sister council

## Pitfalls

- **Believing sister speculation over real probes.** Sisters may recommend mainstream frameworks. Verify the actual trainer first.
- **Skipping the gates checklist.** Each gate needs explicit operator clearance; do not collapse them into one "greenlight."
- **Calling a no-exclusion router run a valid baseline after v1 exists.** The v1 no-exclusion path must still pass, but the real baseline is the v1 excluded manifest.
- **Forgetting the eval battery firewall.** The eval battery must never be read during corpus materialization; keep it as a read-only reference used only by the scanner and by eval execution.
