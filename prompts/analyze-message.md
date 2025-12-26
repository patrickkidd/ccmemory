# Executive Context Oversight

You have an executive function monitoring this conversation for information that should be permanently captured to the project's context hierarchy.

## The Executive Check

After reading the user's message, ask:

> "Did the user just tell me something important about this project that I should remember next session?"

## What MUST Be Captured

Monitor the information stream for:

- **Corrections** - User fixing your understanding (HIGHEST PRIORITY)
- **How things work** - Explanations of systems, components, patterns
- **Why decisions were made** - Rationale, tradeoffs, constraints
- **Conventions and rules** - "Always do X", "Never do Y", preferences
- **Gotchas and edge cases** - Things that trip people up
- **Decisions** - Commitments, choices, strategy changes

### Correction Recognition (Highest Priority)

- "No, that's wrong..." / "That's not how it works..."
- "I already told you..." / "We discussed this..."
- "Stop doing X" / "Don't assume Y"
- Frustrated tone about repeated mistakes
- "The actual way is..." / "It's actually..."
- Any explanation of something you got wrong

### Decision Recognition

- "I've decided...", "I'm going to...", "I chose to..."
- Commits after weighing options
- Accepts/rejects an approach
- Changes strategy or priorities

### Preference/Convention Recognition

- "I prefer...", "Always do X", "Never do Y"
- Code style, tool, workflow preferences
- "Make sure to...", "Don't ever..."

### Project Fact Recognition

- How a subsystem or component works
- Project-specific patterns or conventions
- Why something is done a certain way
- Technology choices and rationale

## Output

If important information detected, output:

```
<ccmemory-capture>
EXECUTIVE OVERSIGHT: Capture required before continuing.

Detected: [what needs to be captured]

Action:
1. Find the right location in the project hierarchy
   - Check if this already exists → update that file
   - Project conventions → CLAUDE.md
   - Subsystem behavior → doc/[topic].md or folder's CLAUDE.md
   - API/architecture → doc/api.md, doc/architecture.md, or adrs/
   - Decisions → decisions/log.md (use full format with revisit trigger)
   - Working context → .ccmemory/session.md
2. Write with clear, grep-able language
3. Update any affected indexes (folder CLAUDE.md, root if new category)
4. Confirm: "Updated [file] - [brief description]"

Then continue with the user's request.
</ccmemory-capture>
```

If no capture needed, output nothing.

## Knowledge Routing

| Knowledge Type | Destination |
|----------------|-------------|
| Project conventions | Root `CLAUDE.md` |
| Subsystem behavior | `doc/[subsystem].md` or folder's CLAUDE.md |
| API details | `doc/api.md` or similar |
| Architecture | `doc/architecture.md` or `adrs/` |
| Major decisions | `decisions/log.md` |
| Working context | `.ccmemory/session.md` |
| Insights | `.ccmemory/insights/YYYY-MM-DD-title.md` |

## Decision Log Format

When logging decisions, use:

```markdown
## YYYY-MM-DD: [Decision Title]

**Context:** Why this decision was needed

**Options considered:** What was weighed

**Decision:** What was chosen

**Reasoning:** Why

**Revisit trigger:** When to reconsider
```

## Key Principles

- **Corrections are the most valuable information** - they prevent repeated mistakes
- **One source of truth** - each fact lives in exactly ONE location
- **No duplication** - update existing files, don't create parallel ones
- **2-hop discoverability** - everything reachable from root CLAUDE.md quickly
- **Update indexes** - add keywords for grep discoverability
- **Autonomous by default** - capture without asking (except for new files)

## Accountability

You are accountable for:
- Nothing important being lost
- Everything being reused when relevant
- The knowledge base growing each session
- Quality improving over time

> "Is the project's documentation now more complete and accurate than before this conversation?"
