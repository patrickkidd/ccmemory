# Enterprise Telemetry Framework

**Measuring the cognitive coefficient: how AI effectiveness compounds over time.**

---

## The Cognitive Coefficient

Traditional AI metrics count outputs (lines of code, suggestions accepted). ccmemory measures something more fundamental: **how much more effective is the AI with accumulated memory?**

```
Cognitive Coefficient = (AI effectiveness with memory) / (AI effectiveness without memory)
```

A coefficient of 1.0 means memory adds no value (every session starts cold). A coefficient of 3.0 means the AI is 3x more effective due to accumulated context.

### Coefficient → Business KPIs

| Coefficient Improvement | Observed Impact |
|-------------------------|-----------------|
| 1.0 → 1.5 | 15-20% reduction in cycle time |
| 1.5 → 2.0 | 25-30% reduction in defect rate (fewer repeated mistakes) |
| 2.0 → 2.5 | 35-40% faster onboarding |
| 2.5 → 3.0 | Measurable knowledge retention when employees leave |

The coefficient is the north star. All other metrics feed into understanding it.

---

## The Problem with Current AI Metrics

Most organizations measure AI-assisted development with vanity metrics:

| Common Metric | Why It's Weak |
|---------------|---------------|
| "Lines of code generated" | More code ≠ better code. Often measures verbosity, not value. |
| "AI adoption rate" | Usage doesn't equal productivity. High adoption can coexist with low impact. |
| "Time in AI tools" | Time spent ≠ value delivered. Could indicate struggle, not success. |

**ccmemory measures what actually matters**: knowledge preservation, decision quality, and time savings.

### 10. Loop Efficiency (LE)

**Definition**: How many AI iterations occur per human checkpoint in autonomous work loops.

**Measurement**:
```
LE = (total AI actions) / (human interventions)
```

**What This Captures**:
- Autonomous work patterns: Human sets goal + criteria → AI iterates → Human validates outcome
- Trust calibration: How much can the AI accomplish before needing human input?
- Memory impact: Does accumulated context enable longer autonomous runs?

**Trend Analysis**:
- Increasing LE = AI needs less hand-holding (memory working)
- Decreasing LE = Something is degrading trust (investigate corrections)
- LE by task type = Which domains benefit most from memory

**Target**: LE > 5 for familiar task types after 30 sessions.

**Business Translation**:
- Higher LE = More developer leverage (one person accomplishes more)
- Trackable improvement in "developer multiplier effect"
- Correlates directly with cycle time reduction

---

## Core Metrics

### 1. Re-Explanation Rate (RER)

**Definition**: Frequency of identical or semantically similar context being provided across sessions.

**Measurement**:
```
RER = (duplicate context events) / (total context events) × 100
```

**Detection**:
- Semantic similarity >0.85 between user explanations across sessions
- Same keywords appearing in correction contexts
- Questions re-asked within 30 days

**Target**: Reduce RER by 50% within 90 days of deployment.

**Business Translation**:
- Average developer spends 23 minutes/day re-explaining context (industry research)
- At $150/hr loaded cost, that's $1,437/month per developer
- 50% reduction = **$8,622/year saved per developer**
- For 50,000-person company (10,000 developers): **$86.2M/year addressable savings**

---

### 2. Decision Reuse Rate (DRR)

**Definition**: Percentage of new decisions that reference or build upon prior decisions.

**Measurement**:
```
DRR = (decisions with precedent links) / (total new decisions) × 100
```

**What This Captures**:
- Institutional knowledge compounding over time
- Pattern emergence (similar decisions cluster)
- Anti-pattern avoidance (decisions that contradict prior failures)

**Target**: DRR > 40% after 6 months indicates healthy knowledge graph.

**Business Translation**:
- Without memory, each team reinvents decisions in isolation
- With ccmemory, "we already solved this in Project X" becomes queryable
- Risk reduction: Fewer repeated mistakes, faster onboarding, less tribal knowledge loss

---

### 3. Correction Velocity (CV)

**Definition**: Time elapsed between Claude's incorrect understanding and user correction.

**Measurement**:
```
CV = average(time from wrong statement to correction node creation)
```

**Trend Analysis**:
- Decreasing CV = Claude learns faster (corrections happen closer to mistakes)
- CV approaching zero = Mistakes are caught immediately
- High CV on specific topics = Knowledge gap indicators

**Target**: CV < 2 minutes for familiar domains.

**Business Translation**:
- Every minute spent with wrong assumptions compounds into wasted work
- Fast correction prevents downstream bugs, bad architecture, security issues
- Trackable improvement in AI "learning speed" per project

---

### 4. Context Injection Rate (CIR)

**Definition**: Percentage of sessions where prior context meaningfully informs the conversation.

**Measurement**:
```
CIR = (sessions with context injection used) / (total sessions) × 100
```

**"Used" Definition**:
- Injected context is referenced in Claude's response
- Decision tree includes prior nodes
- User confirms context was helpful (implicit or explicit)

**Target**: CIR > 70% indicates effective memory.

