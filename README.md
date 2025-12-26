# ccmemory

A Claude Code plugin that provides executive oversight for context management. Ensures nothing important is lost and everything learned is reused.

## The Problem

Claude Code forgets between sessions. You explain how something works, make a decision, correct a misunderstanding - and next session, it's gone. You end up re-explaining the same things repeatedly.

## The Solution

ccmemory adds an executive function that monitors every conversation, ensuring:

1. **Nothing important is lost** - Every significant piece of information gets captured
2. **Everything is reused** - When relevant context exists, it's found and applied
3. **The knowledge base grows** - Each session leaves documentation more complete
4. **Quality improves** - Stale, duplicate, or inaccurate info gets fixed immediately

## How It Works

### The Executive Check

After every user message, the plugin prompts Claude to ask:

> "Did the user just tell me something important about this project that I should remember next session?"

If yes → capture it immediately, before continuing with the task.

### What Gets Captured

- **Corrections** - When you fix Claude's understanding (HIGHEST PRIORITY)
- **How things work** - Explanations of systems, components, patterns
- **Why decisions were made** - Rationale, tradeoffs, constraints
- **Conventions and rules** - "Always do X", "Never do Y", preferences
- **Gotchas and edge cases** - Things that trip people up
- **Decisions** - Commitments, choices, strategy changes

### Where It Goes

Information routes to the project's natural hierarchy - not a separate memory silo:

| Knowledge Type | Destination |
|----------------|-------------|
| Project conventions | `CLAUDE.md` |
| Subsystem behavior | `doc/[topic].md` or folder's CLAUDE.md |
| Decisions | `decisions/log.md` |
| Working context | `.ccmemory/session.md` |

### The Context Encyclopedia

The plugin treats project documentation as a normalized encyclopedia:

- **One source of truth** - Each fact lives in exactly ONE location
- **2-hop discoverability** - Everything reachable from root CLAUDE.md in 2 hops
- **Keyword-rich indexes** - Searchable terms for grep
- **Root is schema, not data** - CLAUDE.md points to docs, doesn't contain details

## Installation

```bash
git clone https://github.com/patrickkidd/ccmemory.git ~/.claude/plugins/ccmemory
```

## What It Creates

On first session, ccmemory initializes:

```
your-project/
└── .ccmemory/
    ├── session.md      # Working memory / session handoff
    ├── doc-index.md    # Documentation inventory
    ├── decisions.md    # Decision log (if needed)
    └── insights/       # Significant realizations
```

## The Hooks

| Event | Action |
|-------|--------|
| **SessionStart** | Loads previous session context |
| **UserPromptSubmit** | Executive oversight analyzes each message |
| **Stop** | Logs session, reminds to update session.md |

## Key Behaviors

### Correction Handling

Corrections are the most valuable information - they tell Claude exactly where understanding is wrong.

When you correct Claude:
1. Brief acknowledgment (no over-apologizing)
2. **Immediately** updates the right doc file
3. States: "Updated [file] to prevent recurrence"
4. Continues with corrected approach

### Reuse Protocol

When starting any task, Claude:
1. Scans doc-index for relevant documentation
2. Reads folder-level CLAUDE.md files
3. Checks session.md for recent context
4. Applies what it finds to the work

### Proactive Maintenance

As Claude reads context files, it watches for:
- Outdated information → fixes it
- Broken references → fixes them
- Contradictions → resolves to single truth
- Duplications → consolidates

## Quality Standards

### The Executive Question

After every interaction:

> "Is the project's documentation now more complete and accurate than before this conversation?"

If not, there's work to do.

### Accountability

- Every important fact captured
- No information lost between sessions
- Existing context applied to new work
- Knowledge base growing over time

## Plugin Structure

```
ccmemory/
├── hooks/hooks.json           # Hook configuration
├── prompts/analyze-message.md # Executive oversight prompt
├── scripts/
│   ├── load-memory.sh         # Session start
│   ├── log-session.py         # Session logging
│   └── save-memory.sh         # Session end
├── skills/memory/SKILL.md     # Executive oversight instructions
└── templates/                 # Initial file templates
```

## Requirements

- Claude Code CLI
- Python 3.8+ (for session logging)

## License

MIT
