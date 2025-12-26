# CLAUDE.md Integration for ccmemory

Add these sections to your project's CLAUDE.md file.

---

## Session Handoff (MANDATORY)

At the START of each session:
1. Read `.ccmemory/session.md` for previous session context
2. Check memory service for relevant stored facts

At the END of each session:
1. Update `.ccmemory/session.md` with:
   - Key learnings from this session
   - Decisions made (with reasoning)
   - Open questions for next session
   - Files modified

## Context Loading

Before starting any task, check `.ccmemory/doc-index.md` to identify which documentation files are relevant to the task at hand.

---

# Optional: Authoritative Docs Table

If you have domain-specific documentation, add a routing table:

```markdown
## Authoritative Docs

| Knowledge Domain | Authoritative Doc |
|------------------|-------------------|
| API endpoints | docs/API.md |
| Database schema | docs/SCHEMA.md |
| Deployment | docs/DEPLOYMENT.md |
| Architecture | docs/ARCHITECTURE.md |
```
