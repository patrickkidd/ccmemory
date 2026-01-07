#!/bin/bash
# SessionStart hook - calls MCP server HTTP endpoint
# Reads JSON from stdin, forwards to server, outputs context to stdout

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/activity_log.sh"

CCMEMORY_URL="${CCMEMORY_URL:-http://localhost:8766}"
HOOK_NAME="session_start"

hookStart "$HOOK_NAME"

# Quality filter thresholds
MIN_SIZE=5000      # 5KB minimum
MAX_SIZE=500000    # 500KB maximum

input=$(cat)
activityLogDebug "hook:$HOOK_NAME" "stdin: ${input:0:200}..."

cwd=$(echo "$input" | jq -r '.cwd // ""' 2>/dev/null)
if [ -z "$cwd" ]; then
    activityLogError "hook:$HOOK_NAME" "No cwd in session start input"
    echo "# Context Graph: unknown"
    echo "Error: No cwd in session start input"
    hookEnd "$HOOK_NAME"
    exit 0
fi

activityLogDebug "hook:$HOOK_NAME" "cwd=$cwd"

folder_name=$(echo "$cwd" | tr '/' '-')
folder_name="${folder_name#-}"
folder_name="-$folder_name"
claude_dir="$HOME/.claude/projects/$folder_name"

conversation_stems="[]"
if [ -d "$claude_dir" ]; then
    # Find files in quality range, sorted by recency, limit 200
    stems=$(find "$claude_dir" -name "*.jsonl" -size +${MIN_SIZE}c -size -${MAX_SIZE}c -print0 2>/dev/null | \
        xargs -0 ls -t 2>/dev/null | \
        head -200 | \
        xargs -I{} basename {} .jsonl 2>/dev/null)
    if [ -n "$stems" ]; then
        stem_count=$(echo "$stems" | wc -l | tr -d ' ')
        activityLogDebug "hook:$HOOK_NAME" "Found $stem_count conversation files in quality range"
        conversation_stems=$(echo "$stems" | jq -R . 2>/dev/null | jq -s . 2>/dev/null) || conversation_stems="[]"
    fi
fi

payload=$(echo "$input" | jq --argjson stems "$conversation_stems" '. + {conversation_stems: $stems}' 2>/dev/null) || payload="$input"

activityLogInfo "hook:$HOOK_NAME" "POST ${CCMEMORY_URL}/hooks/session-start"
response=$(curl -s -X POST "${CCMEMORY_URL}/hooks/session-start" \
    -H "Content-Type: application/json" \
    -d "$payload" \
    --connect-timeout 5 \
    --max-time 10 2>/dev/null)

if [ -z "$response" ]; then
    project=$(basename "$cwd")
    activityLogError "hook:$HOOK_NAME" "Server not responding"
    echo "# Context Graph: $project"
    echo "Server not running. Start with: ccmemory start"
    hookEnd "$HOOK_NAME"
    exit 0
fi

activityLogDebug "hook:$HOOK_NAME" "Response: ${response:0:200}..."

context=$(echo "$response" | jq -r '.context // ""' 2>/dev/null)
if [ -n "$context" ]; then
    context_len=${#context}
    activityLogInfo "hook:$HOOK_NAME" "Got context: ${context_len} chars"
    echo "$context"
fi

hookEnd "$HOOK_NAME"
