#!/bin/bash
# Stop hook - calls MCP server to detect and capture context
# Reads JSON from stdin, forwards to server for detection

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/activity_log.sh"

set -e

CCMEMORY_URL="${CCMEMORY_URL:-http://localhost:8766}"
HOOK_NAME="message_response"

hookStart "$HOOK_NAME"

input=$(cat)
input_len=${#input}
activityLogDebug "hook:$HOOK_NAME" "stdin length: $input_len chars"

activityLogInfo "hook:$HOOK_NAME" "POST ${CCMEMORY_URL}/hooks/message-response"
response=$(curl -s -X POST "${CCMEMORY_URL}/hooks/message-response" \
    -H "Content-Type: application/json" \
    -d "$input" \
    --connect-timeout 5 \
    --max-time 15 2>/dev/null) || {
    activityLogError "hook:$HOOK_NAME" "Server not responding"
    hookEnd "$HOOK_NAME"
    exit 0
}

activityLogDebug "hook:$HOOK_NAME" "Response: ${response:0:200}..."

# Output detection count if any
detections=$(echo "$response" | grep -o '"detections":[0-9]*' | cut -d':' -f2)
if [ -n "$detections" ] && [ "$detections" != "0" ]; then
    activityLogInfo "hook:$HOOK_NAME" "Detections: $detections"
    echo "{\"detections\": $detections}"
else
    activityLogDebug "hook:$HOOK_NAME" "No detections"
fi

hookEnd "$HOOK_NAME"
