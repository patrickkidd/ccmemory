#!/bin/bash
# SessionEnd hook - calls MCP server to finalize session
# Reads JSON from stdin, forwards to server

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/activity_log.sh"

set -e

CCMEMORY_URL="${CCMEMORY_URL:-http://localhost:8766}"
HOOK_NAME="session_end"

hookStart "$HOOK_NAME"

input=$(cat)
activityLogDebug "hook:$HOOK_NAME" "stdin: ${input:0:200}..."

activityLogInfo "hook:$HOOK_NAME" "POST ${CCMEMORY_URL}/hooks/session-end"
response=$(curl -s -X POST "${CCMEMORY_URL}/hooks/session-end" \
    -H "Content-Type: application/json" \
    -d "$input" \
    --connect-timeout 5 \
    --max-time 10 2>/dev/null) || {
    activityLogError "hook:$HOOK_NAME" "Server not responding"
    hookEnd "$HOOK_NAME"
    exit 0
}

activityLogDebug "hook:$HOOK_NAME" "Response: ${response:0:200}..."
echo "$response"

hookEnd "$HOOK_NAME"
