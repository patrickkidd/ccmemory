# When a Graph Doesn't Help

A graph adds overhead. When does it not pay off?

## Anti-Patterns

### 1. Low-Volume, High-Turnover Bugs

If bugs are:
- Fixed quickly (hours, not days)
- Rarely recur
- Don't share root causes

No relationship structure to exploit. A flat Jira list works fine. Graph value comes from traversing connections — no connections, no value.

**Example:** Typos, obvious null checks, config mistakes. Fix once, never see again.

### 2. Isolated, Unrelated Failures

If each bug is truly independent:
- Different code areas
- Different root causes
- No clustering pattern

Then `SHARES_ROOT_CAUSE`, `CLUSTERS_IN`, `INFORMED_BY` edges never form. Just storing nodes with no edges — a worse database.

**Example:** Random integration failures across unrelated services with no common dependency.

### 3. Deterministic, Single-Cause Failures

If the failure → cause → fix chain is 1:1:1 with no ambiguity:
- One symptom maps to one cause
- One cause has one fix
- No hypothesis exploration needed

Hypothesis tracking overhead is wasted. Just log "test X failed, applied fix Y, done."

**Example:** Version mismatch errors. Fix is always "update version." No reasoning chain to capture.

### 4. High Noise-to-Signal Ratio

If most failures are:
- Flaky tests (environment, timing)
- Infrastructure issues (network, disk)
- Not real bugs

Graph fills with noise. Every flaky test creates nodes that pollute similarity searches. More time filtering garbage than finding patterns.

**Example:** Test suite with 30% flake rate. Graph becomes a flaky test cemetery.

### 5. Short-Lived Codebases

If the code:
- Changes radically every few months
- Historical patterns don't predict future bugs
- "What worked before" is irrelevant

Graph's historical knowledge decays faster than it accumulates. By the time you have useful patterns, the code has moved on.

**Example:** Rapid prototyping, throwaway projects, major rewrites.

## When the Graph Adds Value

The inverse:

| Graph Helps | Graph Doesn't Help |
|-------------|-------------------|
| Recurring bugs | Fix-once bugs |
| Shared root causes | Isolated failures |
| Multi-hypothesis RCA | Obvious single cause |
| Stable codebase | Rapid churn |
| Low flake rate | High noise |
| Long-lived projects | Throwaway code |

## Implication for MVP

**Filter what enters the graph.** Not every `TestFailure` deserves a node.

Criteria for graph-worthy failures:
- Passed flake detection (N consecutive failures, or deterministic repro)
- Not infrastructure/environment (or tagged as such, kept separate)
- In stable code areas (not actively being rewritten)

Options:
1. Add `graphWorthy: boolean` property during triage
2. Defer graph insertion until failure proves interesting (recurs, shares cause, etc.)
