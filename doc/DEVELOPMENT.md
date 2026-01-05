# Development Setup

## TL;DR

```bash
# 1. Start Neo4j
docker-compose up -d

# 2. Install package in dev mode
cd mcp-server && uv pip install -e ".[dev]"

# 3. Run Claude Code with local plugin
claude --plugin-dir /path/to/ccmemory
```

Changes to Python code take effect on next Claude Code restart. No hot-reload—restart Claude Code after edits.

---

## Prerequisites

- Docker
- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Claude Code CLI

## Full Setup

### 1. Clone and Install

```bash
git clone https://github.com/patrickkidd/ccmemory
cd ccmemory

# Create venv and install
cd mcp-server
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
cd ..
```

### 2. Start Neo4j

```bash
docker-compose up -d
```

Wait for Neo4j to be ready (check http://localhost:7474).

### 3. Initialize Schema

```bash
# Option A: Use install script
python scripts/install.py

# Option B: Manual via cypher-shell
docker exec -i ccmemory-neo4j cypher-shell -u neo4j -p ccmemory < init.cypher
```

### 4. Run with Local Plugin

```bash
claude --plugin-dir /absolute/path/to/ccmemory
```

The `--plugin-dir` flag loads hooks, skills, and MCP servers directly from source. **Restart Claude Code to pick up changes.**

## Project Structure

```
ccmemory/
├── .claude-plugin/plugin.json   # Plugin manifest
├── docker-compose.yml           # Neo4j container
├── init.cypher                  # Schema initialization
├── mcp-server/src/ccmemory/     # MCP server + CLI source
│   ├── server.py               # MCP entry point
│   ├── graph.py                # Neo4j client
│   ├── embeddings.py           # Ollama embeddings
│   ├── cli.py                  # CLI commands
│   ├── tools/                  # MCP tool implementations
│   └── detection/              # LLM-based detection
├── hooks/                       # Claude Code hooks
│   ├── hooks.json              # Hook configuration
│   ├── session_start.py        # Injects context at session start
│   ├── message_response.py     # Detects decisions/corrections
│   └── session_end.py          # Session cleanup
├── dashboard/                   # Flask web dashboard
├── skills/ccmemory/SKILL.md    # Agent instructions
└── tests/                       # Test suite
```

## Running Tests

```bash
# Unit tests (no Neo4j)
pytest tests/unit -v -m unit

# Integration tests (requires Neo4j running)
pytest tests/integration -v -m integration

# All tests
pytest tests/ -v
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | Yes | - | Required for detection LLM and reranking |
| `CCMEMORY_NEO4J_URI` | No | `bolt://localhost:7687` | Neo4j connection URI |
| `CCMEMORY_NEO4J_PASSWORD` | No | `ccmemory` | Neo4j password |
| `CCMEMORY_OLLAMA_URL` | No | `http://ollama:11434` | Ollama server URL |
| `CCMEMORY_OLLAMA_MODEL` | No | `all-minilm` | Embedding model |
| `CCMEMORY_USER_ID` | No | - | User ID for team mode |

## CLI Commands (Development)

```bash
ccmemory status              # Check Neo4j connection
ccmemory stats               # Project metrics
ccmemory search "<query>"    # Semantic search
ccmemory stale --days 30     # Find old decisions
ccmemory dashboard           # Start web UI (localhost:8765)
```

## Debugging

### MCP Server

Run the MCP server directly for debugging:

```bash
cd mcp-server/src
python -m ccmemory.server
```

### Hooks

Hooks run as subprocesses. Add logging to hook scripts and check Claude Code's output.

### Neo4j

Access Neo4j browser at http://localhost:7474 (user: `neo4j`, password: `ccmemory`).

Useful queries:
```cypher
// All nodes
MATCH (n) RETURN n LIMIT 100

// All decisions
MATCH (d:Decision) RETURN d

// Clear all data (careful!)
MATCH (n) DETACH DELETE n
```

## Workflow

1. Make changes to Python code in `mcp-server/src/ccmemory/`
2. Restart Claude Code (`/exit` then `claude --plugin-dir ...`)
3. Test the changes
4. Run tests before committing

For hook changes, same process—restart Claude Code to reload.