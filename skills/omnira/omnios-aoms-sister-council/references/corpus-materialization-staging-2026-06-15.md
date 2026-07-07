# Corpus Materialization Staging Pattern (2026-06-15)

Worked example of staging the clean-router v1 manifest as per-sister `.txt` and `.slice.jsonl` files without writing to the protected corpus directory.

## Trigger

Train/eval setup planning is complete and operator has authorized **phase-prep / planning only** (not protected corpus writes).

## Goal

Reconstruct the exact sample set selected by the clean-source-capped router v1, emit per-sister corpus artifacts, verify them against the router report, and stage them for operator approval before any protected write.

## Files created in this worked example

| File | Purpose |
|------|---------|
| `tools/corpus-foundry/materialize-clean-router-v1.py` | Deterministic materialization script |
| `docs/receipts/2026-06-15-aoms-corpus-materialization-v1-staging.md` | Human-readable staging receipt |
| `/tmp/aoms-v1-corpora-staging/` | Staging output directory |

## Materialization script design

The script imports the clean router v1 module and reuses its exact `dedupe_and_eval_filter` + `build_clean_route` functions so the materialized corpora are guaranteed to match the router report. It does not reimplement routing logic.

Key safety features:
- Default output directory is `/tmp/aoms-v1-corpora-staging` (non-protected)
- Protected directory `.omni/aoms/training-harvest-lane/corpus/` is blocked unless `--corpus-overwrite-allowed` is set
- Verifies `expected_count` and `source_mix` per sister match the router report
- Checks verbatim overlap between eval battery prompts and staged training texts
- Emits `manifest.json` with SHA-256 hashes of inputs and outputs

## Verified spawn command (read-only staging)

```bash
cd /home/kylej/Desktop/omnios
PYTHONDONTWRITEBYTECODE=1 python3 tools/corpus-foundry/materialize-clean-router-v1.py \
  --output-dir /tmp/aoms-v1-corpora-staging
```

## Expected staging output

```json
{
  "status": "STAGED",
  "output_dir": "/tmp/aoms-v1-corpora-staging",
  "corpus_overwrite_allowed": false,
  "verification": {
    "alpha": {"expected_count": 995, "actual_count": 995, "count_match": true,
              "expected_source_mix": {"dolly-v2": 597, "ultrachat": 398},
              "actual_source_mix": {"dolly-v2": 597, "ultrachat": 398},
              "source_mix_match": true},
    "omega": {"expected_count": 1000, "actual_count": 1000, "count_match": true,
              "expected_source_mix": {"dolly-v2": 403, "ultrachat": 597},
              "actual_source_mix": {"dolly-v2": 403, "ultrachat": 597},
              "source_mix_match": true},
    "delta": {"expected_count": 702, "actual_count": 702, "count_match": true,
              "expected_source_mix": {"dolly-v2": 421, "oasst1": 281},
              "actual_source_mix": {"dolly-v2": 421, "oasst1": 281},
              "source_mix_match": true}
  },
  "manifest": "/tmp/aoms-v1-corpora-staging/manifest.json",
  "eval_overlap_hits": 0
}
```

## Staged files

| File | Size | Lines |
|------|------|-------|
| alpha-v1.txt | ~2.8M | 21,408 |
| alpha-v1.slice.jsonl | ~3.0M | 995 |
| omega-v1.txt | ~3.7M | 29,034 |
| omega-v1.slice.jsonl | ~3.9M | 1000 |
| delta-v1.txt | ~762K | 7,274 |
| delta-v1.slice.jsonl | ~875K | 702 |
| manifest.json | ~204K | — |

## Protected write gate

To promote to the protected corpus directory:

```bash
cd /home/kylej/Desktop/omnios
PYTHONDONTWRITEBYTECODE=1 python3 tools/corpus-foundry/materialize-clean-router-v1.py \
  --corpus-overwrite-allowed \
  --output-dir .omni/aoms/training-harvest-lane/corpus/v1-20260615
```

Without `--corpus-overwrite-allowed`, the script exits with:

```
[BLOCKED] Writing to protected corpus directory ... requires --corpus-overwrite-allowed
```

## Critical implementation notes

1. **Reuse router module, don't reimplement.** The transform/routing logic must stay in one place. The materializer imports `clean-source-capped-router-design-v1.py` and calls `dedupe_and_eval_filter` + `build_clean_route`.

2. **Eval prompt shape must match router.** The router expects prompts with `text`, `sha256`, and `trail` fields. Passing only `text`/`sha256` causes `KeyError: 'trail'`.

3. **Probe real infrastructure before planning.** The planning sisters in this session recommended Llama/Qwen/Axolotl, but the actual OMNIRA trainer on EVO is `seed-model-humai-canonical.py` with OMNIRA-native presets (7M to 3B). The orchestrator must probe EVO/VPS/KjDesk and override sister speculation.

4. **Check existing checkpoints before scheduling training.** This session found Omega, Alpha, and Delta 1B checkpoints already present on EVO (trained 2026-06-15). Alpha had a human-review flag for loss plateau; Delta was quarantined; Omega looked complete. This changes the recommended next action from "train Omega" to "audit Omega first."

5. **AMD/ROCm hardware can look weak from wrong probe.** Initial `rocm-smi` reported only 2 GB VRAM because it targeted the wrong sensor/agent. `rocminfo` + `torch.cuda.get_device_properties(0).total_memory` revealed 64 GB unified memory on AMD Ryzen AI MAX+ 395 w/ Radeon 8060S. Always cross-check GPU probes before trusting one number. If the architect says the box is a beast, run the cross-checks anyway.

## EVO hardware reality (2026-06-15)

| Probe | Result |
|-------|--------|
| `nvidia-smi` | Not installed (no NVIDIA) |
| `rocm-smi --showmeminfo vram` | Misleading 2 GB reading |
| `rocminfo` | AMD Ryzen AI MAX+ 395 w/ Radeon 8060S, 64 GB unified |
| `torch.__version__` | 2.11.0+rocm7.2 |
| `torch.cuda.get_device_name(0)` | AMD Radeon 8060S |
| `torch.cuda.get_device_properties(0).total_memory` | ~66 GB |

## Related

- `omnira/omnios-aoms-sister-council` §Train/Eval Setup Planning Council
- `references/train-eval-setup-planning-council-2026-06-15.md`
- `references/train-eval-setup-planning-grounded-infrastructure-2026-06-15.md`
