# Bug Tracking & Root Cause Analysis with Context Graphs

## Core Fit

The context graph philosophy maps well to bugs because:

1. **Bugs are decisions/events, not just state** — A bug isn't just "status: open/closed", it's a timeline of: discovery → reproduction → hypothesis → failed fix → root cause identified → fix applied → regression. Each step is a decision trace.

2. **Bugs have rich relationships** — They cluster around code areas, share root causes, recur after "fixes", cascade from dependencies. A graph captures these connections better than flat tickets.

3. **The "why" matters more than the "what"** — Knowing *why* a fix worked (or didn't) is more valuable than just recording the fix. This is the decision-trace philosophy.

## Potential Node Types

```
Bug           — The reported symptom
Hypothesis    — "I think X causes this because Y"
FailedFix     — Attempted solution that didn't work (and why)
RootCause     — Confirmed underlying cause
Fix           — Working solution linked to RootCause
Regression    — Bug returning after a Fix
CodeArea      — File/module/function where bugs cluster
```

## High-Value Relationships

- `Bug -[:SHARES_ROOT_CAUSE]-> Bug` — Pattern detection
- `Fix -[:ACTUALLY_FIXED]-> RootCause` (vs just closing the ticket)
- `Hypothesis -[:DISPROVED_BY]-> Evidence`
- `Bug -[:REGRESSED_FROM]-> Fix` — Track fix quality
- `Bug -[:CLUSTERS_IN]-> CodeArea` — Hotspot detection

## How Claude Code Could Use It

**During debugging:**
1. User reports bug → Claude searches graph for similar symptoms
2. Finds related `FailedFix` nodes → Avoids repeating mistakes
3. Finds `RootCause` patterns in same `CodeArea` → Suggests likely causes
4. After fix, records the decision trace for future sessions

**For root cause analysis:**
- Query: "What root causes have affected `auth/` in the last month?"
- Query: "What fixes have regressed?" → Identifies fragile code
- Query: "What hypotheses were disproved for similar bugs?" → Saves investigation time

## Challenges / Open Questions

1. **Granularity** — Is every git commit a "fix"? Every debug session a "hypothesis"? Need clear boundaries.

2. **Extraction** — Unlike decisions in conversation, bugs live in issue trackers, commits, PRs. Would need integration or manual capture.

3. **Signal vs noise** — Not every bug is worth graphing. Typos and trivial fixes add clutter without value.

4. **Automation risk** — Claude suggesting "this looks like bug X" could be wrong and misleading. Confidence thresholds matter.

## Minimum Viable Version

If prototyping with ccmemory's existing structure:

- Use `FailedApproach` for failed fixes (already exists)
- Add a `Bug` node type with properties: `symptom`, `codeArea`, `reproducible`
- Add a `RootCause` node type linked to `Decision` (the fix decision)
- Query by embedding similarity on `symptom` text

Hooks could detect when Claude is debugging (error messages, stack traces in context) and prompt for structured capture.
