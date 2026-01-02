#!/bin/bash
# Load memory context at session start

MEMORY_DIR=".ccmemory"
LOG_FILE="$HOME/.ccmemory-debug.log"

# Debug logging (set CCMEMORY_DEBUG=1 to enable)
log_debug() {
    if [ "${CCMEMORY_DEBUG:-0}" = "1" ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"
    fi
}

log_debug "SessionStart hook fired in: $(pwd)"
SESSION_FILE="$MEMORY_DIR/session.md"
DOC_INDEX="$MEMORY_DIR/doc-index.md"
DECISIONS="$MEMORY_DIR/decisions.md"
INSIGHTS_DIR="$MEMORY_DIR/insights"
PLUGIN_ROOT="$(dirname "$(dirname "$0")")"

# Create .ccmemory directory if it doesn't exist
if [ ! -d "$MEMORY_DIR" ]; then
    mkdir -p "$MEMORY_DIR"
    mkdir -p "$INSIGHTS_DIR"

    # Copy templates
    if [ -f "$PLUGIN_ROOT/templates/doc-index.md" ]; then
        cp "$PLUGIN_ROOT/templates/doc-index.md" "$DOC_INDEX"
    fi
    if [ -f "$PLUGIN_ROOT/templates/session-template.md" ]; then
        cp "$PLUGIN_ROOT/templates/session-template.md" "$SESSION_FILE"
    fi
    if [ -f "$PLUGIN_ROOT/templates/decisions-log.md" ]; then
        cp "$PLUGIN_ROOT/templates/decisions-log.md" "$DECISIONS"
    fi

    echo ""
    echo "<ccmemory-init>"
    echo "Initialized .ccmemory/ directory with:"
    echo "  - session.md (working memory / session handoff)"
    echo "  - doc-index.md (documentation inventory)"
    echo "  - decisions.md (decision log)"
    echo "  - insights/ (realizations and analysis)"
    echo ""
    echo "Edit doc-index.md to list your project documentation."
    echo "</ccmemory-init>"
fi

# Output session context if it exists and has content
if [ -f "$SESSION_FILE" ] && [ -s "$SESSION_FILE" ]; then
    # Check if file has content beyond just the template
    if grep -q "^## " "$SESSION_FILE" 2>/dev/null; then
        log_debug "Loading session context from $SESSION_FILE"
        echo ""
        echo "<ccmemory-session>"
        echo "Previous session context:"
        echo ""
        cat "$SESSION_FILE"
        echo "</ccmemory-session>"
    else
        log_debug "session.md exists but no ## headers found"
    fi
else
    log_debug "No session.md or empty"
fi

# Always output a brief confirmation
echo ""
echo "<ccmemory status=\"active\" dir=\"$(pwd)\" />"
