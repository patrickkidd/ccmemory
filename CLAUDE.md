# ccmemory Development Context

Claude Code instructions for developing the ccmemory plugin itself.

## Project Purpose

A Claude Code plugin providing **executive oversight** for context management. Ensures nothing important is lost and everything learned is reused across sessions.

## Core Concept

The plugin acts as a consultant watching over Claude's shoulder - an executive function that monitors the information stream and ensures every important piece gets captured and reused.

**Not** passive trigger detection. **Active** oversight ensuring the knowledge base grows.

---

## Corrections Log

Lessons learned during development - highest priority context.

### 1. No Separate Memory Silos

**Wrong:** Creating gotchas.md, separate storage files for different info types.

**Correct:** All information goes into the **project's natural hierarchy** - CLAUDE.md, doc/, decisions/, etc. The plugin teaches Claude to use the existing structure, not create parallel storage.

### 2. Include All Source Patterns

**Wrong:** Cherry-picking patterns from source projects.

**Correct:** The self-learning patterns from `/Users/patrick/career/CLAUDE.md` work "very, very well" - include ALL of them:
- "Always be learning" / "Always be optimizing"
- "Sculpt your understanding like a sculptor"
- Meta self-improvement (project teaches itself to learn better)
- Normalized index structure (2-hop max)
- session.md as working memory
- Cross-reference coherence with specific relationship examples
- Archive workflow with living history
- Lossless compression
- Proactive staleness detection AND proactive staleness checks (ask periodically)
- Periodic snapshots for evolving context
- Interview until total picture
- Web resource caching
- Decision capture with confirmation step
- Explicit life change triggers

Also include patterns from `/Users/patrick/theapp/CLAUDE.md`:
- Correction detection (mandatory, highest priority)
- Knowledge routing table
- Decision log format with revisit triggers
- Documentation sync
- ADR system

### 3. Sculpt, Don't Replace

**Wrong:** Wholesale replacing content when making changes.

**Correct:** Refine and add to existing content. Build on what's there. Like a sculptor - becoming more accurate without losing important info.

This applies to developing this plugin AND to what the plugin teaches Claude to do with project context.

### 4. Executive Function Framing

**Wrong:** Passive trigger detection that fires on patterns.

**Correct:** Active executive oversight that:
- Monitors the information stream
- Ensures nothing important is lost
- Ensures everything is reused
- Holds Claude accountable for knowledge base quality

The Executive Check: "Did the user just tell me something important that I should remember next session?"

The Executive Question: "Is documentation more complete and accurate after this conversation?"

### 5. Encyclopedia, Not Storage

**Wrong:** Storing facts in memory files.

**Correct:** Maintaining a **well-indexed encyclopedia** across project folders:
- Normalized like a database
- One source of truth per fact
- 2-hop discoverability from root
- Keyword-rich indexes for grep
- Root CLAUDE.md is schema, not data

---

## File Structure

```
ccmemory/
├── CLAUDE.md                  # This file - project context
├── hooks/hooks.json           # SessionStart, UserPromptSubmit, Stop
├── prompts/analyze-message.md # Executive oversight prompt (LLM)
├── scripts/
│   ├── load-memory.sh         # Session start - load context
│   ├── log-session.py         # Session end - archive conversation
│   └── save-memory.sh         # Session end - reminder
├── skills/memory/SKILL.md     # Full executive oversight instructions
└── templates/                 # Initial file templates for .ccmemory/
```

## Key Files

| File | Purpose |
|------|---------|
| `skills/memory/SKILL.md` | The core teaching - executive oversight instructions |
| `prompts/analyze-message.md` | LLM prompt for UserPromptSubmit hook |
| `scripts/log-session.py` | Session logging with keyword extraction (from career) |

## Development Principles

1. **Practice what we preach** - This plugin's development should follow its own patterns
2. **Sculpt, don't replace** - Refine existing content, don't wholesale replace
3. **Test the teaching** - The skill instructions should work when applied to real projects
4. **Source patterns matter** - The career and theapp patterns are proven; preserve them

---

## Source Projects

Patterns derived from:

- `/Users/patrick/career/CLAUDE.md` - Self-learning context system that works "very, very well"
- `/Users/patrick/theapp/CLAUDE.md` - Correction detection, knowledge routing, decision logging
