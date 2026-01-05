#!/bin/bash
# SessionStart hook - calls MCP server HTTP endpoint
# Reads JSON from stdin, forwards to server, outputs context to stdout

set -e

CCMEMORY_URL="${CCMEMORY_URL:-http://localhost:8766}"

input=$(cat)

response=$(curl -s -X POST "${CCMEMORY_URL}/hooks/session-start" \
    -H "Content-Type: application/json" \
    -d "$input" \
    --connect-timeout 5 \
    --max-time 10 2>/dev/null) || {
    # Server not running - output minimal context
    cwd=$(echo "$input" | grep -o '"cwd":"[^"]*"' | cut -d'"' -f4)
    project=$(basename "$cwd")
    echo "# Context Graph: $project"
    echo "Server not running. Start with: ccmemory start"
    exit 0
}

# Extract and output the context field
context=$(echo "$response" | grep -o '"context":"[^"]*"' | cut -d'"' -f4 | sed 's/\\n/\n/g')
if [ -n "$context" ]; then
    echo "$context"
fi
