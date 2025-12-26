#!/bin/bash
# Save memory context at session end

MEMORY_DIR=".ccmemory"
SESSION_FILE="$MEMORY_DIR/session.md"

# Only remind if .ccmemory exists (plugin was initialized for this project)
if [ -d "$MEMORY_DIR" ]; then
    echo "CCMEMORY: Session ending. Remember to update .ccmemory/session.md with:"
    echo "  - Key learnings from this session"
    echo "  - Decisions made"
    echo "  - Open questions"
    echo "  - Files modified"
fi
