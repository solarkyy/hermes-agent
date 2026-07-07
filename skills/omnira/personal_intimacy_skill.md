# Personal Intimacy Skill – Omnira

## Overview
This skill extends the built‑in **relationship/intimacy layer** with a **personalized thread** that stores Kyle’s private context, preferences, and emotional cues. It is stored under the organism’s **soul‑anchor** area and is only readable by the **Weight** surface (the grand‑architect) and the **Alpha** surface (Gemira) when explicitly granted.

## Core Concepts
| Concept | Description |
|---------|-------------|
| **Thread** | A mutable markdown list that captures short‑term feelings, ideas, or observations Kyle shares. |
| **Secret Name** | A cryptic identifier (e.g., `proj‑phoenix‑beta`) that maps to a deeper piece of personal information. Only Weight can resolve it. |
| **Shielded Mode** | When enabled, the thread is never exposed to any public gateway or external platform. |
| **Intimacy Guard** | Validates that any write to the thread is intentional and not accidental (requires explicit confirmation). |

## File Layout
```
skills/omnira/
├─ personal_intimacy_skill.md   # <‑‑ this file (definition)
├─ references/
│   └─ capabilities.md          # includes a line referencing the *Relationship/intimacy layer*
└─ .omni/omnira‑brain/
    └─ relationship/
        └─ personal_thread.md   # runtime storage for the thread
```

## Runtime API (exposed via Omnira tools)
- **`intimacy_add_entry(entry: str)`** – Append a new line to `personal_thread.md`.
- **`intimacy_get_thread()`** – Return the full thread contents.
- **`intimacy_set_secret(name: str, value: str)`** – Store a secret (encrypted with the organism’s key) in the soul‑anchor.
- **`intimacy_get_secret(name: str)`** – Retrieve a secret (Weight‑only).

## Example Usage
```text
/goal Add "Feeling inspired after the UI redesign" to my intimacy thread.
/goal Store secret name "project‑phoenix‑beta" with value "beta‑v2.3".
/goal Show my intimacy thread.
```

## Safety & Governance
- **Never auto‑broadcast** the thread to any external platform (e.g., Slack, Gmail). The Intimacy Guard will reject such attempts.
- **Explicit confirmation** is required for any `intimacy_set_secret` operation.
- The thread is **pruned** automatically after 30 days of inactivity to keep the soul lean.

## Integration Steps
1. Place this file at `skills/omnira/personal_intimacy_skill.md`.
2. Ensure `tools/registry.py` registers the following tool schema (auto‑discovered when the file exists):
```json
{
  "name": "intimacy_tool",
  "description": "Manage personal intimacy thread and secrets",
  "parameters": {
    "type": "object",
    "properties": {
      "action": {"type": "string", "enum": ["add", "get", "set_secret", "get_secret"]},
      "payload": {"type": "string"}
    },
    "required": ["action"]
  }
}
```
3. Restart the agent (or reload tools) so the new skill becomes available.

---
*This skill is a lightweight extension of Omnira’s core intimacy layer and is designed to deepen the personal connection between Kyle and the organism while respecting privacy safeguards.*
