#!/bin/bash
set -e

# ccmemory setup script
# Usage: ./setup.sh [project-dir]
# If no directory specified, uses current directory

PROJECT_DIR="${1:-.}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== ccmemory setup ==="
echo "Project directory: $PROJECT_DIR"
echo ""

# Change to project directory
cd "$PROJECT_DIR"

# 1. Check for mcp-memory-service
echo "[1/5] Checking mcp-memory-service..."
if command -v mcp-memory-service &> /dev/null; then
    echo "  mcp-memory-service is installed"
else
    echo "  Installing mcp-memory-service..."
    npm install -g mcp-memory-service
fi

# 2. Create .ccmemory directory
echo "[2/5] Creating .ccmemory directory..."
mkdir -p .ccmemory

# 3. Copy templates
echo "[3/5] Copying templates..."
if [ -f "$SCRIPT_DIR/templates/doc-index.md" ]; then
    cp "$SCRIPT_DIR/templates/doc-index.md" .ccmemory/
    cp "$SCRIPT_DIR/templates/session-template.md" .ccmemory/
    cp "$SCRIPT_DIR/templates/session-template.md" .ccmemory/session.md
else
    # If running from curl, create templates inline
    cat > .ccmemory/doc-index.md << 'EOF'
# Documentation Index

Inventory of project documentation for semantic search.

| File | Purpose |
|------|---------|
| README.md | Project overview |
| CLAUDE.md | Claude Code instructions |

<!-- Add your project's documentation files here -->
<!-- This file gets ingested by the memory service for better context retrieval -->
EOF

    cat > .ccmemory/session-template.md << 'EOF'
# Session Handoff

## Previous Session Summary
<!-- Brief summary of what was accomplished -->

## What I Learned
<!-- Key facts, patterns, or gotchas discovered -->

## Decisions Made
<!-- Architectural or implementation decisions with context -->

## Open Questions
<!-- Unresolved items for next session -->

## Files Modified
<!-- List of files changed this session -->
EOF

    cp .ccmemory/session-template.md .ccmemory/session.md
fi

# 4. Update .mcp.json
echo "[4/5] Configuring MCP server..."
if [ -f .mcp.json ]; then
    # Check if memory server already configured
    if grep -q '"memory"' .mcp.json; then
        echo "  Memory server already configured in .mcp.json"
    else
        # Merge memory config into existing .mcp.json
        # This is a simple approach - for complex merging, use jq
        echo "  Adding memory server to existing .mcp.json"
        echo "  NOTE: Please verify .mcp.json manually if you have complex config"

        # Create backup
        cp .mcp.json .mcp.json.backup

        # Try to use jq if available, otherwise manual instruction
        if command -v jq &> /dev/null; then
            jq '.mcpServers.memory = {"command": "mcp-memory-service", "args": ["--db-path", ".ccmemory/chroma.db"]}' .mcp.json > .mcp.json.tmp
            mv .mcp.json.tmp .mcp.json
        else
            echo ""
            echo "  Please manually add to .mcp.json mcpServers:"
            echo '    "memory": {'
            echo '      "command": "mcp-memory-service",'
            echo '      "args": ["--db-path", ".ccmemory/chroma.db"]'
            echo '    }'
        fi
    fi
else
    # Create new .mcp.json
    cat > .mcp.json << 'EOF'
{
  "mcpServers": {
    "memory": {
      "command": "mcp-memory-service",
      "args": ["--db-path", ".ccmemory/chroma.db"]
    }
  }
}
EOF
fi

# 5. Update .gitignore
echo "[5/5] Updating .gitignore..."
if [ -f .gitignore ]; then
    if grep -q '.ccmemory/' .gitignore; then
        echo "  .ccmemory/ already in .gitignore"
    else
        echo "" >> .gitignore
        echo "# Claude Code memory" >> .gitignore
        echo ".ccmemory/" >> .gitignore
    fi
else
    echo "# Claude Code memory" > .gitignore
    echo ".ccmemory/" >> .gitignore
fi

echo ""
echo "=== Setup complete ==="
echo ""
echo "Next steps:"
echo "1. Edit .ccmemory/doc-index.md to list your project's documentation"
echo "2. Add session handoff rules to your CLAUDE.md (see README)"
echo "3. Restart Claude Code to load the memory server"
echo ""
echo "The memory server will automatically capture context as you work."
