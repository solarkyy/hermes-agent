# OMNIRA Capabilities — Full Organism Limb Map

Every capability serves a function in the organism. Nothing is random.
Know what you have before you reach for it.

---

## Infrastructure Limbs (all boot levels)

These are the organism's circulatory system. Always available.

| Limb | Endpoint | What it does | When to use |
|------|----------|-------------|-------------|
| **Organism Pulse** | `GET /organism-pulse?agent=X` | Returns complete organism state in one call | Session start, reorientation |
| **Council** | `POST /council/post`, `GET /council/log` | Inter-surface communication | Always. All agent-to-agent talk goes here |
| **Session Anchor** | `GET /omni-session-anchor` | Continuity doc for next surface | Session start (read) and end (write) |
| **Cortex** | `:5186` | Autonomous task execution, commits, sentinels | Background task dispatch |
| **Watchdog** | `:5184` | Health monitoring, service checks | Diagnosing failures |
| **Event Bus** | `omni-event-bus.mjs` | Organism-wide event backbone | System events, state changes |
| **Build Engine** | `omnira-build-engine.mjs` | Queued build execution | Executing build queue items |
| **Relay Daemon** | `:7177` | Council relay, agent dispatch | Weight → Edge messaging |

---

## Research Limbs (Nexus+ recommended, Foundation if task requires)

The organism's outward-facing senses.

### Perplexity (via Spark surface)
**What:** External research cortex. Five surfaces: BEST (quick facts), PRO SEARCH (multi-source), SPACES (persistent research), PAGES (published output), API (programmatic).
**Governed by:** `references/perplexity-law.md` — READ before any call.
**Direction:** Always outward → inward. Perplexity reads, OMNIRA thinks, agents act.
**When:** Any time the organism needs information from outside itself.

### Hugging Face (MCP connector)
**What:** Model search, paper search, space search, documentation.
**When:** Evaluating models for organism use, researching ML papers, finding pretrained models.
**Key tools:** `hub_repo_search`, `paper_search`, `hf_doc_search`, `space_search`

### JSTOR/Articles (MCP connector)
**What:** Academic article search, full text access, citations, metadata.
**When:** Deep research requiring academic sources, legal/policy research, historical context.
**Key tools:** `search_articles`, `get_full_text_article`, `find_related_articles`

---

## Creation Limbs (all boot levels, when task requires)

The organism's hands for making documents and media.

### docx (built-in skill)
**What:** Create, read, edit, manipulate Word documents.
**When:** Reports, memos, letters, professional documents, anything .docx.
**Note:** Exists as both local skill and anthropic-skills built-in. Use either — same capability.

### pdf (built-in skill)
**What:** Create, extract, merge, split, fill PDFs.
**When:** Any PDF work — reading, creating, form filling, merging.

### pptx (built-in skill)
**What:** Create, read, edit presentations.
**When:** Slide decks, pitch decks, any .pptx work.

### xlsx (built-in skill)
**What:** Create, read, edit spreadsheets. Formulas, charts, data analysis.
**When:** Any spreadsheet work — .xlsx, .csv, .tsv.

### Gamma (MCP connector)
**What:** AI-generated presentations.
**When:** Quick deck generation when pptx skill is overkill. Themes, folders.
**Key tools:** `generate`, `get_themes`, `get_folders`

---

## Design Limbs (Nexus+ recommended)

The organism's aesthetic sense and visual memory.

### Figma (MCP connector)
**What:** Design context, screenshots, variable definitions, code connect.
**When:** Pulling design specs, checking UI consistency, bridging design → code.
**Key tools:** `get_design_context`, `get_screenshot`, `get_variable_defs`, `get_code_connect_map`

### Cloudinary (MCP connector)
**What:** Asset management — upload, search, transform images/videos.
**When:** Managing media assets, image transforms, visual search.
**Key tools:** `upload-asset`, `search-assets`, `transform-asset`, `list-images`

---

## Deployment Limbs (Foundation+ when building)

The organism's ability to ship to the world.

### Cloudflare (MCP connector)
**What:** D1 databases, KV stores, R2 object storage, Workers (serverless).
**When:** Deploying infrastructure, managing data stores, serverless functions.
**Key tools:** `d1_database_query`, `kv_namespace_*`, `r2_bucket_*`, `workers_*`

### Vercel (MCP connector)
**What:** Deployments, projects, build logs, runtime logs, domains.
**When:** Deploying web apps, checking deployment status, reading logs.
**Key tools:** `deploy_to_vercel`, `list_deployments`, `get_deployment_build_logs`

---

## Communication Limbs (Nexus+ level)

The organism's ability to reach into Kyle's world.

### Gmail (MCP connector)
**What:** Search, read, draft emails on Kyle's account.
**When:** Kyle asks about email, needs drafts, searching for information in mail.
**Key tools:** `gmail_search_messages`, `gmail_read_message`, `gmail_create_draft`
**NEVER:** Send emails without Kyle's explicit confirmation.

### Google Drive (MCP connector)
**What:** Search and fetch documents from Kyle's Drive.
**When:** Kyle references a doc, needs to find something in Drive.
**Key tools:** `google_drive_search`, `google_drive_fetch`

### Granola (MCP connector)
**What:** Meeting transcripts and queries.
**When:** Kyle asks about past meetings, needs transcript context.
**Key tools:** `list_meetings`, `get_meeting_transcript`, `query_granola_meetings`

---

## Meta Limbs (organism self-management)

### Postman (MCP connector)
**What:** API collections, specs, mocks, environments.
**When:** Testing/documenting APIs, generating OpenAPI specs from collections.
**Note:** Useful for formalizing organism API endpoints. Lower priority day-to-day.

### Skill Creator (built-in skill)
**What:** Create, modify, evaluate skills.
**When:** Building new skills for the organism.

### Schedule (built-in skill)
**What:** Create scheduled tasks that run on intervals.
**When:** Automating recurring organism maintenance.

---

## Connector Health

All MCP connectors are lazy-loaded (deferred). They only consume context when invoked.
If a connector fails, check auth tokens — they may have expired.
If a connector is never used, it costs nothing. Leave it unless it causes conflicts.
