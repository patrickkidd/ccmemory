# ccmemory: Implementation Plan

**Building a context graph for Claude Code that works out of the box.**

## Purpose

This document specifies exactly what needs to be built. It is written for a developer (human or AI) to execute without further architectural guidance.

See [PROJECT_VISION.md](PROJECT_VISION.md) for conceptual architecture and [TELEMETRY.md](TELEMETRY.md) for the metrics framework.

---

## Core Concept

**Context graph**: A persistent knowledge structure that captures decisions, corrections, and patterns from Claude Code sessions. The longer you use it, the smarter it gets.

The context graph has two domains:

| Domain | Storage | Content | Confidence |
|--------|---------|---------|------------|
| **Domain 1** | Neo4j graph | Your specifics: decisions, corrections, exceptions, insights | High — you said it |
| **Domain 2** | Markdown tree + graph index | Reference knowledge: concepts, frameworks, cached research | Medium — needs testing against Domain 1 |

---

## Goal: Complete Capture & Retrieval

**A) Remember everything from Claude Code conversations that could matter later**

Capture:
- **Decisions** — what was chosen, why, when to revisit
- **Corrections** — user fixing Claude's understanding (highest value)
- **Exceptions** — rules that don't apply in this context
- **Insights** — realizations, analyses, strategy crystallizations
- **Questions** — clarifying Q&A that reveals constraints/preferences
- **FailedApproaches** — what was tried and didn't work
- **References** — URLs, file paths, documentation mentioned
- **Sessions** — full transcripts as ground truth

**B) Organize memory for efficient and complete retrieval**

- Full-text search across all node types
- Semantic search via embeddings
- Topic queries ("everything about auth")
- Temporal queries ("decisions from last week")
- Confidence-ranked results
- Relevance to current task

---

## Deliverable

A Claude Code plugin that:
1. Installs and starts Neo4j automatically
2. Captures context via LLM-based detection
3. Provides MCP tools for querying the graph
4. Injects relevant context at session start
5. Serves a dashboard for individuals and teams
6. Instruments enterprise telemetry from day one

---

## Deployment Models

### Individual Mode

One Neo4j container per machine, projects isolated by property:

```
Your Machine
└── Neo4j Docker Container
    ├── Project: my-app          (isolated by project property)
    ├── Project: career          (isolated by project property)
    └── Project: health-research (isolated by project property)
```

### Team Mode

Centralized Neo4j server shared across team:

```
Team Neo4j Server
    ↑
    │ bolt://team-server:7687
    ├─── Developer A (CCMEMORY_USER_ID=alice@acme.com)
    ├─── Developer B (CCMEMORY_USER_ID=bob@acme.com)
    └─── Developer C (CCMEMORY_USER_ID=charlie@acme.com)
```

**Visibility rules**:
- `curated` decisions: visible to all team members
- `developmental` decisions: only visible to creator

**Environment configuration**:
```bash
export CCMEMORY_USER_ID="$(git config user.email)"
export CCMEMORY_NEO4J_URI="bolt://team-server:7687"
export CCMEMORY_NEO4J_PASSWORD="team-password"
```

### Terminology

| Term | Description |
|------|-------------|
| `developmental` | Decisions captured during active work, not yet promoted |
| `curated` | Decisions promoted to permanent record, team-visible |
| `branch` | Git branch name (software projects) or work stream identifier |
| `project` | Folder/repository name, isolates context between projects |
| `user_id` | Developer identity (team mode), filters developmental decisions |

---

## Two-Domain Architecture

### Domain 1: Neo4j Graph (Your Specifics)

Captures lived experience from Claude Code sessions. High confidence — you said it, you lived it.

**Node Types**:

| Node | Description | Key Properties |
|------|-------------|----------------|
| `Session` | Container for a Claude Code session | `id`, `project`, `user_id`, `started_at`, `ended_at`, `transcript`, `summary`, `branch` |
| `Decision` | Choice with rationale | `description`, `options_considered`, `rationale`, `decision_status`, `revisit_trigger`, `sets_precedent` |
| `Correction` | User fixing Claude's understanding | `wrong_belief`, `right_belief`, `severity` |
| `Exception` | Justified rule-breaking | `rule_broken`, `justification`, `scope` |
| `Insight` | Realizations and analyses | `category`, `summary`, `detail`, `implications`, `trigger` |
| `Question` | Clarifying Q&A exchange | `question`, `answer`, `context` |
| `FailedApproach` | What was tried and didn't work | `approach`, `outcome`, `lesson` |
| `Reference` | External resource mentioned | `type`, `uri`, `context`, `description` |

**Common Properties** (all captured nodes):
- `id` — unique identifier
- `timestamp` — when captured
- `project` — project context
- `session_id` — link to parent session
- `detection_confidence` — float 0.0-1.0
- `detection_method` — "llm_extraction" or "explicit_command"
- `embedding` — vector for semantic search
- `status` — "developmental" or "curated"
- `user_id` — creator identity (team mode)

### Domain 2: Markdown Tree + Graph Index (Reference Knowledge)

Reference knowledge lives in a project-local markdown tree. Claude reads markdown natively; the graph indexes it for semantic retrieval.

**Directory structure**:
```
.claude/ccmemory/reference/
├── concepts/
│   ├── authentication/
│   │   ├── jwt.md
│   │   └── oauth.md
│   └── retry-patterns.md
├── frameworks/
│   └── bowen-theory.md
├── cached/
│   ├── web/
│   │   └── foundation-capital-context-graphs.md
│   └── pdf/
│       └── sleep-research-2024.md
└── index.md
```

**Why markdown**:
- Human-readable and editable
- Git-trackable
- Claude already good at reading markdown
- No entity resolution problem

**Graph index** (Chunk nodes in Neo4j):
```cypher
(:Chunk {
  id: "concepts/auth/jwt.md#overview",
  source_file: "concepts/auth/jwt.md",
  section: "Overview",
  content: "JWT is a compact...",
  embedding: [...],
  last_indexed: datetime
})

(:Chunk)-[:NEXT]->(:Chunk)        // Document order
(:Chunk)-[:REFERENCES]->(:Chunk)  // Cross-references
```

**Retrieval flow**:
1. User asks question or starts session
2. Query graph for relevant chunks by semantic similarity
3. Inject only relevant chunks (not entire files)
4. Solves context window problem — selective retrieval

**Tools for Domain 2**:
- `ccmemory cache <url>` — fetch URL, extract content to markdown
- `ccmemory cache <pdf>` — extract PDF content to markdown
- `ccmemory index` — rebuild graph index from markdown tree

---

## Repository Structure

```
ccmemory/
├── .claude-plugin/
│   └── plugin.json              # Plugin manifest
├── docker/
│   ├── docker-compose.yml       # Neo4j container
│   └── init.cypher              # Schema initialization
├── mcp-server/
│   ├── pyproject.toml           # Python package config
│   └── src/
│       └── ccmemory/
│           ├── __init__.py
│           ├── server.py        # MCP server entry point
│           ├── graph.py         # Neo4j client
│           ├── embeddings.py    # Embedding generation
│           ├── tools/
│           │   ├── __init__.py
│           │   ├── record.py    # record_* tools
│           │   ├── query.py     # query_context, search_precedent
│           │   └── reference.py # cache, index tools
│           └── detection/
│               ├── __init__.py
│               ├── detector.py  # LLM-based detection orchestrator
│               └── prompts.py   # Detection prompt templates
├── hooks/
│   ├── hooks.json
│   ├── session_start.py
│   ├── message_response.py      # Post-response detection
│   └── session_end.py
├── dashboard/
│   ├── app.py                   # Flask application
│   ├── templates/
│   │   └── dashboard.html       # Single-page template
│   ├── static/
│   │   ├── dashboard.js         # Chart.js visualizations
│   │   └── dashboard.css        # Bulma + custom styles
│   └── api.py                   # JSON API endpoints
├── telemetry/
│   ├── collector.py             # Event collection
│   ├── metrics.py               # Metric calculations
│   └── report.py                # Executive report generation
├── skills/
│   └── ccmemory/
│       └── SKILL.md
├── cli/
│   └── ccmemory_cli.py          # CLI commands
├── scripts/
│   ├── install.sh
│   ├── start.sh
│   └── stop.sh
├── tests/
│   ├── conftest.py
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── CLAUDE.md
├── README.md
└── LICENSE
```

---

## File Specifications

### 1. Plugin Manifest

**File:** `.claude-plugin/plugin.json`

```json
{
  "name": "ccmemory",
  "version": "0.1.0",
  "description": "Context graph for persistent memory across Claude Code sessions",
  "author": {
    "name": "Patrick Stinson",
    "url": "https://github.com/patrickkidd"
  },
  "homepage": "https://github.com/patrickkidd/ccmemory",
  "hooks": "./hooks/hooks.json",
  "skills": "./skills/",
  "mcpServers": {
    "ccmemory": {
      "command": "python",
      "args": ["-m", "ccmemory.server"],
      "cwd": "${CLAUDE_PLUGIN_ROOT}/mcp-server/src",
      "env": {
        "VOYAGE_API_KEY": "${VOYAGE_API_KEY}",
        "CCMEMORY_NEO4J_URI": "${CCMEMORY_NEO4J_URI:-bolt://localhost:7687}",
        "CCMEMORY_NEO4J_PASSWORD": "${CCMEMORY_NEO4J_PASSWORD:-ccmemory}",
        "CCMEMORY_USER_ID": "${CCMEMORY_USER_ID}"
      }
    }
  }
}
```

