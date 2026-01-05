#!/bin/bash
# SessionEnd hook - calls MCP server to finalize session
# Reads JSON from stdin, forwards to server

set -e

CCMEMORY_URL="${CCMEMORY_URL:-http://localhost:8766}"

input=$(cat)

response=$(curl -s -X POST "${CCMEMORY_URL}/hooks/session-end" \
    -H "Content-Type: application/json" \
    -d "$input" \
    --connect-timeout 5 \
    --max-time 10 2>/dev/null) || {
    # Server not running - silently skip
    exit 0
}

echo "$response"
