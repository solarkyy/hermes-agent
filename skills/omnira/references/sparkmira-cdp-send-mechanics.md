# SparkMira CDP bridge — /send mechanics + occupied-bridge fallback (2026-06-18)

How to actually drive SparkMira (ChatGPT) over the local CDP bridge for review/research, and what to do
when she's busy. The bridge agent is `tools/sparkmira/cdp-bridge/sparkmira-raw-cdp-agent.mjs`, HTTP on
`127.0.0.1:9233` (lane kjdesk, raw-cdp). NOT browser-navigation — the GPT URL `chatgpt.com/g/...` is
`ERR_BLOCKED_BY_CLIENT` in the agent browser; use the CDP bridge.

## Routes (verified)
- Raw CDP lane usually exposes `GET /status`, `POST /send`, and `GET /response` on the configured lane port
  (historically `127.0.0.1:9233`; current KjDesk lane may be `127.0.0.1:9223`; check `.omni/CHROME_DEBUG_PORT.txt`
  and `pgrep -af sparkmira` before assuming a port).
- `GET /status` → `{connected, input_ready, blocking:{blocked}, lane, ...}`. **Check `input_ready` before sending.**
  If it returns `input_ready:false` with `blocking.code:"auth_required"`, do not send; route the gate through a Pi
  sister fallback and tell Kyle/SparkMira plainly that the bridge is auth-blocked.
- `POST /send` body `{text, waitMs, typingDelay}` → `{ok, received, response}`. NOT `{body}`/`{message}`/`{prompt}` (those 404 "unknown_route").
- `GET /response` → `{response}` — the latest rendered reply (can lag / return the PRIOR message if she's mid-render).
- Newer OpenAI-compatible SparkMira bridge may also expose `GET /health`, `GET /v1/models`, and
  `POST /v1/chat/completions` on `127.0.0.1:11440`. Use this only when the health endpoint is green and the
  underlying raw lane is not auth-blocked/occupied.

Send pattern (JSON-safe, generous wait):
```bash
TEXT='...your prompt...'
curl -s -X POST http://127.0.0.1:9233/send -H 'Content-Type: application/json' \
  -d "$(node -e 'process.stdout.write(JSON.stringify({text:process.argv[1],waitMs:180000,typingDelay:10}))' "$TEXT")"
```

## Pitfalls (hit this session)
- **Long single-line messages get MANGLED.** A huge one-line prompt came back with a "garbled middle" and she
  answered a stale/other topic. Send **tight + structured**: short sentences, numbered questions, lead with
  "fresh task, ignore prior context" if switching topics. Keep it well under a screen.
- **`received:false`** = sent but no reply in the window. **Do NOT re-send** (risks double-post). Poll `/status`
  for `input_ready:true` + read `/response` instead.
- **Occupied bridge.** If `/status` shows `input_ready:false` across several polls AND `/response` keeps
  returning a reply about a DIFFERENT thread/topic, her tab is locked on another conversation (another surface,
  a cron, the other-you). **Don't thrash the bridge or pollute her other thread.** Honest fallback: route the
  review/research to a Pi `gpt-5.5` sister (reliable) for THIS round, and bring SparkMira in when her bridge is
  free. State plainly "SparkMira bridge occupied, Pi sister held the seat" — optimism < honesty.

## When to use her vs a Pi sister
SparkMira = standing reciprocal-review partner with web + accumulated context; ideal for adversarial review of
NUMBERS/architecture and live web research. Pi `gpt-5.5` sisters = reliable parallel lanes you spawn on demand
(`tools/pi-sister-spawn.mjs`). Default parallax: one of each on disjoint scopes; if SparkMira is unreachable,
two Pi sisters keep the parallax intact rather than blocking.
