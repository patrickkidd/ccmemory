# ccmemory

Persistent context management for Claude Code. Stop re-explaining your project every session.

## What It Does

- **Semantic memory** - Automatically captures project context in a local vector database
- **Doc index** - Makes your existing documentation searchable by Claude
- **Session handoff** - Preserves working memory between sessions
- **CLAUDE.md integration** - Routes Claude to the right docs for each task

## Quick Start

```bash
# In your project directory:
git clone https://github.com/patrickkidd/ccmemory.git /tmp/ccmemory
/tmp/ccmemory/setup.sh

# Or one-liner:
curl -sSL https://raw.githubusercontent.com/patrickkidd/ccmemory/main/setup.sh | bash
```

## What Gets Installed

```
your-project/
└── .ccmemory/
    ├── chroma.db           # Vector database (auto-created)
    ├── doc-index.md        # Your doc inventory (you customize)
    ├── session.md          # Current session state
    └── session-template.md # Template for new sessions
```

Plus additions to:
- `.mcp.json` - Memory server configuration
- `.gitignore` - Excludes `.ccmemory/`

## Manual Setup

If you prefer not to run the script:

1. **Install mcp-memory-service:**
   ```bash
   npm install -g mcp-memory-service
   ```

2. **Create directory:**
   ```bash
   mkdir .ccmemory
   ```

3. **Add to `.mcp.json`** (create if doesn't exist):
   ```json
   {
     "mcpServers": {
       "memory": {
         "command": "mcp-memory-service",
         "args": ["--db-path", ".ccmemory/chroma.db"]
       }
     }
   }
   ```

4. **Add to `.gitignore`:**
   ```
   .ccmemory/
   ```

5. **Copy templates:**
   ```bash
   cp templates/doc-index.md .ccmemory/
   cp templates/session-template.md .ccmemory/
   ```

6. **Customize `doc-index.md`** with your project's documentation.

## Customizing Your Doc Index

Edit `.ccmemory/doc-index.md` to list your project's documentation:

```markdown
| File | Purpose |
|------|---------|
| docs/API.md | REST API reference |
| docs/ARCHITECTURE.md | System design overview |
| src/README.md | Code organization |
```

This helps the memory service find relevant context for each task.

## Session Handoff

At the end of each Claude Code session, update `.ccmemory/session.md` with:
- What you learned
- Decisions made
- Open questions
- Files modified

This gives the next session immediate context.

## CLAUDE.md Integration

Add this to your project's `CLAUDE.md` for automatic session handoff:

```markdown
## Session Handoff (MANDATORY)

Before ending any session:
1. Read `.ccmemory/session.md` for previous context
2. Update `.ccmemory/session.md` with:
   - Key learnings from this session
   - Decisions made
   - Open questions
   - Files modified
```

## How It Works

1. **mcp-memory-service** runs as an MCP server, providing Claude with memory tools
2. Claude can store and retrieve facts via semantic search (ChromaDB)
3. Your **doc-index** gets ingested for better context retrieval
4. **Session handoff** preserves working memory in plain markdown

## Requirements

- Node.js 18+ (for mcp-memory-service)
- Claude Code CLI

## License

MIT
