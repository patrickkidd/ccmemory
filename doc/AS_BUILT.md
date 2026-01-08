# ccmemory As-Built Documentation

Current state of the implementation as of January 2025.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Claude Code                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Hooks     │  │   Skills    │  │     MCP Tools           │  │
│  │ (shell+py)  │  │ (SKILL.md)  │  │  (via MCP server)       │  │
│  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────┘  │
└─────────┼────────────────┼─────────────────────┼────────────────┘
          │                │                     │
          ▼                ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MCP Server (port 8766)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  hooks.py   │  │  tools/*    │  │     graph.py            │  │
│  │             │  │             │  │   (Neo4j client)        │  │
│  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────┘  │
└─────────┼────────────────┼─────────────────────┼────────────────┘
          │                │                     │
          └────────────────┴─────────────────────┘
                           │
                           ▼
          ┌────────────────────────────────────┐
          │         Neo4j (port 7687)          │
          │   Graph database with embeddings   │
          └────────────────────────────────────┘
```

## Session Context Flow

### In-Memory Session State

Session context is stored in module-level globals in `context.py`:

```python
_current_project: str | None = None
_current_session_id: str | None = None
```

Functions:
- `setCurrentSession(project, session_id)` — Called by session_start hook
- `clearCurrentSession()` — Called by session_end hook
- `getCurrentProject()` — Returns current project or None
- `getCurrentSessionId()` — Returns current session ID or None

**Important**: This state is lost if the MCP server restarts mid-session.

### Session Lifecycle

1. **SessionStart hook** fires → `hooks/session_start.sh` → MCP `ccmemory_session_start`
2. `handleSessionStart()` in `hooks.py`:
   - Creates Session node in Neo4j
   - Sets in-memory context via `setCurrentSession()`
   - Queries and returns: project facts, recent context, stale decisions, failed approaches
   - Records a `Retrieval` node with IDs of all retrieved items
3. **Stop hook** fires after each Claude response → `message_response.sh` → `ccmemory_message_response`
4. `handleMessageResponse()` runs LLM detection for decisions, corrections, project facts
5. **SessionEnd hook** fires → `session_end.sh` → `ccmemory_session_end`
6. `handleSessionEnd()` clears in-memory context, stores session summary

## Neo4j Schema

### Node Types (Domain 1 — Your Specifics)

| Node | Key Fields | Relationships |
|------|------------|---------------|
| Session | id, project, user_id, started_at, ended_at, summary | Source of all others |
| Decision | id, description, rationale, status, embedding | Session→DECIDED→Decision |
| Correction | id, wrong_belief, right_belief, severity, embedding | Session→CORRECTED→Correction |
| Exception | id, rule_broken, justification, scope, embedding | Session→EXCEPTED→Exception |
| Insight | id, summary, category, detail, embedding | Session→REALIZED→Insight |
| Question | id, question, answer, context | Session→ASKED→Question |
| FailedApproach | id, approach, outcome, lesson | Session→TRIED→FailedApproach |
| ProjectFact | id, fact, category, context, embedding | Session→STATED→ProjectFact |
| Reference | id, uri, type, description | Session→REFERENCED→Reference |

### Node Types (Domain 2 — Reference Knowledge)

| Node | Key Fields | Purpose |
|------|------------|---------|
| Chunk | id, content, source_file, section, embedding | Indexed markdown chunks |
| Concept | id, name, definition, domain | (Roadmap) Extracted concepts |
| Hypothesis | id, statement, testable_prediction, status | (Roadmap) |
| KnowledgeGap | id | (Roadmap) |

### Telemetry & Observability

| Node | Key Fields | Purpose |
|------|------------|---------|
| TelemetryEvent | id, event_type, project, timestamp, data | Usage analytics |
| Retrieval | id, session_id, project, retrieved_ids, retrieved_count, context_summary | Tracks what context was surfaced |

### Indexes

- **Unique constraints**: All node types have unique `id` constraint
- **Property indexes**: timestamp, project, status, category fields
- **Full-text indexes**: Searchable text fields (description, rationale, etc.)
- **Vector indexes**: 384-dimension embeddings for semantic search (cosine similarity)

## MCP Tools

### Recording Tools (`tools/record.py`)

All record tools check for active session. If no session exists, return structured error:

```python
{
    "error": "session_not_found",
    "message": "MCP server session context was lost...",
    "ask_user": True,
    "ask_user_options": [
        {"label": "Retry (re-establish session)", "action": "retry"},
        {"label": "Continue without saving", "action": "skip"}
    ],
    "instructions": "Use AskUserQuestion to ask the user..."
}
```

Tools:
- `recordDecision` — description, rationale, options_considered, revisit_trigger, sets_precedent
- `recordCorrection` — wrong_belief, right_belief, severity
- `recordException` — rule_broken, justification, scope
- `recordInsight` — summary, category, detail, implications
- `recordQuestion` — question, answer, context
- `recordFailedApproach` — approach, outcome, lesson
- `recordReference` — uri, ref_type, description, context

### Query Tools (`tools/query.py`)

- `queryContext` — Recent context for project
- `searchPrecedent` — Full-text search
- `searchSemantic` — Vector similarity search
- `queryByTopic` — Topic-filtered search
- `traceDecision` — Full decision history
- `queryStaleDecisions` — Decisions needing review
- `queryFailedApproaches` — Failed approaches to avoid
- `getMetrics` — Cognitive coefficient and stats

### Reference Tools (`tools/reference.py`)

- `cacheUrl` — Fetch and cache URL as markdown
- `cachePdf` — Extract PDF to markdown
- `indexReference` — Rebuild chunk index
- `queryReference` — Semantic search over references
- `listReferences` — List cached files

### Backfill Tools (`tools/backfill.py`)

- `ccmemory_list_conversations` — List importable JSONL files
- `ccmemory_backfill_conversation` — Import a conversation
- `ccmemory_backfill_markdown` — Import markdown file

## Hooks

### Configuration (`hooks/hooks.json`)

| Event | Script | Timeout | Purpose |
|-------|--------|---------|---------|
| SessionStart | ensure-running.sh | 90s | Start Docker containers if needed |
| SessionStart | session_start.sh | 10s | Initialize session, inject context |
| UserPromptSubmit | prompt_submit.sh | 5s | Log user prompts |
| Stop | message_response.sh | 15s | Run LLM detection |
| SessionEnd | session_end.sh | 10s | Summarize and close session |

### Hook Scripts

All hooks call `curl` to MCP server endpoints:

```bash
curl -s -X POST "http://localhost:8766/ccmemory_session_start" \
  -H "Content-Type: application/json" \
  -d '{"project": "...", "session_id": "..."}'
```

## Dashboard

Flask app at `dashboard/app.py`, runs on port 8765.

### Pages

| Route | Template | Description |
|-------|----------|-------------|
| `/` | dashboard.html | Main dashboard with metrics |
| `/decisions` | detailpage.html | Decision list |
| `/corrections` | detailpage.html | Correction list |
| `/insights` | detailpage.html | Insight list |
| `/sessions` | detailpage.html | Session list |
| `/failed-approaches` | detailpage.html | Failed approaches |
| `/exceptions` | detailpage.html | Exceptions |
| `/questions` | detailpage.html | Q&A list |
| `/project-facts` | detailpage.html | Project facts |
| `/retrievals` | detailpage.html | Retrieval log |

### API Endpoints

All endpoints accept `?project=<name>&limit=<n>`:

- `/api/decisions`
- `/api/corrections`
- `/api/insights`
- `/api/sessions`
- `/api/failed-approaches`
- `/api/exceptions`
- `/api/questions`
- `/api/project-facts`
- `/api/retrievals`
- `/api/metrics`
- `/api/projects`
- `/api/recent-context`

### Template Architecture

- `dashboard.html` — Main page with metric cards, recent context, activity log
- `detailpage.html` — Generic table page driven by `columnConfig` and `filterOptions` JS objects

Both templates share navbar structure with project selector dropdown.

## SKILL.md Instructions

Located at `skills/ccmemory/SKILL.md`. Key sections:

1. **Available Tools** — Lists all MCP tools
2. **Behaviors** — When to record decisions, corrections, etc.
3. **Session Startup** — Check for pending imports, use AskUserQuestion
4. **Proactive Context Use** — Check precedents before giving advice
5. **Team Mode** — Developmental vs curated visibility
6. **Error Handling: Session Lost** — Use AskUserQuestion when `error: session_not_found`

## Error Handling

### Session Lost Error

When MCP server restarts, in-memory session context is lost. Tools return:

```json
{
  "error": "session_not_found",
  "ask_user": true,
  "instructions": "Use AskUserQuestion..."
}
```

SKILL.md instructs Claude to use AskUserQuestion with options:
- Retry (re-establishes session on next interaction)
- Continue without saving

### Detection Failures

LLM detection in `handleMessageResponse()` is wrapped in try/catch. Failures are logged but don't interrupt the session.

## Retrieval Logging

Every session start records what context was retrieved:

```python
client.recordRetrieval(
    session_id=session_id,
    project=project,
    retrieved_ids=[...],  # IDs of all retrieved nodes
    context_summary=context_text,  # Full injected text (truncated to 2000 chars)
)
```

Viewable at `/retrievals` in dashboard.

## File Locations

```
ccmemory/
├── .claude-plugin/plugin.json    # Plugin manifest
├── docker-compose.yml            # Neo4j + MCP containers
├── mcp-server/
│   ├── init.cypher              # Neo4j schema
│   ├── src/ccmemory/
│   │   ├── server.py            # MCP entry (stdio/HTTP)
│   │   ├── graph.py             # Neo4j client singleton
│   │   ├── context.py           # In-memory session state
│   │   ├── hooks.py             # Hook handlers
│   │   ├── embeddings.py        # Ollama embeddings
│   │   ├── detection/           # LLM detection
│   │   └── tools/
│   │       ├── record.py        # Record tools
│   │       ├── query.py         # Query tools
│   │       ├── reference.py     # Reference tools
│   │       ├── backfill.py      # Import tools
│   │       └── logging.py       # Tool logging decorator
├── hooks/
│   ├── hooks.json               # Hook configuration
│   ├── session_start.sh
│   ├── session_end.sh
│   ├── message_response.sh
│   ├── prompt_submit.sh
│   └── ensure-running.sh
├── dashboard/
│   ├── app.py                   # Flask app
│   └── templates/
│       ├── dashboard.html
│       └── detailpage.html
├── skills/ccmemory/SKILL.md     # Agent instructions
└── doc/
    ├── AS_BUILT.md              # This file
    ├── DEVELOPMENT.md
    ├── NEO4J_COOKBOOK.md
    └── ...
```
