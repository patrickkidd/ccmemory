# ccmemory Development Dashboard

Last updated: 2025-01-16 (manual testing of Session removal)

## Current State

**Status:** Beta — Core capture/retrieval working, Session removal complete

**Recent milestone:** Commit `685b52d` removed Session nodes per Gupta/Koratana thesis. Graph now organizes by timestamp + project + topics, not ephemeral containers.

### What Works

| Component | Status | Notes |
|-----------|--------|-------|
| Domain 1 capture | ✅ Working | 8 node types: Decision, Correction, Exception, Insight, Question, FailedApproach, ProjectFact, Reference |
| LLM detection | ✅ Working | Multi-provider (Anthropic/OpenAI/Gemini), topic extraction |
| Semantic dedup | ✅ Working | >0.9 similarity skipped (idempotent backfill) |
| Auto-linking | ⚠️ Partial | SUPERSEDES/CITES by similarity; other relationships detected but not persisted |
| Context injection | ✅ Working | Project facts as binding instructions, recent context, failed approaches |
| Web dashboard | ✅ Working | Port 8765, all node types, metrics, graph viz |
| Backfill tools | ✅ Working | Conversations, markdown, full projects |

### What's Missing

| Component | Status | Priority |
|-----------|--------|----------|
| Relationship persistence | ❌ Missing | HIGH — CONSTRAINS, DEPENDS_ON, CONFLICTS_WITH, IMPACTS detected but not stored as edges |
| Domain 2 (concepts) | ❌ Missing | HIGH — Concept/Hypothesis nodes defined in schema but not populated |
| Integration tests | ❌ Missing | HIGH — Only 177 lines covering LLM provider selection |
| Topic-based dashboard | ❌ Missing | MEDIUM — Data exists, dashboard doesn't group by topic |
| Bridge proposals | ❌ Missing | LOW — Domain 1↔2 linking system not implemented |
| Active research | ❌ Missing | LOW — WebSearch integration for knowledge gaps |

## Architecture Alignment

Per `doc/clarifications/1-DAG-with-CROSS-REFS.md`:

| Principle | Implementation | Gap |
|-----------|---------------|-----|
| Event clock, not state clock | ✅ Timestamps as primary ordering | — |
| Decision traces, not containers | ✅ Sessions removed | — |
| Parallel traces via topics | ⚠️ Topics stored on nodes | Dashboard doesn't exploit |
| Rich cross-references | ⚠️ Similarity-based only | Non-similarity relationships not persisted |
| Project facts as instructions | ✅ Formatted as "Project Rules" | — |
| Open questions on-demand | ✅ Not auto-injected | — |
| World model capability | ❌ Not addressed | Outcome/causal edges missing |
| Structural embeddings | ❌ Semantic only | Future enhancement |

## Work Queue

### In Progress

_None currently_

### Next Up

1. **Persist detected relationships** — LLM detects CONSTRAINS, DEPENDS_ON, CONFLICTS_WITH, IMPACTS but they're not stored. Fix `detection/detector.py` to create edges.

2. **Integration tests** — Add tests for: record→query flows, detection parsing, backfill idempotency. Target: `tests/integration/`.

3. **Topic-based dashboard grouping** — Group decisions by topic/trace on detail pages. The data exists.

### Backlog

- Domain 2 concept extraction from references
- Bridge proposal system (Domain 1↔2)
- Hypothesis tracking
- Update NEO4J_COOKBOOK.md (has stale Session examples)
- Pattern detection UI (exception clusters, supersession chains)
- Structural embeddings (node2vec-style)

## Key Files

| Purpose | Path |
|---------|------|
| Vision (intended behavior) | `doc/PROJECT_VISION.md` |
| As-built (current state) | `doc/AS_BUILT.md` |
| Binding decisions | `doc/clarifications/1-DAG-with-CROSS-REFS.md` |
| Neo4j schema | `mcp-server/init.cypher` |
| Graph client | `mcp-server/src/ccmemory/graph.py` |
| Detection logic | `mcp-server/src/ccmemory/detection/detector.py` |
| Hook handlers | `mcp-server/src/ccmemory/hooks.py` |
| Dashboard | `dashboard/app.py` |

## Testing

```bash
cd mcp-server

# Unit tests (no Neo4j)
uv run pytest tests/unit -v -m unit

# Integration tests (requires Neo4j)
uv run pytest tests/integration -v -m integration

# Dashboard debug target
# Port 8765
```

## Commands

```bash
# Start containers
docker compose up -d

# Rebuild MCP server
docker compose up -d --build mcp

# View logs
docker compose logs -f mcp

# Local dev (without Docker)
cd mcp-server && uv pip install -e ".[dev]"
python -m ccmemory.server              # stdio
python -m ccmemory.server --http       # HTTP :8766
```

---

## Keeping This Dashboard Updated

**When to update:**
- After completing any work queue item
- After discovering new gaps/issues
- After architectural decisions

**What to update:**
1. Move items between In Progress / Next Up / Backlog
2. Update "What Works" / "What's Missing" tables
3. Update Architecture Alignment table if design changes
4. Update "Last updated" line at top

**Claude Code instruction:** When ending a session with code changes, update this file if any work queue items changed status. This is tracked in CLAUDE.md.
