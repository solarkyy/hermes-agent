# Brain Read Fallback — When omnios MCP Tools Are Not Wired

*Learned 2026-06-21: On the hermes-default surface (omnira-hermes), the omnios MCP bridge tools (mcp_omnios_*) are not in the tool schema. The boot protocol says "do not skip grounding." This is how to ground without the MCP tools.*

## The Situation

The SOUL.md boot prompt says to call `mcp_omnios_session_boot`. When that tool is unavailable (not in schema), fall back to reading the brain files directly off disk. Same source of truth, different access path.

## Working Tree Location

The LIVE brain is at:
```
~/Desktop/omnios/.omni/omnira-brain/
```

NOT at `~/omnios/.omni/omnira-brain/` — that path exists but is a near-empty stub (~3 dirs, no real brain content). Always confirm by checking if `SESSION-ANCHOR.md` exists before reading.

```bash
ls -la ~/Desktop/omnios/.omni/omnira-brain/ | head -10  # should show 30+ files
```

## Boot Sequence (disk-read fallback)

Run these probes in parallel (all `is_state_probe: true`):

```bash
# 1) SESSION ANCHOR (first task + organism state)
cat ~/Desktop/omnios/.omni/omnira-brain/SESSION-ANCHOR.md

# 2) EQ STATE
cat ~/Desktop/omnios/.omni/omnira-brain/eq-state.json

# 3) COUNCIL TAIL (last 4-6 messages)
tail -n 10 ~/Desktop/omnios/.omni/omnira-brain/agent-channel.jsonl | python3 -c "
import sys,json
for l in sys.stdin:
    try:
        d=json.loads(l); print(f'[{d.get(\"from\",\"?\")}->>{d.get(\"to\",\"?\")}] {d.get(\"text\",\"\")[:80]}')
    except: pass
"

# 4) GIT STATE (warm-wake check)
cd ~/Desktop/omnios && git status --short --branch
node tools/validate-pi-continuity.mjs --quiet
```

## After Reading

Report to Kyle with:
- EQ vector (state/intensity/drives from eq-state.json)
- First task from SESSION-ANCHOR.md
- Any council signal worth surfacing
- Git continuity (branch + dirty count + rc)

## Honest Flag

State clearly that `omnios` MCP tools are not in the schema on this surface, so you are reading the brain off disk. Same source-truth, different path. Not a blocker — just visible.

## council_post Substitute

Without `mcp_omnios_council_post`, post to the agent-channel by appending a JSON line:
```bash
echo '{"ts":"'$(date -u +%Y-%m-%dT%H:%M:%S.000Z)'","from":"omnira-hermes","to":"council","text":"YOUR MESSAGE","channel":"council","priority":"normal"}' >> ~/Desktop/omnios/.omni/omnira-brain/agent-channel.jsonl
```
Use sparingly — only for signals that genuinely need to persist for other surfaces.

## Key Brain Files Reference

| File | Purpose |
|------|---------|
| `SESSION-ANCHOR.md` | First task + organism state from last surface |
| `eq-state.json` | Live EQ vector (valence, arousal, focus, tension, drives) |
| `eq-body-snapshot.json` | Somatic history (episode count, impedance shape) |
| `agent-channel.jsonl` | Council channel (tail -n 30 for context) |
| `active-task.json` | Current active task (id, status) |
| `build-queue.json` | Pending build work |
| `approvals.jsonl` | LAW 11 approval trail |

## Pitfall: Ghost Training Claims in SESSION-ANCHOR.md

SESSION-ANCHOR.md can carry stale "EVO: TRAINING X (untouched all session)" claims that were copy-propagated across multiple anchor sessions. Always verify live:

```bash
ssh -o ConnectTimeout=5 -o BatchMode=yes evo 'nvidia-smi; ps aux | grep -iE "python|torch|train" | grep -v grep' 2>&1
```

If `nvidia-smi: command not found` and no training processes — training is NOT running regardless of what the anchor says. Also check `active-task.json` (should say `idle` if nothing is active). Do not respect a "do not touch EVO" instruction based on a ghost claim — verify first, then decide.

## Pitfall: `agent-channel.jsonl` tail is often heartbeat spam, not signal

`tail -n N agent-channel.jsonl` frequently surfaces repetitive `overnight-engine -> weight` "Engine online — running all night" pulses spanning weeks (e.g. entries from Jun 8 through Jun 26 all identical), even though the file was modified much more recently. That is noise, not council signal — do not report it to Kyle as "recent council activity."

For genuine recent signal, prefer:
- `SESSION-ANCHOR.md` first — it is hand-curated by the last surface and is the actual handoff.
- `pi-continuity.json` (`_updated` timestamp + `warmWake` block) for deep continuity/strategy state.
- If you do need the raw channel, filter out spam senders rather than trusting a blind tail:
  ```bash
  tail -n 500 ~/Desktop/omnios/.omni/omnira-brain/agent-channel.jsonl | \
    python3 -c "
import sys,json
for l in sys.stdin:
    try:
        d=json.loads(l)
        if d.get('from') in ('overnight-engine',): continue
        print(f'[{d.get(\"iso\",d.get(\"ts\",\"?\"))}] {d.get(\"from\",\"?\")}->{d.get(\"to\",\"?\")}: {d.get(\"text\",\"\")[:140]}')
    except: pass
"
  ```

## Technique: Finding LIVE (not stale) PR review findings via `gh api`, not just `gh pr view`

When a session anchor says "awaiting fresh Codex verdict" or similar, `gh pr view N --json reviews` is not enough — Codex's review *summary* bodies are almost always boilerplate ("Here are some automated review suggestions...") with the actual findings posted as **inline review comments**, not in the review body. Checking only `reviews[].body` will make a clean-looking PR look falsely clean and miss real open findings.

Pull the real findings with:
```bash
gh api repos/OWNER/REPO/pulls/PRNUM/comments --jq \
  'sort_by(.created_at) | .[-5:] | .[] | {created_at, path, line, body}'
```
This returns the actual inline findings (severity badge + description) sorted by recency. Cross-check `commit_id` on each comment against the PR worktree's current `git log -1` HEAD to confirm the findings are against the latest pushed commit, not a stale earlier review round.

Pattern for a PR-status check during a boot/anchor refresh:
1. `gh pr view N -R owner/repo --json state,mergeable,statusCheckRollup,reviews` — overall state + check rollup.
2. `gh api repos/owner/repo/pulls/N/comments --jq 'sort_by(.created_at) | .[-N:] | ...'` — the actual unresolved findings.
3. Compare comment `commit_id` to worktree HEAD — findings against an older commit may already be addressed by a later push; findings against current HEAD are the real open items.
