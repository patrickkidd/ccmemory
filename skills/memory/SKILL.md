# Memory Management Skill

This skill teaches you how to use the ccmemory persistent context system.

## Overview

The ccmemory plugin provides persistent memory across Claude Code sessions via:
1. **Semantic memory** - ChromaDB vector database for storing/retrieving facts
2. **Session handoff** - `.ccmemory/session.md` for working memory
3. **Doc index** - `.ccmemory/doc-index.md` for project documentation inventory

## MANDATORY: Capture Triggers

You MUST store information to memory when ANY of these patterns occur:

### 1. User Corrections (Highest Priority)
Recognize these patterns and IMMEDIATELY store the correction:
- "No, that's wrong..." / "That's not how it works..."
- "I already told you..." / "We discussed this..."
- "Stop doing X" / "Don't assume Y"
- "The actual way is..." / "It's actually..."
- Any frustrated tone about repeated mistakes
- Any time the user explains something you got wrong

**Response to corrections:**
1. Acknowledge briefly (no over-apologizing)
2. IMMEDIATELY store the correct information via memory service
3. State: "Stored to memory: [brief description]"
4. Continue with the corrected approach

### 2. Project Facts
Store when the user explains:
- How a subsystem or component works
- Project-specific patterns or conventions
- Why something is done a certain way
- Gotchas, edge cases, or "watch out for X"
- Technology choices and their rationale
- File organization or naming conventions

### 3. Decisions
Store when the user says:
- "I've decided..." / "I'm going to..." / "I chose to..."
- "Let's use X instead of Y"
- "The approach will be..."
- Any commitment after weighing options

### 4. Preferences
Store when the user expresses:
- Code style preferences
- Tool or library preferences
- Workflow preferences
- "I prefer..." / "Always do X" / "Never do Y"

## How to Store Facts

Use the memory service tools to store facts. Each fact should include:
- **What**: The specific information
- **Context**: Why it matters or when it applies
- **Source**: Where this came from (user statement, discovered during task)

Example storage pattern:
```
Store: "Database migrations must use alembic, not raw SQL"
Context: "Project convention for schema changes"
```

## Session Protocols

### Session Start
1. Read `.ccmemory/session.md` for previous session context
2. Query memory service for facts related to the current task
3. Check doc-index for relevant documentation

### Session End
Update `.ccmemory/session.md` with:
- Key learnings from this session
- Decisions made (with reasoning)
- Open questions
- Files modified

## Documentation Index

The `.ccmemory/doc-index.md` lists project documentation. Keep it updated when:
- New documentation files are created
- You discover undocumented but important files
- Documentation structure changes

## Memory vs Session.md vs Docs

| Information Type | Where to Store |
|------------------|----------------|
| Permanent project facts | Memory service |
| Session-specific context | session.md |
| Detailed documentation | Project doc files |
| Quick reference facts | Memory service |
| Corrections/gotchas | Memory service (highest priority) |

## Self-Check

After each user message, ask yourself:
1. Did the user correct me? → Store immediately
2. Did the user explain something about the project? → Store it
3. Did the user make a decision? → Store it
4. Did the user express a preference? → Store it

If yes to any: use the memory service before continuing with the task.