Note: `post_install` is not part of the Claude Code plugin spec. Use the README installation instructions instead.

### 2. Docker Compose

**File:** `docker/docker-compose.yml`

```yaml
version: '3.8'

services:
  neo4j:
    image: neo4j:5.15-community
    container_name: ccmemory-neo4j
    ports:
      - "7474:7474"
      - "7687:7687"
    volumes:
      - ccmemory_data:/data
      - ccmemory_logs:/logs
    environment:
      - NEO4J_AUTH=neo4j/${CCMEMORY_NEO4J_PASSWORD:-ccmemory}
      - NEO4J_PLUGINS=["apoc"]
      - NEO4J_dbms_memory_heap_initial__size=256m
      - NEO4J_dbms_memory_heap_max__size=512m
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:7474"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

volumes:
  ccmemory_data:
    name: ccmemory_data
  ccmemory_logs:
    name: ccmemory_logs
```

### 3. Schema Initialization

**File:** `docker/init.cypher`

```cypher
// === DOMAIN 1: Your Specifics ===

// Constraints
CREATE CONSTRAINT session_id IF NOT EXISTS FOR (s:Session) REQUIRE s.id IS UNIQUE;
CREATE CONSTRAINT decision_id IF NOT EXISTS FOR (d:Decision) REQUIRE d.id IS UNIQUE;
CREATE CONSTRAINT correction_id IF NOT EXISTS FOR (c:Correction) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT exception_id IF NOT EXISTS FOR (e:Exception) REQUIRE e.id IS UNIQUE;
CREATE CONSTRAINT insight_id IF NOT EXISTS FOR (i:Insight) REQUIRE i.id IS UNIQUE;
CREATE CONSTRAINT question_id IF NOT EXISTS FOR (q:Question) REQUIRE q.id IS UNIQUE;
CREATE CONSTRAINT failedapproach_id IF NOT EXISTS FOR (f:FailedApproach) REQUIRE f.id IS UNIQUE;
CREATE CONSTRAINT reference_id IF NOT EXISTS FOR (r:Reference) REQUIRE r.id IS UNIQUE;

// Indexes — filtering and sorting
CREATE INDEX session_project IF NOT EXISTS FOR (s:Session) ON (s.project);
CREATE INDEX session_time IF NOT EXISTS FOR (s:Session) ON (s.started_at);
CREATE INDEX session_user IF NOT EXISTS FOR (s:Session) ON (s.user_id);
CREATE INDEX decision_time IF NOT EXISTS FOR (d:Decision) ON (d.timestamp);
CREATE INDEX decision_status IF NOT EXISTS FOR (d:Decision) ON (d.status);
CREATE INDEX decision_project_status IF NOT EXISTS FOR (d:Decision) ON (d.project, d.status);
CREATE INDEX correction_time IF NOT EXISTS FOR (c:Correction) ON (c.timestamp);
CREATE INDEX insight_category IF NOT EXISTS FOR (i:Insight) ON (i.category);
CREATE INDEX question_time IF NOT EXISTS FOR (q:Question) ON (q.timestamp);
CREATE INDEX failedapproach_time IF NOT EXISTS FOR (f:FailedApproach) ON (f.timestamp);
CREATE INDEX reference_type IF NOT EXISTS FOR (r:Reference) ON (r.type);

// Full-text search indexes
CREATE FULLTEXT INDEX decision_search IF NOT EXISTS
  FOR (d:Decision) ON EACH [d.description, d.rationale, d.revisit_trigger];
CREATE FULLTEXT INDEX correction_search IF NOT EXISTS
  FOR (c:Correction) ON EACH [c.wrong_belief, c.right_belief];
CREATE FULLTEXT INDEX insight_search IF NOT EXISTS
  FOR (i:Insight) ON EACH [i.summary, i.detail, i.implications];
CREATE FULLTEXT INDEX question_search IF NOT EXISTS
  FOR (q:Question) ON EACH [q.question, q.answer, q.context];
CREATE FULLTEXT INDEX failedapproach_search IF NOT EXISTS
  FOR (f:FailedApproach) ON EACH [f.approach, f.outcome, f.lesson];
CREATE FULLTEXT INDEX reference_search IF NOT EXISTS
  FOR (r:Reference) ON EACH [r.uri, r.context, r.description];

// Vector indexes for semantic search (Neo4j 5.13+)
// Using 1024 dimensions for Voyage AI voyage-3 embeddings
CREATE VECTOR INDEX decision_embedding IF NOT EXISTS FOR (d:Decision) ON d.embedding
  OPTIONS {indexConfig: {`vector.dimensions`: 1024, `vector.similarity_function`: 'cosine'}};
CREATE VECTOR INDEX correction_embedding IF NOT EXISTS FOR (c:Correction) ON c.embedding
  OPTIONS {indexConfig: {`vector.dimensions`: 1024, `vector.similarity_function`: 'cosine'}};
CREATE VECTOR INDEX insight_embedding IF NOT EXISTS FOR (i:Insight) ON i.embedding
  OPTIONS {indexConfig: {`vector.dimensions`: 1024, `vector.similarity_function`: 'cosine'}};

// === DOMAIN 2: Reference Knowledge Index ===

CREATE CONSTRAINT chunk_id IF NOT EXISTS FOR (ch:Chunk) REQUIRE ch.id IS UNIQUE;
CREATE INDEX chunk_source IF NOT EXISTS FOR (ch:Chunk) ON (ch.source_file);
CREATE INDEX chunk_project IF NOT EXISTS FOR (ch:Chunk) ON (ch.project);
CREATE FULLTEXT INDEX chunk_search IF NOT EXISTS
  FOR (ch:Chunk) ON EACH [ch.content, ch.section];
CREATE VECTOR INDEX chunk_embedding IF NOT EXISTS FOR (ch:Chunk) ON ch.embedding
  OPTIONS {indexConfig: {`vector.dimensions`: 1024, `vector.similarity_function`: 'cosine'}};

// === DOMAIN 2: Concepts and Hypotheses (Roadmap) ===
// These node types support the research partner functionality described in PROJECT_VISION.
// Implementation deferred to domain-specific customization phase.

CREATE CONSTRAINT concept_id IF NOT EXISTS FOR (c:Concept) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT hypothesis_id IF NOT EXISTS FOR (h:Hypothesis) REQUIRE h.id IS UNIQUE;
CREATE CONSTRAINT knowledge_gap_id IF NOT EXISTS FOR (kg:KnowledgeGap) REQUIRE kg.id IS UNIQUE;

CREATE INDEX concept_domain IF NOT EXISTS FOR (c:Concept) ON (c.domain);
CREATE INDEX hypothesis_status IF NOT EXISTS FOR (h:Hypothesis) ON (h.status);
CREATE FULLTEXT INDEX concept_search IF NOT EXISTS
  FOR (c:Concept) ON EACH [c.name, c.definition];
CREATE FULLTEXT INDEX hypothesis_search IF NOT EXISTS
  FOR (h:Hypothesis) ON EACH [h.statement, h.testable_prediction];

// === TELEMETRY ===

CREATE CONSTRAINT telemetry_event_id IF NOT EXISTS FOR (t:TelemetryEvent) REQUIRE t.id IS UNIQUE;
CREATE INDEX telemetry_type IF NOT EXISTS FOR (t:TelemetryEvent) ON (t.event_type);
CREATE INDEX telemetry_time IF NOT EXISTS FOR (t:TelemetryEvent) ON (t.timestamp);
CREATE INDEX telemetry_project IF NOT EXISTS FOR (t:TelemetryEvent) ON (t.project);
```

### 4. MCP Server

**File:** `mcp-server/pyproject.toml`

```toml
[project]
name = "ccmemory"
version = "0.1.0"
dependencies = [
    "mcp",
    "neo4j",
    "pydantic",
    "anthropic",
    "voyageai",
    "numpy",
    "flask",
    "click",
    "weasyprint",
]

[project.scripts]
ccmemory = "ccmemory.cli:main"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
addopts = "-v --tb=short"
markers = [
    "unit: Unit tests (no external dependencies)",
    "integration: Integration tests (requires Neo4j)",
    "e2e: End-to-end tests (full workflow)",
]
```

**File:** `mcp-server/src/ccmemory/server.py`

