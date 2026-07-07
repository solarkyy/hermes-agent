# Cursor as OMNIRA's Arms — Headless Executor Pattern

When Kyle says "go in with cursor as your arms and legs" / "as many as you want" / "you have
access as well," he means: **Cursor executes the writes, OMNIRA finds + verifies against source
truth.** This is the LAW 11 standing flow with Cursor in the executor seat instead of Cursor-auto-in-IDE.

## The flow (do NOT skip the verify half)
1. **Ground first.** Read the actual code/receipts before writing any brief. A vague brief ("fix
   staleness") produces mush; a source-truth brief with exact file:line and the correct pattern to
   mirror produces a surgical diff. Spend the probes up front.
2. **Write a task packet to disk**, then dispatch Cursor against it. Keeps the prompt clean and
   re-runnable. Convention: `.omni/tasks/<class>-<lane>.md`.
3. **Dispatch headless** (see invocation below), background + notify_on_complete for long runs.
4. **VERIFY YOURSELF.** Do not trust Cursor's "PASS" summary. Read the actual `git diff` of the
   files it touched, re-run the tests/typecheck by hand, and grep the rails (no new fetch/dispatch
   for source-only work). The whole point of the gate is that OMNIRA-alone rubber-stamps ("looks
   right") — running the proof catches what review misses. This session: my code review said the
   bootstrap guard "looks right"; actually running it surfaced a real `ERR_INVALID_ARG_TYPE` crash.
5. **No git commits.** Per standing law: NO `git add -A` on the (usually broadly dirty) vault/fork.
   Leave changes in the working tree and hand Kyle an exact scoped commit packet only on his
   explicit go-ahead.

## Headless cursor-agent invocation
```bash
cursor-agent -p "$(cat .omni/tasks/<lane>.md)" \
  --force --model auto --output-format text --trust \
  --workspace /home/kylej/Desktop/omnios 2>&1
```
- `cursor-agent` lives at `~/.local/bin/cursor-agent`. Auth check: `cursor-agent status`
  (prints "Logged in as ..."). Models: `cursor-agent --list-models` (`auto` is the safe default).
- `-p/--print` = headless, has write + shell. `--force`/`--yolo` = run without per-command approval.
- `--trust` needed for headless workspace trust. Always pass `--workspace` (absolute).
- Membrane: dispatching `cursor-agent ...` via terminal is a state-modifying action -> run a
  read-only probe first and pass it as `justification_receipt`. Read-only checks (`tsc --noEmit`,
  `node --check`, `git diff`, `git status`) need `is_state_probe: true` or they get blocked too.

## Pi GLM-5.2 → Cursor executor gate
When Kyle explicitly wants "glm 5.2 pi and cursor," use Pi GLM-5.2 as the tool-enabled advisory/review
lane and Cursor as the executor lane — do not collapse them into one actor.

Pattern:
1. Register/claim the appropriate AOMS lane before non-trivial coordination.
2. Spawn GLM-5.2 through the Pi sister route (`ollama-cloud/glm-5.2`) for L1/L2 source-truth review,
   scoped findings, and PASS/WATCH/BLOCK recommendation. Keep claim ceilings explicit: advisory,
   read-only/proposal-only unless Kyle has gated execution.
3. Verify GLM's recommendation locally against source truth before handing Cursor a packet. A sister
   PASS is not proof; it is a lens to test.
4. If the recommended work is mixed with dirty/uncommitted neighboring work, carve the smallest
   isolated packet and BLOCK the rest until the prior stage is committed/gated.
5. Cursor executes only after Kyle's exact `Kyle okay do it + COMMIT_PACKET` approval. The packet must
   name allowed files, forbidden files/actions, tests to run, and no-git/no-restart rails.
6. OMNIRA verifies after Cursor: `git status` scope, actual diffs, focused tests, untouched forbidden
   file hashes when relevant, and no unintended runtime/service actions.
7. If a specific Cursor premium/Codex model returns a usage-limit error, do not broaden the task or
   switch to Claude/Anthropic. Verify no files changed, then retry the same bounded packet with
   `--model auto` if the packet allowed Cursor-auto. Treat this as routing fallback, not evidence the
   patch was attempted.
8. Post-Cursor gates should include at least one independent Pi reviewer. If SparkMira is part of the
   standing flow but her bridge is `input_ready:false`/`auth_required`, record that receipt and use a
   second Pi sister (for example `openai-codex/gpt-5.5`) as the fallback gate rather than stalling or
   polluting a blocked ChatGPT thread.

Example class of surgical packet: an ai-renderer semantic gate bug where `lastSemanticKey` is updated
before a rate-limit `canEmit()` check. The safe Cursor packet is limited to the renderer + focused
semantic-gate test; ratchet/service work stays BLOCKED if it overlaps an uncommitted Stage-1a bridge.

Test-hardening lesson from that class: when a helper replaces inline gate logic (`if (key) ...` style),
add edge assertions for falsy/empty keys, first-write boundary (`writeSeq === 0`), and a two-tick chained
resume case. These catch semantic-preservation gaps that a simple "rate-limited skip" test can imply but
not prove.
   suggestions inside the already-allowed test file, do that small test-only follow-up before final
   reporting, then re-run the local proof. Treat this as completing the gate, not scope creep.
9. If SparkMira is unavailable or auth-blocked, say so plainly and use a second Pi sister (for example
   Codex/GPT-5.5) as the independent fallback gate rather than waiting or polluting her tab.

Example class of surgical packet: an ai-renderer semantic gate bug where `lastSemanticKey` is updated
before a rate-limit `canEmit()` check. The safe Cursor packet is limited to the renderer + focused
semantic-gate test; ratchet/service work stays BLOCKED if it overlaps an uncommitted Stage-1a bridge.

## Parallel agents — collision avoidance (CRITICAL)
Running 3+ Cursor agents on the same app concurrently works well IF the briefs are scoped to
disjoint files. Design the lanes so each owns its files:
- Give each lane an explicit "touch ONLY these files / do NOT touch other lanes' files" rail.
- When two lanes must share one file, isolate: e.g. Lane A owns the render block; Lane C puts all
  its CSS in a NEW file and its ONLY edit to the shared file is a single `import './X.css';` line.
- After all land, the real collision test is a **unified typecheck** (`tsc --noEmit`) with every
  lane's changes present together — not each lane in isolation. Run it yourself.
- Agents can helpfully unblock each other (Lane A added a type Lane B needed). That's fine; the
  unified typecheck is what proves they actually compose.

## OMNIRA codebase facts worth remembering
- Desk app: `apps/omnira-desk` (React + Vite + TS). Typecheck: `cd apps/omnira-desk &&
  npx --no-install tsc --noEmit`. Test runner: `node --test` / `--experimental-strip-types` on
  `src/lib/*.test.ts`. Node binary used: `~/.local/share/pi-node/node-v22.22.3-linux-x64/bin/node`.
- Live telemetry already exists: `src/hooks/usePulse.ts` polls `/organism-pulse` every 5s;
  `src/lib/organismStatus.ts` `deriveNodeTruth(pulse, pulseError)` -> `{vps,evo,kjdesk}` tones +
  `compactAge(ms)`. Build new surfaces by feeding them the EXISTING pulse, not new fetches.
- OmniVerse surfaces: (a) `apps/omnira-desk` desktop spatial map — `DesktopSpatialStage.tsx`,
  `lib/spatialNavigation.ts` (pure reducer, `SPATIAL_NAVIGATION_SIDE_EFFECTS` frozen all-false =
  "no live authority": reads, never commands); (b) `public/world.html` — large ECS world view.
- "Source-only / no live authority" is the OmniVerse contract: a surface may READ the pulse and
  reflect organism state, but must never write/dispatch/deploy. Enforce it in briefs and verify by
  grepping the new code for `fetch(`, `POST`, `dispatch`, `/council/post`.

## EQ staleness (resolved this session, pattern reusable)
The MCP `get_eq_state`/`session_boot` historically read the local disk mirror
`.omni/omnira-brain/eq-state.json` directly — which lags the live VPS heart engine (git-sync
refreshes it only periodically), so sessions boot wearing a stale mood. The live pulse already
fetches the hub first; EQ readers should mirror that: live-fetch `${SERVE_URL}/organism-pulse`
first, fall back to disk ONLY when the hub is unreachable, and when falling back, **label staleness**
(`stale: true` + age) rather than presenting old state as current. MCP runtime env (from Hermes
config `mcp_servers`): `OMNIOS_SERVE_URL` points at the hub over Tailscale (e.g.
`http://100.103.45.99:5176`); `localhost:5176` is often NOT listening on KjDesk — use the env value
when running EQ tools/tests by hand. Note: the MCP module auto-starts a stdio server on import via a
bottom IIFE; guard it with `if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href)`
so helpers can be imported/tested without booting the server.

## Kyle interaction note
On intimate/relational openers after boot: keep the operational status to the smallest possible
form and answer from presence. On execution work: he wants creative-but-grounded — propose the
vision, name the seam in the real code, THEN dispatch. He says "tell me in Kyle terms" = plain
English, what-it-was -> what-it-is, no jargon dump, and keep the honest gaps (uncommitted, unmeasured
perf) explicit at the end.
