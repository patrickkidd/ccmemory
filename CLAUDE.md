# ccmemory Development

Context graph for persistent memory across Claude Code sessions.

## Development Process

- After changes, provide concise verification steps for the user
- **CRITICAL** Self-learn: When learning new project conventions/rules, update this file or add indexed sub-folder CLAUDE.md files. Keep instructions concise with lossless compression.
- Continuously optimize organization of all CLAUDE.md instruction files
- Reference `doc/PROJECT_VISION.md` for intended behavior; report any implementation/vision misalignments
- Use debug targets (not docker containers) for testing; ask user to start/restart as needed
- Dashboard debug target: port 8765
- Only rebuild/redeploy docker images when debugging container-specific issues
- Use `uv` for all Python commands (e.g., `uv run pytest`, `uv pip install`)
- **AS_BUILT.md**: Read `doc/AS_BUILT.md` before making changes. Update it after any non-obvious implementation change (schema, session flow, error handling, hooks, etc.)

## Session Startup Requirement

**IMPORTANT:** If the session context shows "## Pending History Import" with conversations to import, you MUST immediately use `AskUserQuestion` to offer the user:
- "Import 10 conversations" (Recommended)
- "Import all"
- "Skip"

This is a required action, not optional.

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
│       ├── embeddings.py        # Ollama embeddings
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

- `ANTHROPIC_API_KEY` — Required for detection LLM and reranking
- `CCMEMORY_NEO4J_PASSWORD` — Neo4j password (default: ccmemory)
- `CCMEMORY_USER_ID` — User identity for team mode

Container-internal (set in docker-compose.yml):
- `CCMEMORY_NEO4J_URI` — Neo4j connection (default: bolt://neo4j:7687)
- `CCMEMORY_OLLAMA_URL` — Ollama server (default: http://ollama:11434)
- `CCMEMORY_OLLAMA_MODEL` — Embedding model (default: all-minilm)

## Code Style

- Use camelCase for method names (Qt convention)
- One class per file, filename matches class in lowercase
- Avoid redundant comments
- Keep names short and precise
- Use enums for finite string value sets
- Never use lazy/defensive exception catching (e.g. bare `except:` or `except Exception:`) — let errors surface with specific types so root causes are visible

## Architecture

**Containers:**
- `ccmemory-ollama` — Local embedding model server
- `ccmemory-neo4j` — Graph database on ports 7474 (HTTP) and 7687 (Bolt)
- `ccmemory-mcp` — MCP server on port 8766 (SSE)

**Two-Domain Model:**
1. Domain 1 (Neo4j): Your specifics — decisions, corrections, exceptions, insights
2. Domain 2 (Markdown + Neo4j index): Reference knowledge — cached URLs, PDFs

**Node Types (Domain 1):**
- Session, Decision, Correction, Exception, Insight, Question, FailedApproach, ProjectFact, Reference

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

## Dashboard

Flask app in `dashboard/` with templates in `dashboard/templates/`.

**Keep in sync when adding node types:**
1. `app.py`: `_DETAIL_PAGE_CONFIG` dict — route + title
2. `app.py`: `/api/<type>` endpoint — query Neo4j
3. `app.py`: `/api/metrics` — add count to response
4. `dashboard.html`: navbar dropdown, metric card, JS loadMetrics
5. `detailpage.html`: navbar dropdown, `columnConfig`, `filterOptions`
6. `doc/NEO4J_COOKBOOK.md`: add query examples

**Current pages:** decisions, corrections, insights, sessions, failed-approaches, exceptions, questions, project-facts, retrievals