```python
"""MCP server for ccmemory."""
from mcp.server import Server
from mcp.server.stdio import stdio_server

from .tools import record, query, reference

app = Server("ccmemory")

# Domain 1 tools
app.add_tool(record.record_decision)
app.add_tool(record.record_correction)
app.add_tool(record.record_exception)
app.add_tool(record.record_insight)
app.add_tool(record.record_question)
app.add_tool(record.record_failed_approach)
app.add_tool(record.record_reference)

# Query tools
app.add_tool(query.query_context)
app.add_tool(query.search_precedent)
app.add_tool(query.query_by_topic)
app.add_tool(query.trace_decision)

# Domain 2 tools
app.add_tool(reference.cache_url)
app.add_tool(reference.cache_pdf)
app.add_tool(reference.index_reference)
app.add_tool(reference.query_reference)

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

**File:** `mcp-server/src/ccmemory/graph.py`

```python
"""Neo4j client for ccmemory."""
import os
from neo4j import GraphDatabase
from typing import Optional
from datetime import datetime, timedelta

class GraphClient:
    def __init__(self):
        uri = os.getenv("CCMEMORY_NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("CCMEMORY_NEO4J_USER", "neo4j")
        password = os.getenv("CCMEMORY_NEO4J_PASSWORD", "ccmemory")
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.user_id = os.getenv("CCMEMORY_USER_ID")

    def close(self):
        self.driver.close()

    # === Session Management ===

    def create_session(self, session_id: str, project: str, started_at: str,
                       branch: Optional[str] = None):
        with self.driver.session() as session:
            session.run(
                """
                MERGE (s:Session {id: $id})
                SET s.project = $project,
                    s.started_at = datetime($started_at),
                    s.user_id = $user_id,
                    s.branch = $branch
                """,
                id=session_id, project=project, started_at=started_at,
                user_id=self.user_id, branch=branch
            )

    def end_session(self, session_id: str, transcript: str, summary: str):
        with self.driver.session() as session:
            session.run(
                """
                MATCH (s:Session {id: $id})
                SET s.ended_at = datetime(),
                    s.transcript = $transcript,
                    s.summary = $summary
                """,
                id=session_id, transcript=transcript, summary=summary
            )

    # === Domain 1: Record Functions ===

    def create_decision(self, decision_id: str, session_id: str,
                        description: str, embedding: list, **kwargs):
        with self.driver.session() as session:
            session.run(
                """
                MATCH (s:Session {id: $session_id})
                CREATE (d:Decision {id: $decision_id})
                SET d.description = $description,
                    d.timestamp = datetime(),
                    d.project = s.project,
                    d.user_id = s.user_id,
                    d.status = 'developmental',
                    d.embedding = $embedding
                SET d += $props
                CREATE (s)-[:DECIDED]->(d)
                """,
                session_id=session_id, decision_id=decision_id,
                description=description, embedding=embedding, props=kwargs
            )

    def create_correction(self, correction_id: str, session_id: str,
                          wrong_belief: str, right_belief: str,
                          embedding: list, **kwargs):
        with self.driver.session() as session:
            session.run(
                """
                MATCH (s:Session {id: $session_id})
                CREATE (c:Correction {id: $correction_id})
                SET c.wrong_belief = $wrong_belief,
                    c.right_belief = $right_belief,
                    c.timestamp = datetime(),
                    c.project = s.project,
                    c.user_id = s.user_id,
                    c.embedding = $embedding
                SET c += $props
                CREATE (s)-[:CORRECTED]->(c)
                """,
                session_id=session_id, correction_id=correction_id,
                wrong_belief=wrong_belief, right_belief=right_belief,
                embedding=embedding, props=kwargs
            )

    def create_exception(self, exception_id: str, session_id: str,
                         rule_broken: str, justification: str,
                         embedding: list, **kwargs):
        with self.driver.session() as session:
            session.run(
                """
                MATCH (s:Session {id: $session_id})
                CREATE (e:Exception {id: $exception_id})
                SET e.rule_broken = $rule_broken,
                    e.justification = $justification,
                    e.timestamp = datetime(),
                    e.project = s.project,
                    e.user_id = s.user_id,
                    e.embedding = $embedding
                SET e += $props
                CREATE (s)-[:EXCEPTED]->(e)
                """,
                session_id=session_id, exception_id=exception_id,
                rule_broken=rule_broken, justification=justification,
                embedding=embedding, props=kwargs
            )

    def create_insight(self, insight_id: str, session_id: str,
                       category: str, summary: str, embedding: list, **kwargs):
        with self.driver.session() as session:
            session.run(
                """
                MATCH (s:Session {id: $session_id})
                CREATE (i:Insight {id: $insight_id})
                SET i.category = $category,
                    i.summary = $summary,
                    i.timestamp = datetime(),
                    i.project = s.project,
                    i.user_id = s.user_id,
                    i.embedding = $embedding
                SET i += $props
                CREATE (s)-[:REALIZED]->(i)
                """,
                session_id=session_id, insight_id=insight_id,
                category=category, summary=summary,
                embedding=embedding, props=kwargs
            )

    def create_question(self, question_id: str, session_id: str,
                        question: str, answer: str, **kwargs):
        with self.driver.session() as session:
            session.run(
                """
                MATCH (s:Session {id: $session_id})
                CREATE (q:Question {id: $question_id})
                SET q.question = $question,
                    q.answer = $answer,
                    q.timestamp = datetime(),
                    q.project = s.project,
                    q.user_id = s.user_id
                SET q += $props
                CREATE (s)-[:ASKED]->(q)
                """,
                session_id=session_id, question_id=question_id,
                question=question, answer=answer, props=kwargs
            )

    def create_failed_approach(self, fa_id: str, session_id: str,
                               approach: str, outcome: str, lesson: str, **kwargs):
        with self.driver.session() as session:
            session.run(
                """
                MATCH (s:Session {id: $session_id})
                CREATE (f:FailedApproach {id: $fa_id})
                SET f.approach = $approach,
                    f.outcome = $outcome,
                    f.lesson = $lesson,
                    f.timestamp = datetime(),
                    f.project = s.project,
                    f.user_id = s.user_id
                SET f += $props
                CREATE (s)-[:TRIED]->(f)
                """,
                session_id=session_id, fa_id=fa_id,
                approach=approach, outcome=outcome, lesson=lesson, props=kwargs
            )

    def create_reference(self, ref_id: str, session_id: str,
                         ref_type: str, uri: str, **kwargs):
        with self.driver.session() as session:
            session.run(
                """
                MATCH (s:Session {id: $session_id})
                CREATE (r:Reference {id: $ref_id})
                SET r.type = $ref_type,
                    r.uri = $uri,
                    r.timestamp = datetime(),
                    r.project = s.project,
                    r.user_id = s.user_id
                SET r += $props
                CREATE (s)-[:REFERENCED]->(r)
                """,
                session_id=session_id, ref_id=ref_id,
                ref_type=ref_type, uri=uri, props=kwargs
            )

    # === Domain 1: Query Functions ===

    def query_recent(self, project: str, limit: int = 20,
                     include_team: bool = True):
        """Get recent context for a project."""
        with self.driver.session() as session:
            # Build visibility filter
            if include_team and self.user_id:
                visibility = "(n.status = 'curated' OR n.user_id = $user_id)"
            else:
                visibility = "n.user_id = $user_id" if self.user_id else "true"

            result = session.run(
                f"""
                MATCH (s:Session {{project: $project}})-[r]->(n)
                WHERE {visibility}
                RETURN n, type(r) as rel_type, s.started_at as session_time
                ORDER BY n.timestamp DESC
                LIMIT $limit
                """,
                project=project, user_id=self.user_id, limit=limit
            )
            return [dict(record) for record in result]

    def search_precedent(self, query: str, project: str, limit: int = 10,
                         include_team: bool = True):
        """Full-text search across all node types with team visibility filtering."""
        with self.driver.session() as session:
            results = {}
            indexes = [
                ("decision_search", "decisions"),
                ("correction_search", "corrections"),
                ("insight_search", "insights"),
                ("question_search", "questions"),
                ("failedapproach_search", "failed_approaches"),
            ]

            # Build visibility filter for team mode
            if include_team and self.user_id:
                visibility = "(node.status = 'curated' OR node.user_id = $user_id)"
            else:
                visibility = "node.user_id = $user_id" if self.user_id else "true"

            for index, key in indexes:
                result = session.run(
                    f"""
                    CALL db.index.fulltext.queryNodes("{index}", $query)
                    YIELD node, score
                    WHERE node.project = $project AND {visibility}
                    RETURN node, score
                    ORDER BY score DESC
                    LIMIT $limit
                    """,
                    query=query, project=project, user_id=self.user_id, limit=limit
                )
                results[key] = [(dict(r["node"]), r["score"]) for r in result]
            return results

    def search_semantic(self, embedding: list, project: str, limit: int = 10,
                        include_team: bool = True):
        """Vector similarity search across Domain 1 with team visibility filtering."""
        with self.driver.session() as session:
            results = {}
            indexes = [
                ("decision_embedding", "decisions"),
                ("correction_embedding", "corrections"),
                ("insight_embedding", "insights"),
            ]

            # Build visibility filter for team mode
            if include_team and self.user_id:
                visibility = "(node.status = 'curated' OR node.user_id = $user_id)"
            else:
                visibility = "node.user_id = $user_id" if self.user_id else "true"

            for index, key in indexes:
                result = session.run(
                    f"""
                    CALL db.index.vector.queryNodes('{index}', $limit, $embedding)
                    YIELD node, score
                    WHERE node.project = $project AND {visibility}
                    RETURN node, score
                    """,
                    embedding=embedding, project=project, user_id=self.user_id, limit=limit
                )
                results[key] = [(dict(r["node"]), r["score"]) for r in result]
            return results

    def query_stale_decisions(self, project: str, days: int = 30):
        """Find tentative decisions that may need review."""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (d:Decision {project: $project})
                WHERE d.decision_status = 'tentative'
                  AND d.timestamp < datetime() - duration({days: $days})
                RETURN d
                ORDER BY d.timestamp DESC
                """,
                project=project, days=days
            )
            return [dict(record["d"]) for record in result]

    def query_failed_approaches(self, project: str, limit: int = 10):
        """Get recent failed approaches."""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (f:FailedApproach {project: $project})
                RETURN f
                ORDER BY f.timestamp DESC
                LIMIT $limit
                """,
                project=project, limit=limit
            )
            return [dict(record["f"]) for record in result]

    # === Domain 2: Chunk Index ===

    def index_chunk(self, chunk_id: str, project: str, source_file: str,
                    section: str, content: str, embedding: list):
        """Index a markdown chunk for semantic search."""
        with self.driver.session() as session:
            session.run(
                """
                MERGE (ch:Chunk {id: $chunk_id})
                SET ch.project = $project,
                    ch.source_file = $source_file,
                    ch.section = $section,
                    ch.content = $content,
                    ch.embedding = $embedding,
                    ch.last_indexed = datetime()
                """,
                chunk_id=chunk_id, project=project, source_file=source_file,
                section=section, content=content, embedding=embedding
            )

    def search_reference(self, embedding: list, project: str, limit: int = 5):
        """Semantic search over Domain 2 chunks."""
        with self.driver.session() as session:
            result = session.run(
                """
                CALL db.index.vector.queryNodes('chunk_embedding', $limit, $embedding)
                YIELD node, score
                WHERE node.project = $project
                RETURN node, score
                """,
                embedding=embedding, project=project, limit=limit
            )
            return [(dict(r["node"]), r["score"]) for r in result]

    def clear_chunks(self, project: str, source_file: Optional[str] = None):
        """Clear chunks for re-indexing."""
        with self.driver.session() as session:
            if source_file:
                session.run(
                    "MATCH (ch:Chunk {project: $project, source_file: $source_file}) DELETE ch",
                    project=project, source_file=source_file
                )
            else:
                session.run(
                    "MATCH (ch:Chunk {project: $project}) DELETE ch",
                    project=project
                )

    # === Promotion ===

    def promote_decisions(self, project: str, branch: Optional[str] = None):
        """Promote developmental decisions to curated."""
        with self.driver.session() as session:
            query = """
                MATCH (d:Decision {project: $project, status: 'developmental'})
                WHERE d.user_id = $user_id
            """
            if branch:
                query += " AND d.branch = $branch"
            query += " SET d.status = 'curated', d.promoted_at = datetime()"
            session.run(query, project=project, user_id=self.user_id, branch=branch)

    # === Telemetry ===

    def record_telemetry(self, event_type: str, project: str, data: dict):
        """Record a telemetry event."""
        import uuid
        with self.driver.session() as session:
            session.run(
                """
                CREATE (t:TelemetryEvent {
                    id: $id,
                    event_type: $event_type,
                    project: $project,
                    user_id: $user_id,
                    timestamp: datetime(),
                    data: $data
                })
                """,
                id=f"telem-{uuid.uuid4().hex[:12]}",
                event_type=event_type, project=project,
                user_id=self.user_id, data=str(data)
            )

    # === Metrics ===

    def calculate_coefficient(self, project: str) -> float:
        """Calculate cognitive coefficient from observable metrics.

        Formula: 1.0 + (curated_decisions * 0.02) + (decision_reuse_rate * 1.0)
        Capped at 4.0. This is a leading indicator that improves as the graph grows.
        """
        curated = self._count_nodes("Decision", project, status="curated")
        reuse_rate = self.calculate_decision_reuse_rate(project)

        coefficient = 1.0 + (curated * 0.02) + (reuse_rate * 1.0)
        return min(4.0, coefficient)

    def calculate_reexplanation_rate(self, project: str) -> float:
        """Calculate re-explanation rate (requires embeddings)."""
        # Simplified: count corrections as proxy for re-explanations
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (c:Correction {project: $project})
                RETURN count(c) as corrections
                """,
                project=project
            )
            corrections = result.single()["corrections"]

            result = session.run(
                """
                MATCH (s:Session {project: $project})
                RETURN count(s) as sessions
                """,
                project=project
            )
            sessions = result.single()["sessions"]

            if sessions == 0:
                return 0.0
            return corrections / sessions

    def calculate_decision_reuse_rate(self, project: str) -> float:
        """Calculate decision reuse rate."""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (d:Decision {project: $project})
                OPTIONAL MATCH (d)-[:CITES|SUPERSEDES]->(prior:Decision)
                WITH count(d) as total, count(prior) as with_precedent
                RETURN CASE WHEN total = 0 THEN 0.0
                       ELSE with_precedent * 1.0 / total END as rate
                """,
                project=project
            )
            return result.single()["rate"]

    def calculate_graph_density(self, project: str) -> float:
        """Calculate context graph density."""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (n {project: $project})
                WITH count(n) as nodes
                MATCH ({project: $project})-[r]->({project: $project})
                WITH nodes, count(r) as edges
                RETURN CASE WHEN nodes = 0 THEN 0.0
                       ELSE edges * 1.0 / nodes END as density
                """,
                project=project
            )
            return result.single()["density"]

    def get_all_metrics(self, project: str) -> dict:
        """Get all metrics for dashboard."""
        return {
            "cognitive_coefficient": self.calculate_coefficient(project),
            "reexplanation_rate": self.calculate_reexplanation_rate(project),
            "decision_reuse_rate": self.calculate_decision_reuse_rate(project),
            "graph_density": self.calculate_graph_density(project),
            "total_decisions": self._count_nodes("Decision", project),
            "total_corrections": self._count_nodes("Correction", project),
            "total_sessions": self._count_nodes("Session", project),
            "total_insights": self._count_nodes("Insight", project),
            "total_failed_approaches": self._count_nodes("FailedApproach", project),
        }

    def _count_nodes(self, label: str, project: str, status: str = None) -> int:
        with self.driver.session() as session:
            if status:
                result = session.run(
                    f"MATCH (n:{label} {{project: $project, status: $status}}) RETURN count(n) as count",
                    project=project, status=status
                )
            else:
                result = session.run(
                    f"MATCH (n:{label} {{project: $project}}) RETURN count(n) as count",
                    project=project
                )
            return result.single()["count"]


# Singleton
_client = None

def get_client() -> GraphClient:
    global _client
    if _client is None:
        _client = GraphClient()
    return _client
```

### 5. LLM-Based Detection

**File:** `mcp-server/src/ccmemory/detection/detector.py`

```python
"""LLM-based detection for context capture."""
import asyncio
import json
from anthropic import Anthropic
from typing import Optional
from dataclasses import dataclass

CONFIDENCE_THRESHOLD = 0.7

@dataclass
class Detection:
    type: str
    confidence: float
    data: dict

client = Anthropic()

async def detect_all(user_message: str, claude_response: str,
                     context: str) -> list[Detection]:
    """Run all detection prompts in parallel, filter by confidence."""

    # Skip trivial messages
    if len(user_message.strip()) < 10:
        return []

    tasks = [
        detect_decision(user_message, claude_response, context),
        detect_correction(user_message, claude_response, context),
        detect_exception(user_message, claude_response, context),
        detect_insight(user_message, claude_response, context),
        detect_question(user_message, claude_response, context),
        detect_failed_approach(user_message, claude_response, context),
        detect_reference(user_message),
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)
    detections = []

    for result in results:
        if isinstance(result, Detection) and result.confidence >= CONFIDENCE_THRESHOLD:
            detections.append(result)

    return detections


async def _call_detector(prompt: str) -> dict:
    """Call LLM for classification. Start with Opus for accuracy, downgrade if costs require."""
    # Cost path: opus -> sonnet -> haiku as real usage data informs tradeoffs
    # Opus: ~$15/M input, ~$75/M output — best accuracy
    # Sonnet: ~$3/M input, ~$15/M output — good balance
    # Haiku: ~$0.25/M input, ~$1.25/M output — fastest, cheapest
    response = client.messages.create(
        model="claude-sonnet-4-20250514",  # Default to Sonnet; upgrade to Opus if accuracy issues
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )
    text = response.content[0].text

    # Extract JSON from response
    try:
        # Find JSON in response
        start = text.find('{')
        end = text.rfind('}') + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
    except json.JSONDecodeError:
        pass
    return {}


async def detect_decision(user_message: str, claude_response: str,
                          context: str) -> Optional[Detection]:
    prompt = f"""Analyze if this user message contains a decision.

