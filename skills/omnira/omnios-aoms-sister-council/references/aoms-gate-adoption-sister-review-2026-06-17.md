# Worked Example — AOMS Gate-Adoption Sister Review (2026-06-17)

Reference for the "Gate-Adoption Requires Sister Review" pattern in `omnios-aoms-sister-council/SKILL.md`. Use as the concrete shape, not a copy-paste template.

## Trigger

Kyle approved HRO-organism gates 2 and 3 (Instrument Coherence Model + Guardrail Signature Primitive) after gate 1 had been approved via a simple "yes" without sister review. Kyle's exact words for gates 2+3: "yess approved but check first and work with sisters aoms" — establishing that gate adoption requires sister review BEFORE the adoption receipt is written.

## Goal

Close the same-model-adversary open loop from the original overnight review (all gpt-5.5 reviewers — I3-correlated theater by the doctrine's own standard) by spawning model-different sisters to re-review the artifacts before Kyle's "yes" becomes an adoption receipt.

## Setup

### Output directory structure

```
/tmp/aoms-gates-23-review/
├── sister-architect.md      # task file for Nemotron Ultra
├── sister-adversary.md      # task file for DeepSeek v4 Pro
├── sister-membrane.md       # task file for GLM 5.1
├── architect/
│   ├── spawn.log            # pi-sister-spawn stdout
│   └── stdout.log          # sister output (after spawn completes)
├── adversary/
│   ├── spawn.log
│   └── stdout.log
└── membrane/
    ├── spawn.log
    └── stdout.log
```

Create the directories first with one probe:
```bash
mkdir -p /tmp/aoms-gates-23-review/{architect,adversary,membrane}
```

### Task file shape (each sister)

Each task file contains:
1. **Mission** — one-sentence objective specific to the lens
2. **Context — Full artifact text** — the actual doctrine/spec content (not just the receipt summary). Sisters are L1 advisory with no file access, so the artifact text must be in the prompt.
3. **Your task (lens name)** — 5-7 specific questions for that lens
4. **Output format** — explicit JSON schema the sister should produce
5. **Boundary** — L1 advisory only, no tools, no mutation, no protected-action authorization

Three lenses used:
- **Architect** (Nemotron Ultra): graph completeness, F1-F5 soundness, missing loops, human-root framing, adoption safety, hidden authority laundering. Verdicts on each finding.
- **Adversary/Falsifier** (DeepSeek v4 Pro): false-pass attack (control that passes all six bounds but shouldn't be admissible), false-fail attack (control that fails but should be admissible), provisional-admission loophole, bound gaming per bound, self-test sufficiency, adoption safety, authority laundering.
- **Membrane/Risk** (GLM 5.1): authority laundering audit, adopt-vs-not-adopt risk asymmetry, vocabulary power terms, hidden gates, reciprocal risk with prior gate-1 adoption (rubber-stamp pattern), adoption safety, stop conditions to watch in next 7 days.

## Spawn commands

Three parallel background spawns. Each needs `justification_receipt` from a prior `is_state_probe=true` probe that confirmed: pi-sister-spawn.mjs exists, Pi CLI resolves, no existing spawns to collide with, PATH includes /home/kylej/.npm-global/bin, target output dir exists and is empty.

**Critical: probe the live Pi config first to verify model strings.** The strings below are the validated pattern as of 2026-06-17. Pi's `providers` object keys are NOT optional — bare prefixes like `deepseek/` or `zai/` cause silent `No API key found for <bare>` failures in ~500ms with empty stdout. See "Route Discovery Before Model-Different Spawns" in the parent SKILL.md.

```bash
# Probe first (read-only):
cat /home/kylej/.pi/agent/models.json | python3 -c "
import json,sys
d=json.load(sys.stdin)
for k,v in d.get('providers',{}).items():
    has_key = bool(v.get('apiKey') or v.get('api_key') or v.get('env') or v.get('authToken'))
    if has_key: print(f'{k}: {[m.get(\"id\") for m in (v.get(\"models\") or [])]}')
"

# Architect (Nemotron Ultra via NIM)
node tools/pi-sister-spawn.mjs \
  --worker-model nim/nvidia/nemotron-3-ultra-550b-a55b \
  --lane coord \
  --task-file /tmp/aoms-gates-23-review/sister-architect.md \
  --no-tools \
  --claim-ceiling "L1 advisory verdict only; no local verification, no authorization, no code changes, no protected actions" \
  --forbidden-actions "claim local state, authorize protected actions, execute tools, write files, inspect secrets" \
  --output-dir /tmp/aoms-gates-23-review/architect \
  --timeout 300 \
  --nonce gates23-architect-20260617

# Adversary (DeepSeek v4 Pro via deepseek-api)
node tools/pi-sister-spawn.mjs \
  --worker-model deepseek-api/deepseek-v4-pro \
  --lane coord \
  --task-file /tmp/aoms-gates-23-review/sister-adversary.md \
  --no-tools \
  --claim-ceiling "L1 advisory falsification verdict only; no local verification, no authorization, no code changes, no protected actions" \
  --forbidden-actions "claim local state, authorize protected actions, execute tools, write files, inspect secrets" \
  --output-dir /tmp/aoms-gates-23-review/adversary \
  --timeout 300 \
  --nonce gates23-adversary-20260617

# Membrane (GLM 5.1 via ollama-cloud)
node tools/pi-sister-spawn.mjs \
  --worker-model ollama-cloud/glm-5.1 \
  --lane coord \
  --task-file /tmp/aoms-gates-23-review/sister-membrane.md \
  --no-tools \
  --claim-ceiling "L1 advisory membrane/risk verdict only; no local verification, no authorization, no code changes, no protected actions" \
  --forbidden-actions "claim local state, authorize protected actions, execute tools, write files, inspect secrets" \
  --output-dir /tmp/aoms-gates-23-review/membrane \
  --timeout 300 \
  --nonce gates23-membrane-20260617
```

**Pitfall captured this session:** the first attempt used `deepseek/deepseek-v4-pro` and `zai/glm-5.1` — both exited in ~500ms with `exit_code=1`, empty stdout, and stderr `No API key found for deepseek` / `No API key found for zai`. The 500ms exit time (vs the 30-300s a real spawn takes) is the diagnostic signal: if you see exit in under 1s with empty stdout, the route is wrong, not the model. Recovery is to probe the live Pi config, find a keyed provider that lists the model family you want, and retry with the correct `<pi-provider>/<model-id>` string.

Use `terminal(background=true, notify_on_complete=true)` for each — three parallel spawns complete in ~5min wall time vs ~15min sequential.

## Synthesis

After all three return (poll with `process(action='poll')`):

1. Read each `stdout.log` from `/tmp/aoms-gates-23-review/{architect,adversary,membrane}/`
2. Extract verdicts + key findings from each
3. Cross-map: where do the three sisters agree? Where do they disagree?
4. Write a unified synthesis with: overall verdict (PASS/WATCH/BLOCK), per-lens verdicts, conditions attached, smallest risk of adopting, smallest risk of not adopting
5. Present synthesis to Kyle
6. If Kyle says yes (or "go" or "proceed") after seeing the synthesis: write the adoption receipt citing the sister verdicts and conditions
7. Post to council with both the adoption and the sister review summary
8. Append to diary

## Lessons

### Pattern that worked

- Three model families (Nemotron / DeepSeek / GLM) closes the same-model open loop that the all-gpt-5.5 overnight review created
- Three lenses (architect / adversary / membrane) cover different question shapes — soundness, falsification, and authority laundering — without overlap
- L1 advisory + no-tools + explicit claim ceiling kept all three sisters read-only
- Parallel background spawns with notify_on_complete=true completed in wall time, not serial time
- One state probe (mkdir + ls + which pi + ps aux) justified all three task-file writes AND all three spawn commands — six total operations off one probe

### What NOT to do (anti-patterns observed earlier in the session)

- Writing the gate-1 adoption receipt solo, before any sister review. The receipt is fine — gate 1 ratifies vocabulary only — but the precedent is bad. From gate 2 onward, sister review first.
- Trying to write task files without `justification_receipt` from a state probe. The membrane blocks this; don't argue with it, just probe first.
- Trying to spawn sisters without `justification_receipt`. Same membrane rule applies to `terminal(background=true)` for spawn commands.
- Continuing to retry `write_file` after the tool-loop warning fires at 3 failures. Diagnose first — usually missing `justification_receipt`, not a real failure.
- Treating `mcp_omnios_session_registry_register` LOCK_TIMEOUT as fatal. It isn't — only triad-mode spawns need the registry. Simple parallel spawns proceed without it.

### What to improve next time

- When Kyle asks "wanna see what's being claimed" or "what are the invariants" or "what's being adopted," use the three-column extraction pattern from this session (claims / explicit de-claims / gates parked) and the three-flag pattern (inconsistencies / structural limits / missing attestations). It worked well as a presentation shape even without a dedicated skill.
- Cross-link this reference from the parent SKILL.md's References list — it already is (added in the same patch pass that fixed the model strings).
- Consider whether gates 4+ (which actually build things, not just vocabulary) need a stronger sister review pattern — e.g., a 4th lens (build-feasibility / cost / rollback), or a higher claim ceiling for builder sisters with tools.

## Stop conditions

- Any sister returns BLOCK on adoption safety → do not write the adoption receipt. Present the BLOCK to Kyle and stop.
- Any sister identifies authority laundering that pre-authorizes gates 4-8 → present the laundering risk to Kyle and stop.
- Any sister identifies a missing attestation that can't be filled by L1 advisory review alone → name the gap, present to Kyle, stop.
- Kyle says "stop" or "wait" or "not yet" after seeing the synthesis → do not write the receipt. Park the gate.

## Boundary

This entire pattern is L1 advisory. Sisters cannot authorize, execute, mutate, or attest. The orchestrator (Voice surface) synthesizes; Kyle decides; the receipt is written only after Kyle's yes. The receipt itself is still P0-P1 AI-self-attested evidence unless and until AEPL is built — but at least it's P0-P1 evidence from three model families, not one.