# Closed-Loop Resolution: E2E Bug Fixing Vision

> **Supplemental vision doc** — Extends [PROJECT_VISION.md](../PROJECT_VISION.md) for automated error-to-fix workflows in validation and CI environments.

## Naming

**Closed-Loop Resolution (CLR)** — The full cycle from error detection to verified fix.

Why "closed-loop":
- Engineering term (control systems) — output feeds back as input
- Captures the autonomous feedback nature
- Generic across software CI and hardware validation (DUT automation)

Alternative names considered:
- Autonomous Defect Resolution (ADR)
- Agentic Resolution Pipeline (ARP)
- Self-Healing CI/Validation

---

## The Problem

Today's validation infrastructure captures **what failed** but loses **why it failed** and **how it was fixed**:

| What We Capture | What We Lose |
|-----------------|--------------|
| Test X failed at timestamp T | "Initially looked like timing, turned out to be firmware" |
| Jira-1234 exists | "Jira-1234 was initially thought duplicate of 1200, root cause differs" |
| PR-5678 merged | "This fix also resolves Jira-1235 and 1240 (same root cause)" |
| Build is red | "Same failure pattern as last week, same DUT type, thermal correlation" |

Engineers re-discover root causes. Duplicate Jiras proliferate. Tribal knowledge dies when people leave.

---

## The Closed Loop

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌───────────┐ │
│   │  Automation │     │   Error     │     │   Error     │     │   Jira    │ │
│   │    Run      │────►│  Detection  │────►│   Ident/    │────►│  Create/  │ │
│   │             │     │             │     │   Dedup     │     │   Link    │ │
│   └─────────────┘     └─────────────┘     └─────────────┘     └─────┬─────┘ │
│         ▲                                                           │       │
│         │                                                           ▼       │
│   ┌─────┴─────┐     ┌─────────────┐     ┌─────────────┐     ┌───────────┐   │
│   │    PR     │     │  Root Cause │     │  Hypothesis │     │ Hypothesis│   │
│   │  Verify   │◄────│   Testing   │◄────│  Generation │◄────│  Ranking  │   │
│   │           │     │  (Agentic)  │     │             │     │           │   │
│   └───────────┘     └─────────────┘     └─────────────┘     └───────────┘   │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Stage 1: Error Detection

Source: Automation harness, CI pipeline, test logs

Capture:
- Error signature (stack trace, error code, test name)
- Context (DUT info, environment, parameters, timing)
- Logs (filtered/relevant sections)

Output: `Error` node in graph with embeddings

### Stage 2: Error Identification / Deduplication

Query graph for similar errors:
- Vector similarity on error signature
- Graph traversal for same root cause patterns
- Temporal clustering (errors that co-occur)

Decision tree:
```
Is this error similar to existing error?
  ├─ Yes, same root cause known → Link to existing RootCause
  ├─ Yes, similar but different → Create new Error, link as SIMILAR_TO
  └─ No match → Create new Error, flag for RCA
```

### Stage 3: Jira Create/Link

If new root cause:
- Create Jira ticket with:
  - Error signature
  - Affected tests
  - Frequency/impact metrics
  - Link to graph node

If existing root cause:
- Link error to existing Jira
- Update impact metrics
- Add new context if novel

### Stage 4: Hypothesis Generation

For unresolved root causes, generate hypotheses from:
- **Domain 1**: Similar past errors and their resolutions
- **Domain 2**: Known patterns, errata, spec violations

Output: Ranked list of `Hypothesis` nodes with:
- Statement: "Error caused by X"
- Basis: Evidence from graph
- Testable prediction: "If true, then Y"
- Confidence: Based on evidence strength

### Stage 5: Root Cause Testing (Agentic)

**Key insight**: Headless Claude Code can test hypotheses autonomously.

For each hypothesis:
1. Generate candidate fix based on hypothesis
2. Apply fix in isolated environment
3. Run relevant test suite
4. Evaluate:
   - Test passes → Hypothesis supported
   - Test fails same way → Hypothesis refuted
   - Test fails differently → New information, update hypothesis

Constraints for agentic testing:
- Sandboxed environment (no production impact)
- Bounded scope (specific tests, not full suite)
- Domain 2 as guardrails (known patterns, spec compliance)
- Fallback: Flag for human review if uncertain

### Stage 6: PR Generation & Verification

On successful root cause discovery:
1. Generate PR with fix
2. Include in PR description:
   - Root cause explanation
   - Evidence trail (link to graph)
   - Tests that verify fix
   - Related Jiras resolved
3. Run full verification suite
4. Human review for merge (initially)

Over time, with sufficient confidence:
- Auto-merge for low-risk fixes
- Human review for high-risk changes

---

## Backfill: The Day-One Value Proposition

**Critical**: CLR must be usable immediately from historical data, not just future events.

### Backfill Sources