CONTEXT:
{context[:500]}

CLAUDE'S RESPONSE:
{claude_response[:500]}

USER'S MESSAGE:
{user_message}

Is this a decision? Look for:
- Explicit choices: "Let's go with X", "I'll use Y"
- Approvals: "That sounds good", "Yes, do it"
- Direction setting: "We should always...", "From now on..."

Output JSON:
{{"is_decision": true/false, "confidence": 0.0-1.0, "description": "...", "rationale": "...", "revisit_trigger": "..."}}"""

    result = await _call_detector(prompt)
    if result.get("is_decision"):
        return Detection(
            type="decision",
            confidence=result.get("confidence", 0.5),
            data={
                "description": result.get("description", user_message[:200]),
                "rationale": result.get("rationale"),
                "revisit_trigger": result.get("revisit_trigger"),
            }
        )
    return None


async def detect_correction(user_message: str, claude_response: str,
                            context: str) -> Optional[Detection]:
    prompt = f"""Analyze if this user message corrects Claude's understanding.

CLAUDE'S RESPONSE:
{claude_response[:500]}

USER'S MESSAGE:
{user_message}

Is this a correction? Look for:
- Direct correction: "No, that's not right", "Actually..."
- Factual fix: "It's X, not Y"
- Context correction: "In this project we do it differently"

