# ccmemory Development

Context graph for persistent memory across Claude Code sessions.

## Project Structure

```
ccmemory/
├── .claude-plugin/plugin.json    # Plugin manifest (SSE transport)
├── docker-compose.yml            # Neo4j + MCP server containers
├── mcp-server/
│   ├── Dockerfile               # MCP server container
│   ├── init.cypher              # Neo4j schema init
│   ├── pyproject.toml           # Python dependencies
│   └── src/ccmemory/
│       ├── server.py            # MCP entry point (stdio or HTTP)
│       ├── graph.py             # Neo4j client
│       ├── embeddings.py        # Voyage AI embeddings
│       ├── cli.py               # CLI commands
│       ├── tools/               # MCP tools
│       └── detection/           # LLM-based detection
├── hooks/                       # Claude Code hooks
├── dashboard/                   # Flask web dashboard
├── skills/ccmemory/SKILL.md    # Agent instructions
└── tests/                       # Test suite
```

## Development Commands

```bash
# Start all containers (Neo4j + MCP server)
docker compose up -d

# Rebuild MCP server after code changes
docker compose up -d --build mcp

# View logs
docker compose logs -f mcp

# Run MCP server locally (for debugging)
cd mcp-server && uv pip install -e ".[dev]"
python -m ccmemory.server              # stdio mode
python -m ccmemory.server --http       # HTTP mode on :8766

# Run tests
cd mcp-server && uv run pytest tests/ -v
```

## Environment Variables

Set in shell or `.env` file:

- `VOYAGE_API_KEY` — Required for embeddings
- `ANTHROPIC_API_KEY` — Required for detection LLM
- `CCMEMORY_NEO4J_PASSWORD` — Neo4j password (default: ccmemory)
- `CCMEMORY_USER_ID` — User identity for team mode

Container-internal (set in docker-compose.yml):
- `CCMEMORY_NEO4J_URI` — Neo4j connection (default: bolt://neo4j:7687)

## Code Style

- Use camelCase for method names (Qt convention)
- One class per file, filename matches class in lowercase
- Avoid redundant comments
- Keep names short and precise
- Use enums for finite string value sets

## Architecture

**Containers:**
- `ccmemory-neo4j` — Graph database on ports 7474 (HTTP) and 7687 (Bolt)
- `ccmemory-mcp` — MCP server on port 8766 (SSE)

**Two-Domain Model:**
1. Domain 1 (Neo4j): Your specifics — decisions, corrections, exceptions, insights
2. Domain 2 (Markdown + Neo4j index): Reference knowledge — cached URLs, PDFs

**Node Types (Domain 1):**
- Session, Decision, Correction, Exception, Insight, Question, FailedApproach, Reference

**Detection Flow:**
1. Stop hook fires after each Claude response
2. LLM analyzes user message for decisions/corrections/etc
3. Detections above 0.7 confidence get stored
4. Embeddings generated for semantic search

## Testing

```bash
cd mcp-server

# Unit tests (no Neo4j required)
uv run pytest tests/unit -v -m unit

# Integration tests (requires Neo4j running)
uv run pytest tests/integration -v -m integration

# All tests
uv run pytest tests/ -v
```