| Source | What It Contains | Import Strategy |
|--------|-----------------|-----------------|
| **Git history** | Commits, file changes, commit messages | Parse commits for fix patterns, link to issues |
| **PR history** (Bitbucket/GitHub API) | Reviews, comments, approvals, linked issues | Extract decisions, corrections, RCA context |
| **Test automation logs** | Pass/fail history, error signatures, timing | Build error signature corpus, temporal patterns |
| **Jira history** | Issue lifecycle, comments, resolutions, duplicates | Extract root causes, build duplicate clusters |
| **MS Teams threads** | Discussions, decisions, troubleshooting | LLM extraction of decisions/corrections |
| **Outlook emails** | RCA discussions, escalations, resolutions | LLM extraction (with permission model) |

### Why Copilot Has This and We Don't

Microsoft Copilot "Work" mode accesses:
- SharePoint, OneDrive, Teams, Outlook, Calendar
- Via Microsoft Graph API with user's OAuth token

**We can do the same** with appropriate OAuth flows:
- Microsoft Graph API for Teams/Outlook
- Bitbucket/GitHub APIs for PR history
- Jira API for issue history
- Direct log file access for automation

The difference: Copilot is read-only retrieval. CLR **learns** from this data and builds a reasoning graph.

### Backfill Pipeline

```python
def backfill_from_source(source_type, source_config):
    """
    Import historical data and extract graph nodes.
    """
    if source_type == "git":
        for commit in git_log(source_config.repo):
            # Extract fix patterns from commit messages
            if looks_like_fix(commit.message):
                fix = extract_fix_info(commit)
                linked_issues = extract_issue_refs(commit.message)
                create_fix_node(fix, linked_issues)

    elif source_type == "jira":
        for issue in jira_api.search(source_config.project):
            # Build issue graph with duplicates, root causes
            create_issue_node(issue)
            for linked in issue.links:
                create_relationship(issue, linked)
            # Extract RCA from comments
            for comment in issue.comments:
                if looks_like_rca(comment):
                    create_rca_session(issue, comment)

    elif source_type == "teams":
        for thread in teams_api.get_threads(source_config.channel):
            # LLM extraction of decisions/corrections
            extractions = llm_extract_decisions(thread.messages)
            for ext in extractions:
                create_node(ext.type, ext.content, source="teams")

    # ... similar for other sources
```

---

## Graph Schema for CLR

Extends ccmemory's core schema:

### Domain 1 (Your Specifics)

```cypher
// Test infrastructure
(:AutomationRun {
    id: string,
    started_at: datetime,
    ended_at: datetime,
    environment: string,
    parameters: map,
    status: "passed" | "failed" | "error"
})

(:Error {
    id: string,
    signature: string,        // Normalized error fingerprint
    raw_message: string,
    stack_trace: string,
    test_name: string,
    first_seen: datetime,
    last_seen: datetime,
    occurrence_count: int,
    embedding: vector         // For similarity search
})

(:RootCause {
    id: string,
    description: string,
    category: string,         // "code_bug" | "test_flaw" | "environment" | "infra" | "external"
    confirmed: boolean,
    confirmed_at: datetime,
    confirmed_by: string
})

(:Hypothesis {
    id: string,
    statement: string,
    basis: [string],          // Evidence node IDs
    testable_prediction: string,
    status: "proposed" | "testing" | "supported" | "refuted",
    confidence: float,
    tested_at: datetime
})

(:Fix {
    id: string,
    description: string,
    pr_url: string,
    commit_hash: string,
    automated: boolean,       // Was this generated by CLR?
    verified: boolean
})

// ccmemory core types still apply
(:Decision), (:Correction), (:Exception), (:FailedApproach), (:Insight)
```

### Domain 2 (Reference Knowledge)

```cypher
(:ErrorPattern {
    id: string,
    name: string,
    description: string,
    signature_regex: string,
    typical_root_cause: string,
    typical_fix: string
})

(:KnownIssue {
    id: string,
    description: string,
    affected_components: [string],
    workaround: string,
    permanent_fix: string
})

(:SpecSection {
    id: string,
    spec_name: string,
    section: string,
    content: string,
    embedding: vector
})
```

### Relationships

```cypher
// Error lifecycle
(Error)-[:DURING]->(AutomationRun)
(Error)-[:SIMILAR_TO {confidence: float}]->(Error)
(Error)-[:CAUSED_BY]->(RootCause)
(RootCause)-[:TRACKED_BY]->(JiraIssue)

// Resolution flow
(Hypothesis)-[:FOR]->(RootCause)
(Hypothesis)-[:BASED_ON]->(Error | Decision | Insight)
(Hypothesis)-[:TESTED_BY]->(AutomationRun)
(Fix)-[:RESOLVES]->(RootCause)
(Fix)-[:VERIFIED_BY]->(AutomationRun)

// Domain 2 bridges
(Error)-[:MATCHES_PATTERN]->(ErrorPattern)
(Error)-[:VIOLATES]->(SpecSection)
(RootCause)-[:INSTANCE_OF]->(KnownIssue)
```

---

## Agentic Layer: Headless Claude Code

### Why Claude Code for Root Cause Testing