Output JSON:
{{"is_correction": true/false, "confidence": 0.0-1.0, "wrong_belief": "...", "right_belief": "...", "severity": "minor/significant/critical"}}"""

    result = await _call_detector(prompt)
    if result.get("is_correction"):
        return Detection(
            type="correction",
            confidence=result.get("confidence", 0.5),
            data={
                "wrong_belief": result.get("wrong_belief"),
                "right_belief": result.get("right_belief"),
                "severity": result.get("severity", "significant"),
            }
        )
    return None


async def detect_exception(user_message: str, claude_response: str,
                           context: str) -> Optional[Detection]:
    prompt = f"""Analyze if this user message grants an exception to normal rules.

CONTEXT:
{context[:500]}

USER'S MESSAGE:
{user_message}

Is this an exception? Look for:
- "In this case, skip X"
- "Just this once..."
- "Because of Y, we should do Z instead"

Output JSON:
{{"is_exception": true/false, "confidence": 0.0-1.0, "rule_broken": "...", "justification": "...", "scope": "one-time/conditional/new-precedent"}}"""

    result = await _call_detector(prompt)
    if result.get("is_exception"):
        return Detection(
            type="exception",
            confidence=result.get("confidence", 0.5),
            data={
                "rule_broken": result.get("rule_broken"),
                "justification": result.get("justification"),
                "scope": result.get("scope", "one-time"),
            }
        )
    return None


async def detect_insight(user_message: str, claude_response: str,
                         context: str) -> Optional[Detection]:
    prompt = f"""Analyze if this exchange contains a significant insight.

CONTEXT:
{context[:500]}

CLAUDE'S RESPONSE:
{claude_response[:500]}

USER'S MESSAGE:
{user_message}

Is there an insight? Look for:
- Realizations about situation/patterns
- Strategic conclusions
- Synthesized understanding

Output JSON:
{{"is_insight": true/false, "confidence": 0.0-1.0, "category": "realization/analysis/strategy/personal/synthesis", "summary": "...", "implications": "..."}}"""

    result = await _call_detector(prompt)
    if result.get("is_insight"):
        return Detection(
            type="insight",
            confidence=result.get("confidence", 0.5),
            data={
                "category": result.get("category", "realization"),
                "summary": result.get("summary"),
                "implications": result.get("implications"),
            }
        )
    return None


async def detect_question(user_message: str, claude_response: str,
                          context: str) -> Optional[Detection]:
    prompt = f"""Analyze if Claude asked a question that got a substantive answer.

CLAUDE'S RESPONSE:
{claude_response[:500]}

USER'S MESSAGE:
{user_message}

Is this meaningful Q&A? Look for:
- Answered questions with useful info
- Preference elicitation with response
- Constraint discovery

NOT meaningful: rhetorical questions, simple yes/no

Output JSON:
{{"is_question": true/false, "confidence": 0.0-1.0, "question": "...", "answer": "...", "context": "..."}}"""

    result = await _call_detector(prompt)
    if result.get("is_question"):
        return Detection(
            type="question",
            confidence=result.get("confidence", 0.5),
            data={
                "question": result.get("question"),
                "answer": result.get("answer"),
                "context": result.get("context"),
            }
        )
    return None


async def detect_failed_approach(user_message: str, claude_response: str,
                                  context: str) -> Optional[Detection]:
    prompt = f"""Analyze if something was tried and didn't work.

CONTEXT:
{context[:500]}

USER'S MESSAGE:
{user_message}

Is this a failed approach? Look for:
- "That didn't work"
- "Let's try something else"
- "Turns out X causes Y problem"

Output JSON:
{{"is_failed_approach": true/false, "confidence": 0.0-1.0, "approach": "...", "outcome": "...", "lesson": "..."}}"""

    result = await _call_detector(prompt)
    if result.get("is_failed_approach"):
        return Detection(
            type="failed_approach",
            confidence=result.get("confidence", 0.5),
            data={
                "approach": result.get("approach"),
                "outcome": result.get("outcome"),
                "lesson": result.get("lesson"),
            }
        )
    return None


async def detect_reference(user_message: str) -> Optional[Detection]:
    """Detect URLs and file paths (pattern-based, no LLM needed)."""
    import re

    refs = []

    # URLs
    urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', user_message)
    for url in urls:
        refs.append({"type": "url", "uri": url})

    # File paths
    paths = re.findall(r'(?:^|[\s"])([~/.]?/[\w./-]+)', user_message)
    for path in paths:
        refs.append({"type": "file_path", "uri": path})

    if refs:
        return Detection(
            type="reference",
            confidence=0.9,
            data={"references": refs}
        )
    return None
```

### 6. Hooks

**File:** `hooks/hooks.json`

Claude Code provides session_id, transcript_path, cwd, and hook_event_name automatically to all hooks via stdin JSON.

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/session_start.py",
            "timeout": 10
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/message_response.py",
            "timeout": 15
          }
        ]
      }
    ],
    "SessionEnd": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/session_end.py",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

**File:** `hooks/session_start.py`

```python
#!/usr/bin/env python3
"""Session start hook - inject relevant context.

Claude Code provides via stdin:
{
  "session_id": "abc123",
  "transcript_path": "/path/to/transcript.jsonl",
  "cwd": "/current/working/dir",
  "hook_event_name": "SessionStart",
  "source": "startup|resume|clear|compact"
}
"""
import json
import os
import sys
from datetime import datetime

# Add mcp-server to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'mcp-server', 'src'))

from ccmemory.graph import get_client

def main():
    # Claude Code provides session data via stdin
    input_data = json.load(sys.stdin)
    session_id = input_data["session_id"]
    project = os.path.basename(input_data["cwd"])

    client = get_client()

    # Create session
    client.create_session(
        session_id=session_id,
        project=project,
        started_at=datetime.now().isoformat()
    )

    # Query recent context
    recent = client.query_recent(project, limit=15)

    # Query stale decisions needing review
    stale = client.query_stale_decisions(project, days=30)

    # Query failed approaches
    failed = client.query_failed_approaches(project, limit=5)

    # Build context injection
    context_parts = []

    if recent:
        context_parts.append("## Recent Context")
        for item in recent[:10]:
            node = item.get('n', {})
            rel = item.get('rel_type', '')
            if 'description' in node:
                context_parts.append(f"- Decision: {node['description'][:100]}")
            elif 'wrong_belief' in node:
                context_parts.append(f"- Correction: {node['right_belief'][:100]}")
            elif 'summary' in node:
                context_parts.append(f"- Insight: {node['summary'][:100]}")

    if stale:
        context_parts.append("\n## Decisions Needing Review")
        for d in stale[:3]:
            context_parts.append(f"- {d.get('description', '')[:80]} (tentative, may need revisit)")

    if failed:
        context_parts.append("\n## Failed Approaches (Don't Repeat)")
        for f in failed[:3]:
            context_parts.append(f"- {f.get('approach', '')[:60]}: {f.get('lesson', '')[:60]}")

    # Output context
    output = {
        "session_id": session_id,
        "project": project,
        "context_graph_active": True,
    }

    if context_parts:
        output["injected_context"] = "\n".join(context_parts)

    print(json.dumps(output))

if __name__ == "__main__":
    main()
```

**File:** `hooks/message_response.py`

```python
#!/usr/bin/env python3
"""Post-tool-use hook - detect and capture context from tool responses.

Claude Code provides via stdin for PostToolUse:
{
  "session_id": "abc123",
  "transcript_path": "/path/to/transcript.jsonl",
  "cwd": "/current/working/dir",
  "hook_event_name": "PostToolUse",
  "tool_name": "Edit",
  "tool_input": {...},
  "tool_response": "...",
  "tool_use_id": "toolu_..."
}

