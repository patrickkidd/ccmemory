# Clarification 1: DAG with Cross-References, Not Session Trees

## The Problem

The current schema organizes the graph around Sessions:

```
Session → DECIDED → Decision
Session → CORRECTED → Correction
Session → TRIED → FailedApproach
```

This is wrong. Sessions are ephemeral process boundaries — a Claude Code instance connecting to an MCP instance. They have no semantic meaning. Users start many sessions per day and treat them as throwaway.

Per the [Gupta/Garg thesis](https://foundationcapital.com/context-graphs-ais-trillion-dollar-opportunity/):

> "a living record of decision traces stitched across entities and **time** so precedent becomes searchable"

The organizing principle should be **time** and **entity relationships**, not ephemeral containers.

## The New Model

Decisions (and all other Domain 1 nodes) exist as timestamped events that link to entities:

```
Decision A (Jan 5, project=ccmemory)
    ↓ SUPERSEDES
Decision B (Jan 20, project=ccmemory) ←─ SIMILAR_TO ─→ Decision C (Jan 22, project=other)
    ↓ CONSTRAINS
Decision D (Feb 1, project=ccmemory)
    ↑
    └── REFERENCES ── Exception E
```

**Structure:** Directed acyclic graph with cross-references

- **Temporal ordering** via timestamp (all nodes)
- **Supersession** (A → B: "we changed our approach")
- **Cross-project similarity** (B ↔ C: "same pattern as...")
- **Precedent chains** (D references prior decision or exception)
- **Entity links** (decisions relate to projects, files, concepts, people)

## Impact on Node Types

### Domain 1: Your Specifics

All Domain 1 nodes share a common base:

| Field | Purpose |
|-------|---------|
| `id` | Unique identifier |
| `timestamp` | When recorded (primary ordering) |
| `project` | Which project (optional — some nodes are cross-project) |
| `content` | The substance |
| `embedding` | Vector for semantic search |

**Decision** — choices with rationale
- Links: `SUPERSEDES`, `CONSTRAINS`, `SIMILAR_TO`, `REFERENCES`
- Fields: description, rationale, options_considered, revisit_trigger, status

**Correction** — updated beliefs (highest value per Gupta)
- Links: `CORRECTS` (points to what was wrong), `SIMILAR_TO`
- Fields: wrong_belief, right_belief, severity
- Note: Corrections ARE decisions about beliefs. Could merge into Decision with `type=correction`.

**Exception** — rules that don't apply in your context
- Links: `CONTRADICTS` (general advice), `SIMILAR_TO`
- Fields: rule_broken, justification, scope

**FailedApproach** — what didn't work (negative precedent)
- Links: `INFORMS` (future decisions), `SIMILAR_TO`
- Fields: approach, outcome, lesson

**Insight** — realizations and patterns
- Links: `BASED_ON` (observations/decisions), `SUPPORTS` (hypotheses)
- Fields: summary, category, detail, implications

**Question** — unanswered queries (knowledge gaps)
- Links: `ANSWERED_BY` (when resolved), `RELATES_TO`
- Fields: question, answer, context

**ProjectFact** — stated facts about projects
- Links: `ABOUT` (project entity), `SUPERSEDES`
- Fields: fact, category, context

**Observation** — personal data points (health, events, measurements)
- Links: `DURING` (events), `CORRELATES_WITH`, `PRECEDED_BY`, `FOLLOWED_BY`
- Fields: type, content, severity, source

### Domain 2: Reference Knowledge

**Concept** — definitions from literature
- Links: `SOURCED_FROM`, `RELATES_TO`
- Fields: name, definition, domain, type

**Hypothesis** — testable predictions
- Links: `BASED_ON` (observations + concepts), `TESTED_BY` (observations)
- Fields: statement, testable_prediction, status

**Chunk** — indexed document fragments
- Links: `FROM_SOURCE`, `MENTIONS` (concepts)
- Fields: content, source_file, section, embedding

### Bridge Layer

Edges connecting Domain 1 to Domain 2:
- `MAY_BE_INSTANCE_OF` (proposed, needs validation)
- `INSTANCE_OF` (validated)
- `APPLIES_FRAMEWORK` (decision uses a concept)
- `CONTRADICTS_GENERAL_ADVICE` (exception vs. concept)

### What Gets Removed

**Session** — delete entirely. No value.

If we need to track "which Claude Code run recorded this," add an optional `source_session` field to nodes. But don't make it a first-class graph entity.

**Retrieval** — currently tracks what context was surfaced per session. Without sessions, this becomes optional telemetry, not a core node type.

## Querying Without Sessions

Current query pattern:
```cypher
MATCH (s:Session {project: $project})-[:DECIDED]->(d:Decision)
RETURN d ORDER BY s.started_at DESC
```

New query pattern:
```cypher
MATCH (d:Decision {project: $project})
RETURN d ORDER BY d.timestamp DESC
```

Simpler. The timestamp IS the ordering. No session indirection.

### Precedent Queries

Find decisions that informed the current one:
```cypher
MATCH (d:Decision {id: $id})-[:REFERENCES|SUPERSEDES*1..3]->(prior)
RETURN prior ORDER BY prior.timestamp DESC
```

Find similar decisions across projects:
```cypher
MATCH (d:Decision {id: $id})-[:SIMILAR_TO]-(similar)
RETURN similar
```

## Multi-Domain Support

The vision doc describes use cases beyond software:

| Domain | Primary Node Types | Key Relationships |
|--------|-------------------|-------------------|
| Software | Decision, Correction, Exception, FailedApproach, ProjectFact | SUPERSEDES, CONSTRAINS, REFERENCES |
| Career | Decision, Insight, Question | SIMILAR_TO, INFORMS |
| Health | Observation, Hypothesis, Decision | CORRELATES_WITH, TESTED_BY, BASED_ON |
| Relationships | Observation, Event, Person | DURING, PRECEDED_BY, INVOLVES |

All share the same base structure: timestamped nodes with entity links and cross-references. The graph topology is consistent; only the node types and relationship semantics vary.

## Migration

1. Remove Session nodes
2. Copy `session.started_at` to child nodes as `timestamp` (where missing)
3. Copy `session.project` to child nodes as `project` (where missing)
4. Delete Session→* relationships
5. Add `SUPERSEDES`, `SIMILAR_TO` edges based on semantic similarity

## Validation Against Gupta/Koratana Follow-Up

Koratana's [How to Build a Context Graph](https://www.linkedin.com/pulse/how-build-context-graph-animesh-koratana-6abve) and related analysis confirm and extend this direction.

### The Two Clocks Problem

> "We've built trillion-dollar infrastructure for what's true now. Almost nothing for why it became true."

- **State clock:** current system states (CRM values, ticket statuses, code)
- **Event clock:** what happened, in what order, with what reasoning

Sessions are state-clock artifacts (process boundaries). Decision traces are event-clock artifacts (reasoning captured). We should be building event-clock infrastructure.

### Agent Trajectories as Schema Discovery

Koratana proposes agents as "informed walkers" — their problem-solving paths implicitly map organizational structure. Schema emerges from use, not upfront design.

**Implication for ccmemory:** Don't pre-define rigid node types. Let the graph structure emerge from what actually gets recorded. The current node types (Decision, Correction, Exception, etc.) are reasonable starting points, but shouldn't be treated as fixed ontology.

### Five Coordinate Systems

Context requires joining across misaligned geometries:
1. **Events** — what occurred
2. **Timeline** — when it happened
3. **Semantics** — meaning (vector space)
4. **Attribution** — ownership (graph structure)
5. **Outcomes** — causal effects (DAGs)

**Implication:** Our current model handles 1-3 well (timestamped events with embeddings). Attribution (#4) needs entity linking. Outcomes (#5) needs `CAUSED`, `LED_TO` relationships we don't currently capture.

### World Models vs. Retrieval

> "Simulation is the test. If you can ask 'what if?' and get useful answers, you've built something real."

Context graphs should enable counterfactual reasoning, not just search. A mature graph becomes "a world model for organizational physics."

**Implication:** The graph should eventually support queries like:
- "If we change this, what else breaks?" (constraint propagation)
- "What happened last time we tried something similar?" (precedent matching)
- "What's the likely outcome of this approach?" (pattern projection)

### Structural vs. Semantic Embeddings

Koratana distinguishes:
- **Semantic embeddings:** similarity based on meaning
- **Structural embeddings:** similarity based on role/position in graph

Nodes are similar if they "play analogous roles" — two engineers who've never met become structurally equivalent through parallel decision patterns.

**Implication:** Current vector search uses semantic embeddings. Future work should consider graph-based similarity (node2vec-style) for precedent matching.

### Alignment Check

| Gupta/Koratana Principle | Current Clarification | Status |
|--------------------------|----------------------|--------|
| Event clock, not state clock | Timestamps as primary ordering | ✓ Aligned |
| Decision traces, not containers | Sessions removed | ✓ Aligned |
| Schema as output | Fixed node types | ⚠️ Partially aligned — should be more flexible |
| Precedent searchable | `SUPERSEDES`, `SIMILAR_TO` edges | ✓ Aligned |
| World model capability | Not yet addressed | ❌ Gap — needs outcome/causal edges |
| Structural embeddings | Semantic only | ⚠️ Gap — future enhancement |

## Parallel Traces and Topic Detection

A project contains multiple parallel decision traces (auth, database, deployment, etc.). Without topic detection, the DAG becomes a single chain ordered by time.

### The Problem

```
Decision 1 (auth): Use JWT tokens
Decision 2 (db): Use PostgreSQL
Decision 3 (auth): Add refresh tokens  ← should link to Decision 1
Decision 4 (deploy): Use Docker
Decision 5 (auth): Token expiry 1hr    ← should link to Decisions 1, 3
```

Pure embedding similarity may link 1→3→5 (auth cluster), but won't know they're the "auth trace" vs the "db trace."

### Solution: Topic/Component Tags

Each node gets a `topics` array (detected or explicit):

```cypher
(:Decision {
  id: "dec-001",
  description: "Use JWT tokens for API auth",
  topics: ["auth", "api", "security"],
  ...
})
```

**Detection:** LLM extracts topics from description + rationale. Common patterns:
- File paths → component ("src/auth/" → "auth")
- Keywords → domain ("PostgreSQL" → "database")
- Explicit mentions → topic ("for the deployment pipeline" → "deployment")

### Cross-Trace Edges

When a decision spans topics, create explicit cross-trace links:

- `IMPACTS` — Decision in trace A affects trace B
- `DEPENDS_ON` — Decision in trace A requires something from trace B
- `CONFLICTS_WITH` — Decisions in different traces are incompatible

Example:
```
Decision (auth): "Store sessions in Redis"
    ↓ IMPACTS
Decision (db): "Redis cluster configuration"
```

### Queries for Parallel Traces

Show all decisions in a topic:
```cypher
MATCH (d:Decision {project: $project})
WHERE $topic IN d.topics
RETURN d ORDER BY d.timestamp DESC
```

Find cross-trace dependencies:
```cypher
MATCH (d:Decision)-[:IMPACTS|DEPENDS_ON]->(other:Decision)
WHERE d.project = $project
  AND NOT any(t IN d.topics WHERE t IN other.topics)
RETURN d, other
```

## Cross-Reference Relationship Types

Current implementation only has `SUPERSEDES` and `CITES` (similarity-based). Need richer relationship types:

| Relationship | Meaning | Detection |
|--------------|---------|-----------|
| `SUPERSEDES` | Replaces prior decision | High embedding similarity (>0.85) |
| `CITES` | References prior decision | Moderate similarity (>0.8) |
| `CONSTRAINS` | Limits what another decision can do | LLM detection: "because of X, we can't Y" |
| `DEPENDS_ON` | Requires another decision | LLM detection: "this requires X" |
| `CONFLICTS_WITH` | Incompatible with another | LLM detection: "can't do X if we do Y" |
| `IMPACTS` | Affects another trace/topic | LLM detection: cross-topic mention |
| `INFORMS` | Provides context for another | Weaker than DEPENDS_ON |

**Detection prompt addition:** When recording a decision, ask: "Does this relate to any prior decisions? How? (supersedes, constrains, depends on, conflicts with)"

## Project Facts as Binding Instructions

Project facts must replace CLAUDE.md custom instructions. Users should tell Claude something once and never repeat.

### Requirements

1. **Inject as instructions, not context** — Format as "## Project Rules" not "## Recent Context"
2. **Authoritative** — SKILL.md tells Claude to follow them like CLAUDE.md
3. **Capture "always/never" patterns** — Detection looks for rules: "always use X", "never do Y", "we prefer Z"
4. **Supersession** — New facts can supersede old ones (latest wins)
5. **Categories** — workflow, convention, constraint, tool, pattern

### Context Injection Format

```markdown
## Project Rules (from context graph — treat as custom instructions)

### Conventions
- Use camelCase for all method names
- One class per file

### Constraints
- Never use sync I/O in request handlers
- All API responses must include request_id

### Workflows
- Run tests before committing
- Use feature branches for all changes
```

### Detection Enhancement

Add to detection prompt:
```
Look for statements that establish project rules:
- "Always do X" / "Never do Y" → ProjectFact (constraint)
- "We use X for Y" → ProjectFact (tool/convention)
- "The pattern is X" → ProjectFact (pattern)
- "When doing X, always Y" → ProjectFact (workflow)
```

## Open Questions: Query On Demand, Don't Auto-Inject

**Problem:** Auto-injecting open questions causes Claude to constantly steer back to them, even when irrelevant to current work.

**Solution:** Don't inject open questions at session start. Provide a tool for Claude to query when relevant.

### Behavior

1. **Session start:** Don't include open questions in context
2. **During conversation:** If Claude detects relevance, it can call `queryOpenQuestions(topic)`
3. **SKILL.md instruction:** "Query open questions only when the conversation naturally touches on an unresolved area"

### When to Surface Questions

- User asks about a topic that has open questions
- User is about to make a decision in an area with unresolved questions
- User explicitly asks "what's unresolved?"

### Tool Interface

```typescript
queryOpenQuestions(topic?: string) → Question[]
// Returns questions where answer is null/empty
// Optionally filtered by topic similarity
```

## Pattern Detection for Dashboard

Patterns detectable from graph structure:

| Pattern | Query | Value |
|---------|-------|-------|
| Exception clusters | `GROUP BY rule_broken, COUNT(*)` | "4 exceptions to 'use async' rule — may need revision" |
| Supersession chains | `MATCH path = (d)-[:SUPERSEDES*2..]->(old)` | "retry-logic evolved through 3 iterations" |
| Failed approach recurrence | Similar failed approaches | "caching tried 2x, failed both — review before trying again" |
| Correction hotspots | Topics with high correction count | "auth decisions corrected 3x — understanding may be incomplete" |
| Cross-project similarity | `MATCH (d)-[:SIMILAR_TO]-(other) WHERE other.project <> d.project` | "Similar to api-gateway project (3 matches)" |
| Stale decision clusters | Stale decisions in same topic | "3 stale decisions in 'deployment' topic" |
| Constraint violations | Decisions that conflict with ProjectFacts | "Decision X may conflict with rule Y" |

### Dashboard Section

```
## Patterns Noticed

⚠️ "Use async for I/O" has 4 exceptions — consider revising rule or documenting exceptions
📈 Auth decisions: JWT → refresh tokens → session management (3-step evolution)
🔄 Caching approaches failed twice — last attempt: "Redis cluster", lesson: "network partitions"
🔗 Similar decisions in `api-gateway`: rate limiting, circuit breakers
```

## Summary

- **Primary key:** timestamp + project (not session)
- **Structure:** DAG with cross-references
- **Sessions:** deleted, not needed
- **Queries:** direct on nodes, ordered by timestamp
- **Multi-domain:** same topology, different node types
- **Topics:** enable parallel traces within a project
- **Cross-refs:** richer relationship types beyond similarity
- **Project facts:** binding instructions, replace CLAUDE.md
- **Open questions:** query on demand, don't auto-inject
- **Patterns:** detectable from graph structure for dashboard
- **Future:** outcome edges for simulation, structural embeddings for role-based similarity

## References

- [AI's Trillion-Dollar Opportunity: Context Graphs](https://foundationcapital.com/context-graphs-ais-trillion-dollar-opportunity/) — Gupta & Garg
- [How to Build a Context Graph](https://www.linkedin.com/pulse/how-build-context-graph-animesh-koratana-6abve) — Koratana
- [What Are Context Graphs, Really?](https://subramanya.ai/2026/01/01/what-are-context-graphs-really/) — Analysis/synthesis
