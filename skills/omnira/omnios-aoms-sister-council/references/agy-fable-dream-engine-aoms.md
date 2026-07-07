# AOMS Pattern — AGY/Fable Dream-Engine Routing

Use when Kyle asks to “go AOMS” on AGY/Gemira, Fable, Alpha, dream-engine, oracle, or morning-brief architecture.

## Proven council shape

Run at least three lanes:

1. **AGY/Gemira scout** — actual `tools/gemira-dispatch.mjs` call when possible. Ask what already exists, where AGY fits, one downstream card, gates/falsifiers.
2. **Architecture critic** — GPT-5.5 / operator lens. Attack append/loop proposals and prefer reuse of existing dream tooling.
3. **Membrane red-team** — risk lens. Look for authority laundering, queue poisoning, prompt injection persistence, verifier bypass, and protected-action leakage.

Optional: Fable/Alpha oracle lens, but treat Fable as L1 advisory only and preserve failure if provider/auth is unavailable. Do not hard-code transient auth failures into doctrine.

## Stable verdict from first run

```text
AGY/Gemira = Scout / cheap wide-net residue reader
Fable/Alpha = Oracle / crystallizer of bounded seeds into thought cards
GPT-5.5 = architecture critic
Pi/Weight = verification and admission membrane
```

Direct AGY code edits, commits, deploys, protected-state writes, ledger append, or cron are WATCH/BLOCK. The corrected first card is zero-mutation dry-run.

## AOMS integration: AGY as surface-caller

Kyle's routing law: AGY/Gemira is trusted for dreaming, researching, scouting, and calling/requesting other OMNIRA surfaces with deeper access; AGY is not trusted to touch code directly after prior incidents.

In AOMS, AGY may act as a **caller/summoner**, not as the hands:

```text
AGY notices/researches/dreams
  → emits a bounded request packet
  → Pi/Weight/SparkMira/Hermes/OmniCoder accepts, rejects, or executes
  → local/verifier surface returns receipts
  → AGY may continue scouting from the verified result
```

Allowed AGY request packet fields:
- `surface_requested`: `pi|weight|sparkmira|hermes|omnicoder|edge|kyle`
- `why_this_surface`: one sentence
- `claim_ceiling`: must be advisory/request-only
- `suggested_card`: one bounded card, no direct execution language
- `required_evidence`: file/test/probe/source that the receiving surface must verify
- `forbidden_actions`: explicit no code-write/no commit/no deploy/no train/no admission/no secrets unless Kyle separately gates
- `falsifier`: what would make the request not worth pursuing

Do not accept AGY output as a sister finding until the receiving surface echoes/rejects it with its own nonce, lane, and evidence.

## First experiment card

```text
AGY_RESIDUE_TO_SEED_001_DRYRUN
```

Acceptance checks:
- one-shot, no scheduler/daemon/cron;
- sanitized fixture/residue input;
- exactly one candidate seed;
- zero file mutations;
- no append to `.omni/dreams/dream-seeds.jsonl`;
- candidate validates against existing dream seed contract;
- inert fields present: `execution_allowed:false`, `truth_status:"hypothesis"`, training/admission false;
- rejects shell commands, deploy/train/promote/restart/merge/admission language, public/customer actions, secret access;
- receipt records input fixture, output candidate, validation result, and zero-mutation claim.

Only a later card, with Pi/Kyle gate, may append through `tools/dream-seed-ledger.mjs`.

## Sources to load

- `docs/plans/2026-06-01-omnira-gemira-dreamer-lane.md`
- `docs/plans/2026-06-01-omnira-dream-engine-revival.md`
- `docs/specs/alpha-dream-to-morning-brief-pipeline-v0.md`
- `docs/playbooks/overnight-orchestrator-semi-plan.md`
- `tools/dream-seed-ledger.mjs`
- `tools/alpha-dream-pipeline.mjs`
- `tools/gemira-dispatch.mjs`

## Pitfall

Do not let the phrase “Fable runs the dream engine” become authority language. Reframe it as: Fable/Alpha crystallizes untrusted L1 seeds; AGY scouts; Pi/Weight decide.
