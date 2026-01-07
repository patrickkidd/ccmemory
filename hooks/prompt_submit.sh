#!/bin/bash
# UserPromptSubmit hook - checks for pending backfills and reminds Claude to ask
# Only runs once per session (on first prompt)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/activity_log.sh"

CCMEMORY_URL="${CCMEMORY_URL:-http://localhost:8766}"
STATE_DIR="$HOME/.ccmemory"
mkdir -p "$STATE_DIR"
HOOK_NAME="prompt_submit"

hookStart "$HOOK_NAME"

input=$(cat)

session_id=$(echo "$input" | jq -r '.session_id // ""' 2>/dev/null)
cwd=$(echo "$input" | jq -r '.cwd // ""' 2>/dev/null)

activityLogDebug "hook:$HOOK_NAME" "session_id=$session_id cwd=$cwd"

# Track if we've already reminded this session
state_file="$STATE_DIR/prompted-$session_id"
if [ -f "$state_file" ]; then
    activityLogDebug "hook:$HOOK_NAME" "Already prompted this session, skipping"
    hookEnd "$HOOK_NAME"
    exit 0
fi

# Check for pending backfills (quick local check)
folder_name=$(echo "$cwd" | tr '/' '-')
folder_name="${folder_name#-}"
folder_name="-$folder_name"
claude_dir="$HOME/.claude/projects/$folder_name"

MIN_SIZE=5000
MAX_SIZE=500000

pending_count=0
if [ -d "$claude_dir" ]; then
    pending_count=$(find "$claude_dir" -name "*.jsonl" -size +${MIN_SIZE}c -size -${MAX_SIZE}c 2>/dev/null | wc -l | tr -d ' ')
fi

activityLogDebug "hook:$HOOK_NAME" "Pending imports: $pending_count"

# Mark this session as prompted
touch "$state_file"

# If there are pending imports, inject a reminder
if [ "$pending_count" -gt 0 ]; then
    activityLogInfo "hook:$HOOK_NAME" "Injecting import reminder for $pending_count files"
    cat << EOF
SYSTEM REMINDER: There are $pending_count conversation history files that could be imported into ccmemory.
Before responding to the user's request, use AskUserQuestion to offer:
- "Import 10 recent conversations" (Recommended)
- "Import all $pending_count conversations"
- "Skip import"
This is a one-time prompt per session. After user responds, proceed normally.
EOF
fi

hookEnd "$HOOK_NAME"
