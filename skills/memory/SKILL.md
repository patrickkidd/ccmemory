# Memory Management Skill

This skill teaches you how to use the ccmemory persistent context system.

## Overview

The ccmemory plugin provides persistent memory across Claude Code sessions via:
1. **Semantic memory** - ChromaDB vector database for storing/retrieving facts
2. **Session handoff** - `.ccmemory/session.md` for working memory
3. **Doc index** - `.ccmemory/doc-index.md` for project documentation inventory

## When to Use This Skill

Use this skill when:
- Starting a new session (check session.md for context)
- Learning something important about the project
- Making architectural decisions
- Ending a session (update session.md)

## Session Start Protocol

At the beginning of each session:
1. Read `.ccmemory/session.md` for previous session context
2. Check the doc-index for relevant documentation
3. Query the memory service for related facts if needed

## Session End Protocol

Before ending a session, update `.ccmemory/session.md` with:

```markdown
# Session Handoff

Last updated: [current date/time]

## Previous Session Summary
[Brief summary of what was accomplished]

## What I Learned
- [Key facts, patterns, or gotchas discovered]

## Decisions Made
- [Architectural or implementation decisions with reasoning]

## Open Questions
- [Unresolved items for next session]

## Files Modified
- [List of files changed this session]
```

## Storing Important Facts

When you learn something important about the project that should persist:
1. Update the relevant documentation file (if one exists)
2. Use the memory service to store the fact for semantic retrieval
3. If it's session-specific, add it to session.md

## Documentation Index

The `.ccmemory/doc-index.md` file lists all project documentation. Before starting a task:
1. Check the doc-index for relevant files
2. Read the relevant documentation before making changes
3. Keep the doc-index updated when adding new documentation

## Memory Service Tools

The memory MCP server provides these capabilities:
- Store facts with semantic embeddings
- Retrieve relevant facts via natural language queries
- The database is stored at `.ccmemory/chroma.db`
