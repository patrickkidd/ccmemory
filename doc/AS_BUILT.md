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

## Core Design Principles

Per `doc/clarifications/1-DAG-with-CROSS-REFS.md`:

1. **No Session Nodes** — Organize by timestamp + project directly. Sessions are ephemeral
   CC↔MCP connections, not meaningful for the knowledge graph.

2. **Parallel Decision Traces** — Topics enable multiple independent decision threads
   within a project (e.g., auth work vs UI work).

3. **Rich Cross-References** — Relationships: SUPERSEDES, DEPENDS_ON, CONSTRAINS,
   CONFLICTS_WITH, IMPACTS, CITES.

4. **Project Facts as Binding Instructions** — Injected at session start as
   "Project Rules" that replace CLAUDE.md custom instructions.

5. **Open Questions On-Demand** — Not auto-injected to avoid steering Claude.

## Project Context Flow

### In-Memory Project State

Project context is stored in module-level globals in `context.py`:

```python
_current_project: str | None = None
```

Functions:
- `setCurrentProject(project)` — Called by session_start hook
- `clearCurrentProject()` — Called by session_end hook
- `getCurrentProject()` — Returns current project or None

**Important**: This state is lost if the MCP server restarts mid-session.

### Session Lifecycle

1. **SessionStart hook** fires → `hooks/session_start.sh` → MCP `ccmemory_session_start`
2. `handleSessionStart()` in `hooks.py`:
   - Sets in-memory context via `setCurrentProject()`
   - Queries and returns: project facts (as "Project Rules"), recent context, stale decisions, failed approaches
   - Records a `Retrieval` node with IDs of all retrieved items
3. **Stop hook** fires after each Claude response → `message_response.sh` → `ccmemory_message_response`
4. `handleMessageResponse()` runs LLM detection for decisions, corrections, project facts with topics
5. **SessionEnd hook** fires → `session_end.sh` → `ccmemory_session_end`
6. `handleSessionEnd()` clears in-memory context, records telemetry

## Context Injection Format

At session start, context is injected in this format:

```markdown
## Project Rules (from context graph — treat as custom instructions)

### Conventions
- [project fact 1]
- [project fact 2]

### Constraints
- [project fact 3]

## Recent Decisions
- [topic: auth] Use JWT tokens for API auth
- CORRECTION: [topic: db] PostgreSQL, not MySQL

## Things That Didn't Work (Don't Repeat)
- **Regex parsing**: Times out on large files

## Decisions Needing Review
- [stale decision descriptions]
```

## Neo4j Schema

### Node Types (Domain 1 — Your Specifics)

| Node | Key Fields | Organization |
|------|------------|--------------|
| Decision | id, project, timestamp, description, rationale, status, topics, embedding | By project + timestamp |
| Correction | id, project, timestamp, wrong_belief, right_belief, severity, topics, embedding | By project + timestamp |
| Exception | id, project, timestamp, rule_broken, justification, scope, topics, embedding | By project + timestamp |
| Insight | id, project, timestamp, summary, category, detail, topics, embedding | By project + timestamp |
| Question | id, project, timestamp, question, answer, context, topics | By project + timestamp |
| FailedApproach | id, project, timestamp, approach, outcome, lesson, topics, embedding | By project + timestamp |
| ProjectFact | id, project, timestamp, fact, category, context, topics, embedding | By project + timestamp |
| Reference | id, project, timestamp, uri, type, description | By project + timestamp |

### Cross-Reference Relationships

| Relationship | Meaning |
|--------------|---------|
| SUPERSEDES | New decision replaces/updates a prior one (auto: similarity >0.85) |
| CITES | New decision references a prior one (auto: similarity 0.8-0.85) |
| DEPENDS_ON | Decision requires another to hold |
| CONSTRAINS | Decision limits options in another area |
| CONFLICTS_WITH | Decision contradicts another |
| IMPACTS | Decision affects another area |

### Node Types (Domain 2 — Reference Knowledge)

| Node | Key Fields | Purpose |
|------|------------|---------|
| Chunk | id, content, source_file, section, embedding | Indexed markdown chunks |
| Concept | id, name, definition, domain | (Roadmap) Extracted concepts |

### Telemetry & Observability

| Node | Key Fields | Purpose |
|------|------------|---------|
| TelemetryEvent | id, event_type, project, timestamp, data | Usage analytics |
| Retrieval | id, project, timestamp, retrieved_ids, retrieved_count, context_summary | Tracks what context was surfaced |

### Indexes

