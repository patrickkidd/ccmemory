# Closed-Loop Resolution (CLR): Unified Vision

> **Synthesis doc** — Combines the conceptual foundation (1-CLR--RCA.md) with the automation pipeline (2-CLR--E2E.md) into a coherent system design.

## What CLR Is

**Closed-Loop Resolution** is a context graph application for bug tracking, root cause analysis, and automated remediation. It extends ccmemory's core philosophy to the defect lifecycle.

The name captures the essential insight: defect resolution should be a **closed loop** where:
- Outcomes feed back into knowledge
- Past failures prevent future mistakes
- Patterns emerge from accumulated experience

## Two Modes, One Graph

CLR operates in two complementary modes:

| Mode | Trigger | Human Role | Automation Role |
|------|---------|------------|-----------------|
| **Interactive RCA** | Engineer debugging | Primary investigator | Knowledge assistant |
| **Autonomous CLR** | Automation failure | Reviewer/approver | Primary investigator |

Both modes read from and write to the same graph. An interactive debugging session enriches the graph; the autonomous system uses that knowledge for future errors.

```
                    ┌─────────────────────────────────────┐
                    │         CLR Context Graph           │
                    │                                     │
                    │  Errors, RootCauses, Hypotheses,    │
                    │  Fixes, FailedApproaches, Patterns  │
                    └──────────────┬──────────────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
              ▼                    │                    ▼
    ┌─────────────────┐            │          ┌─────────────────┐
    │  Interactive    │            │          │   Autonomous    │
    │     RCA         │◄───────────┴─────────►│      CLR        │
    │                 │                       │                 │
    │ Engineer + AI   │                       │ AI + Engineer   │
    │ debugging       │                       │ review          │
    └─────────────────┘                       └─────────────────┘
```

### Interactive RCA (Doc 1 Focus)

When an engineer is debugging:

1. **Context retrieval** — Claude searches graph for similar symptoms, related failed fixes, patterns in the same code area
2. **Hypothesis tracking** — Each theory about the cause becomes a node, linked to evidence
3. **Failure memory** — "I tried X, it didn't work because Y" is preserved
4. **Resolution capture** — The root cause and fix are recorded with full decision trace

Value: **Don't repeat mistakes**. Every debugging session enriches the graph for future sessions.

### Autonomous CLR (Doc 2 Focus)

When automation detects a failure:

1. **Error ingestion** — Signature extraction, embedding, deduplication
2. **Pattern matching** — Link to known error patterns, similar past errors
3. **Hypothesis generation** — Propose root causes from graph knowledge
4. **Agentic testing** — Headless Claude Code tests hypotheses in sandbox
5. **PR generation** — Verified fixes become pull requests
6. **Feedback loop** — Merge outcomes update hypothesis confidence

Value: **Close the loop automatically**. Simple bugs get fixed without human intervention.

---

## Unified Ontology

Reconciling the node types from both docs:

### Domain 1: Your Specifics (Events)

| Node Type | Description | Source |
|-----------|-------------|--------|
| **Error** | A specific failure instance with signature, stack trace, context | Automation logs, test runs |
| **Bug** | A ticket/issue tracking one or more related errors | Jira, manual creation |
| **Hypothesis** | A proposed explanation for an error's root cause | Interactive or generated |
| **FailedApproach** | An attempted fix that didn't work (and why) | ccmemory core type |
| **RootCause** | Confirmed underlying cause of one or more errors | Promoted from Hypothesis |
| **Fix** | A code change that resolves a RootCause | PR, commit |
| **Regression** | An error returning after a Fix was applied | Detected by automation |
| **RCASession** | A debugging trajectory (interactive mode) | Conversation capture |

### Domain 1: Infrastructure Context

| Node Type | Description | Source |
|-----------|-------------|--------|
| **AutomationRun** | A single test/validation execution | CI, test harness |
| **CodeArea** | File, module, or component where errors cluster | Static analysis, git |
| **Environment** | Runtime context (OS, versions, config) | Automation metadata |

### Domain 2: Reference Knowledge

| Node Type | Description | Source |
|-----------|-------------|--------|
| **ErrorPattern** | Canonical error shape with typical cause/fix | Curated from experience |
| **KnownIssue** | Documented bug/limitation with workaround | Errata, release notes |
| **SpecSection** | Specification text for compliance checking | Imported docs |

### Key Relationships

