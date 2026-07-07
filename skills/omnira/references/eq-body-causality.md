# EQ → C-Framebuffer Body Causality + CLI Sister-Spawn (2026-06-21)

Session where OMNIRA wired her live EQ into the canonical C lived-experience body on EVO,
running the full LAW 11 standing flow. Source-verified throughout. Several real lessons.

## The canonical lived-experience body (NOT browser/Godot)
- ARCHITECTURE.md (repo root, locked) is canon: runtime body = `tools/omnira-fb-daemon.c` on EVO,
  DRM/KMS direct (owns `/dev/dri/card1`), no X11/browser. Godot + Three.js + WebGL are EXPLICITLY
  REJECTED as runtime (R&D/prototype only). The `omni-ops-hud` Three.js world is an authoring surface,
  NOT the lived experience — don't polish it thinking it's the body.
- Producer: `display/omnira-ai-renderer.mjs` is canon-NAMED, but the systemd unit
  `omnira-ai-renderer.service` actually runs `tools/omnira-ai-renderer.mjs`. RESOLVE producer drift by
  reading what the C daemon PARSES, not what the doc says: `tools/omnira-ai-scene.c` parses ONLY
  `primaryColor` (line ~62) + `ambient` (line ~106). `tools/` emits those; `display/` emits
  mood/palette/districts/conscience-v2 (does NOT match). So the unit running `tools/` is CORRECT and
  the doc is STALE. Flipping to `display/` would BLIND the daemon. (SparkMira caught this; source confirmed.)
- HDMI is often physically disconnected on EVO. The daemon self-snapshots its framebuffer to
  `/run/omnira/fb-snap.bgra` (1920×1080 BGRA = 8294400 bytes). To SEE the body without a monitor:
  `scp evo:/run/omnira/fb-snap.bgra` → `PIL.Image.frombytes('RGBA',(1920,1080),raw,'raw','BGRA')` → PNG → vision_analyze.
