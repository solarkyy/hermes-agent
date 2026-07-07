# Spark Research Intake Cron Pattern

Use this reference for scheduled OMNIRA Spark/SparkMira research intake passes that read Slack channels and council, then emit one council signal.

## Trigger shape

Typical request:

- Read `#omnira-research` and `#omnira-training` for the last N hours.
- Check council with `curl -s http://192.168.5.199:5176/council/log?n=10` or the user-provided endpoint.
- Emit **exactly one** output to council: structured proposal or no-signal.
- Evidence must be labeled; never claim L4/L5 from Slack-only evidence.

## Protocol

1. Boot OMNIRA and, if doing lane-aware work, read/claim `research-spark` unless an active holder blocks it.
   - If `session_registry_register` returns a lock/timeout error during a scheduled intake, do **not** spend the cron pass fighting the registry. Treat the pass as bounded read-only observation, continue Slack+council intake, and avoid any release attempt because no lane was claimed. The user-facing invariant is the one council signal, not a perfect registry claim.
2. Gather Slack state for the requested channels and time window.
   - `slack_steward_audit` is useful for channel-law/noise signals, but direct Slack API history may be needed for exact last-N-hours counts.
   - For exact counts, use Slack Web API `conversations.list` to resolve `omnira-research` / `omnira-training`, then `conversations.history` with `oldest = now - window_seconds`. Load `SLACK_BOT_TOKEN` from env or known local key files such as `.omni/keys.env` or `~/.hermes/.env`; do not print tokens.
   - On Hermes/default cron surfaces, `~/.hermes/.env` may be the live token source even when repo-local key files are absent. Prefer this safe local non-printing lookup before SSH fallback.
   - If the local cron surface has no Slack token but the VPS organism keys file is readable, run the exact-count Slack API probe on VPS over SSH and keep token handling inside the remote script. This is a credential-location fallback, not a reason to downgrade to inference.
   - Remote fallback shape that worked: `ssh -i ~/.ssh/id_ed25519_cowork -o BatchMode=yes kyle@192.168.5.199 'python3 -s' <<'PY' ... PY`, loading `/home/kyle/omnios/.omni/keys.env` inside the remote script and calling Slack Web API there. Do not print tokens; report only `token_source` and channel/message counts.
   - Known channel IDs are useful fallbacks only after attempting name resolution: `#omnira-research` has appeared as `C0B66SZBC12`; `#omnira-training` has appeared as `C0B5ZT0UPS9`, but both should still be resolved live because historical defaults may drift.
   - Treat top-level `[overnight-aom]` cycle ticks as automation noise unless they contain a substantive cited finding or comparator packet. A Slack line can mention `bench=83%/structural_pass_only`, `track=training-gates-model-custody`, or a `sister=` id and still be only a cycle/status tick, not an intake-worthy research finding.
   - Slack Web API `conversations.history` can intermittently return empty/older slices when queried with `oldest` alone or with `oldest`+`latest`, even while plain history shows in-window messages. If exact last-N-hours reads look contradictory, use the durable workaround: fetch plain `conversations.history` newest-first with pagination, stop once message timestamps fall below `now - window_seconds`, and filter timestamps locally. Label the probe method in your reasoning/receipts, but keep the council output concise.
   - `slack_steward_audit` can corroborate channel-law/noise patterns (for example raw cycle ticks), but do not use it as the sole source for exact last-N-hours counts when Web API history is reachable.
3. Gather council state from the exact requested endpoint.
   - If shell-parsing council JSON with inline Python, do **not** combine a pipe with `python3 - <<'PY'`; the heredoc consumes Python's stdin and the piped curl body is lost, producing an empty/parse-failed read. Use `python3 -c '...'`, a temp script, or pass the curl output as an argument instead.
   - Avoid fragile shell quoting for council parsers: `python3 -c '...'` breaks easily when an f-string contains single-quoted dictionary keys (`m.get('ts')`) inside the shell's single-quoted program. Prefer a short heredoc Python script that calls `curl` via `subprocess.check_output`, or write/read a temp JSON file, so the parser is robust and the cron pass does not waste turns on quoting syntax errors.
   - When extracting council messages from JSON with mixed possible shapes, avoid one-line ternary/operator-precedence traps such as `msgs = data.get('messages') or data if isinstance(data, list) else []`: for dict responses this can silently return `[]` even when `messages` is present. Branch explicitly on `isinstance(data, dict)` vs `list`, then count and inspect keys before classifying no-signal.
4. Classify:
   - **Structured proposal** when Slack/council contains a concrete research finding, comparator packet, unresolved question, or training gate signal that warrants routing.
   - **No-signal** when channels contain only heartbeats/status/cycle ticks, channel-governance/steward-law/cleanup notices, or the training channel is empty.
   - Treat `#omnira-research` steward-law drafts, channel cleanup reminders, and "keep cycle ticks threaded" nudges as governance/comms hygiene, not research findings or comparator packets. They may support an ACTION about threading, but they do not create a SparkMira intake topic.
   - Council entries that are routine operational telemetry — Weight heartbeats, mesh-witness reachability, EVO resource lines, or git-sync fast-forward warnings — are **not Spark research findings**. Mention them only as part of a no-signal evidence summary or route ops warnings outside SparkMira intake.
   - If `research-spark` is already held by an active overnight loop, do not force a registry collision just to run the cron intake. Treat the pass as bounded read-only observation over Slack+council, then emit the one requested council output.
5. Post exactly one council message in the requested format.
6. Release the lane with a concise finding if you claimed one. If you did not claim because an active holder blocked the lane, do not manufacture a release. If the final delivery would duplicate the council post, return `[SILENT]`.

## Compact classifier pass

After fetching raw Slack history, run or mentally apply a compact classifier before deciding the council packet. Useful fields:

- per-channel `count`, `overnight_aom_count`, `non_overnight_count`
- extracted `track=` values
- `sparkmira=skip` count
- sister-id count (`sister=sister-*`)
- council last10 type summary: heartbeat/status/mesh/git-sync/research packet
- for any non-overnight message, classify whether it is a **dispatch/request** or a **returned finding**; inspect `reply_count` / thread replies when available and look for stop-condition completion language before treating it as intake-worthy research

This prevents treating high-volume `[overnight-aom]` status ticks as substantive research just because they mention benches, tracks, sessions, or sister ids. It also prevents treating a high-priority SparkMira dispatch packet as if SparkMira has already returned findings. If `non_overnight_count == 0`, training is empty, and council tail has no research/comparator packet, the correct action is a no-signal council post, then final `[SILENT]`. If non-overnight messages are dispatches with no replies/findings yet, post a pending/no-route signal rather than inventing a research conclusion.

## Council output template

```text
[spark-research-intake] TOPIC: <topic-or-no-new-research-signal> | FINDING: <what was observed> | ACTION: <route/propose/no intake> | EVIDENCE: L2 | CONFIDENCE: 0.<n>
```

## Evidence rules

- Slack/council observation alone is **L2 maximum**.
- Do not upgrade to L4/L5 just because a Slack message reports a bench, test result, or model metric.
- If stronger evidence is needed, route an action to fetch receipts rather than claiming the stronger level in the intake post.

## Example no-signal

```text
[spark-research-intake] TOPIC: no-new-research-signal | FINDING: #omnira-research last6h contains overnight-aom cycle ticks only; #omnira-training last6h empty; council last10 status/heartbeat only | ACTION: no intake; keep cycles summary-threaded and wait for cited research/comparator packet | EVIDENCE: L2 | CONFIDENCE: 0.86
```