```cypher
// Error lifecycle
(Error)-[:DURING]->(AutomationRun)
(Error)-[:IN_AREA]->(CodeArea)
(Error)-[:TRACKED_BY]->(Bug)
(Error)-[:SIMILAR_TO {confidence}]->(Error)
(Error)-[:CAUSED_BY]->(RootCause)

// Investigation
(Hypothesis)-[:FOR]->(Error)
(Hypothesis)-[:BASED_ON]->(Error | Pattern | Insight)
(Hypothesis)-[:DISPROVED_BY]->(Evidence)
(RCASession)-[:INVESTIGATED]->(Error)
(RCASession)-[:PRODUCED]->(Hypothesis | RootCause)

// Resolution
(RootCause)-[:SHARED_BY]->(Error)      // Multiple errors, one cause
(Fix)-[:RESOLVES]->(RootCause)
(Fix)-[:VERIFIED_BY]->(AutomationRun)
(Regression)-[:OF]->(Fix)              // This fix regressed
(Regression)-[:MANIFESTS_AS]->(Error)  // As this new error

// Patterns (Domain 2 bridges)
(Error)-[:MATCHES]->(ErrorPattern)
(RootCause)-[:INSTANCE_OF]->(KnownIssue)
(CodeArea)-[:HOTSPOT_FOR]->(ErrorPattern)
```

---

## The Ontology Question

From our earlier discussion: **Does CLR need to discover its ontology dynamically?**

### Current Position: Fixed Core, Extensible Edges

The node types above are **fixed** — they represent the universal structure of how defects are discovered, investigated, and resolved. This mirrors ccmemory's philosophy: the 8 core types (Decision, Correction, Exception, etc.) capture how understanding evolves, not domain-specific entities.

What's **extensible**:
- Properties on nodes (arbitrary metadata)
- Relationship types (domain-specific connections)
- ErrorPattern definitions (new patterns from experience)
- CodeArea granularity (file, function, module)

### Why This Works for Defect Tracking

Unlike general knowledge graphs, defect tracking has a **well-defined lifecycle**:

```
Error → Bug → Hypothesis → [FailedApproach]* → RootCause → Fix → [Regression]?
```

This lifecycle is invariant across domains (software, hardware, validation). The specific error signatures, code areas, and patterns vary — but the structure doesn't.

### When Discovery Might Be Needed

If CLR expands to capture:
- **Domain-specific entities** (e.g., "Protocol", "Register", "Timing constraint")
- **Cross-system dependencies** (e.g., "Firmware version X requires driver version Y")
- **Organizational knowledge** (e.g., "Team A owns module B")

These would be **Domain 2 extensions**, not core ontology changes. They'd be imported from external sources or defined per-deployment.

---

## Backfill Strategy

Both modes benefit from historical data. The richer the graph at day one, the more valuable both interactive and autonomous modes become.

### Priority Order (by value/effort ratio)

1. **Jira history** — Richest source of RootCause/Fix/Regression relationships
2. **Git history** — Fix commits, linked issues, code area changes
3. **PR history** — Review discussions often contain RCA reasoning
4. **Test automation logs** — Error signatures, temporal patterns
5. **Teams/Outlook** — RCA discussions (lower signal, higher extraction cost)

### Backfill Creates ErrorPatterns

The key insight: backfill isn't just populating Domain 1. It's **discovering Domain 2 patterns**.

```python
def discover_patterns_from_history(errors: List[Error]) -> List[ErrorPattern]:
    """
    Cluster historical errors by signature similarity.
    Extract common root causes from resolved clusters.
    Generate ErrorPattern nodes for future matching.
    """
    clusters = cluster_by_embedding(errors)

    patterns = []
    for cluster in clusters:
        resolved = [e for e in cluster if e.root_cause]
        if len(resolved) >= 3:  # Enough signal
            pattern = ErrorPattern(
                signature_regex=generalize_signatures(cluster),
                typical_root_cause=most_common(e.root_cause for e in resolved),
                typical_fix=most_common(e.fix for e in resolved),
                confidence=len(resolved) / len(cluster)
            )
            patterns.append(pattern)

    return patterns
```

---

## Integration Points

### With ccmemory Core

CLR extends, not replaces, ccmemory:

| ccmemory Type | CLR Usage |
|---------------|-----------|
| `Session` | RCASession is a specialized session |
| `Decision` | Fix decisions use the same structure |
| `Correction` | "Actually, the root cause was X, not Y" |
| `FailedApproach` | Failed fixes, disproved hypotheses |
| `Insight` | Patterns discovered during RCA |
| `ProjectFact` | "This codebase uses X testing framework" |

