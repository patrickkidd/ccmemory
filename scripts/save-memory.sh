#!/bin/bash
# Save memory context at session end

MEMORY_DIR=".ccmemory"
SESSION_FILE="$MEMORY_DIR/session.md"
LOG_FILE="$HOME/.ccmemory-debug.log"

# Debug logging (set CCMEMORY_DEBUG=1 to enable)
log_debug() {
    if [ "${CCMEMORY_DEBUG:-0}" = "1" ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"
    fi
}

log_debug "Stop hook (save-memory) fired in: $(pwd)"

# Only remind if .ccmemory exists (plugin was initialized for this project)
if [ -d "$MEMORY_DIR" ]; then
    log_debug ".ccmemory dir exists, showing reminder"
    echo "CCMEMORY: Session ending. Remember to update .ccmemory/session.md with:"
    echo "  - Key learnings from this session"
    echo "  - Decisions made"
    echo "  - Open questions"
    echo "  - Files modified"
fi
