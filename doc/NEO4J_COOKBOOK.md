# Neo4j Query Cookbook

Run at http://localhost:7474. Return nodes and relationships to see graph visualizations.

---

## See Your AI Getting Smarter

### The Cognitive Coefficient in Action

Every session builds on the last. This query shows accumulated knowledge over time:

```cypher
// Your growing knowledge graph
MATCH (s:Session {project: 'ccmemory'})-[r]->(n)
RETURN s, r, n
```

Sessions appear as hubs. Decisions, corrections, and insights branch off. More connections = smarter AI.

### Project Facts: Your Instructions File in Graph Form

Project conventions captured once, surfaced at every session start. This is the graph equivalent of CLAUDE.md or .cursorrules — but with semantic deduplication and automatic capture:

```cypher
// All project conventions and tools
MATCH (s:Session {project: 'ccmemory'})-[:STATED]->(pf:ProjectFact)
RETURN s, pf
```

Each fact shows category (tool/pattern/convention/environment/constraint) and the convention itself. Say "we use pytest" once and it's captured forever.

```cypher
// Facts by category
MATCH (pf:ProjectFact {project: 'ccmemory'})
RETURN pf.category, collect(pf.fact) as facts
```

### What You'll Never Explain Again

Decisions captured once, available forever:

```cypher
// All decisions with session context
MATCH (s:Session {project: 'ccmemory'})-[:DECIDED]->(d:Decision)
RETURN s, d
```

Hover any decision node to see the description. The AI retrieves these automatically in future sessions.

### Corrections: The Highest-Value Knowledge

When you correct the AI, it learns permanently:

```cypher
// Every time you taught the AI something
MATCH (s:Session {project: 'ccmemory'})-[:CORRECTED]->(c:Correction)
RETURN s, c
```

Each correction node shows `wrong_belief` → `right_belief`. Clusters indicate sessions with heavy learning.

### Mistakes You'll Never Repeat

Failed approaches are captured so the AI doesn't suggest them again:

```cypher
// What didn't work
MATCH (s:Session {project: 'ccmemory'})-[:TRIED]->(f:FailedApproach)
RETURN s, f
```

### Rules That Don't Apply to You

Exceptions document when general advice is wrong for your situation:

```cypher
// Your documented exceptions
MATCH (s:Session {project: 'ccmemory'})-[:EXCEPTED]->(e:Exception)
RETURN s, e
```

---

## Trace Decision History

### Why Did We Build It This Way?

Trace backward through decisions:

```cypher
// Decision evolution — what superseded what
MATCH path = (d1:Decision {project: 'ccmemory'})-[:SUPERSEDES]->(d2:Decision)
RETURN path
```

### Decisions That Reference Earlier Work

```cypher
// Precedent chains
MATCH path = (d1:Decision {project: 'ccmemory'})-[:CITES]->(d2:Decision)
RETURN path
```

---

## Team Knowledge

### Institutional Memory That Never Leaves

When team members leave, their curated decisions stay:

```cypher
// All curated (team-visible) knowledge
MATCH (s:Session {project: 'ccmemory'})-[r]->(n)
WHERE n.status = 'curated'
RETURN s, r, n
```

### Who Contributed What

```cypher
// Team contribution breakdown
MATCH (d:Decision {project: 'ccmemory', status: 'curated'})
RETURN d.user_id, count(d) as decisions
ORDER BY decisions DESC
```

---

## Pattern Detection

### Sessions Where Learning Happened

Find sessions with heavy correction activity:

```cypher
// Sessions with multiple corrections
MATCH (s:Session {project: 'ccmemory'})-[:CORRECTED]->(c:Correction)
WITH s, count(c) as corrections
WHERE corrections > 1
MATCH (s)-[r]->(n)
RETURN s, r, n
```

### Co-Occurring Decisions

Decisions made in the same session may be related:

```cypher
// What decisions happen together
MATCH (s:Session {project: 'ccmemory'})-[:DECIDED]->(d1:Decision)
MATCH (s)-[:DECIDED]->(d2:Decision)
WHERE d1.id < d2.id
WITH d1, d2, count(s) as sessions_together
WHERE sessions_together > 1
RETURN d1.description, d2.description, sessions_together
```

---

## Search & Discovery

### Find Relevant Decisions