### With External Systems

| System | Integration |
|--------|-------------|
| **Jira** | Bidirectional: import issues, create tickets, update status |
| **Git/Bitbucket/GitHub** | Import commits, PRs; push generated fixes |
| **CI/CD** | Webhook on failure → Error ingestion |
| **Test harness** | Log parsing, error signature extraction |
| **Claude Code** | Headless mode for agentic testing |

---

## Implementation Strategy

### Phase 0: Validate with Interactive RCA

Before building automation, prove value with the simpler mode:

1. Add `Error`, `RootCause`, `Hypothesis` to ccmemory schema
2. Add hooks to detect debugging context (stack traces, error messages)
3. Prompt for structured capture: "What was the root cause? What did you try first?"
4. Query similar errors when new ones appear

**Success metric**: Engineers report finding relevant past context during debugging.

### Phase 1: Backfill Foundation

Populate the graph from history:

1. Jira importer with relationship extraction
2. Git history parser for fix/issue linking
3. Error signature extraction and embedding
4. Initial ErrorPattern discovery from clusters

**Success metric**: Graph contains >70% of resolved bugs from last 6 months.

### Phase 2: Deduplication & Pattern Matching

Close the loop on error identification:

1. Real-time error ingestion from automation
2. Similarity search for deduplication
3. ErrorPattern matching for known issues
4. Auto-link errors to existing Bugs or create new

**Success metric**: 50% reduction in duplicate Jira tickets.

### Phase 3: Hypothesis Engine

Generate and rank root cause hypotheses:

1. Hypothesis generation from graph context
2. Evidence-based confidence scoring
3. Ranking by testability and likelihood
4. Human review workflow for validation

**Success metric**: >30% of hypotheses ranked #1 are confirmed as root cause.

### Phase 4: Agentic Testing

Autonomous fix verification:

1. Headless Claude Code integration
2. Sandboxed test execution
3. Result capture and graph update
4. Human checkpoint for generated fixes

**Success metric**: 10% of simple errors fixed without human code changes.

### Phase 5: Full Closed Loop

End-to-end automation:

1. Auto Jira creation with rich context
2. PR generation from verified fixes
3. Confidence-based auto-merge (low risk)
4. Regression detection and fix quality tracking

**Success metric**: 50% reduction in time-to-resolution for automation failures.

---

## Open Questions

### From Doc 1 (Interactive RCA)

1. **Granularity** — When does a debug session warrant capture? Need clear triggers.
2. **Signal vs noise** — Not every error is worth graphing. Severity/frequency thresholds?
3. **Automation risk** — "This looks like bug X" could mislead. Confidence UX matters.

### From Doc 2 (Autonomous CLR)

1. **Sandboxing** — Docker vs VM vs cloud ephemeral. Speed/isolation tradeoff.
2. **Test flakiness** — How to distinguish real failures from flaky tests?
3. **Partial fixes** — What if a fix resolves some but not all related errors?

### New Questions (Synthesis)

1. **Mode transition** — When does interactive RCA trigger autonomous follow-up? (e.g., "I found the root cause, auto-generate the fix?")
2. **Confidence calibration** — Interactive mode has implicit human validation. Autonomous mode needs explicit confidence thresholds. How to calibrate?
3. **Knowledge promotion** — When does an interactively-discovered pattern become a curated ErrorPattern?

---

## Relationship to ccmemory Vision

CLR is a **vertical application** of ccmemory's horizontal platform:

| ccmemory Principle | CLR Application |
|--------------------|-----------------|
| Event clock > state clock | Bug lifecycle as events, not just "open/closed" |
| Decision traces | Full RCA trajectory preserved |
| Two-domain architecture | Your errors (D1) + Known patterns (D2) |
| Corrections as highest value | "Actually the root cause was X" |
| Trajectories as data | Debugging sessions are informed walks |
| Schema as output | ErrorPatterns discovered from clusters |

The vision doc's statement applies directly:

> "You don't need to understand a system to represent it. Traverse it enough times and the representation emerges."

CLR traverses the defect space. Patterns emerge. The graph becomes a world model for predicting root causes.

---

## References

- [1-CLR--RCA.md](1-CLR--RCA.md) — Conceptual foundation, interactive mode
- [2-CLR--E2E.md](2-CLR--E2E.md) — Automation pipeline, system integration
- [PROJECT_VISION.md](../PROJECT_VISION.md) — Core ccmemory philosophy
- [WHY_GRAPH.md](../WHY_GRAPH.md) — Why graphs over search
