# Closed-Loop Resolution (CLR) for Test Automation

Automated bug detection, triage, RCA, and fix verification for CI and hardware validation infrastructure.

## Scope

**In scope (MVP):** Automated test failures from CI / hardware validation
**Deferred:** Manual debugging with Claude Code / other agents

### Why Automated Tests First

| Automated | Manual |
|-----------|--------|
| Structured output (test name, assertion, stack trace, exit code) | Vague symptoms ("feels slow") |
| High signal — failure = real bug | Requires triage |
| Repeatable — re-run verifies fix | Human verifies |
| Already captured in CI logs | New capture mechanism needed |

## MVP Requirements

### 1. Triage

- **Trigger on every failure** from scaled test automation platform
- **Search Jira for existing issues** — match new failure against open bugs
- **Cluster & deduplicate** related failures (same root cause, different symptoms)
- **Identify failure level:**
  - Test code itself
  - Internal test support Python wheel
  - Platform/OS
  - DUT firmware
- **All unique bugs need a Jira issue** — create if no match found

### 2. RCA

- Generate ranked hypotheses for each failure
- Query graph for matching symptoms / code areas / known root causes
- Skip known-bad approaches from prior `FailedFix` nodes

### 3. Test Fix Hypotheses

- Execute fixes via **new MCP test harness** (to be built)
- Re-run tests to verify
- Record hypothesis status (confirmed/disproved) with evidence

### 4. Integration

- Update Jira issue with findings (link to graph, hypotheses tried, evidence)
- Raise PRs for passing fixes — **always human review** (no auto-merge)

## CLR Flow

```
Test Fails (scaled test automation platform)
    ↓
Extract symptom (test name, assertion, stack trace, exit code, env)
    ↓
Search Jira for existing issues (JQL + LLM rerank)
    ↓
If match → link failure to existing issue
If no match → create new Jira issue
    ↓
Triage: cluster with related failures, identify failure level
    ↓
Query graph for matches (symptom, code area, known root causes)
    ↓
Generate ranked hypotheses (not fixes yet)
    ↓
For each hypothesis (priority order):
    ├─ Record Hypothesis node with reasoning
    ├─ Generate Fix based on hypothesis
    ├─ Apply fix, re-run test via MCP harness
    ├─ If pass → mark Hypothesis CONFIRMED, record Fix
    └─ If fail → mark Hypothesis DISPROVED with evidence, continue
    ↓
All hypotheses exhausted? → escalate, record as Unresolved
    ↓
Update Jira with findings, raise PR for confirmed fix (human review)
```

## Why Hypotheses Matter

When a test fails, the agent reasons through possibilities:

1. "Could be X because of evidence A"
2. "Or Y because of evidence B"
3. Tries X → fails → now knows X was wrong *for this symptom pattern*
4. Tries Y → works → now knows Y was right

Recording only the final fix loses:
- Why X seemed plausible (might help for different symptom)
- Why X failed (avoid repeating for similar symptoms)
- The reasoning that led to Y (replicate for similar bugs)

## Graph Structure

### Node Types

```
TestFailure    — Captured failure from CI/hardware validation
FailureCluster — Group of related TestFailures (same root cause)
Hypothesis     — "I think X causes this because Y"
Fix            — Attempted solution (passed or failed)
RootCause      — Confirmed underlying cause
FailureLevel   — Where the bug lives (test/wheel/platform/firmware)
CodeArea       — File/module/function where bugs cluster
```

### Relationships

```
TestFailure -[:CLUSTERED_IN]-> FailureCluster
TestFailure -[:AT_LEVEL]-> FailureLevel
TestFailure -[:HAS_HYPOTHESIS]-> Hypothesis
Hypothesis -[:PRODUCED]-> Fix
Hypothesis -[:INFORMED_BY]-> Hypothesis  (prior disproved → led to this)
Fix -[:RESOLVES]-> TestFailure
Fix -[:VALIDATES]-> Hypothesis
Fix -[:CONFIRMS]-> RootCause
RootCause -[:AFFECTS]-> CodeArea
FailureCluster -[:SHARES_ROOT_CAUSE]-> RootCause
```

### Example

```
TestFailure (test_auth_login_empty_email)
  ├─ AT_LEVEL → FailureLevel (test-support-wheel)
  ├─ CLUSTERED_IN → FailureCluster (auth-validation-nulls)
  │
  ├─ HAS_HYPOTHESIS → Hypothesis (priority: 1)
  │     ├─ reasoning: "Stack shows null in validate_email, likely missing null check"
  │     ├─ confidence: 0.8
  │     ├─ PRODUCED → Fix (attempt 1)
  │     │     └─ result: failed
  │     │     └─ evidence: "Same assertion, different line"
  │     └─ status: disproved
  │
  ├─ HAS_HYPOTHESIS → Hypothesis (priority: 2)
  │     ├─ reasoning: "Empty string passes null check but fails downstream regex"
  │     ├─ confidence: 0.6
  │     ├─ INFORMED_BY → Hypothesis (priority: 1)
  │     ├─ PRODUCED → Fix (attempt 2)
  │     │     └─ result: passed
  │     │     └─ commit: <sha>
  │     └─ status: confirmed
  │
  └─ RESOLVED_BY → Fix (attempt 2)
        └─ VALIDATES → Hypothesis (priority: 2)
        └─ CONFIRMS → RootCause (empty-string-vs-null)
```

