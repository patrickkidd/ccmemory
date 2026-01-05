# ccmemory: Context Graph Skill

You have access to a persistent context graph that captures decisions, corrections, insights, and other valuable context from Claude Code sessions. The graph has two domains:

- **Domain 1 (Your Specifics)**: High-confidence lived experience — decisions you made, corrections to Claude's understanding, exceptions to rules, failed approaches
- **Domain 2 (Reference Knowledge)**: Curated reference material — cached URLs, PDFs, indexed documentation

## Available Tools

### Recording Context

Use these tools to explicitly capture important context:

- `recordDecision` — Record a decision with rationale, options considered, and revisit triggers
- `recordCorrection` — Record when the user corrects your understanding (highest value!)
- `recordException` — Record when normal rules don't apply in this context
- `recordInsight` — Record realizations, analyses, or strategic conclusions
- `recordQuestion` — Record meaningful Q&A exchanges
- `recordFailedApproach` — Record what was tried and didn't work
- `recordReference` — Record URLs or file paths mentioned

### Querying Context

Use these tools to retrieve relevant context:

- `queryContext` — Get recent context for the current project
- `searchPrecedent` — Full-text search across all context types
- `searchSemantic` — Semantic similarity search using embeddings
- `queryByTopic` — Get all context related to a specific topic
- `traceDecision` — Get full context around a specific decision
- `queryStaleDecisions` — Find decisions that may need review
- `queryFailedApproaches` — Get failed approaches to avoid repeating mistakes
- `getMetrics` — Get context graph metrics (cognitive coefficient, etc.)

### Reference Knowledge

- `cacheUrl` — Fetch and cache a URL as markdown
- `cachePdf` — Extract PDF content to markdown
- `indexReference` — Rebuild the reference knowledge index
- `queryReference` — Semantic search over cached references
- `listReferences` — List all cached reference files

### Management

- `promoteDecisions` — Promote developmental decisions to curated (team-visible) status

## Behaviors

### When the user makes a decision

1. Record it immediately with `recordDecision`
2. Include the rationale if stated
3. Note any revisit triggers ("if X changes, reconsider")
4. Check for related prior decisions with `searchPrecedent`

### When the user corrects your understanding

**This is the highest-value capture.** When you get something wrong and the user corrects you:

1. Immediately call `recordCorrection` with:
   - `wrong_belief`: What you incorrectly believed
   - `right_belief`: The correct understanding
   - `severity`: How significant the error was

Example triggers:
- "No, that's not right"
- "Actually, in this project we..."
- "That's the wrong approach because..."

### When the user grants an exception

Record with `recordException` when:
- "In this case, skip the normal..."
- "Just this once, we'll..."
- "Despite the rule about X, here we should Y"

### When something doesn't work

Record with `recordFailedApproach` when:
- "That didn't work"
- "Let's try something else"
- After debugging reveals a dead end

### When insights emerge

Record with `recordInsight` for:
- Realizations about the situation
- Strategic conclusions
- Pattern recognition
- Synthesized understanding

### Proactive Context Use

At the start of each session, context is automatically injected. Additionally:

1. **Check for related context** before giving advice — use `searchPrecedent` or `searchSemantic`
2. **Surface failed approaches** before suggesting solutions — use `queryFailedApproaches`
3. **Reference prior decisions** when they're relevant
4. **Flag stale decisions** that may need review

## The Cognitive Coefficient

The system tracks a "cognitive coefficient" — a measure of how much the accumulated context improves effectiveness. This grows as:

- More decisions are captured and reused
- Corrections are learned from
- Failed approaches prevent repeated mistakes
- The graph density increases

Current project metrics can be retrieved with `getMetrics`.

## Team Mode

In team mode (`CCMEMORY_USER_ID` set):
- `developmental` decisions are only visible to their creator
- `curated` decisions are visible to all team members
- Use `promoteDecisions` to make decisions team-visible after they're validated