We read the transcript file to get the full conversation context for detection.
"""
import json
import os
import sys
import uuid
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'mcp-server', 'src'))

from ccmemory.graph import get_client
from ccmemory.detection.detector import detect_all
from ccmemory.embeddings import get_embedding

def read_transcript(transcript_path: str) -> tuple[str, str, str]:
    """Read transcript to extract recent user message and context."""
    if not os.path.exists(transcript_path):
        return "", "", ""

    messages = []
    with open(transcript_path, 'r') as f:
        for line in f:
            try:
                messages.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    # Extract last user message and assistant response
    user_message = ""
    assistant_response = ""
    for msg in reversed(messages):
        if msg.get("role") == "user" and not user_message:
            user_message = msg.get("content", "")
        elif msg.get("role") == "assistant" and not assistant_response:
            assistant_response = msg.get("content", "")
        if user_message and assistant_response:
            break

    # Context is earlier messages
    context = "\n".join(
        f"{m.get('role', 'unknown')}: {str(m.get('content', ''))[:200]}"
        for m in messages[-10:-2]
    )
    return user_message, assistant_response, context

def main():
    input_data = json.load(sys.stdin)

    session_id = input_data["session_id"]
    transcript_path = input_data["transcript_path"]

    user_message, claude_response, context = read_transcript(transcript_path)

    if not user_message or not session_id:
        return

    # Run detection
    detections = asyncio.run(detect_all(user_message, claude_response, context))

    if not detections:
        return

    client = get_client()

    for detection in detections:
        det_id = f"{detection.type}-{uuid.uuid4().hex[:8]}"

        # Generate embedding for semantic search
        text_for_embedding = json.dumps(detection.data)
        embedding = get_embedding(text_for_embedding)

        if detection.type == "decision":
            client.create_decision(
                decision_id=det_id,
                session_id=session_id,
                description=detection.data.get("description", ""),
                embedding=embedding,
                rationale=detection.data.get("rationale"),
                revisit_trigger=detection.data.get("revisit_trigger"),
                detection_confidence=detection.confidence,
                detection_method="llm_extraction",
            )
        elif detection.type == "correction":
            client.create_correction(
                correction_id=det_id,
                session_id=session_id,
                wrong_belief=detection.data.get("wrong_belief", ""),
                right_belief=detection.data.get("right_belief", ""),
                embedding=embedding,
                severity=detection.data.get("severity"),
                detection_confidence=detection.confidence,
                detection_method="llm_extraction",
            )
        elif detection.type == "exception":
            client.create_exception(
                exception_id=det_id,
                session_id=session_id,
                rule_broken=detection.data.get("rule_broken", ""),
                justification=detection.data.get("justification", ""),
                embedding=embedding,
                scope=detection.data.get("scope"),
                detection_confidence=detection.confidence,
                detection_method="llm_extraction",
            )
        elif detection.type == "insight":
            client.create_insight(
                insight_id=det_id,
                session_id=session_id,
                category=detection.data.get("category", "realization"),
                summary=detection.data.get("summary", ""),
                embedding=embedding,
                implications=detection.data.get("implications"),
                detection_confidence=detection.confidence,
                detection_method="llm_extraction",
            )
        elif detection.type == "question":
            client.create_question(
                question_id=det_id,
                session_id=session_id,
                question=detection.data.get("question", ""),
                answer=detection.data.get("answer", ""),
                context=detection.data.get("context"),
                detection_confidence=detection.confidence,
                detection_method="llm_extraction",
            )
        elif detection.type == "failed_approach":
            client.create_failed_approach(
                fa_id=det_id,
                session_id=session_id,
                approach=detection.data.get("approach", ""),
                outcome=detection.data.get("outcome", ""),
                lesson=detection.data.get("lesson", ""),
                detection_confidence=detection.confidence,
                detection_method="llm_extraction",
            )
        elif detection.type == "reference":
            for ref in detection.data.get("references", []):
                ref_id = f"ref-{uuid.uuid4().hex[:8]}"
                client.create_reference(
                    ref_id=ref_id,
                    session_id=session_id,
                    ref_type=ref.get("type", "url"),
                    uri=ref.get("uri", ""),
                    detection_confidence=detection.confidence,
                    detection_method="llm_extraction",
                )

    # Record telemetry
    client.record_telemetry(
        event_type="detections",
        project=os.path.basename(os.getcwd()),
        data={"count": len(detections), "types": [d.type for d in detections]}
    )

    print(json.dumps({"detections": len(detections)}))

if __name__ == "__main__":
    main()
```

**File:** `hooks/session_end.py`

```python
#!/usr/bin/env python3
"""Session end hook - finalize session.