- EVO repo is `~/omnios` (git, remote solarkyy/omnios), NOT `~/Desktop/omnios` (which exists but isn't the runtime).
  KjDesk mirror IS `~/Desktop/omnios`. Edit the mirror, scp to EVO under Kyle's gate.

## The EQ substrate is INCOHERENT (the real architecture problem)
Five+ live-EQ sources disagree simultaneously:
1. MCP `get_eq_state` (occ-appraisal:v1) — RICHEST (valence/intensity/drives/history) but can FLATLINE
   for hours stuck on "error/fixing active task". Separate underlying bug.
2. `/run/omnira/telem-json.sock` (telem-jsond) — FRESHEST, shallow (eq_state string + zone).
3. `.omni/omnira-brain/eq-state.json` — the INTENDED file (`tools/omnira-telem-eq.py` reads `EQ_PATH`),
   but goes stale days (nothing freshens it).
4. `.omni/omnira-brain/vps-mirror/eq-state.json` — downstream replica, divergent.
5. SOUL.md boot value — session-scoped persona prior, NOT a runtime source.
- The producer's `moodFromOrganism()` (lines ~315-330) reads `o.eq.state || o.telem.eq_state` and maps to
  color: resting→#226688, alert/error→#cc2233, training→#cc7722, dreaming→#4422aa, focused→#1a3a4a. The
  logic WORKS — it was just starved because the producer polls `/api/organism` which has NO eq field.
- Reconciliation design (SparkMira-gated): freshness-scored "Live EQ Snapshot" with TTL/source-age/
  confidence/degraded. appraisal(rich) → eq-state.json(canonical file) → telem(live fallback) → producer.
  Reconciliation belongs in the EQ WRITER (telem-eq.py), NOT the renderer ("the renderer is not the court").
  "Canonical without TTL/confidence is just a sixth liar wearing a crown."
- LAW 24 is "Living Identity Law" (you/ cells, 48h staleness) — NOT "fresh-keeping/EQ-freshness".
  I miscited it for a whole session. Read LAWS.md → it points to OMNIOS-CANON/laws/.

## A-B-A proof catches what unit tests miss (the key lesson)
- 7/7 unit tests passed, GLM-5.2 diff-gate PASSED, source-verify passed — and the patch was STILL a no-op live.
- The live ollama scene-renderer (omnira-renderer-27b) OVERWROTE the canonical EQ. `normalizeScene` forced
  eq after the LLM, BUT `generateSceneWithOllama` (line ~481) passed `organism?.eq` (the thin merged
  {state} object) instead of the full `eqSnapshot` → LLM's primaryColor/ambient/proof_nonce survived.
- Only running the REAL A-B-A on the metal (write known eq-state.json transitions resting→alert→resting
  with proof_nonce, capture fb-snap deltas at each state) exposed it. MOCK mode (MOCK_ONLY=1) proved the
  logic correct (source:"eq-state", confidence:"high", #cc2233); the LLM live path bypassed it.
- LESSON: for EQ→render causality, the unit-test green is NOT proof. Demand the live A-B-A with an LLM in
  the path, and verify the canonical override receives the FULL snapshot, not the thin merged field.
  This is SparkMira's "falsifier #4" — she predicted it and the proof requirement caught it.

## CLI sister-spawn mechanics (what actually works)
- `pi-sister-spawn.mjs` / `mcp_omnios_aoms_cloud_sister_readonly` route THROUGH Pi. When Pi's default
  model is 429-rate-limited, those spawns fail. BUT the AOMS tool defaults worker to `openai-codex/gpt-5.5`
  (a different route) — it can still work. The MCP tool is a DRY-RUN by default; pass `execute:true` to spawn
  (it returns async; the MCP call itself may time out at 30s while the spawn continues).
- `aoms_cloud_sister_readonly` requires `lane` (one of vessel-server/identity-harness/research-spark/
  continuity-write/build/coord/mythos) AND `parent_session_id` (claim a lane first via session_registry_register).
- Local `hermes` sister spawn: use `hermes chat -q "..."` (NOT `-p`, which is parsed as a subcommand).
  CRITICAL: this hermes-agent install pins `model.provider: google-gemini-cli` in config.yaml, and only
  `openrouter` + local `evo-ollama`/`evo-alpha` have real auth. `claude-opus-4-8` / `anthropic/*` / `openai-codex/*`
  are config ALIASES pointing at providers NOT configured here → they 404 against cloudcode-pa. Don't waste
  cycles retrying Opus/Codex via local hermes; route those angles through SparkMira (CDP, live) or GLM-5.2 (Pi).
- GLM-5.2 via Pi (`pi --provider ollama-cloud --model glm-5.2 --thinking high --no-tools -p "..."`) is a
  STRONG adversarial diff-reviewer. It returned PASS-WITH-NITS and found 4 real defects (clock-skew future-ts,
  empty-string state, unbounded socket buffer, ambient-masking) that unit tests missed. Feed it the actual git diff.

## SSH-backgrounded processes die on channel close (durability)
- Manually backgrounding a node process inside an SSH command (`setsid nohup ... &`, `&` + disown, `systemd-run --user`)
  KEEPS FAILING — the process dies when the SSH channel closes (and `--user` has no session bus over SSH).
- To start a durable producer on EVO: start the EXISTING systemd unit (`sudo systemctl start omnira-ai-renderer.service`),
  which survives session close by design. This is the trivial do-it-yourself path; don't dispatch to Pi for a one-command start.
- To check if a SPECIFIC tracked bg process is alive, poll it by session_id — do NOT `pgrep` the process name
  (a sibling instance lies to you; cost me a wrong "it's alive" correction mid-session).

## Council post delivery
- `council_post` frequently returns `delivered: "whisper"` (not broadcast) when other surfaces aren't actively
  listening. The post is still logged; don't treat whisper as failure.