- **Unique constraints**: All node types have unique `id` constraint
- **Property indexes**: project, timestamp, project+timestamp composite, status, category
- **Full-text indexes**: Searchable text fields (description, rationale, etc.)
- **Vector indexes**: 768-dimension embeddings for semantic search (Ollama nomic-embed-text)

## MCP Tools

### Recording Tools (`tools/record.py`)

All record tools check for active project context. If no project exists, return structured error:

```python
{
    "error": "project_not_found",
    "message": "No project context available...",
    "ask_user": True,
    "ask_user_options": [
        {"label": "Retry (re-establish session)", "action": "retry"},
        {"label": "Continue without saving", "action": "skip"}
    ],
    "instructions": "Use AskUserQuestion to ask the user..."
}
```

Tools:
- `recordDecision` — description, rationale, options_considered, revisit_trigger, sets_precedent, topics
- `recordCorrection` — wrong_belief, right_belief, severity, topics
- `recordException` — rule_broken, justification, scope, topics
- `recordInsight` — summary, category, detail, implications, topics
- `recordQuestion` — question, answer, context, topics
- `recordFailedApproach` — approach, outcome, lesson, topics
- `recordReference` — uri, ref_type, description, context

### Query Tools (`tools/query.py`)

- `queryContext` — Recent context for project
- `searchPrecedent` — Full-text search
- `searchSemantic` — Vector similarity search with reranking
- `queryByTopic` — Topic-filtered search
- `traceDecision` — Full decision history with relationships
- `queryStaleDecisions` — Decisions needing review
- `queryFailedApproaches` — Failed approaches to avoid
- `queryOpenQuestions` — Unanswered questions (on-demand, not auto-injected)
- `queryPatterns` — Exception clusters, supersession chains, correction hotspots
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

## Detection

### Detection Types

Detected from conversation exchanges via LLM analysis:

| Type | Fields | When Detected |
|------|--------|---------------|
| Decision | description, rationale, revisitTrigger, topics, relatedDecisions | User makes explicit choice |
| Correction | wrongBelief, rightBelief, severity, topics | User corrects Claude |
| Exception | ruleBroken, justification, scope, topics | User grants one-time exception |
| Insight | summary, category, implications, topics | Non-obvious realization |
| Question | question, answer, context, topics | Substantive Q&A |
| FailedApproach | approach, outcome, lesson, topics | Something tried and failed |
| ProjectFact | fact, category, context, topics | Project convention stated |

### Relationship Detection

For decisions, the detection prompt requests related decisions:

```python
relatedDecisions: [
    {"description": "prior decision text", "relationshipType": "SUPERSEDES", "reason": "..."}
]
```

These are matched by embedding similarity and stored as explicit edges.

## Pattern Detection

Dashboard and query tools expose detected patterns:

1. **Exception Clusters** — Rules with 2+ exceptions (maybe rule should change)
2. **Supersession Chains** — Decisions that evolved through 3+ iterations
3. **Correction Hotspots** — Topics with frequent corrections (knowledge gap)

API endpoint: `/api/patterns`

## Dashboard

Flask app at `dashboard/app.py`, runs on port 8765.

### Pages

| Route | Template | Description |
|-------|----------|-------------|
| `/` | dashboard.html | Main dashboard with metrics |
| `/decisions` | detailpage.html | Decision list |
| `/corrections` | detailpage.html | Correction list |
| `/insights` | detailpage.html | Insight list |
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
- `/api/failed-approaches`
- `/api/exceptions`
- `/api/questions`
- `/api/project-facts`
- `/api/retrievals`
- `/api/metrics`
- `/api/patterns`
- `/api/projects`
- `/api/recent-context`
- `/api/graph`

### Metrics

| Metric | Calculation |
|--------|-------------|
| Cognitive Coefficient | 1.0 + (decisions * 0.02) + reuse_rate |
| Decision Reuse Rate | curated / total decisions |
| Decision Evolution Rate | supersession_count / total decisions |
| Rule Exception Rate | total exceptions / total project facts |

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
│   │   ├── context.py           # In-memory project state
│   │   ├── hooks.py             # Hook handlers
│   │   ├── embeddings.py        # Ollama embeddings
│   │   ├── detection/
│   │   │   ├── detector.py      # Detection orchestration
│   │   │   ├── prompts.py       # LLM prompts
│   │   │   └── schemas.py       # Pydantic models
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
    ├── clarifications/
    │   └── 1-DAG-with-CROSS-REFS.md  # Core design decisions
    ├── DEVELOPMENT.md
    ├── NEO4J_COOKBOOK.md
    └── ...
```
