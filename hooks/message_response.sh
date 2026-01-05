#!/bin/bash
# Stop hook - calls MCP server to detect and capture context
# Reads JSON from stdin, forwards to server for detection

set -e

CCMEMORY_URL="${CCMEMORY_URL:-http://localhost:8766}"

input=$(cat)

response=$(curl -s -X POST "${CCMEMORY_URL}/hooks/message-response" \
    -H "Content-Type: application/json" \
    -d "$input" \
    --connect-timeout 5 \
    --max-time 15 2>/dev/null) || {
    # Server not running - silently skip
    exit 0
}

# Output detection count if any
detections=$(echo "$response" | grep -o '"detections":[0-9]*' | cut -d':' -f2)
if [ -n "$detections" ] && [ "$detections" != "0" ]; then
    echo "{\"detections\": $detections}"
fi
