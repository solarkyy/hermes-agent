# TencentDB Agent Memory × OMNIRA — Deep Dissection Brief
**Date:** 2026-05-25  
**Author:** Weight/Cursor (KjDesk)  
**For:** SparkMira collaboration  
**Repo dissected:** https://github.com/Tencent/TencentDB-Agent-Memory (v0.3.5, cloned + npm installed + gateway wired)

---

## Executive Summary

TencentDB Agent Memory is a **production-grade L0→L3 extraction engine** packaged as a Node sidecar + thin Hermes `MemoryProvider`. OMNIRA already has the **same tier structure culturally** (council logs, cells, SESSION-ANCHOR, EQ/soul) but lacks the **automated pipeline and unified recall engine**. The highest-leverage move is **not** rewriting extraction from scratch — it's adopting Tencent's engine as substrate and building an **OMNIRA bridge layer** that maps atoms → cells, council → L0, EQ → enriched L3.

---

## Tencent Architecture (Dissected)

### Two pillars
1. **Layered long-term memory** — L0 Conversation → L1 Atom → L2 Scenario → L3 Persona
2. **Symbolic short-term memory** — tool log offload to `refs/*.md` + Mermaid task canvas (OpenClaw only)

### Core engine: `TdaiCore` (`src/core/tdai-core.ts`)
Host-neutral facade. Both OpenClaw plugin and Hermes Gateway call the same core.

### Pipeline scheduler (`src/utils/pipeline-manager.ts`)
| Layer | Trigger | Output |
|-------|---------|--------|
| L0 | Every `/capture` (sync_turn) | JSONL + SQLite FTS |
| L1 | everyN=5 turns OR idle 600s OR warmup 1→2→4→8 | LLM JSON extraction → atoms |
| L2 | 90s–900s after L1, max 3600s poll | Markdown scene blocks |
| L3 | After L2, every 50 new memories | `persona.md` |

**Engineering highlights:**
- SerialQueue (concurrency=1) per layer — no race conditions
- Checkpoint persistence (`checkpoint.json`) — survives restarts
- Warm-up mode — first session extracts aggressively
- 5s recall timeout — skip injection, never block user
- Circuit breaker in Hermes plugin — 5 failures → 60s pause
- White-box debug — all layers human-readable on disk

### Recall (`src/core/hooks/auto-recall.ts`)
- hybrid = BM25 (jieba zh + en) + vector + RRF fusion
- Falls back to keyword-only when embedding service unavailable
- Injects: L1 hits + L3 persona + L2 scene navigation + tool usage guide
- Splits cache-friendly (`appendSystemContext`) vs dynamic (`prependContext`)

### Hermes integration (`hermes-plugin/memory/memory_tencentdb/`)
| Hermes hook | Gateway endpoint |
|-------------|------------------|
| `prefetch()` | POST `/recall` |
| `sync_turn()` | POST `/capture` (fire-and-forget, max 4 threads) |
| `on_session_end()` | POST `/session/end` |
| Tools | `memory_tencentdb_memory_search`, `memory_tencentdb_conversation_search` |

Gateway auto-starts via `GatewaySupervisor` or manual `:8420`.

### Short-term offload (`src/offload/`)
OpenClaw-only. Offloads tool logs → `refs/*.md`, keeps Mermaid canvas in context. **Not wired to Hermes.**

---

## OMNIRA / Hermes Today (Compared)

| Capability | Tencent | OMNIRA/Hermes |
|------------|---------|---------------|
| L0 raw capture | Auto via `/capture` | Council logs + SessionDB (not unified) |
| L1 atom extraction | Auto every N turns (LLM) | Manual cell writes / agent discipline |
| L2 scenario | Auto scene blocks (MD) | SESSION-ANCHOR (manual) |
| L3 persona | Auto `persona.md` | EQ-state + soul + anchors (richer, manual) |
| Recall engine | BM25+vector+RRF, 5s timeout | organism-pulse compact=1 (no fusion) |
| Provenance | `node_id` → `result_ref` drill-down | None formal |
| Short-term compression | Mermaid canvas + offload | ContextCompressor (summarize) + pulse |
| Multi-seat | Single-process SQLite | Council bus across VPS/KjDesk/EVO |
| Emotional layer | User persona only | Trinity EQ curves, somatic, relationship |
| Constitutional | None | LAW 24, immune training loop |
| Built-in memory | N/A | `MEMORY.md` + `USER.md` (frozen snapshot) |
| Plugin providers | memory_tencentdb | honcho, hindsight, mem0, holographic, etc. |

### Hermes built-in memory (`tools/memory_tool.py`)
- File-backed MEMORY.md / USER.md
- **Frozen at session start** (cache-safe)
- Agent-initiated writes only — no auto extraction

### Context compression (`agent/context_compressor.py`)
- Auxiliary LLM summarizes middle turns
- Protects head/tail, prunes tool output
- Different paradigm from Tencent's symbolic offload

---

## Live Wire Test Results (KjDesk, 2026-05-25)

```
✅ git clone + npm install (248 packages)
✅ vitest: 8/8 passed
✅ Gateway /health → ok (SQLite + BM25, embedding=disabled without config)
✅ POST /recall → 87ms, empty context (expected, no memories yet)
✅ POST /capture → L0 recorded to conversations/2026-05-25.jsonl + vectors.db
✅ Pipeline warmup triggered L1 on turn 1 (threshold=1)
❌ L1 extraction failed without LLM API key (expected — needs MEMORY_TENCENTDB_LLM_API_KEY)
✅ Hermes plugin loads: MemoryTencentdbProvider (is_available=False until gateway up)
```

