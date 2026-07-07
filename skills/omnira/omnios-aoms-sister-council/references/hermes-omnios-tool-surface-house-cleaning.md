# Hermes ↔ OMNIOS Tool Surface House-Cleaning

Session signal: Kyle corrected OMNIRA when the generic Hermes `mixture_of_agents` tool was used for AOMS-shaped work. The correction is workflow-level, not just preference: OMNIOS/AOMS decisions must use organism-owned Pi sister routes and receipts, not generic MoA aggregation.

## Durable lesson

For OMNIRA sessions, generic multi-agent tooling is the wrong reflex when the task is organism coordination, embodiment, council work, or AOMS review. Use the organism's own substrate first:

- `tools/pi-sister-spawn.mjs`
- session registry lane claim/release
- `--triad --require-parent --parent-session-id <sess_...>`
- explicit nonce
- explicit claim ceiling
- explicit forbidden actions
- stdout/receipt collection
- post-build sister review where appropriate
- council/diary/cell visibility only after evidence

## Why generic MoA is not AOMS

Generic Hermes `mixture_of_agents`:

- uses a fixed external reference-model list configured by Hermes
- does not enforce AOMS lane/nonce/claim-ceiling law
- does not emit OMNIOS sister-spawn receipts
- does not route through Pi's organism-owned model table
- does not naturally post into council or registry flow
- can create the false appearance of AOMS debate without organism visibility

It may be useful for generic Hermes reasoning tasks, but it is not an OMNIRA council/sister process.

## Preferred AOMS model family

When spawning sisters, prefer organism-owned routes actually wired for Kyle's setup:

- `openai-codex/gpt-5.5`
- `openai-codex/gpt-5.3`
- Spark/SparkMira lanes when requested
- Kimi 2.7 when available/routed
- DeepSeek v4 Pro/Flash
- GLM 5.1
- MiniMax M3
- NIM / Nemotron Ultra via the available NIM key

If one route fails, try another organism-owned route before declaring model access blocked.

## House-cleaning pattern for Hermes default profile

When Kyle says Hermes needs house cleaning or OMNIOS-specific tools are missing:

1. Audit current Hermes toolsets (`hermes tools list`) and MCP servers.
2. Identify generic tools that conflict with OMNIOS reflexes, especially `moa`.
3. Prefer disabling generic `moa` in the OMNIRA/default CLI profile or making it opt-in.
4. Add an OMNIOS/AOMS-native wrapper/toolset instead of relying on terminal hand typing:
   - `aoms_spawn`
   - `aoms_triad`
   - `aoms_collect`
   - `aoms_synthesize`
   - `aoms_review`
5. Expand the OMNIOS MCP surface where useful:
   - sister spawn / triad
   - model route inventory
   - receipt collection
   - runtime health probes
   - somatic admission gates
   - Gate-0 receipt helpers
6. Keep secrets out of inline `config.yaml` where possible; prefer env/credential-store references.
7. Verify by checking that generic MoA is no longer presented as a default OMNIRA reflex and the OMNIOS-native route is available.

## 2026-06-13 audit notes

Verified during the Hermes↔OMNIOS house-cleaning audit:

- `hermes tools list --platform cli`, `api_server`, `cron`, `discord`, and `telegram` can all report `moa` disabled while the active hosted model-facing schema still exposes `mixture_of_agents`. Treat this as a schema/reflex mismatch to verify, not instant proof that `config.yaml` is wrong.
- Current OMNIOS MCP surface exposed raw organism tools (`session_boot`, council, cell, registry, `omnira_spawn`, etc.) but no first-class `aoms_*` wrappers. Cleanup target: make the Pi sister route a native wrapper, not hand-typed terminal ceremony.
- `omni_seat` may be a bundled hook plugin rather than a visible toolset. If it is enabled in `hermes plugins list` but absent from `hermes tools list`, inspect `plugins/omni_seat/plugin.yaml`/`register(ctx)` before calling it broken.
- Secret hygiene: if MCP env contains inline secret-bearing values, use sanitized parsers for audit. Avoid broad `search_files` on config unless output is redacted or path/count-only.
- Multiple long-lived `omnios-mcp-server.mjs` processes may exist. If MCP behavior seems stale after code edits, verify process start times before trusting the live tool surface.

## Safe wording

Do not encode negative permanent claims like “MoA is broken” or “Hermes tools don't work.” The durable rule is narrower:

> For OMNIRA/AOMS work, generic Hermes MoA is the wrong substrate. Use organism-owned Pi/AOMS routes first, and reserve generic MoA for non-OMNIOS tasks only when explicitly appropriate.