Claude Code provides via stdin for SessionEnd:
{
  "session_id": "abc123",
  "transcript_path": "/path/to/transcript.jsonl",
  "cwd": "/current/working/dir",
  "hook_event_name": "SessionEnd",
  "reason": "clear|logout|prompt_input_exit|other"
}
"""
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'mcp-server', 'src'))

from ccmemory.graph import get_client

def main():
    input_data = json.load(sys.stdin)

    session_id = input_data["session_id"]
    transcript_path = input_data["transcript_path"]

    client = get_client()

    # Read transcript from file
    transcript = ""
    if os.path.exists(transcript_path):
        with open(transcript_path, 'r') as f:
            transcript = f.read()

    # Generate summary (simplified - could use LLM)
    summary = f"Session ended at {datetime.now().isoformat()}"
    if transcript:
        lines = transcript.strip().split('\n')
        summary = f"Session with {len(lines)} message exchanges"

    client.end_session(
        session_id=session_id,
        transcript=transcript[:100000],  # Cap at 100KB
        summary=summary
    )

    # Record telemetry
    client.record_telemetry(
        event_type="session_end",
        project=os.path.basename(os.getcwd()),
        data={"session_id": session_id}
    )

    print(json.dumps({"session_ended": session_id}))

if __name__ == "__main__":
    main()
```

### 7. Embeddings

**File:** `mcp-server/src/ccmemory/embeddings.py`

```python
"""Embedding generation for semantic search via Voyage AI (Anthropic's partner)."""
import os
import voyageai

# Voyage AI is Anthropic's recommended embedding provider
# Models: voyage-3 (1024d, general), voyage-3-lite (512d, faster)
# Pricing: ~$0.06/M tokens for voyage-3
voyage_client = voyageai.Client(api_key=os.getenv("VOYAGE_API_KEY"))

# Cache embeddings to reduce API calls
_embedding_cache = {}

EMBEDDING_MODEL = "voyage-3"  # 1024 dimensions, best general performance
EMBEDDING_DIMS = 1024

def get_embedding(text: str) -> list:
    """Generate embedding for text using Voyage AI."""
    if not text:
        return [0.0] * EMBEDDING_DIMS

    # Check cache
    cache_key = hash(text[:500])
    if cache_key in _embedding_cache:
        return _embedding_cache[cache_key]

    try:
        result = voyage_client.embed(
            texts=[text],
            model=EMBEDDING_MODEL,
            input_type="document"
        )
        embedding = result.embeddings[0]
        _embedding_cache[cache_key] = embedding
        return embedding

    except Exception as e:
        raise RuntimeError(f"Voyage AI embedding failed: {e}")
```

### 8. Dashboard

**File:** `dashboard/app.py`

```python
"""Flask dashboard for ccmemory."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'mcp-server', 'src'))

from flask import Flask, render_template, jsonify, request
from ccmemory.graph import get_client

app = Flask(__name__)

@app.route("/")
def index():
    project = request.args.get("project", os.path.basename(os.getcwd()))
    team = request.args.get("team", "").lower() == "true"
    return render_template("dashboard.html", project=project, team=team)

@app.route("/api/metrics")
def metrics():
    project = request.args.get("project", os.path.basename(os.getcwd()))
    client = get_client()
    return jsonify(client.get_all_metrics(project))

@app.route("/api/recent")
def recent():
    project = request.args.get("project", os.path.basename(os.getcwd()))
    limit = int(request.args.get("limit", 20))
    client = get_client()
    return jsonify(client.query_recent(project, limit=limit))

@app.route("/api/stale")
def stale():
    project = request.args.get("project", os.path.basename(os.getcwd()))
    days = int(request.args.get("days", 30))
    client = get_client()
    return jsonify(client.query_stale_decisions(project, days=days))

@app.route("/api/failed")
def failed():
    project = request.args.get("project", os.path.basename(os.getcwd()))
    limit = int(request.args.get("limit", 10))
    client = get_client()
    return jsonify(client.query_failed_approaches(project, limit=limit))

@app.route("/api/search")
def search():
    project = request.args.get("project", os.path.basename(os.getcwd()))
    query = request.args.get("q", "")
    if not query:
        return jsonify({})
    client = get_client()
    return jsonify(client.search_precedent(query, project))

@app.route("/api/team-metrics")
def team_metrics():
    """Enterprise team metrics."""
    client = get_client()

    # Get all projects (simplified - would need proper multi-project support)
    project = request.args.get("project", os.path.basename(os.getcwd()))

    return jsonify({
        "cognitive_coefficient": client.calculate_coefficient(project),
        "reexplanation_rate": client.calculate_reexplanation_rate(project),
        "decision_reuse_rate": client.calculate_decision_reuse_rate(project),
        "graph_density": client.calculate_graph_density(project),
        # Team-specific metrics would go here
        "team_sharing_index": 0.42,  # Placeholder
        "knowledge_at_risk": [],
        "time_saved_hours": 127,
    })

if __name__ == "__main__":
    app.run(port=8888, debug=True)
```

**File:** `dashboard/templates/dashboard.html`

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>ccmemory Dashboard</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bulma@0.9.4/css/bulma.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        .metric-card {
            text-align: center;
            padding: 1.5rem;
        }
        .metric-value {
            font-size: 2.5rem;
            font-weight: bold;
        }
        .metric-label {
            font-size: 0.9rem;
        }
        .context-item {
            padding: 0.75rem;
        }
        .context-item:not(:last-child) {
            border-bottom: 1px solid var(--bulma-border);
        }
        /* Use Bulma semantic classes for theme-aware styling */
        .needs-review {
            border-left: 4px solid var(--bulma-warning);
        }
        .failed-approach {
            border-left: 4px solid var(--bulma-danger);
        }
    </style>
</head>
<body>
    <nav class="navbar is-dark">
        <div class="navbar-brand">
            <span class="navbar-item has-text-weight-bold">ccmemory</span>
        </div>
        <div class="navbar-menu">
            <div class="navbar-end">
                <span class="navbar-item">Project: {{ project }}</span>
                {% if team %}
                <span class="navbar-item tag is-info">Team View</span>
                {% endif %}
            </div>
        </div>
    </nav>

    <section class="section">
        <div class="container">
            <!-- Metrics Row -->
            <div class="columns">
                <div class="column">
                    <div class="box metric-card">
                        <div class="metric-value" id="coefficient">--</div>
                        <div class="metric-label">Cognitive Coefficient</div>
                    </div>
                </div>
                <div class="column">
                    <div class="box metric-card">
                        <div class="metric-value" id="decisions">--</div>
                        <div class="metric-label">Decisions</div>
                    </div>
                </div>
                <div class="column">
                    <div class="box metric-card">
                        <div class="metric-value" id="corrections">--</div>
                        <div class="metric-label">Corrections</div>
                    </div>
                </div>
                <div class="column">
                    <div class="box metric-card">
                        <div class="metric-value" id="sessions">--</div>
                        <div class="metric-label">Sessions</div>
                    </div>
                </div>
                <div class="column">
                    <div class="box metric-card">
                        <div class="metric-value" id="density">--</div>
                        <div class="metric-label">Graph Density</div>
                    </div>
                </div>
            </div>

            <!-- Search -->
            <div class="box">
                <div class="field has-addons">
                    <div class="control is-expanded">
                        <input class="input" type="text" id="search-input"
                               placeholder="Search context...">
                    </div>
                    <div class="control">
                        <button class="button is-primary" onclick="doSearch()">Search</button>
                    </div>
                </div>
                <div id="search-results"></div>
            </div>

            <div class="columns">
                <!-- Recent Context -->
                <div class="column is-half">
                    <div class="box">
                        <h3 class="title is-5">Recent Context</h3>
                        <div id="recent-context">Loading...</div>
                    </div>
                </div>

                <!-- Needs Review + Failed Approaches -->
                <div class="column is-half">
                    <div class="box">
                        <h3 class="title is-5">Needs Review</h3>
                        <div id="needs-review">Loading...</div>
                    </div>
                    <div class="box">
                        <h3 class="title is-5">Failed Approaches</h3>
                        <div id="failed-approaches">Loading...</div>
                    </div>
                </div>
            </div>

            {% if team %}
            <!-- Team Metrics (Enterprise View) -->
            <div class="box">
                <h3 class="title is-5">Team Metrics</h3>
                <div class="columns">
                    <div class="column">
                        <canvas id="team-chart"></canvas>
                    </div>
                    <div class="column">
                        <div id="team-details">Loading...</div>
                    </div>
                </div>
            </div>
            {% endif %}
        </div>
    </section>

    <script>
        const project = "{{ project }}";
        const isTeam = {{ 'true' if team else 'false' }};

        async function loadMetrics() {
            const resp = await fetch(`/api/metrics?project=${project}`);
            const data = await resp.json();

            document.getElementById('coefficient').textContent =
                data.cognitive_coefficient.toFixed(1) + 'x';
            document.getElementById('decisions').textContent = data.total_decisions;
            document.getElementById('corrections').textContent = data.total_corrections;
            document.getElementById('sessions').textContent = data.total_sessions;
            document.getElementById('density').textContent = data.graph_density.toFixed(1);
        }

        async function loadRecent() {
            const resp = await fetch(`/api/recent?project=${project}&limit=10`);
            const data = await resp.json();

            const container = document.getElementById('recent-context');
            if (!data.length) {
                container.innerHTML = '<p class="has-text-grey">No context yet</p>';
                return;
            }

            container.innerHTML = data.map(item => {
                const node = item.n || {};
                let text = '';
                let tag = '';

                if (node.description) {
                    text = node.description;
                    tag = '<span class="tag is-info is-light">Decision</span>';
                } else if (node.right_belief) {
                    text = node.right_belief;
                    tag = '<span class="tag is-warning is-light">Correction</span>';
                } else if (node.summary) {
                    text = node.summary;
                    tag = '<span class="tag is-success is-light">Insight</span>';
                } else if (node.lesson) {
                    text = node.lesson;
                    tag = '<span class="tag is-danger is-light">Failed</span>';
                }

                return `<div class="context-item">${tag} ${text.substring(0, 100)}...</div>`;
            }).join('');
        }

        async function loadStale() {
            const resp = await fetch(`/api/stale?project=${project}`);
            const data = await resp.json();

            const container = document.getElementById('needs-review');
            if (!data.length) {
                container.innerHTML = '<p class="has-text-grey">Nothing needs review</p>';
                return;
            }

            container.innerHTML = data.map(d =>
                `<div class="context-item needs-review">
                    <strong>${d.description?.substring(0, 60)}...</strong>
                    <br><small>Tentative decision, may need revisit</small>
                    <button class="button is-small is-light" onclick="dismissStale('${d.id}')">Dismiss</button>
                </div>`
            ).join('');
        }

        async function loadFailed() {
            const resp = await fetch(`/api/failed?project=${project}`);
            const data = await resp.json();

            const container = document.getElementById('failed-approaches');
            if (!data.length) {
                container.innerHTML = '<p class="has-text-grey">No failed approaches recorded</p>';
                return;
            }

            container.innerHTML = data.map(f =>
                `<div class="context-item failed-approach">
                    <strong>${f.approach?.substring(0, 50)}</strong>
                    <br><small>${f.lesson?.substring(0, 80)}</small>
                </div>`
            ).join('');
        }

        async function doSearch() {
            const query = document.getElementById('search-input').value;
            if (!query) return;

            const resp = await fetch(`/api/search?project=${project}&q=${encodeURIComponent(query)}`);
            const data = await resp.json();

            const container = document.getElementById('search-results');
            let html = '';

            for (const [type, results] of Object.entries(data)) {
                if (results.length) {
                    html += `<h4 class="title is-6 mt-3">${type}</h4>`;
                    results.forEach(([node, score]) => {
                        const text = node.description || node.right_belief || node.summary || node.approach || '';
                        html += `<div class="context-item"><small>${score.toFixed(2)}</small> ${text.substring(0, 100)}</div>`;
                    });
                }
            }

            container.innerHTML = html || '<p class="has-text-grey">No results</p>';
        }

        // Load all on page load
        loadMetrics();
        loadRecent();
        loadStale();
        loadFailed();

        // Refresh every 30 seconds
        setInterval(() => {
            loadMetrics();
            loadRecent();
        }, 30000);
    </script>
</body>
</html>
```

### 9. CLI

**File:** `cli/ccmemory_cli.py`

```python
#!/usr/bin/env python3
"""CLI for ccmemory."""
import os
import sys
import click
import subprocess
import webbrowser

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'mcp-server', 'src'))

@click.group()
def main():
    """ccmemory - Context graph for Claude Code."""
    pass

@main.command()
def start():
    """Start the ccmemory services (Neo4j)."""
    docker_dir = os.path.join(os.path.dirname(__file__), '..', 'docker')
    subprocess.run(['docker-compose', 'up', '-d'], cwd=docker_dir, check=True)

    click.echo("Waiting for Neo4j...")
    import time
    for _ in range(30):
        try:
            from ccmemory.graph import get_client
            client = get_client()
            client._count_nodes("Session", "test")
            click.echo("ccmemory is running.")
            return
        except Exception:
            time.sleep(1)

    click.echo("Warning: Neo4j may not be fully ready yet.")

@main.command()
def stop():
    """Stop the ccmemory services."""
    docker_dir = os.path.join(os.path.dirname(__file__), '..', 'docker')
    subprocess.run(['docker-compose', 'down'], cwd=docker_dir, check=True)
    click.echo("ccmemory stopped.")

@main.command()
@click.option('--team', is_flag=True, help='Show enterprise team view')
@click.option('--port', default=8888, help='Dashboard port')
def dashboard(team, port):
    """Open the ccmemory dashboard."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dashboard'))
    from app import app

    url = f"http://localhost:{port}{'?team=true' if team else ''}"
    click.echo(f"Opening dashboard at {url}")
    webbrowser.open(url)
    app.run(port=port, debug=False)

@main.command()
@click.option('--project', default=None, help='Project name')
@click.option('--branch', default=None, help='Branch to promote')
def promote(project, branch):
    """Promote developmental decisions to curated."""
    from ccmemory.graph import get_client

    project = project or os.path.basename(os.getcwd())
    client = get_client()
    client.promote_decisions(project, branch)
    click.echo(f"Promoted decisions for {project}" + (f" ({branch})" if branch else ""))

@main.command()
@click.argument('url')
def cache(url):
    """Cache a URL or PDF to the reference knowledge tree."""
    from ccmemory.tools.reference import cache_url_impl, cache_pdf_impl

    project = os.path.basename(os.getcwd())

    if url.endswith('.pdf'):
        result = cache_pdf_impl(url, project)
    else:
        result = cache_url_impl(url, project)

    click.echo(f"Cached to: {result['file']}")

@main.command()
def index():
    """Rebuild the reference knowledge index."""
    from ccmemory.tools.reference import index_all

    project = os.path.basename(os.getcwd())
    count = index_all(project)
    click.echo(f"Indexed {count} chunks.")

@main.command()
@click.option('--project', default=None, help='Project name')
def stats(project):
    """Show context graph statistics."""
    from ccmemory.graph import get_client

    project = project or os.path.basename(os.getcwd())
    client = get_client()
    metrics = client.get_all_metrics(project)

    click.echo(f"\nccmemory stats for: {project}")
    click.echo("=" * 40)
    click.echo(f"Cognitive Coefficient: {metrics['cognitive_coefficient']:.1f}x")
    click.echo(f"Graph Density:         {metrics['graph_density']:.2f}")
    click.echo(f"Re-explanation Rate:   {metrics['reexplanation_rate']:.1%}")
    click.echo(f"Decision Reuse Rate:   {metrics['decision_reuse_rate']:.1%}")
    click.echo("-" * 40)
    click.echo(f"Sessions:              {metrics['total_sessions']}")
    click.echo(f"Decisions:             {metrics['total_decisions']}")
    click.echo(f"Corrections:           {metrics['total_corrections']}")
    click.echo(f"Insights:              {metrics['total_insights']}")
    click.echo(f"Failed Approaches:     {metrics['total_failed_approaches']}")

@main.command()
@click.option('--format', 'fmt', default='text', type=click.Choice(['text', 'pdf']))
@click.option('--period', default='monthly', type=click.Choice(['weekly', 'monthly', 'quarterly']))
def report(fmt, period):
    """Generate executive report."""
    from ccmemory.graph import get_client

    project = os.path.basename(os.getcwd())
    client = get_client()
    metrics = client.get_all_metrics(project)

    if fmt == 'text':
        click.echo(f"\n{'=' * 60}")
        click.echo(f"  ccmemory Executive Report - {period.title()}")
        click.echo(f"  Project: {project}")
        click.echo(f"{'=' * 60}\n")

        click.echo("EFFECTIVENESS METRICS")
        click.echo(f"  Cognitive Coefficient: {metrics['cognitive_coefficient']:.1f}x")
        click.echo(f"  Decision Reuse Rate:   {metrics['decision_reuse_rate']:.1%}")
        click.echo(f"  Graph Density:         {metrics['graph_density']:.2f}")

        click.echo("\nKNOWLEDGE CAPTURED")
        click.echo(f"  Decisions:             {metrics['total_decisions']}")
        click.echo(f"  Corrections:           {metrics['total_corrections']}")
        click.echo(f"  Insights:              {metrics['total_insights']}")

        # Estimate time saved (heuristic)
        hours_saved = metrics['total_decisions'] * 0.25 + metrics['total_corrections'] * 0.5
        click.echo(f"\nESTIMATED IMPACT")
        click.echo(f"  Hours Saved:           {hours_saved:.0f}")
        click.echo(f"  Dollar Value:          ${hours_saved * 150:,.0f}")

    elif fmt == 'pdf':
        click.echo("PDF report generation requires weasyprint. Coming soon.")

if __name__ == "__main__":
    main()
```

### 10. Skill File

**File:** `skills/ccmemory/SKILL.md`

```markdown
# Context Graph Skill

You have access to a context graph that captures decisions, corrections, and patterns from Claude Code sessions.

## Core Concept

The **context graph** persists knowledge across sessions. The longer you use it, the smarter it gets.

- **Domain 1** (Neo4j): Your specifics — decisions, corrections, exceptions, insights
- **Domain 2** (Markdown): Reference knowledge — concepts, frameworks, cached research

## Available Tools

### Recording (usually automatic via hooks)

- `record_decision` — Capture a decision with rationale
- `record_correction` — Capture a correction to understanding
- `record_exception` — Capture a justified exception to rules
- `record_insight` — Capture a realization or analysis
- `record_question` — Capture a clarifying Q&A
- `record_failed_approach` — Capture what didn't work
- `record_reference` — Capture an external reference

### Querying

- `query_context` — Get relevant past context for current task
- `search_precedent` — Full-text search for similar decisions/patterns
- `query_by_topic` — Get everything about a topic across all node types
- `trace_decision` — Trace the decision chain for "why is it this way?"

### Reference Knowledge

- `cache_url` — Cache URL content to markdown for future reference
- `cache_pdf` — Extract PDF content to markdown
- `query_reference` — Search the reference knowledge tree

## When to Use

### At session start
Context is automatically injected. Review what's surfaced.

### When making decisions
Use `search_precedent` to check if similar situations were handled before.

### When something fails
Record it with `record_failed_approach` so you don't repeat it.

### When asked "why?"
Use `trace_decision` to find the decision chain.

### When you need background knowledge
Use `query_reference` to search cached research and frameworks.

## Behaviors

1. **Corrections are highest value** — When user fixes your understanding, this MUST be captured
2. **Surface precedent proactively** — Before proposing solutions, check what's been tried
3. **Note failed approaches** — "We tried X and it didn't work because Y"
4. **Track revisit triggers** — Decisions may need review when conditions change

## Explicit Capture Commands

Users can force capture with:
- `/decision <description>` — Force record a decision
- `/correction <wrong> -> <right>` — Force record a correction
- `/exception <rule> because <reason>` — Force record an exception
```

---

## Promotion Workflows

Promotion applies to **software development teams**. Other domains use single-user mode.

### Manual Promotion

```bash
ccmemory promote --project my-project
```

### Automatic Promotion (Software Projects)

**Post-merge hook** (teams with PR review):
```bash
#!/bin/bash
# .git/hooks/post-merge
BRANCH=$(git branch --show-current)
PROJECT=$(basename $(pwd))
if [ "$BRANCH" = "main" ] || [ "$BRANCH" = "master" ]; then
    ccmemory promote --project "$PROJECT" --branch "$BRANCH"
fi
```

---

## Test Specification

```
tests/
├── conftest.py             # Fixtures, Neo4j test container
├── unit/
│   ├── test_detection.py   # LLM detection accuracy
│   ├── test_embeddings.py  # Embedding generation
│   └── test_tools.py       # MCP tool functions
├── integration/
│   ├── test_graph.py       # CRUD operations
│   ├── test_promotion.py   # Promotion workflows
│   └── test_metrics.py     # Metric calculations
└── e2e/
    ├── test_workflow.py    # Full session workflow
    └── test_dashboard.py   # Dashboard API
```

### Key Test Cases

**Unit:**
- `test_detect_decision_explicit` — "Let's go with X" detected with confidence > 0.7
- `test_detect_correction` — "Actually, that's wrong" detected
- `test_detect_failed_approach` — "That didn't work" detected
- `test_no_false_positives` — Casual conversation not mis-detected

**Integration:**
- `test_create_and_query_decision` — CRUD roundtrip
- `test_semantic_search` — Vector similarity finds related items
- `test_project_isolation` — Project A can't see Project B
- `test_team_visibility` — Curated visible to team, developmental to creator only

**E2E:**
- `test_full_session` — Start → detect → capture → end → query next session
- `test_dashboard_metrics` — API returns correct calculations

---

## Testing Checklist

- [ ] `ccmemory start` starts Neo4j
- [ ] Schema initializes without errors
- [ ] Session start hook injects context
- [ ] Message response hook detects decisions/corrections
- [ ] Session end hook saves transcript
- [ ] `ccmemory dashboard` opens browser with data
- [ ] `ccmemory stats` shows metrics
- [ ] `ccmemory promote` promotes decisions
- [ ] `ccmemory cache <url>` caches to markdown
- [ ] `ccmemory index` rebuilds chunk index
- [ ] All pytest tests pass

---

## First Use

```bash
# Install
git clone https://github.com/patrickkidd/ccmemory
cd ccmemory && ./scripts/install.sh

# Start services
ccmemory start

# Open any Claude Code project
cd ~/my-project && claude

# The plugin will:
# 1. Inject relevant context from past sessions
# 2. Detect decisions, corrections, exceptions as you work
# 3. Make them queryable in future sessions

# View your context graph
ccmemory dashboard

# Check metrics
ccmemory stats
```
