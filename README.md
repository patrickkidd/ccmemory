# ccmemory

**Persistent memory for Claude Code. The longer you use it, the smarter it gets.**

---

## In-Depth

- [doc/DEVELOPMENT.md](doc/DEVELOPMENT.md) — Development setup
- [doc/PROJECT_VISION.md](doc/PROJECT_VISION.md) — Full conceptual architecture
- [doc/NEO4J_COOKBOOK.md](doc/NEO4J_COOKBOOK.md) — Query recipes for exploring the graph
- [doc/TELEMETRY.md](doc/TELEMETRY.md) — Enterprise metrics framework
- [doc/IMPLEMENTATION_PLAN.md](doc/IMPLEMENTATION_PLAN.md) — Phase 1 build specs

Inspired by [AI's trillion-dollar opportunity: Context graphs](https://foundationcapital.com/ais-trillion-dollar-opportunity-context-graphs/) by Gupta & Garg.


---

## The Problem

Every AI conversation starts from zero. You explain your project, your preferences, your constraints—then the session ends and it's all forgotten. Tomorrow, you're talking to a stranger again.

**ccmemory fixes this.** Decisions, corrections, and context accumulate over time. Session 50 is dramatically more effective than session 1.

---

## Getting Started

### Requirements

- Docker
- Claude Code CLI

### Install

```bash
# 1. Clone and start the containers
git clone https://github.com/patrickkidd/ccmemory
cd ccmemory
docker compose up -d

# 2. Install the Claude Code plugin
/plugin marketplace add patrickkidd/ccmemory
/plugin install ccmemory@patrickkidd/ccmemory
```

That's it. Start a new Claude Code session and ccmemory is active.

### Verify It Works

Have a conversation with a decision:

```
You: "Let's use Postgres instead of SQLite — we need concurrent writes"
Claude: [implements the change]
```

ccmemory automatically detects and stores the decision. Start a new session and it resurfaces:

```
# Context Graph: your-project
## Recent Decisions
- Use Postgres for concurrent write support (Jan 4)
```

### Web Interfaces

Once containers are running, access:

- **Dashboard:** http://localhost:8765 — Browse and manage stored memories
- **Neo4j Browser:** http://localhost:7474 — Direct graph database access

### Visualizing the Graph

In Neo4j Browser (http://localhost:7474), try these queries:

```cypher
// Your decision history — sessions with their decisions
MATCH (s:Session {project: 'your-project'})-[:DECIDED]->(d:Decision)
RETURN s, d

// Full knowledge graph — sessions, decisions, corrections, insights
MATCH (s:Session {project: 'your-project'})-[r]->(n)
RETURN s, r, n
LIMIT 100

// Learning from mistakes — corrections over time
MATCH (s:Session {project: 'your-project'})-[:CORRECTED]->(c:Correction)
RETURN s, c
```

Click any node to expand connections. See [doc/NEO4J_COOKBOOK.md](doc/NEO4J_COOKBOOK.md) for more queries.

---

## What Gets Captured

| Type | Example | Value |
|------|---------|-------|
| **Decision** | "Let's use retry with fixed delays" | Future sessions know why |
| **Correction** | "Actually, that endpoint returns JSON, not XML" | Claude doesn't repeat mistake |
| **Exception** | "Skip the linter for this file, it's generated" | Rule-breaking is justified |
| **Failed Approach** | "Tried async but race conditions killed it" | Don't repeat failed experiments |

---

## Team Mode

For shared memory across a team, point everyone at the same Neo4j:

```bash
# Each developer adds to ~/.bashrc or ~/.zshrc
export CCMEMORY_USER_ID="$(git config user.email)"
export CCMEMORY_NEO4J_URI="bolt://your-team-server:7687"
export CCMEMORY_NEO4J_PASSWORD="your-team-password"
```

Decisions start as `developmental` (private). Promote to `curated` (team-visible) via the dashboard.

---

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Claude Code   │────▶│  MCP Server     │────▶│     Neo4j       │
│                 │     │  (container)    │     │   (container)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │
        │ Hooks detect          │ Stores decisions,
        │ decisions/corrections │ corrections, insights
```

Both Neo4j and the MCP server run in Docker containers. The Claude Code plugin connects to the MCP server via HTTP.

---

## Commands

```bash
docker compose up -d      # Start
docker compose down       # Stop
docker compose logs -f    # View logs
```

---

## Backfilling Historical Data

Import existing conversations and documentation into the context graph.

### Import Conversations

Copy this prompt exactly:

```
Use the ccmemory_backfill_conversation tool to import my Claude Code conversation history for THIS project only. The JSONL files are at ~/.claude/projects/ in a folder matching my current directory path with slashes replaced by dashes (e.g., /Users/patrick/myapp -> -Users-patrick-myapp). Read each JSONL file from that folder and call the tool with the project name (basename of cwd), session_id (filename without .jsonl), and the file content.
```

**Important:** Only import from the folder matching your current working directory. Do NOT import from other project folders.

### Import Markdown

Copy this prompt exactly:

```
Use the ccmemory_backfill_markdown tool to import my project's markdown files. Read each .md file and call the tool with project name, relative file path, and the file content.
```

### Decision Log Format

Files with `## YYYY-MM-DD: Title` entries are parsed into Decision nodes:

```markdown
## 2025-01-15: Use JWT for Authentication
**Context:** Need stateless auth for horizontal scaling
**Options considered:** Sessions, JWT, OAuth tokens
**Decision:** JWT with short expiry + refresh tokens
**Reasoning:** Stateless required for K8s deployment
**Revisit trigger:** If we need real-time session revocation
```

Other markdown is chunked and indexed as reference knowledge.

---

## License

Apache 2.0