Claude Code excels at:
- Reading code and understanding context
- Generating targeted fixes
- Running tests and interpreting results
- Iterating based on feedback

### Integration Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     CLR Orchestrator                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Select hypothesis to test                                   │
│  2. Prepare context:                                            │
│     - Error details from graph                                  │
│     - Relevant code files                                       │
│     - Domain 2 constraints (patterns, spec)                     │
│     - Similar past fixes                                        │
│  3. Spawn headless Claude Code session                          │
│  4. Provide prompt:                                             │
│                                                                 │
│     "Hypothesis: {statement}                                    │
│      Error: {signature}                                         │
│      Test: {test_name}                                          │
│                                                                 │
│      Constraints:                                               │
│      - Fix must make test pass                                  │
│      - If test logic is flawed, document why                    │
│      - Reference patterns: {domain_2_patterns}                  │
│                                                                 │
│      Task: Generate minimal fix and verify with test run"       │
│                                                                 │
│  5. Collect results:                                            │
│     - Fix generated (if any)                                    │
│     - Test outcome                                              │
│     - Reasoning trace                                           │
│  6. Update graph with results                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Safety Constraints

- **Sandboxed execution**: Isolated environment, no production access
- **Bounded scope**: Only touch files related to the error
- **Human checkpoints**: Flag for review if confidence < threshold
- **Audit trail**: Full reasoning trace stored in graph
- **Rollback capability**: All changes reversible

---

## Team Deployment

Per ccmemory vision, CLR supports team workflows:

### Node Status for Knowledge Curation

```cypher
(:RootCause {
    ...
    status: "developmental" | "curated",
    curated_by: string,
    curated_at: datetime
})
```

- `developmental`: Auto-detected or proposed, not yet reviewed
- `curated`: Human-verified, promoted to team knowledge

### Workflow

1. CLR detects error, creates `developmental` nodes
2. Engineers investigate, add context, corrections
3. On resolution, promote to `curated`
4. Curated knowledge informs future detection/dedup

### Permissions (Future)

For cross-team deployments:
- Read access to all curated knowledge
- Write access scoped to team's errors
- Admin for promoting to org-wide curated

---

## Success Metrics

### Primary: Time to Resolution

Measure: Time from error detection to verified fix

Target: 50% reduction in median TTR within 6 months

### Secondary: Duplicate Reduction

Measure: Jira tickets closed as duplicate / total new tickets

Target: Reduce duplicate rate by 70%

### Tertiary: Hypothesis Accuracy

Measure: Hypotheses supported / hypotheses tested

Target: >40% accuracy (random would be ~10%)

### Agentic: Autonomous Fix Rate

Measure: Fixes generated and verified without human intervention

Target: 20% of simple bugs fixed autonomously by month 6

---

## Implementation Phases

### Phase 1: Graph Foundation

- [ ] Extend ccmemory schema for CLR node types
- [ ] Build error signature extraction and embedding
- [ ] Implement similarity search for deduplication
- [ ] Basic automation log import

### Phase 2: Backfill Pipeline

- [ ] Git history importer
- [ ] PR history importer (Bitbucket/GitHub API)
- [ ] Jira history importer
- [ ] Test automation log importer
- [ ] LLM extraction for decisions/corrections from history

### Phase 3: Hypothesis Engine

- [ ] Hypothesis generation from error patterns
- [ ] Ranking based on evidence strength
- [ ] Domain 2 pattern matching
- [ ] Manual hypothesis entry and tracking

### Phase 4: Agentic Testing

- [ ] Headless Claude Code integration
- [ ] Sandboxed test execution environment
- [ ] Result capture and graph update
- [ ] Human review workflow for generated fixes

### Phase 5: Closed Loop

- [ ] Auto Jira creation/linking
- [ ] PR generation from verified fixes
- [ ] Confidence-based auto-merge (low risk)
- [ ] Feedback loop: merge outcomes update hypothesis confidence

### Phase 6: Enterprise Backfill

- [ ] MS Teams integration (Microsoft Graph API)
- [ ] Outlook integration (with permission model)
- [ ] Cross-source entity resolution
- [ ] Historical pattern mining

---

## Open Questions

1. **Sandboxing strategy**: Docker? VM? Cloud ephemeral? Trade-offs between isolation and speed.

2. **Confidence thresholds**: What confidence level justifies auto-merge? Probably domain-specific.

3. **Test flakiness**: How to distinguish real failures from flaky tests? May need flakiness scoring.

4. **Partial fixes**: What if a fix resolves some but not all related errors? Graph needs to track partial resolution.

5. **Adversarial cases**: Can the system be gamed? (e.g., tests that pass but don't actually verify the fix)

---

## References

- [PROJECT_VISION.md](../PROJECT_VISION.md) — Core ccmemory vision
- [WHY_GRAPH.md](WHY_GRAPH.md) — Why graphs over search
- [Microsoft Graph API](https://docs.microsoft.com/en-us/graph/) — Teams/Outlook access
- [Claude Code Headless Mode](https://docs.anthropic.com/claude-code) — Agentic execution