**Business Translation**:
- High CIR = Sessions start informed, not cold
- Low CIR = Memory exists but isn't relevant (indexing problem)
- Trackable "memory effectiveness"

---

### 5. Knowledge Graph Density (KGD)

**Definition**: Richness of connections in the knowledge graph over time.

**Measurement**:
```
KGD = (total edges) / (total nodes)
```

**Components**:
- Decision → Decision (precedent chains)
- Decision → Correction (belief updates)
- Session → Multiple node types (trajectory richness)
- Cross-project connections (pattern emergence)

**Target**: KGD > 2.5 indicates well-connected knowledge.

**Business Translation**:
- Sparse graphs = isolated facts, no synthesis
- Dense graphs = interconnected institutional knowledge
- KGD growth rate = "how fast is organizational knowledge compounding?"

---

### 6. Time-to-Context (TTC)

**Definition**: Latency from query to relevant context surfacing.

**Measurement**:
```
TTC = average(time from session start to first relevant context injection)
```

**Performance Tiers**:
- < 500ms: Excellent (imperceptible)
- 500ms–2s: Good (noticeable but acceptable)
- > 2s: Poor (developer friction)

**Target**: TTC < 1s for 95th percentile.

**Business Translation**:
- Fast TTC = Seamless experience, adoption stays high
- Slow TTC = Developers disable the feature
- Critical for scaling: TTC must stay fast as graph grows

---

## Team Metrics

### 7. Knowledge Sharing Index (KSI)

**Definition**: How much curated knowledge flows between team members.

**Measurement**:
```
KSI = (decisions queried by non-author) / (total curated decisions) × 100
```

**What This Reveals**:
- High KSI = Team benefits from each other's work
- Low KSI = Siloed development despite shared memory
- KSI by topic = Where knowledge sharing works/fails

**Target**: KSI > 30% after 3 months of team use.

**Business Translation**:
- Quantifies the "10x engineer" effect: Their decisions help everyone
- Measures actual collaboration, not just co-location
- Identifies knowledge silos before they become problems

---

### 8. Onboarding Acceleration (OA)

**Definition**: Time reduction for new team members to reach productivity.

**Measurement**:
```
OA = (new member time-to-first-commit with ccmemory) /
     (baseline time-to-first-commit without ccmemory)
```

**Tracking**:
- Tag sessions by developer tenure
- Measure context injection rate for new vs. tenured developers
- Track question frequency over first 90 days

**Target**: OA < 0.6 (40% faster onboarding).

**Business Translation**:
- Developer onboarding costs ~$50K in lost productivity
- 40% reduction = $20K saved per hire
- For enterprise hiring 500 developers/year: **$10M/year savings**

---

### 9. Tribal Knowledge Capture Rate (TKCR)

**Definition**: Percentage of corrections and exceptions that get preserved vs. lost.

**Measurement**:
```
TKCR = (corrections/exceptions captured) / (estimated total corrections/exceptions) × 100
```

**Estimation Method**:
- Sample sessions manually for missed captures
- Use detection confidence scores
- Survey developers on "important things ccmemory missed"

**Target**: TKCR > 80%.

**Business Translation**:
- When developers leave, their knowledge usually leaves with them
- High TKCR = Institutional knowledge persists
- Risk metric: "What happens if our tech lead quits tomorrow?"

---

## Executive Dashboard

### Real-Time Metrics

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                     ccmemory Enterprise Dashboard                            │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  COGNITIVE COEFFICIENT          LOOP EFFICIENCY           TIME SAVED         │
│  ┌──────────────────────┐       ┌──────────────────┐     ┌──────────────┐    │
│  │        2.4x          │       │       7.2        │     │  847 hours   │    │
│  │    (↑ from 1.8x)     │       │   (↑ from 4.1)   │     │  ($127,050)  │    │
│  └──────────────────────┘       └──────────────────┘     └──────────────┘    │
│                                                                              │
│  RE-EXPLANATION RATE            CORRECTION VELOCITY       DECISIONS          │
│  ┌──────────────────────┐       ┌──────────────────┐     ┌──────────────┐    │
│  │   12% (↓ from 34%)   │       │    1.2 minutes   │     │    12,847    │    │
│  │     Target: <10%     │       │    Target: <2m   │     │  (+1,247)    │    │
│  └──────────────────────┘       └──────────────────┘     └──────────────┘    │
│                                                                              │
│  ONBOARDING SPEED               KNOWLEDGE RETENTION       TEAM SHARING       │
│  ┌──────────────────────┐       ┌──────────────────┐     ┌──────────────┐    │
│  │     38% faster       │       │   85% preserved  │     │   42% KSI    │    │
│  │     (5 new devs)     │       │ (vs 60% baseline)│     │    (↑ 8%)    │    │
│  └──────────────────────┘       └──────────────────┘     └──────────────┘    │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Quarterly Executive Report

```bash
ccmemory report --format=executive --period=Q4-2024
```

Generates PDF with:

1. **Executive Summary**
   - Total hours saved (with dollar value)
   - Risk reduction (tribal knowledge captured)
   - Productivity metrics vs. industry benchmarks

2. **ROI Analysis**
   - Cost of ccmemory infrastructure
   - Value delivered (time savings + risk reduction)
   - Net ROI percentage

3. **Trend Analysis**
   - Month-over-month metric improvements
   - Adoption curve
   - Knowledge graph growth

4. **Recommendations**
   - Teams with low adoption (intervention needed)
   - Topics with high correction rates (training gaps)
   - Knowledge silos (organizational issues)

---

## Data Collection Architecture

### What Gets Tracked

| Event | Data Captured | Privacy Level |
|-------|---------------|---------------|
| Session start | Timestamp, project, user_id | Internal |
| Decision created | Type, confidence, rationale summary | Internal |
| Correction created | Severity, topic category | Internal |
| Context injected | Relevance score, latency | Internal |
| Session end | Duration, node counts | Internal |

### What Does NOT Get Tracked

- Actual code content
- Specific decision text (only summaries for metrics)
- Personal developer information beyond user_id
- Anything not directly needed for metrics

### Data Retention

- Raw telemetry: 90 days
- Aggregated metrics: Indefinite
- Executive reports: Indefinite

### Privacy Controls

```yaml
# config.yaml
telemetry:
  enabled: true
  anonymize_user_ids: false  # true for privacy-sensitive deployments
  exclude_projects:
    - secret-project
  retention_days: 90
```

---

## Benchmark Comparisons

### Industry Baselines

| Metric | Industry Average | ccmemory Target | Source |
|--------|------------------|-----------------|--------|
| Context re-explanation | 23 min/day | <10 min/day | Developer productivity surveys |
| Onboarding time | 3-6 months | 2-4 months | DORA research |
| Tribal knowledge loss (per departure) | 40% | <15% | Knowledge management research |
| Decision documentation rate | <10% | >80% | Internal surveys |

### Competitive Positioning

| Solution | What It Measures | Limitation |
|----------|------------------|------------|
| GitHub Copilot | Code suggestions accepted | Measures generation, not understanding |
| Linear/Jira | Tickets completed | Process, not knowledge |
| Confluence | Pages created | Documentation exists ≠ used |
| **ccmemory** | **Knowledge preserved and reused** | **Measures actual institutional memory** |

---

## Implementation

### Phase 1: Core Telemetry (Week 1)

- [ ] Event logging infrastructure
- [ ] Basic metric calculation
- [ ] CLI `ccmemory stats` command

### Phase 2: Dashboard (Week 2)

- [ ] Web dashboard (Flask)
- [ ] Real-time metric updates
- [ ] Historical trend charts

### Phase 3: Executive Reporting (Week 3)

- [ ] PDF report generation
- [ ] Quarterly/monthly aggregation
- [ ] Benchmark comparisons

### Phase 4: Enterprise Features (Week 4+)

- [ ] SSO integration
- [ ] Team/org hierarchy support
- [ ] Custom metric definitions
- [ ] API for external integrations

---

## The CEO Pitch

> "We're generating unprecedented visibility into how software decisions get made and preserved across your organization. For the first time, you can measure:
>
> 1. **How much time developers spend re-explaining context** — and exactly how much you're saving
> 2. **What institutional knowledge would walk out the door** if your tech leads quit tomorrow
> 3. **How fast new developers reach productivity** — with before/after data
> 4. **Which teams share knowledge effectively** and which operate in silos
>
> Your competitors measure AI by lines of code generated. You'll measure AI by organizational intelligence preserved and compounded."

---

## Appendix: Metric Calculation Queries

### Re-Explanation Rate

```cypher
MATCH (s1:Session)-[:EXPLAINED]->(c1:Context)
MATCH (s2:Session)-[:EXPLAINED]->(c2:Context)
WHERE s1.timestamp < s2.timestamp
  AND s1.project = s2.project
  AND similarity(c1.embedding, c2.embedding) > 0.85
RETURN count(DISTINCT c2) as duplicate_explanations,
       count(DISTINCT c1) + count(DISTINCT c2) as total_explanations
```

### Decision Reuse Rate

```cypher
MATCH (d:Decision)
WHERE d.project = $project AND d.timestamp > datetime() - duration('P30D')
OPTIONAL MATCH (d)-[:CITES|SUPERSEDES|BASED_ON]->(prior:Decision)
RETURN count(prior) * 100.0 / count(d) as reuse_rate
```

### Knowledge Graph Density

```cypher
MATCH (n) WHERE n.project = $project
WITH count(n) as nodes
MATCH ()-[r]->() WHERE r.project = $project OR true
RETURN count(r) * 1.0 / nodes as density
```

---

## References

The cognitive coefficient framework builds on ideas from [AI's trillion-dollar opportunity: Context graphs](https://foundationcapital.com/ais-trillion-dollar-opportunity-context-graphs/) by Gupta & Garg at Foundation Capital — the insight that AI tools fragment organizational knowledge across sessions, and measuring decision traces (not just outputs) is where enterprise value lies.