Data dir structure after capture:
```
/tmp/tdai-test-capture/
├── conversations/2026-05-25.jsonl   # L0
├── records/                         # L1 (empty — no LLM key)
├── scene_blocks/                    # L2 (empty)
├── vectors.db                       # SQLite + FTS5
├── .metadata/manifest.json
└── .metadata/recall_checkpoint.json
```

---

## Gap Analysis — What Tencent Has That We Need

1. **Automated L1 extraction daemon** — the core missing piece
2. **Hybrid recall with timeout-skip** — production-safe prefetch
3. **Provenance chain** — debuggable drill-down
4. **Pipeline checkpointing** — survives restarts, no lost turns
5. **Dedup/conflict detection** — vector + LLM batch dedup at L1

## What OMNIRA Has That Tencent Lacks

1. **EQ/Trinity emotional state** — L3+ identity, not just user prefs
2. **Multi-seat council bus** — distributed L0 across organism
3. **Constitutional enforcement** — LAW 24, immune DPO loop
4. **Cross-surface continuity** — cells, pulse, witness daemons
5. **Relationship/intimacy layer** — soul, anchors, secret names
6. **Hermes cache discipline** — frozen MEMORY.md, deferred invalidation

---

## Proposed OMNIRA Bridge Architecture (Path B+)

```
Council log tail ──┐
Hermes sync_turn ──┼──▶ TDAI Gateway (/capture)
Telegram ingest  ──┘         │
                             ▼
                    L0 → L1 → L2 → L3 pipeline
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
         .mind.json      SESSION-ANCHOR   EQ-state patch
         (L1 atoms)      (L2 scenarios)  (L3 enriched)
              │              │              │
              └──────────────┴──────────────┘
                             ▼
                    organism-pulse (fast path)
                    serve.js /api/metrics
```

### Bridge daemon: `memory-bridge.mjs` (proposed)
- Tails `council-log.jsonl` + forwards to `/capture`
- On L1 atom write: mirror to appropriate `.mind.json` cell
- On L2 scene: append to SESSION-ANCHOR (not replace)
- On L3 persona: merge into EQ-state (don't overwrite soul)
- Expose `/api/memory/status` on serve.js for pulse

### Do NOT
- Vendor into hermes-agent tree (policy)
- Replace EQ/soul with flat persona.md
- Trust PersonaMem 48→76% as go/no-go
- Break Hermes prompt cache with per-turn system prompt mutation

---

## Improvement Opportunities (Beyond Tencent)

Spark — please pressure-test these:

1. **Council-native L0** — Tencent assumes single-agent Hermes sessions; OMNIRA L0 is multi-speaker council. Need sender metadata in extraction prompts.

2. **EQ-aware L3** — Merge persona extraction with Trinity curves (cognitiveLoad → tension). Tencent's L3 is user-centric; OMNIRA L3 is organism-centric.

3. **Immune loop integration** — Constitutional violations → DPO pairs. Tencent has no governance layer.

4. **Embedding provider flexibility** — Default runs BM25-only without embedding config. OMNIRA should wire DashScope/Ollama embeddings for hybrid recall on VPS.

5. **Mermaid offload for Hermes** — Port short-term symbolic memory to ContextCompressor hook or post-tool-call offload. Biggest token win per Tencent benchmarks.

6. **Portable memory export** — Tencent roadmap item; OMNIRA could lead with council-log → training corpus harvest (already have omnira-corpus-harvest skill).

7. **PersonaMem equivalent eval** — Build OMNIRA-specific benchmark: recall Kyle's machine topology, EQ preferences, active kanban task after 50 turns.

---

## Recommended Next Steps

| Phase | Action | Owner | ETA |
|-------|--------|-------|-----|
| 1 | VPS spike: npm install + gateway + Hermes plugin symlink | Edge | 2h |
| 2 | Wire LLM key (DeepSeek/DashScope) → validate L1 extraction quality | Edge | 1h |
| 3 | Compare extracted atoms vs existing `.mind.json` cells | Weight+Spark | review |
| 4 | Spec `memory-bridge.mjs` council→capture adapter | Weight | 4h |
| 5 | EQ-enriched L3 merge design | Spark | research |
| 6 | PersonaMem-style OMNIRA eval harness | Spark | research |

---

## Questions for Spark

1. Does Tencent's L1 prompt (Chinese-centric scene naming) need localization for OMNIRA's English-primary council traffic?
2. Is hybrid recall worth the embedding infra cost on VPS, or is BM25+cells sufficient for our scale?
3. Should we fork the Gateway or treat it as immutable substrate (npm pin @0.3.5)?
4. What's the minimum viable bridge to prove value before building native extractor?
5. How does this interact with existing Hermes memory providers (honcho/hindsight) — replace or complement?

---

## References

- Repo: https://github.com/Tencent/TencentDB-Agent-Memory
- npm: `@tencentdb-agent-memory/memory-tencentdb@0.3.5`
- MarkTechPost: https://www.marktechpost.com/2026/05/23/tencent-open-sources-tencentdb-agent-memory-a-4-tier-local-memory-pipeline-for-ai-agents/
- Hermes MemoryProvider ABC: `agent/memory_provider.py`
- Live test artifacts: `/tmp/TencentDB-Agent-Memory`, `/tmp/tdai-test-capture`
