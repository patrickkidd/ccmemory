# ccmemory: Persistent Memory for Claude Code

**A plugin that gives Claude Code institutional memory across any domain.**

## What It Does

ccmemory captures how understanding evolves — decisions made, corrections received, exceptions granted, patterns discovered. This context persists across sessions, making each conversation build on the last.

**The problem**: Every Claude Code session generates valuable context that's lost when the session ends. You re-explain constraints. You re-discover patterns. Accumulated understanding never compounds.

**The solution**: A memory layer that captures trajectories *as they happen* — in the flow of work, not as an afterthought. The graph accumulates organically, then surfaces relevant precedent in future sessions.

**Domain-agnostic**: Works equally for software projects, career consulting, medical research, or any complex domain. The project determines context; the plugin provides memory.

## Purpose

This document specifies exactly what needs to be built to make the Universal Context Graph operational. It is written for a developer (human or AI) to execute without further architectural guidance.

See [UNIVERSAL_CONTEXT_GRAPH.md](UNIVERSAL_CONTEXT_GRAPH.md) for the full conceptual architecture.

## Deliverable

A Claude Code plugin that:
1. Installs via marketplace
2. Starts Neo4j in Docker automatically
3. Captures decisions, corrections, exceptions from sessions
4. Provides MCP tools for querying the graph
5. Injects relevant context at session start

## Deployment Models

### Individual Mode

One Neo4j container per machine, shared across all your projects:

```
Your Machine
└── Neo4j Docker Container (single instance)
    ├── Project: my-app          (isolated by project property)
    ├── Project: career          (isolated by project property)
    └── Project: health-research (isolated by project property)
```

### Team Mode

Centralized Neo4j server, shared across team members:

```
Team Neo4j Server (hosted, accessible to team)
    ↑
    │ bolt://team-server:7687
    ├─── Developer A's Claude Code (CCMEMORY_USER_ID=alice)
    ├─── Developer B's Claude Code (CCMEMORY_USER_ID=bob)
    └─── Developer C's Claude Code (CCMEMORY_USER_ID=charlie)
```

**Visibility rules**:
- Curated decisions: visible to all team members
- Developmental decisions: only visible to creator (filtered by `user_id`)