```cypher
// Full-text search with session context
CALL db.index.fulltext.queryNodes("decision_search", "authentication")
YIELD node, score
WHERE node.project = 'ccmemory'
WITH node
MATCH (s:Session)-[:DECIDED]->(node)
RETURN s, node
```

### Find What Went Wrong

```cypher
// Search corrections
CALL db.index.fulltext.queryNodes("correction_search", "async")
YIELD node, score
WHERE node.project = 'ccmemory'
RETURN node.wrong_belief, node.right_belief, score
ORDER BY score DESC
```

### Find Failed Approaches

```cypher
// Search failures
CALL db.index.fulltext.queryNodes("failedapproach_search", "timeout")
YIELD node, score
WHERE node.project = 'ccmemory'
RETURN node.approach, node.lesson, score
ORDER BY score DESC
```

### Find Project Conventions

```cypher
// Search project facts
CALL db.index.fulltext.queryNodes("projectfact_search", "pytest")
YIELD node, score
WHERE node.project = 'ccmemory'
RETURN node.category, node.fact, score
ORDER BY score DESC
```

---

## Metrics

### Measure Your Cognitive Coefficient

```cypher
MATCH (d:Decision {project: 'ccmemory'})
WITH count(d) as total_decisions,
     sum(CASE WHEN d.status = 'curated' THEN 1 ELSE 0 END) as curated
MATCH (c:Correction {project: 'ccmemory'})
WITH total_decisions, curated, count(c) as total_corrections
MATCH (s:Session {project: 'ccmemory'})
WITH total_decisions, curated, total_corrections, count(s) as sessions
MATCH (pf:ProjectFact {project: 'ccmemory'})
WITH total_decisions, curated, total_corrections, sessions, count(pf) as project_facts
RETURN
    total_decisions,
    curated,
    total_corrections,
    project_facts,
    sessions,
    round(curated * 100.0 / total_decisions) + '% curated' as curation_rate,
    round(total_corrections * 1.0 / sessions, 2) as corrections_per_session
```

### Stale Decisions Needing Review

```cypher
// Developmental decisions older than 30 days
MATCH (d:Decision {project: 'ccmemory', status: 'developmental'})
WHERE d.timestamp < datetime() - duration({days: 30})
RETURN d.description, d.timestamp,
       duration.inDays(d.timestamp, datetime()).days as days_old
ORDER BY d.timestamp ASC
```

### Decisions with Revisit Triggers

```cypher
MATCH (d:Decision {project: 'ccmemory'})
WHERE d.revisit_trigger IS NOT NULL
RETURN d.description, d.revisit_trigger
```

---

## Time-Based Views

### Last 7 Days

```cypher
MATCH path = (s:Session {project: 'ccmemory'})-[r]->(n)
WHERE s.started_at > datetime() - duration({days: 7})
RETURN path
```

### Last 30 Days

```cypher
MATCH path = (s:Session {project: 'ccmemory'})-[r]->(n)
WHERE s.started_at > datetime() - duration({days: 30})
RETURN path
```

### Activity by Week

```cypher
MATCH (d:Decision {project: 'ccmemory'})
RETURN date(d.timestamp).year as year,
       date(d.timestamp).week as week,
       count(d) as decisions
ORDER BY year DESC, week DESC
```

---

## Multi-Project

### All Your Projects

```cypher
MATCH (s:Session)
WITH s.project as project, count(s) as sessions
OPTIONAL MATCH (d:Decision {project: project})
RETURN project, sessions, count(d) as decisions
ORDER BY sessions DESC
```

### Cross-Project Search

```cypher
CALL db.index.fulltext.queryNodes("decision_search", "API")
YIELD node, score
RETURN node.project, node.description, score
ORDER BY score DESC
LIMIT 20
```

---

## Maintenance

```cypher
// Promote developmental decisions to curated
MATCH (d:Decision {project: 'ccmemory', status: 'developmental'})
SET d.status = 'curated', d.promoted_at = datetime()
RETURN count(d) as promoted

// Find orphan nodes
MATCH (n)
WHERE n.project = 'ccmemory'
  AND NOT (n:Session) AND NOT (n:Chunk) AND NOT (n:TelemetryEvent)
  AND NOT ()-[]->(n)
RETURN labels(n), n.id

// Empty sessions
MATCH (s:Session {project: 'ccmemory'})
WHERE NOT (s)-[]->()
RETURN s.id, s.started_at
```
