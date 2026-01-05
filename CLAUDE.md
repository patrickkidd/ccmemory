# ccmemory Development

Context graph for persistent memory across Claude Code sessions.

## Project Structure

```
ccmemory/
├── .claude-plugin/plugin.json    # Plugin manifest
├── docker/                       # Neo4j container config
├── mcp-server/src/ccmemory/     # MCP server + CLI
│   ├── server.py                # MCP entry point
│   ├── graph.py                 # Neo4j client
│   ├── embeddings.py            # Voyage AI embeddings
│   ├── cli.py                   # CLI commands
│   ├── tools/                   # MCP tools
│   └── detection/               # LLM-based detection
├── hooks/                       # Claude Code hooks
├── dashboard/                   # Flask web dashboard
├── skills/ccmemory/SKILL.md    # Agent instructions
└── tests/                       # Test suite
```

## Development Commands

```bash
# Start Neo4j
cd docker && docker-compose up -d

# Install package in dev mode
cd mcp-server && pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run MCP server directly
python -m ccmemory.server

# Run dashboard
python dashboard/app.py
```

## Environment Variables

- `VOYAGE_API_KEY` — Required for embeddings
- `CCMEMORY_NEO4J_URI` — Neo4j connection (default: bolt://localhost:7687)
- `CCMEMORY_NEO4J_PASSWORD` — Neo4j password (default: ccmemory)
- `CCMEMORY_USER_ID` — User identity for team mode

## Code Style

- Use camelCase for method names (Qt convention)
- One class per file, filename matches class in lowercase
- Avoid redundant comments
- Keep names short and precise
- Use enums for finite string value sets

## Architecture

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
# Unit tests (no Neo4j required)
pytest tests/unit -v -m unit

# Integration tests (requires Neo4j)
pytest tests/integration -v -m integration

# All tests
pytest tests/ -v
```