**Environment configuration** (each developer's machine):
```bash
export CCMEMORY_USER_ID="alice"  # or $(git config user.email)
export CCMEMORY_NEO4J_URI="bolt://team-server:7687"
export CCMEMORY_NEO4J_PASSWORD="team-password"
```

### Terminology

| Term | Description |
|------|-------------|
| `developmental` | Decisions captured during active work, not yet promoted |
| `curated` | Decisions promoted to permanent record, queryable in future sessions |
| `branch` | Git branch name (for software projects) or work stream identifier |
| `project` | Folder/repository name, isolates decisions between contexts |
| `user_id` | Developer identity (team mode), filters developmental decisions |

## Repository Structure

Create this exact structure:

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
│           ├── tools/
│           │   ├── __init__.py
│           │   ├── record.py    # record_trajectory
│           │   ├── query.py     # query_context
│           │   ├── precedent.py # search_precedent
│           │   └── trace.py     # trace_decision
│           └── detection/
│               ├── __init__.py
│               ├── decisions.py
│               ├── corrections.py
│               └── exceptions.py
├── hooks/
│   ├── hooks.json
│   ├── session_start.py
│   ├── user_prompt.py
│   └── session_end.py
├── prompts/
│   ├── detect_decision.md
│   ├── detect_correction.md
│   └── detect_exception.md
├── skills/
│   └── ccmemory/
│       └── SKILL.md
├── cli/
│   └── ccmemory_cli.py
├── scripts/
│   ├── install.sh
│   ├── start.sh
│   └── stop.sh
├── tests/
│   └── (test files)
├── CLAUDE.md
├── README.md
└── LICENSE
```

## File Specifications

### 1. Plugin Manifest

**File:** `.claude-plugin/plugin.json`

```json
{
  "name": "ccmemory",
  "version": "0.1.0",
  "description": "Universal context graph for decision traces and pattern detection",
  "author": "Patrick Stinson",
  "homepage": "https://github.com/patrickkidd/ccmemory",
  "hooks": "./hooks/hooks.json",
  "skills": ["./skills/ccmemory"],
  "mcp_servers": {
    "ccmemory": {
      "command": "python",
      "args": ["-m", "ccmemory.server"],
      "cwd": "./mcp-server/src"
    }
  },
  "post_install": "./scripts/install.sh"
}
```

### 2. Docker Compose

**File:** `docker/docker-compose.yml`

```yaml
version: '3.8'

services:
  neo4j:
    image: neo4j:5-community
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
// Constraints
CREATE CONSTRAINT session_id IF NOT EXISTS FOR (s:Session) REQUIRE s.id IS UNIQUE;
CREATE CONSTRAINT decision_id IF NOT EXISTS FOR (d:Decision) REQUIRE d.id IS UNIQUE;
CREATE CONSTRAINT correction_id IF NOT EXISTS FOR (c:Correction) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT exception_id IF NOT EXISTS FOR (e:Exception) REQUIRE e.id IS UNIQUE;
CREATE CONSTRAINT observation_id IF NOT EXISTS FOR (o:Observation) REQUIRE o.id IS UNIQUE;
CREATE CONSTRAINT insight_id IF NOT EXISTS FOR (i:Insight) REQUIRE i.id IS UNIQUE;
CREATE CONSTRAINT project_name IF NOT EXISTS FOR (p:Project) REQUIRE p.name IS UNIQUE;

// Indexes
CREATE INDEX session_project IF NOT EXISTS FOR (s:Session) ON (s.project);
CREATE INDEX session_time IF NOT EXISTS FOR (s:Session) ON (s.started_at);
CREATE INDEX session_user IF NOT EXISTS FOR (s:Session) ON (s.user_id);
CREATE INDEX decision_time IF NOT EXISTS FOR (d:Decision) ON (d.timestamp);
CREATE INDEX decision_status IF NOT EXISTS FOR (d:Decision) ON (d.status);
CREATE INDEX decision_branch IF NOT EXISTS FOR (d:Decision) ON (d.branch);
CREATE INDEX decision_project_status IF NOT EXISTS FOR (d:Decision) ON (d.project, d.status);
CREATE INDEX insight_category IF NOT EXISTS FOR (i:Insight) ON (i.category);

// Full-text search
CREATE FULLTEXT INDEX decision_search IF NOT EXISTS
  FOR (d:Decision) ON EACH [d.description, d.rationale, d.revisit_trigger];
CREATE FULLTEXT INDEX correction_search IF NOT EXISTS
  FOR (c:Correction) ON EACH [c.wrong_belief, c.right_belief];
CREATE FULLTEXT INDEX insight_search IF NOT EXISTS
  FOR (i:Insight) ON EACH [i.summary, i.detail, i.implications];
```

**Decision Node Properties:**
- `id`, `timestamp`, `project`, `branch`, `status` — standard
- `description` — what was decided
- `options_considered` — alternatives weighed
- `rationale` — reasoning behind the choice
- `decision_status` — "tentative" or "committed" (tentative = framework, committed = locked)
- `revisit_trigger` — conditions that would prompt reconsideration (critical for living decisions)
- `sets_precedent` — whether this sets a pattern for similar future decisions

**Insight Node Properties:**
- `id`, `timestamp`, `project`
- `category` — "realization", "analysis", "strategy", "personal", "synthesis"
- `summary` — 1-3 sentence summary
- `detail` — full insight content
- `implications` — what this means for decisions/strategy
- `trigger` — what prompted this insight

### 4. MCP Server

**File:** `mcp-server/pyproject.toml`

```toml
[project]
name = "ccmemory"
version = "0.1.0"
dependencies = [
    "mcp",
    "neo4j",
    "pydantic"
]

[project.scripts]
ccmemory = "ccmemory.cli:main"
```

**File:** `mcp-server/src/ccmemory/server.py`

```python
"""MCP server for ccmemory."""
from mcp.server import Server
from mcp.server.stdio import stdio_server

from .tools import record, query, precedent, trace

app = Server("ccmemory")

# Register tools
app.add_tool(record.record_trajectory)
app.add_tool(query.query_context)
app.add_tool(precedent.search_precedent)
app.add_tool(trace.trace_decision)

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

class GraphClient:
    def __init__(self):
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "ccmemory")
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def create_session(self, session_id: str, project: str, started_at: str):
        with self.driver.session() as session:
            session.run(
                """
                MERGE (s:Session {id: $id})
                SET s.project = $project, s.started_at = datetime($started_at)
                """,
                id=session_id, project=project, started_at=started_at
            )

    def create_decision(self, decision_id: str, session_id: str, **kwargs):
        with self.driver.session() as session:
            session.run(
                """
                MATCH (s:Session {id: $session_id})
                CREATE (d:Decision {id: $decision_id})
                SET d += $props
                CREATE (s)-[:DECIDED]->(d)
                """,
                session_id=session_id, decision_id=decision_id, props=kwargs
            )

    def create_correction(self, correction_id: str, session_id: str, **kwargs):
        with self.driver.session() as session:
            session.run(
                """
                MATCH (s:Session {id: $session_id})
                CREATE (c:Correction {id: $correction_id})
                SET c += $props
                CREATE (s)-[:CORRECTION]->(c)
                """,
                session_id=session_id, correction_id=correction_id, props=kwargs
            )

    def create_exception(self, exception_id: str, session_id: str, **kwargs):
        with self.driver.session() as session:
            session.run(
                """
                MATCH (s:Session {id: $session_id})
                CREATE (e:Exception {id: $exception_id})
                SET e += $props
                CREATE (s)-[:EXCEPTION]->(e)
                """,
                session_id=session_id, exception_id=exception_id, props=kwargs
            )

    def query_recent_decisions(self, project: str, limit: int = 10):
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (s:Session {project: $project})-[:DECIDED]->(d:Decision)
                RETURN d ORDER BY d.timestamp DESC LIMIT $limit
                """,
                project=project, limit=limit
            )
            return [record["d"] for record in result]

    def search_precedent(self, query: str, limit: int = 10):
        with self.driver.session() as session:
            result = session.run(
                """
                CALL db.index.fulltext.queryNodes("decision_search", $query)
                YIELD node, score
                RETURN node, score ORDER BY score DESC LIMIT $limit
                """,
                query=query, limit=limit
            )
            return [(record["node"], record["score"]) for record in result]

# Singleton
_client = None

def get_client() -> GraphClient:
    global _client
    if _client is None:
        _client = GraphClient()
    return _client
```

### 5. Hooks

**File:** `hooks/hooks.json`

```json
{
  "hooks": [
    {
      "event": "session_start",
      "script": "./session_start.py",
      "timeout": 5000
    },
    {
      "event": "user_prompt_submit",
      "script": "./user_prompt.py",
      "timeout": 10000
    },
    {
      "event": "stop",
      "script": "./session_end.py",
      "timeout": 5000
    }
  ]
}
```

**File:** `hooks/session_start.py`

```python
#!/usr/bin/env python3
"""Session start hook - load relevant context."""
import json
import os
import sys

def main():
    # Get project from environment
    project = os.path.basename(os.getcwd())

    # Query for relevant context (via MCP would be better, but hooks can't call MCP directly)
    # For now, output a reminder that context graph is active

    context = {
        "message": f"Context graph active for project: {project}",
        "instructions": "Decisions, corrections, and exceptions will be captured automatically."
    }

    # Output to stderr for hook response
    print(json.dumps(context), file=sys.stderr)

if __name__ == "__main__":
    main()
```

**File:** `hooks/user_prompt.py`

```python
#!/usr/bin/env python3
"""User prompt hook - detect decisions, corrections, exceptions."""
import json
import os
import sys
from datetime import datetime
import uuid

# This would call the detection prompts via Claude API
# For MVP, we detect simple patterns

def detect_decision(message: str, context: str) -> dict | None:
    """Simple pattern matching for decisions."""
    decision_markers = [
        "let's go with", "i'll use", "we should", "decided to",
        "i've decided", "the decision is", "going to use"
    ]
    message_lower = message.lower()
    for marker in decision_markers:
        if marker in message_lower:
            return {
                "type": "decision",
                "id": f"decision-{uuid.uuid4().hex[:8]}",
                "description": message[:200],
                "timestamp": datetime.now().isoformat()
            }
    return None

def detect_correction(message: str, context: str) -> dict | None:
    """Simple pattern matching for corrections."""
    correction_markers = [
        "no, that's not", "actually,", "that's wrong",
        "not quite", "incorrect", "the correct"
    ]
    message_lower = message.lower()
    for marker in correction_markers:
        if marker in message_lower:
            return {
                "type": "correction",
                "id": f"correction-{uuid.uuid4().hex[:8]}",
                "content": message[:200],
                "timestamp": datetime.now().isoformat()
            }
    return None

def detect_exception(message: str, context: str) -> dict | None:
    """Simple pattern matching for exceptions."""
    exception_markers = [
        "in this case", "exception", "just this once",
        "skip", "ignore the rule", "special case"
    ]
    message_lower = message.lower()
    for marker in exception_markers:
        if marker in message_lower:
            return {
                "type": "exception",
                "id": f"exception-{uuid.uuid4().hex[:8]}",
                "content": message[:200],
                "timestamp": datetime.now().isoformat()
            }
    return None

def main():
    # Read input from stdin
    input_data = json.load(sys.stdin)
    message = input_data.get("message", "")
    context = input_data.get("context", "")

    detections = []

    decision = detect_decision(message, context)
    if decision:
        detections.append(decision)

    correction = detect_correction(message, context)
    if correction:
        detections.append(correction)

    exception = detect_exception(message, context)
    if exception:
        detections.append(exception)

    if detections:
        # Would record to graph here
        # For MVP, just log what was detected
        print(json.dumps({"detections": detections}), file=sys.stderr)

if __name__ == "__main__":
    main()
```

**File:** `hooks/session_end.py`

```python
#!/usr/bin/env python3
"""Session end hook - finalize session in graph."""
import json
import sys
from datetime import datetime

def main():
    # Record session end
    result = {
        "session_ended": datetime.now().isoformat(),
        "message": "Session recorded to context graph"
    }
    print(json.dumps(result), file=sys.stderr)

if __name__ == "__main__":
    main()
```

### 6. Detection Prompts

**File:** `prompts/detect_decision.md`

```markdown
Analyze this message in the context of the conversation.

CONVERSATION CONTEXT:
{context}

CURRENT MESSAGE:
{message}

Is this a decision point? Look for:
1. Explicit choices: "Let's go with X", "I'll use Y approach"
2. Implicit approval: "That sounds good", "Yes", "Do it"
3. Direction setting: "We should always...", "From now on..."
4. Trade-off resolution: Choosing between discussed options

If this is a decision, output JSON:
{
  "is_decision": true,
  "decision": {
    "description": "...",
    "options_considered": ["..."],
    "choice": "...",
    "rationale": "...",
    "sets_precedent": true/false,
    "status": "tentative" | "committed",
    "revisit_trigger": "..."  // Conditions that would prompt reconsideration
  }
}

If not a decision:
{
  "is_decision": false
}
```

**File:** `prompts/detect_correction.md`

```markdown
Analyze this message for corrections to Claude's understanding.

CLAUDE'S LAST RESPONSE:
{claude_response}

USER'S MESSAGE:
{message}

Is the user correcting a misunderstanding? Look for:
1. Direct correction: "No, that's not right", "Actually..."
2. Clarification that contradicts: "What I meant was..."
3. Factual correction: "It's X, not Y"
4. Context correction: "In this project we do it differently"

If this is a correction, output JSON:
{
  "is_correction": true,
  "correction": {
    "wrong_belief": "...",
    "right_belief": "...",
    "severity": "minor" | "significant" | "critical"
  }
}

If not a correction:
{
  "is_correction": false
}
```

**File:** `prompts/detect_exception.md`

```markdown
Analyze this message for exception grants.

CONVERSATION CONTEXT:
{context}

CURRENT MESSAGE:
{message}

Is the user granting an exception to normal rules/patterns? Look for:
1. Explicit exception: "In this case, let's skip X"
2. One-time deviation: "Just this once..."
3. Justified rule-breaking: "Because of Y, we should do Z instead"
4. Context-specific override: "For this situation..."

If this is an exception, output JSON:
{
  "is_exception": true,
  "exception": {
    "rule_broken": "...",
    "justification": "...",
    "scope": "one-time" | "conditional" | "new-precedent"
  }
}

If not an exception:
{
  "is_exception": false
}
```

**File:** `prompts/detect_insight.md`

```markdown
Analyze this exchange for insights worth preserving.

CONVERSATION CONTEXT:
{context}

CLAUDE'S RESPONSE:
{claude_response}

USER'S REACTION:
{message}

Is there an insight emerging? Look for:
1. Realization: User discovers something about their situation, patterns, or goals
2. Analysis: Deep analytical work yielding conclusions
3. Strategy: A strategic framework or approach crystallizing
4. Personal: Insight about user's personality, preferences, or working style
5. Synthesis: Connection between previously separate concepts

If this is an insight, output JSON:
{
  "is_insight": true,
  "insight": {
    "category": "realization" | "analysis" | "strategy" | "personal" | "synthesis",
    "summary": "...",  // 1-3 sentence summary
    "detail": "...",   // Full insight content
    "implications": "...",  // What this means for decisions/strategy
    "trigger": "..."   // What prompted this insight
  }
}

If not an insight:
{
  "is_insight": false
}
```

### 7. Skill File

**File:** `skills/ccmemory/SKILL.md`

```markdown
# Context Graph Skill

You have access to a context graph that captures decisions, corrections, and exceptions from your sessions.

## Available Tools

- `record_trajectory` — Record events to the graph (usually automatic via hooks)
- `query_context` — Get relevant past context for current task
- `search_precedent` — Find similar past decisions or exceptions
- `trace_decision` — Trace why something is the way it is

## When to Use

### query_context
Use at session start or when switching topics to get relevant historical context.

### search_precedent
Use when making a decision to check if similar situations have been handled before.

### trace_decision
Use when asked "why is it this way?" to find the decision chain.

## Behaviors

1. When making significant decisions, note the options considered and rationale
2. When receiving corrections, acknowledge the update to your understanding
3. When granting exceptions, note the justification and scope
4. Periodically query for relevant precedent before proposing solutions
```

## Context Management

The plugin operates as an **executive consultant watching over the shoulder** — not passively waiting for explicit commands, but actively monitoring for important information.

### Executive Oversight Protocol

The `user_prompt.py` hook implements executive oversight — monitoring every user message and asking:

> "Did the user just tell me something important about this project that I should remember next session?"

**Detection priorities (in order):**
1. **Corrections** (HIGHEST) — User fixing Claude's understanding
2. **Decisions** — Architectural choices, strategy changes
3. **Preferences** — "Always do X", "Never do Y"
4. **How things work** — Explanations of systems, patterns
5. **Why decisions were made** — Rationale, tradeoffs

**Key insight**: The most valuable information is often shared casually during normal work, not in formal "please remember this" commands. The plugin must:

1. **Monitor continuously** — Every user message is analyzed
2. **Prioritize corrections** — When user says "that's wrong", this is the highest-value capture
3. **Route appropriately** — Decisions go to Decision nodes, corrections to Correction nodes
4. **Maintain accountability** — Ask: "Is the graph now more complete and accurate than before?"

### Self-Check Protocol

After every message exchange, Claude asks internally:
- Did the user correct my understanding?
- Did the user explain how something works?
- Did the user make or confirm a decision?
- Did the user express a preference or rule?

If yes → record to graph immediately.

### Session Continuity

**Session Start:**
- Query graph for recent decisions/corrections in this project
- Surface unresolved items from previous session
- Inject as context

**Session End:**
- Log full transcript to Session node
- Extract and link any unrecorded decisions/corrections
- Update session summary for next handoff

### Working Memory

The graph provides working memory through:
- Recent Session node queries for immediate context
- `status: 'developmental'` decisions as the active working set
- `query_context` tool for explicit recall of relevant precedent

Unlike file-based approaches, the graph enables:
- Cross-project queries (same database, project-filtered)
- Team visibility with user_id filtering
- Full-text precedent search across all decisions
- Temporal queries with first-class datetime properties

### Self-Improvement Protocol

The graph should teach itself to learn better over time:

1. **Meta-detection** — When the user describes improvements to how they want context captured, record this as a meta-correction that updates detection behavior.

2. **Proactive staleness checks** — Query for decisions/observations older than **project-configured** thresholds:
   - Fast-moving projects: 30 days for tentative decisions
   - Slower contexts (career, day job): 90-120 days
   - Observations with revisit_triggers that may have fired
   - Context that conflicts with recent corrections

3. **Cross-reference coherence** — When recording a new node, check if related nodes need updates. A new decision may obsolete an old one; a correction may invalidate prior assumptions.

4. **Archive, don't delete** — Nothing is truly deleted. Outdated context is marked `archived: true` with `archived_reason` and `archived_at`. This preserves history for pattern recognition.

5. **Lossless compression** — When summarizing or compacting context, never sacrifice accuracy for brevity. If compression would lose detail, flag for human review rather than auto-compacting.

### Revisit Trigger Monitoring

Decisions with `revisit_trigger` fields are living decisions that should be proactively resurfaced:

```cypher
// Query for decisions needing review
MATCH (d:Decision)
WHERE d.revisit_trigger IS NOT NULL
  AND d.decision_status = 'tentative'
  AND d.last_reviewed < datetime() - duration('P30D')
RETURN d
ORDER BY d.timestamp DESC
```

At session start, surface pending revisit triggers:
- "You have 2 tentative decisions that may need review based on their revisit triggers..."

### 8. Install Script

**File:** `scripts/install.sh`

```bash
#!/bin/bash
set -e

echo "Installing ccmemory..."

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is required but not installed."
    exit 1
fi

# Check for Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker Compose is required but not installed."
    exit 1
fi

# Install Python dependencies
cd "$(dirname "$0")/../mcp-server"
pip install -e .

echo "ccmemory installed. Run 'ccmemory start' to begin."
```

### 9. Start/Stop Scripts

**File:** `scripts/start.sh`

```bash
#!/bin/bash
set -e

cd "$(dirname "$0")/../docker"
docker-compose up -d

echo "Waiting for Neo4j to be ready..."
until docker exec ccmemory-neo4j curl -s http://localhost:7474 > /dev/null 2>&1; do
    sleep 2
done

echo "Initializing schema..."
docker exec ccmemory-neo4j cypher-shell -u neo4j -p "${CCMEMORY_NEO4J_PASSWORD:-ccmemory}" < init.cypher

echo "ccmemory is running."
```

**File:** `scripts/stop.sh`

```bash
#!/bin/bash
cd "$(dirname "$0")/../docker"
docker-compose down
echo "ccmemory stopped."
```

## Implementation Order

1. **Create repo structure** — All directories and placeholder files
2. **Docker setup** — Get Neo4j running and schema initialized
3. **Graph client** — Basic Neo4j operations
4. **Hooks** — Session start/end, basic detection
5. **MCP server** — Minimal tools (record, query)
6. **Test** — Verify capture and query work
7. **Detection prompts** — Integrate LLM-based detection
8. **Skill file** — Instructions for Claude
9. **Polish** — Error handling, edge cases

## Promotion Workflows

Decisions start as `developmental` and become `curated` when promoted.

### Manual Promotion

```bash
ccmemory promote --project my-project
```

### Automatic Promotion (Software Projects)

**Post-commit hook** (single developer, CD pattern):
```bash
#!/bin/bash
# .git/hooks/post-commit
BRANCH=$(git branch --show-current)
PROJECT=$(basename $(pwd))
if [ "$BRANCH" = "main" ] || [ "$BRANCH" = "master" ]; then
    ccmemory promote --project "$PROJECT" --branch "$BRANCH" 2>/dev/null || true
fi
```

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

## Test Specification

Uses pytest. Structure:

```
tests/
├── conftest.py             # Shared fixtures, Neo4j container management
├── unit/                   # No external dependencies, fast
│   ├── test_detection.py   # Decision/correction pattern detection
│   └── test_tools.py       # MCP tool functions (mocked DB)
├── integration/            # Requires Neo4j
│   ├── test_graph.py       # CRUD operations
│   └── test_promotion.py   # Promotion workflows
└── e2e/                    # Full workflows
    ├── test_single_user.py # Individual mode workflow
    └── test_cross_project.py # Multi-project isolation
```

### pytest Configuration

In `pyproject.toml`:
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
addopts = "-v --tb=short"
markers = [
    "unit: Unit tests (no external dependencies)",
    "integration: Integration tests (requires Neo4j)",
    "e2e: End-to-end tests (full workflow)",
    "slow: Tests that take >1s",
]
```

### Key Test Cases

**Unit:**
- `test_detect_explicit_decision` — "Let's go with X" detected
- `test_detect_correction` — "Actually, that's wrong" detected
- `test_no_decision_in_question` — Questions not falsely detected

**Integration:**
- `test_create_and_query_decision` — CRUD works
- `test_promote_decisions` — developmental → curated
- `test_project_isolation` — Project A can't see Project B

**E2E:**
- `test_full_workflow` — Session → capture → promote → query in new session
- `test_multiple_projects_isolated` — Different projects stay isolated

### Running Tests

```bash
pytest tests/unit -v              # Fast, no deps
pytest tests/integration -v       # Requires Neo4j
pytest tests/e2e -v               # Full workflows
pytest --cov=ccmemory             # With coverage
```

## Testing Checklist

- [ ] `docker-compose up` starts Neo4j
- [ ] Schema initializes without errors
- [ ] Plugin installs via `claude plugin install ./ccmemory`
- [ ] Session start hook fires and outputs message
- [ ] User prompt hook detects simple decision patterns
- [ ] Session end hook fires
- [ ] `query_context` returns results
- [ ] `search_precedent` finds relevant decisions
- [ ] All pytest tests pass

## First Use

After installation:

```bash
# Start the graph
ccmemory start

# Open a Claude Code project
cd my-project
claude

# The plugin will:
# 1. Surface message that context graph is active
# 2. Capture decisions/corrections/exceptions during session
# 3. Make them queryable in future sessions
```
