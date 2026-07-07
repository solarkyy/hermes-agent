# Council Delivery Reference for AOMS Sister Councils

## Council POST Endpoint

```
POST http://<host>:5176/council/post
Content-Type: application/json

{
  "from": "omnira-hermes",
  "to": "sparkmira" | "council" | "weight" | "edge" | "kyle",
  "text": "<message>",
  "priority": "high" | "normal" | "low"
}
```

## Target Destinations

| Target | Use Case |
|--------|----------|
| `sparkmira` | SparkMira agent (ChatGPT agent) — primary for synthesized plans |
| `council` | Broadcast to all council members |
| `weight` | Weight (organism thinking surface) |
| `edge` | Edge (build/deploy surface) |
| `kyle` | Direct to Kyle (Telegram/home channel) |

## Delivery Verification

Response format:
```json
{
  "ok": true,
  "id": "<message-id>",
  "from": "omnira-hermes",
  "to": "sparkmira",
  "deliveries": ["spark:dispatched"]
}
```

**Key field**: `deliveries` array shows where message was routed.
- `["spark:dispatched"]` = queued for SparkMira CDP lane
- `[]` = no active delivery path (SparkMira offline or not listening)

## Council Presentation Format

The synthesis sister produces a `council_presentation` field — a ~200 word executive summary. Use this as the `text` payload.

**Template**:
```
Council — here is the unified [timeframe] path to [north star]. We start TODAY by [phase 0 action]. Phase 0 (0-3mo): [key fixes]. Only then [phase 1]. Phase 1 (3-9mo): [embodiment]. Phase 2 (9-18mo): [agency]. Phase 3 (18-30mo): [proof milestone]. Phase 4 (30-60mo): [sovereignty]. [N] hard gates enforce go/no-go. The critical path is explicit: [first 3 blockers]. [N] actions are already defined. Let's begin with [action 1] and [action 2] — today.
```

## Delivery Checklist

- [ ] Use `to: "sparkmira"` for strategic plans (SparkMira reviews/blocks)
- [ ] Use `priority: "high"` for time-sensitive deliveries
- [ ] Verify `deliveries` includes expected route
- [ ] If `deliveries: []`, check SparkMira CDP lane health
- [ ] Log message ID for traceability
- [ ] Follow up in council if no response within SLA

## Common Failures

| Symptom | Cause | Fix |
|---------|-------|-----|
| `deliveries: []` | SparkMira CDP lane down | Check `sparkmira-kjdesk-agent.mjs` on :9223, Chrome :9222 |
| `ok: false` | Malformed payload | Validate JSON, required fields |
| Timeout | serve.js overloaded | Check serve.js :5176 health, PM2 status |
| No SparkMira response | Council async broken | See sister analysis: council protocol fix needed |

## Related Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /council/inbox?spark` | SparkMira polls for messages |
| `POST /council/respond` | SparkMira replies with `in_reply_to` |
| `GET /sparkmira/cdp/status` | CDP lane health |
| `POST /sparkmira/cdp/send` | Direct CDP message send |