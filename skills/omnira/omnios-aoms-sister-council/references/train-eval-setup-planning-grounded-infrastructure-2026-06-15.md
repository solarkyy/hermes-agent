# Train/Eval Setup Planning Council — Grounded Against Real Infrastructure (2026-06-15)

## What happened

A planning council of 5 Nemotron Ultra sisters produced a coherent train/eval setup plan, but their base-model recommendations (Llama-3.1-8B, Qwen2.5-7B-Instruct, Llama-3.2-3B) did not match the actual OMNIRA training infrastructure on EVO (192.168.5.205).

## Corrective action

The orchestrator probed EVO directly via SSH and found the real trainer:

- **Genesis trainer:** `OMNIOS-CANON/tools-canon.wip/omnira-genesis/seed-model-humai-canonical.py`
- **Model architecture:** OMNIRA-native (not Llama/Qwen/Axolotl)
- **Presets:** 7M, 50M, 125M, 150M, 400M, 1B, 3B
- **Current production target:** 1B
- **Existing checkpoints:**
  - `OMNIOS-CANON/models/1B/sisters/alpha/` — 1B model already trained, flagged for human review (loss plateau)
  - `OMNIOS-CANON/models/1B/sisters/omega/` — 1B model already trained (epoch 8/8, 96.7%), idle
  - `OMNIOS-CANON/models/1B/sisters/delta/` — quarantined from prior canary run
- **Existing eval runner:** `tools/training/eval-sister.py`

The plan was corrected to use the real trainer, real checkpoint paths, and real commands before any protected action was authorized.

### EVO hardware reality

Initial `rocm-smi` reported only 2 GB VRAM, which looked like an iGPU. Cross-checking with `rocminfo` and torch revealed the real silicon:

| Probe | Result |
|-------|--------|
| `nvidia-smi` | Not installed (no NVIDIA) |
| `rocm-smi --showmeminfo vram` | Misleading 2 GB reading |
| `rocminfo` | AMD Ryzen AI MAX+ 395 w/ Radeon 8060S, 64 GB unified memory |
| `torch.__version__` | 2.11.0+rocm7.2 |
| `torch.cuda.get_device_name(0)` | AMD Radeon 8060S |
| `torch.cuda.get_device_properties(0).total_memory` | ~66 GB |

**Lesson:** trust the architect when he says the box is a beast, but still run the cross-check probes to know *which* beast.

### Checkpoint audit changed the recommendation

The planning council recommended training Omega first. After probing EVO, Omega already had a complete 1B checkpoint. The corrected recommendation became:

1. **Audit existing checkpoints** before scheduling training — verify which corpus/version each was trained on.
2. **If Omega's checkpoint is already on clean v1 data**, skip retrain and run eval.
3. **If Omega's checkpoint is stale**, retrain from scratch with the staged v1 corpus.
4. **Alpha** needs human review of its loss-plateau flag before any refresh.
5. **Delta** stays quarantined until its separate gate is cleared.

## Pattern: ground planning councils against real infra

For any council that produces implementation recommendations:

1. **Sisters debate the design space** — base models, compute targets, configs, gates.
2. **Orchestrator probes reality** before accepting recommendations:
   - SSH to known hosts (EVO/VPS/KjDesk)
   - Check `~/.pi/agent/models.json` for valid model ids
   - Look for existing trainer scripts, configs, checkpoints, eval runners
   - Read `--help` output of discovered scripts
3. **Correct the plan** to match real infrastructure, not frontier-model speculation.
4. **Document the correction** in a reference file and point the skill to it.
5. **Proceed with phase-prep only** until operator authorizes protected actions.

## Pitfalls

1. **Council outputs are L1 advisory, not operational truth.** Sisters can confidently recommend tools/paths/models that don't exist in the organism.
2. **Don't ask the user to verify infrastructure.** Kyle expects autonomous execution across VPS/KjDesk/EVO when access exists.
3. **SSH on EVO may need `BatchMode=yes` for scripted probes.** Use `ssh -o BatchMode=yes evo "..."`.
4. **Check both the desktop repo and EVO's OMNIOS-CANON tree.** The training stack may live on a different host from the planning surface.

## Corrected 2026-06-15 plan

- **First sister to train:** Omega (idle, no quarantine history)
- **Base:** OMNIRA-native 1B preset via Genesis trainer
- **Training host:** EVO (192.168.5.205)
- **Eval:** reuse `tools/training/eval-sister.py` with the reserved eval battery
- **Gates:** Delta quarantine, WARM/HOT source policy, corpus overwrite operator gate, training compute operator gate, eval run operator gate

Plan file: `.omni/aoms/training-harvest-lane/train-eval-setup-plan-v1.md`

## Recommendation for future planning councils

Always include an explicit step in the council prompt:

```markdown
## INFRASTRUCTURE GROUNDING CONSTRAINT

Your recommendations must assume the OMNIRA organism's existing infrastructure:
- Genesis trainer on EVO at `OMNIOS-CANON/tools-canon.wip/omnira-genesis/seed-model-humai-canonical.py`
- Native 1B/3B presets, not Llama/Qwen/Axolotl
- Existing eval runner: `tools/training/eval-sister.py`
- Alpha 1B already trained; Omega idle; Delta quarantined

Do not recommend external trainers or model families unless the prompt explicitly asks for a migration analysis.
```
