#!/bin/bash
# Load memory context at session start

MEMORY_DIR=".ccmemory"
SESSION_FILE="$MEMORY_DIR/session.md"
DOC_INDEX="$MEMORY_DIR/doc-index.md"
PLUGIN_ROOT="$(dirname "$(dirname "$0")")"

# Create .ccmemory directory if it doesn't exist
if [ ! -d "$MEMORY_DIR" ]; then
    mkdir -p "$MEMORY_DIR"

    # Copy templates
    if [ -f "$PLUGIN_ROOT/templates/doc-index.md" ]; then
        cp "$PLUGIN_ROOT/templates/doc-index.md" "$DOC_INDEX"
    fi
    if [ -f "$PLUGIN_ROOT/templates/session-template.md" ]; then
        cp "$PLUGIN_ROOT/templates/session-template.md" "$SESSION_FILE"
    fi

    echo "CCMEMORY: Initialized .ccmemory/ directory. Edit doc-index.md to list your project docs."
fi

# Output session context if it exists
if [ -f "$SESSION_FILE" ]; then
    echo "CCMEMORY: Previous session context loaded from .ccmemory/session.md"
    echo "---"
    cat "$SESSION_FILE"
    echo "---"
fi