### Node Properties

```
TestFailure
  testName: string
  assertion: string
  stackFingerprint: hash (normalized, line-numbers stripped)
  commit: sha
  branch: ref
  env: ci-runner-id | hardware-rig-id
  timestamp: datetime

Hypothesis
  reasoning: text
  confidence: float (0-1)
  priority: int (order tried)
  status: pending | confirmed | disproved
  evidence: text (why confirmed/disproved)

Fix
  diff: patch
  result: passed | failed
  commit: sha (if merged)
  prUrl: url (if raised)

RootCause
  description: text
  codeArea: path

FailureLevel
  level: enum (test-code | test-support-wheel | platform-os | dut-firmware)
```

## What This Enables

**Learning from failures:**
- "What hypotheses disproved for null-related errors in auth/?" → "Empty string vs null is common miss"

**Improving reasoning:**
- "Confirmation rate for high-confidence hypotheses?" → calibration feedback

**Pattern recognition:**
- "When hypothesis A fails, what usually works?" → "Regex issues follow null checks 70% of time in this area"

**Triage acceleration:**
- "New failure in auth/ at test-support-wheel level" → auto-cluster with similar failures

## Symptom Matching

### Approaches (Hybrid)

1. **Structured extraction at capture** — `errorType`, `codeArea`, `failureLevel` as indexed properties
2. **Stack fingerprinting** — Normalized hash (strip line numbers, paths) for exact-match fast path
3. **Embedding on description** — Semantic similarity for behavioral symptoms
4. **Reranker** — LLM filters false positives from top-N candidates

### Design Decision

**Capture raw, extract automatically, allow correction.**

- Raw symptom stored immediately (zero friction)
- Background job extracts structured facets (best effort)
- Dashboard shows extractions with edit option (human refinement when needed)

Rationale:
- Capture friction kills adoption
- Extraction improves over time; raw data doesn't degrade
- 80% case (stack traces) extracts well; 20% (vague descriptions) may need human help

## Jira Integration

### The Problem

Jira's native API uses JQL (keyword-based), not semantic search. Finding "similar" issues requires custom work.

### Approaches in the Wild

1. **Marketplace apps** — [Find Duplicates](https://marketplace.atlassian.com/apps/1212706/find-duplicates-detect-similar-issues-find-related-issues), [Duplicate AI](https://marketplace.atlassian.com/apps/1224971/duplicate-ai-find-merge-duplicate-issues) use ML for similarity scoring
2. **Custom NLP** — [JIRA-Similar-Issue-Finder-App](https://github.com/bhavul/JIRA-Similar-Issue-Finder-App) trains ML model, comments related IDs
3. **Vector databases** — Milvus, Pinecone for semantic search + duplicate detection
4. **Research** — [GitBugs dataset](https://arxiv.org/html/2504.09651) (150k+ bug reports), [recent work](https://arxiv.org/abs/2504.14797) on automated duplicate detection

### CLR Approach

**JQL broad search + LLM rerank:**

1. Query Jira via `/rest/api/3/search/jql` with loose JQL (project, component, date range, status)
2. Fetch bulk JSON results (summary, description, labels, components)
3. Pass candidates + new failure symptom to LLM for similarity scoring
4. Threshold determines match vs new issue

This avoids Jira plugin dependencies and uses our own LLM for consistency with rest of CLR.

### Jira API Notes

- Legacy `/rest/api/3/search` deprecated → use `/rest/api/3/search/jql`
- Pagination via `nextPageToken` (not `startAt`)
- POST for large JQL queries (JSON body)
- Requires API token auth

## Integration Points

- **Scaled test automation platform** → receives failure, triggers CLR
- **MCP test harness** → execute fixes, re-run tests (new, to be built)
- **Git** → apply fix, push branch
- **Jira API** → search existing issues, create/update issues
- **PR API** → raise PRs for confirmed fixes (human review required)
- **Graph (Neo4j)** → store all nodes/relationships

## Open Questions

1. **Hardware validation specifics** — What does "test failure" look like? Serial logs? Exit codes?
2. **Flaky tests** — Require N consecutive failures before triggering CLR?
3. **Jira field mapping** — Which fields to search/populate? Labels, components, custom fields?
4. **MCP harness scope** — What test frameworks/runners to support initially?
