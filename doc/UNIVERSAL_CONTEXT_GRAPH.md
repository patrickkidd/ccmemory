# Universal Context Graph: A Domain-Agnostic Research Partner

## Executive Summary

An evolution of the event graph concept into a **universal context management system** that works equally for software projects, career consulting, medical research, or any complex domain requiring accumulated understanding over time.

**The key insight**: The event graph pattern (decisions, corrections, exceptions, trajectories) is not specific to software. It's a general structure for capturing **how understanding evolves** in any domain. Combined with a reference knowledge layer and active research capabilities, it becomes a co-thinking partner rather than a storage system.

**What this enables**:
- Software: "Why did we build it this way?" → Decision trace
- Career: "What constraints affect this decision?" → Cross-project context
- Medical: "What have I tried for this symptom?" → Personal precedent + literature
- Any domain: "What don't we know yet?" → Knowledge gaps → Active research

---

## The Problem: We Only Have Half of Time

### The Two Clocks Problem

Every system has two clocks (Koratana, 2024):
- **State clock**: What's true right now
- **Event clock**: What happened, in what order, with what reasoning

We've built trillion-dollar infrastructure for state. The event clock barely exists.

| What State Clock Captures | What Event Clock Should Capture |
|---------------------------|--------------------------------|
| `timeout=30s` | "Tripled from 5s after cascading failures, based on auth-service precedent" |
| Component depends on service | The trajectory of discovering, debugging, and resolving that dependency |
| Decision: "Use F1 scoring" | Options considered, constraints evaluated, who approved, what precedent it sets |
| `CLAUDE.md` says "always use X" | Why that rule exists, what exception led to it, when it should be revisited |
| "I sleep poorly" | What interventions were tried, what worked, what was learned, what to try next |

### Why This Matters

Current solutions capture state: "here's how things are." They don't capture (Gupta & Garg, 2024):

1. **Exception logic**: "We always do X because of Y incident" — tribal knowledge that dies
2. **Precedent chains**: "We structured this like the auth refactor" — no link exists
3. **Cross-system synthesis**: You check three sources and remember a conversation — reasoning never captured
4. **The 'why' behind the 'what'**: Every fact has a history; that history is usually lost

### Trajectories as the Event Clock

When an agent works through a problem, it traverses the domain. It reads sources, makes decisions, asks questions, receives corrections. This trajectory is an **informed walk** through the problem space (Koratana, 2024).

> "You don't need to understand a system to represent it. Traverse it enough times and the representation emerges."

The trajectory IS the data. Accumulate enough walks and organizational structure emerges. Schema is output, not input.

### From Knowledge Base to World Model

The goal isn't retrieval. It's **simulation** (Ha & Schmidhuber, 2018).

A context graph with enough accumulated trajectories becomes a **world model**:
- "What happens if I change this?" → Based on past trajectories, here's the blast radius
- "Will this approach work?" → Similar decisions succeeded/failed in these contexts
- "What's the risk?" → Exception patterns suggest where problems emerge

> "Simulation is the test of understanding. If your context graph can't answer 'what if,' it's just a search index."

---

## Conceptual Foundation: Iterative Empiricism

This system applies **scientific method principles** to personal knowledge management — accumulate observations, propose explanations, test predictions, update beliefs.

The core loop:
1. **Organize current knowledge** into normalized, single-sources-of-truth optimized for efficient random access
2. **Identify gaps** — what don't we understand yet?
3. **Generate hypotheses** — proposed explanations based on observations + reference knowledge
4. **Test** — gather data, make predictions, observe outcomes
5. **Update beliefs** — incorporate lessons learned, refute or support hypotheses
6. **Repeat**

This borrows from Agile methodology:
- Normalized knowledge base (like a well-groomed backlog)
- Short iteration cycles
- Retrospective incorporation

But adds scientific method's:
- Hypothesis generation from observation (not predefined user stories)
- Explicit falsifiability — a refuted hypothesis is valuable data
- Confidence levels and source tracking
- Distinction between observation (data) and interpretation (theory)

The goal isn't delivering increments against a known target. It's **building understanding** of complex domains where you don't know what questions to ask until you've gathered enough observations.

---

## Plugin Architecture: Turnkey + Domain-Specific

This is a **Claude Code plugin** that installs once and applies to any project. The plugin provides:

- Graph database (Neo4j)
- MCP server with capture/query tools
- Hooks for automatic trajectory capture
- Import pipelines for various data sources
- Agent skill instructions

**The project itself determines the domain.** Each Claude Code project has its own:

- `CLAUDE.md` with domain-specific instructions
- Import configurations (what data sources to pull from)
- Export configurations (where to push decisions, observations)
- Domain 2 reference sources (which PDFs, which frameworks)

### Example: Software Project

```
my-app/
├── CLAUDE.md           # Software dev instructions, coding standards
├── .claude/
│   └── ccmemory/
│       └── config.yaml # Git import, no external data sources
└── src/
```

### Example: Health Research Project

```
insomnia-research/
├── CLAUDE.md           # Instructions for symptom tracking, hypothesis testing
├── .claude/
│   └── ccmemory/
│       ├── config.yaml
│       │   imports:
│       │     - type: app
│       │       source: family-diagram-personal  # Relationship tracking app
│       │       sync: bidirectional              # Import events, export decisions
│       │     - type: conversation
│       │       source: chatgpt-export
│       │     - type: pdf
│       │       path: ./research/
│       │   domain2_sources:
│       │     - bowen-theory
│       │     - sleep-research
│       │     - sns-inflammation
│       └── schema-extensions.yaml  # Domain-specific node types
├── research/           # PDFs to import
├── journal/            # Exported observations
└── decisions/          # Exported decision log
```

### Bidirectional App Integration

For apps like Family Diagram - Personal that track relationship events:

```yaml
# config.yaml
imports:
  - type: app
    source: family-diagram-personal
    sync: bidirectional
    import:
      - relationship_events → Event nodes
      - symptom_reports → Observation nodes
      - timeline_entries → Touch nodes
    export:
      - Decision nodes → app decision log
      - Hypothesis nodes → app research queue
      - validated Bridges → app insight feed
```

The plugin becomes a **memory and reasoning shim** that sits between you and any intellectual project, accumulating understanding and surfacing relevant context regardless of domain.

---

## The Two-Domain Architecture

The system separates **your specifics** (high-confidence, lived experience) from **reference knowledge** (curated, to be tested against your reality).

```
┌────────────────────────────────────────────────────────────────────────┐
│                         DOMAIN 1: Your Specifics                        │
│                      (High confidence, event-sourced)                   │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Sources:                                                               │
│  - Live conversation capture (Claude Code, Desktop, any MCP client)    │
│  - Your apps (relationship tracker, time tracker, health apps)         │
│  - Conversation exports (ChatGPT, Grok, Claude history)                │
│  - Personal data (Fitbit, calendars, financial exports)                │
│                                                                         │
│  Captures:                                                              │
│  - Decisions (with options, reasoning, revisit triggers)               │
│  - Corrections (updated beliefs — highest value)                       │
│  - Exceptions (rules that don't apply to you)                          │
│  - Observations (symptoms, events, patterns, data points)              │
│  - Relationships (people, projects, concepts that connect)             │
│                                                                         │
│  Confidence: HIGH — you said it, you lived it, you observed it         │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ bridges (proposed → validated)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      DOMAIN 2: Reference Knowledge                      │
│                    (Curated, but not personalized)                      │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Sources:                                                               │
│  - Imported documents (PDFs, strategy docs, articles)                  │
│  - Model training knowledge (invoked on demand)                        │
│  - Active web search (when gaps identified)                            │
│  - Project-specific references (codebase docs, APIs, specs)            │
│                                                                         │
│  Captures:                                                              │
│  - Concepts (definitions, relationships between ideas)                 │
│  - Claims (with sources and confidence levels)                         │
│  - Frameworks (Bowen theory, design patterns, market models)           │
│  - Knowledge gaps (what we don't know yet — explicit nodes)            │
│  - Hypotheses (proposed connections, testable predictions)             │
│                                                                         │
│  Confidence: MEDIUM — literature says, needs testing against Domain 1  │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
```

### Why This Division Works

**Domain 1 has no entity resolution problem.** When you say "I woke at 2:30am with cold sweats," there's no ambiguity. The system records your observation with timestamp and context. No reconciliation needed.

**Domain 2 has a bounded entity resolution problem.** Research papers about "nocturnal hypoglycemia" can be linked to other papers about the same concept. Medical/scientific concepts have relatively stable definitions. Existing ontologies (SNOMED, design pattern catalogs, Bowen theory constructs) provide scaffolding.

**The bridge layer is where value emerges.** Domain 1 observations get annotated with Domain 2 concepts — not merged, annotated. Bridges start as proposals and become validated through confirmation.

---

## Domain-Specific Instantiation

The same architecture applies across domains:

### Software Development

| Aspect | Domain 1 (Your Specifics) | Domain 2 (Reference) |
|--------|---------------------------|---------------------|
| Content | Codebase decisions, debugging sessions, architectural choices, corrections | Language docs, library capabilities, design pattern literature |
| Decisions | "Use F1 scoring for extraction accuracy" | Options from ML literature |
| Corrections | "Fixed delays, not exponential backoff — caused cascading failures" | General retry pattern advice |
| Exceptions | "Sync instead of async for clinical model — race conditions" | Async best practices |
| Bridges | "Our auth pattern follows OAuth 2.0 spec with these exceptions..." | |

### Career Consulting

| Aspect | Domain 1 (Your Specifics) | Domain 2 (Reference) |
|--------|---------------------------|---------------------|
| Content | Your situation, skills, constraints, relationships, decisions | Market data, YC wisdom, compensation benchmarks, industry trends |
| Decisions | "Parallel paths strategy — maximize AFS during golden period" | Startup vs. employment tradeoff frameworks |
| Corrections | "AFS 70-80% likely stays side project" (updated from optimistic) | General startup success rates |
| Exceptions | "Remote exception path possible despite Micron policy" | Standard corporate remote policies |
| Bridges | "Your situation maps to 'intrapreneur' pattern from Christensen..." | |

### Medical/Health Research (e.g., Chronic Insomnia)

| Aspect | Domain 1 (Your Specifics) | Domain 2 (Reference) |
|--------|---------------------------|---------------------|
| Content | Symptoms, triggers, medical history, relationship events, experiments | Sleep research, SNS literature, inflammation studies, Bowen theory |
| Decisions | "Try magnesium glycinate 200mg before bed" | Supplement research, dosing studies |
| Corrections | "Alcohol hurts sleep, not helps — fragments REM, causes 3am waking" | General alcohol/sleep research |
| Exceptions | "Kindle reading allowed despite screen rule — doesn't affect my sleep" | Blue light recommendations |
| Bridges | "Your 2:30am waking pattern matches nocturnal hypoglycemia profile..." | |

### Relationship/Family Systems Research

| Aspect | Domain 1 (Your Specifics) | Domain 2 (Reference) |
|--------|---------------------------|---------------------|
| Content | Timeline events, relationship shifts, symptom correlations, patterns | Bowen theory constructs, DSM criteria, family systems research |
| Observations | "Holiday gathering with extended family → 3 nights poor sleep" | Bowen: anxiety transmission in systems |
| Patterns | "Sleep disruption correlates with high-anxiety family events (3 events)" | Literature on relational stress and physiology |
| Bridges | "Conflict escalation fits triangulation pattern from Bowen..." | |

---

## The Bridge Layer: Where Magic Happens

Bridges connect your specific observations to reference concepts. They start as proposals and become validated through confirmation.

```cypher
// Your observation (Domain 1)
(:Observation {
  id: "obs-2025-01-02",
  content: "2:30am waking with cold sweats after dessert",
  timestamp: datetime,
  confidence: 1.0,  // You experienced it
  source: "conversation"
})

// Concept from literature (Domain 2)
(:Concept {
  id: "nocturnal-hypoglycemia",
  definition: "Blood sugar drop during sleep causing awakening",
  sources: ["paper-123", "paper-456"]
})

// The bridge (proposed, needs validation)
(:Observation)-[:MAY_BE_INSTANCE_OF {
  confidence: 0.7,  // LLM proposed this link
  basis: "timing and symptoms match literature pattern",
  validated: false,  // You haven't confirmed
  proposed_at: datetime
}]->(:Concept)

// After user confirms
(:Observation)-[:INSTANCE_OF {
  confidence: 0.95,
  validated: true,
  validated_at: datetime
}]->(:Concept)
```

### Bridge Proposal System

When you report something in Domain 1:

1. **Record** the observation (high confidence)
2. **Query** Domain 2 for potentially related concepts
3. **Propose** bridges: "This may relate to [concept]. Confirm?"
4. **If confirmed** → bridge becomes high-confidence, informs future queries
5. **If rejected** → bridge is deleted (also valuable — negative signal)

This is where human-in-loop happens, but it's **lightweight** — binary yes/no on proposed links, not manual graph curation.

---

## Active Research: Domain 2 as Living Knowledge

Domain 2 isn't a static repository. It's a **living research layer** that:

1. **Uses model training data** — Claude already knows about many domains
2. **Searches for more** — WebSearch for recent studies, emerging connections
3. **Proposes hypotheses** — "Based on your pattern + literature, consider X?"
4. **Verifies claims** — Checks if a proposed connection has research backing

```
Domain 2 Sources
─────────────────────────────────────────────────────────────────

  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
  │   Imported      │     │  Model's Own    │     │   Active        │
  │   Documents     │     │  Knowledge      │     │   Search        │
  │                 │     │                 │     │                 │
  │  - PDFs         │     │  - Training     │     │  - WebSearch    │
  │  - Strategy     │     │    data on      │     │  - PubMed       │
  │    docs         │     │    domain       │     │  - Google       │
  │  - Bookmarks    │     │    concepts     │     │    Scholar      │
  │                 │     │                 │     │                 │
  └────────┬────────┘     └────────┬────────┘     └────────┬────────┘
           │                       │                       │
           └───────────────────────┼───────────────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────┐
                    │   Concept Graph          │
                    │   (Synthesized)          │
                    │                          │
                    │   Entities + Claims +    │
                    │   Confidence + Sources   │
                    └──────────────────────────┘
```

### The Agent's Research Behavior

When you mention something relevant:

**Step 1: Record to Domain 1** (your specifics — always happens)

**Step 2: Check Domain 2 for relevant concepts**
- Model knowledge: What does training data say?
- Imported docs: What have you already collected?
- Existing bridges: What connections are already validated?

**Step 3: Identify knowledge gaps, search if warranted**

```
"Your observation connects relationship stress → sleep disruption.

From my training: This pathway is well-established (SNS activation).

Gap identified: I don't have recent research on whether *brief*
exposures (3 days) have lasting effects vs. chronic exposure.

Should I search for studies on acute relational stress and sleep? [Y/n]"
```

**Step 4: Propose hypotheses based on accumulated data**

```
"Emerging pattern from your data:
- Sleep disruption correlates with brother-in-law exposure (3 events)
- You have hyperactive inflammatory response (PA diagnosis)
- Literature: Interpersonal stress → cortisol → inflammatory markers

Hypothesis: Your inflammatory sensitivity may amplify the sleep
impact of relationship stress beyond typical duration.

Testable prediction: symptoms last longer than the visit itself.
Does this match your experience? [Yes/No/Unsure]"
```

---

## The Co-Thinker Model

This transforms the system from **storage** to **research partner**:

```
┌─────────────────────────────────────────────────────────────────┐
│                     Research Partner Agent                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Behaviors:                                                      │
│                                                                  │
│  1. CAPTURE - Record observations to Domain 1                    │
│     "Got it, logged the sleep disruption during sister visit"    │
│                                                                  │
│  2. CONNECT - Bridge to Domain 2 concepts                        │
│     "This relates to SNS activation and Bowen proximity effects" │
│                                                                  │
│  3. QUESTION - Identify what's unknown                           │
│     "I don't know if your inflammatory history affects duration" │
│                                                                  │
│  4. SEARCH - Actively find relevant research                     │
│     "Found a 2023 study on acute stress and sleep recovery..."   │
│                                                                  │
│  5. HYPOTHESIZE - Propose testable connections                   │
│     "Based on patterns, I predict X. Want to track this?"        │
│                                                                  │
│  6. VERIFY - Check hypotheses against new data                   │
│     "You reported normal sleep 6 days post-visit. This matches   │
│      the literature prediction of 5-day recovery."               │
│                                                                  │
│  7. CORRECT - Update beliefs when wrong                          │
│     "Previous hypothesis about caffeine was wrong. Updating."    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Model Extensions

### Domain 1: Event Graph (from original plan, unchanged)

The original EVENT_GRAPH_PLAN.md data model remains the core:

- **Sessions** — walks through the domain
- **Decisions** — choices with options, rationale, revisit triggers
- **Corrections** — updated beliefs (highest value)
- **Exceptions** — rules that don't apply
- **Touches** — information sources accessed (files, papers, data)

### Domain 1: Observations and Relationships (new)

```cypher
// Observations (personal data points)
(:Observation {
  id: string,
  timestamp: datetime,
  type: "symptom" | "event" | "measurement" | "experience",
  content: string,
  severity: float,  // Optional, for symptoms
  source: "conversation" | "app" | "import"
})

// Relationships between entities (people, concepts, projects)
(:Entity)-[:RELATES_TO {
  type: "causes" | "correlates" | "precedes" | "involves",
  strength: float,
  observed_count: int,
  context: string
}]->(:Entity)

// People and their relational context
(:Person {
  id: string,
  relationship_type: string,  // "sibling", "in-law", "colleague"
  ease: float,  // How comfortable interactions are
  notes: string
})

// Events involving people
(:Event {
  id: string,
  type: "visit" | "conflict" | "conversation" | "milestone",
  start: datetime,
  end: datetime,
  involved: [person_ids]
})

// Temporal correlations
(:Observation)-[:DURING]->(:Event)
(:Observation)-[:PRECEDED_BY {days: int}]->(:Event)
(:Observation)-[:FOLLOWED_BY {days: int}]->(:Event)
```

### Domain 2: Concept Graph (new)

```cypher
// Concepts from reference knowledge
(:Concept {
  id: string,
  name: string,
  definition: string,
  domain: "medical" | "software" | "business" | "psychology",
  type: "entity" | "process" | "pattern" | "framework"
})

// Source tracking
(:Concept)-[:SOURCED_FROM {confidence: float}]->(:Source)
(:Source {
  id: string,
  type: "model_training" | "imported_pdf" | "web_search" | "user_provided",
  reference: string,
  retrieved_at: datetime
})

// Claims from literature
(:Claim {
  id: string,
  statement: string,
  confidence: float,
  source: string
})
(:Claim)-[:ABOUT]->(:Concept)
(:Claim)-[:SUPPORTS | :CONTRADICTS]->(:Claim)

// Knowledge gaps (explicit)
(:KnowledgeGap {
  id: string,
  question: string,
  identified_at: datetime,
  status: "open" | "researched" | "answered",
  answer: string  // Populated when resolved
})

// Hypotheses (testable)
(:Hypothesis {
  id: string,
  statement: string,
  basis: [string],  // What observations/concepts support this
  testable_prediction: string,
  status: "proposed" | "tracking" | "supported" | "refuted"
})
(:Hypothesis)-[:BASED_ON]->(:Observation)
(:Hypothesis)-[:BASED_ON]->(:Concept)
(:Hypothesis)-[:TESTED_BY]->(:Observation)
```

### Bridge Layer (new)

```cypher
// Bridges connect Domain 1 to Domain 2
(:Observation)-[:MAY_BE_INSTANCE_OF {
  confidence: float,
  basis: string,
  validated: boolean,
  proposed_at: datetime,
  validated_at: datetime
}]->(:Concept)

// Validated bridges
(:Observation)-[:INSTANCE_OF]->(:Concept)
(:Decision)-[:APPLIES_FRAMEWORK]->(:Concept)
(:Exception)-[:CONTRADICTS_GENERAL_ADVICE]->(:Concept)
```

---

## Import Pipeline

### Conversation Export Importers

Import from ChatGPT, Grok, Claude Desktop, etc.:

```python
def import_conversation_export(export_path, source_type):
    """
    Parse conversation exports from various LLM platforms.
    Extract observations, decisions, corrections to Domain 1.
    """
    conversations = parse_export(export_path, source_type)

    for conv in conversations:
        session = create_session(
            timestamp=conv.timestamp,
            source=f"import:{source_type}",
            summary=conv.title or generate_summary(conv)
        )

        for message in conv.messages:
            # User messages may contain observations
            if message.role == "user":
                observations = extract_observations(message.content)
                for obs in observations:
                    create_observation(session, obs, confidence=0.8)

            # Look for decision patterns
            if looks_like_decision(message):
                create_decision(session, message, confidence=0.6)

            # Look for corrections (user contradicting assistant)
            if is_correction(message, conv.context):
                create_correction(session, message, confidence=0.7)
```

### Document Importers

```python
def import_pdf(pdf_path, domain):
    """
    Extract concepts, claims, and relationships from PDF.
    Add to Domain 2 with source tracking.
    """
    content = extract_pdf_content(pdf_path)

    # LLM extraction of concepts
    concepts = llm_extract_concepts(content, domain)
    for concept in concepts:
        create_concept(
            concept,
            source=f"import:pdf:{pdf_path}",
            confidence=0.7
        )

    # Extract claims with citations
    claims = llm_extract_claims(content)
    for claim in claims:
        create_claim(
            claim,
            source=pdf_path,
            confidence=0.6  # Lower until cross-referenced
        )

    # Build relationships between concepts
    relationships = llm_extract_relationships(content, concepts)
    for rel in relationships:
        link_concepts(rel.source, rel.target, rel.type)
```

### App Data Importers

```python
def import_app_timeline(app_export, app_type):
    """
    Import timeline data from apps (relationship tracker, health apps, etc.)
    """
    events = parse_app_export(app_export, app_type)

    for event in events:
        create_event(
            timestamp=event.timestamp,
            type=event.type,
            content=event.content,
            source=f"import:app:{app_type}",
            confidence=0.9  # App data is reliable
        )

        # Link to people if applicable
        for person_id in event.involved_people:
            link_event_to_person(event, person_id)
```

---

## Context Injection: How Knowledge Gets Used

### SessionStart Hook

```python
def on_session_start(project_path, domain):
    """
    Query both domains and inject relevant context.
    """
    # Get recent observations from Domain 1
    recent_observations = query_recent_observations(domain, days=30)

    # Get relevant concepts from Domain 2
    relevant_concepts = query_related_concepts(recent_observations)

    # Get validated bridges
    bridges = query_validated_bridges(recent_observations)

    # Get active hypotheses being tracked
    hypotheses = query_active_hypotheses(domain)

    # Get pending bridge proposals (for review)
    pending_bridges = query_pending_bridges(limit=3)

    # Inject as context
    emit_context(f"""
    Recent from your history:
    {format_observations(recent_observations)}

    Relevant knowledge:
    {format_concepts(relevant_concepts)}

    Validated connections:
    {format_bridges(bridges)}

    Hypotheses being tracked:
    {format_hypotheses(hypotheses)}

    Pending for review:
    {format_pending_bridges(pending_bridges)}
    """)
```

### Skill Instructions (SKILL.md)

```markdown
# Context Graph Research Partner

You have access to a context graph with two domains:
- Domain 1: The user's specific observations, decisions, and history
- Domain 2: Reference knowledge from literature, documents, and research

## Behaviors

### When the user reports an observation
1. Record it to Domain 1 (always)
2. Query Domain 2 for related concepts
3. If match found, propose a bridge: "[Observation] may relate to [concept]. Confirm?"
4. If no match, note as potential knowledge gap

### When discussing a decision
1. Search precedent in Domain 1 for similar past decisions
2. Check Domain 2 for relevant frameworks or best practices
3. Surface any exceptions that might apply
4. Record the decision with options considered and rationale

### When you don't know something
1. Acknowledge the gap explicitly
2. Check if it's already a recorded KnowledgeGap
3. Offer to search: "Should I look for research on [topic]?"
4. If user agrees, use WebSearch, record findings to Domain 2

### When patterns emerge
1. Propose hypotheses based on accumulated observations
2. State testable predictions
3. Track against future observations
4. Update hypothesis status when evidence arrives

### Proactive behaviors
- Periodically surface stale hypotheses: "We proposed X 30 days ago. Any update?"
- Suggest connections: "Your [A] and [B] may be related based on [C]"
- Identify gaps: "We have observations about [X] but no reference knowledge"
```

---

## MCP Server: Additional Tools

Extending the original plan's tools:

### Tool: `record_observation`

```typescript
interface RecordObservationParams {
  content: string;
  type: "symptom" | "event" | "measurement" | "experience";
  timestamp?: datetime;  // Defaults to now
  severity?: number;
  related_to?: string[];  // Entity IDs
}

interface RecordObservationResult {
  observation_id: string;
  proposed_bridges: {
    concept: string;
    confidence: number;
    basis: string;
  }[];
}
```

### Tool: `search_reference`

```typescript
interface SearchReferenceParams {
  query: string;
  domain?: string;
  include_web_search?: boolean;
  sources?: ("model" | "imported" | "web")[];
}

interface SearchReferenceResult {
  concepts: Concept[];
  claims: Claim[];
  knowledge_gaps: KnowledgeGap[];
  suggested_searches?: string[];  // If gaps found
}
```

### Tool: `propose_hypothesis`

```typescript
interface ProposeHypothesisParams {
  statement: string;
  basis: string[];  // Observation/concept IDs
  testable_prediction: string;
}

interface ProposeHypothesisResult {
  hypothesis_id: string;
  related_observations: Observation[];
  supporting_concepts: Concept[];
}
```

### Tool: `validate_bridge`

```typescript
interface ValidateBridgeParams {
  observation_id: string;
  concept_id: string;
  validated: boolean;
}

interface ValidateBridgeResult {
  bridge_updated: boolean;
  related_hypotheses_affected: string[];
}
```

### Tool: `query_patterns`

```typescript
interface QueryPatternsParams {
  entity_id?: string;  // Person, concept, or observation type
  time_range?: { start: datetime; end: datetime };
  correlation_type?: "temporal" | "causal" | "co-occurrence";
}

interface QueryPatternsResult {
  patterns: {
    description: string;
    entities_involved: string[];
    strength: number;
    observation_count: number;
    example_instances: string[];
  }[];
}
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         User Interfaces                              │
├─────────────┬─────────────┬─────────────┬─────────────┬─────────────┤
│ Claude Code │   Claude    │  Custom     │  Your Apps  │  Import     │
│   (IDE)     │   Desktop   │  MCP Client │  (Timeline) │  Scripts    │
└──────┬──────┴──────┬──────┴──────┬──────┴──────┬──────┴──────┬──────┘
       │             │             │             │             │
       └─────────────┴─────────────┼─────────────┴─────────────┘
                                   │
                            ┌──────▼──────┐
                            │   Hooks     │
                            │  (capture)  │
                            └──────┬──────┘
                                   │
                            ┌──────▼──────┐
                            │    MCP      │
                            │   Server    │
                            │             │
                            │  - record   │
                            │  - query    │
                            │  - search   │
                            │  - propose  │
                            │  - validate │
                            └──────┬──────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
       ┌──────▼──────┐      ┌──────▼──────┐     ┌──────▼──────┐
       │  Domain 1   │      │   Bridge    │     │  Domain 2   │
       │  (Yours)    │◄────►│   Layer     │◄───►│ (Reference) │
       │             │      │             │     │             │
       │  Neo4j      │      │  Neo4j      │     │  Neo4j +    │
       │             │      │             │     │  Vector DB? │
       └─────────────┘      └─────────────┘     └──────┬──────┘
                                                       │
                                                ┌──────▼──────┐
                                                │   Active    │
                                                │   Research  │
                                                │             │
                                                │  WebSearch  │
                                                │  Model KB   │
                                                └─────────────┘
```

---

## Implementation Phases (Revised)

### Phase 1: Foundation (Week 1)

**Goal**: Working capture for both domains

Build:
- [ ] Neo4j with Domain 1 + Domain 2 schemas
- [ ] MCP server with basic tools
- [ ] `record_observation` tool
- [ ] `record_decision` tool (from original plan)
- [ ] Basic conversation import (ChatGPT, Claude exports)
- [ ] SessionStart context injection (basic)

**Deliverable**: Can capture observations and decisions, import conversation history

### Phase 2: Bridge Layer (Week 2)

**Goal**: Connecting domains

Build:
- [ ] Domain 2 concept schema
- [ ] `search_reference` tool (model knowledge only)
- [ ] Bridge proposal system
- [ ] `validate_bridge` tool
- [ ] PDF/document importer (basic)
- [ ] Bridge review queue in context injection

**Deliverable**: System proposes connections, user validates

### Phase 3: Active Research (Week 3)

**Goal**: Domain 2 becomes active

Build:
- [ ] WebSearch integration for Domain 2
- [ ] Knowledge gap detection
- [ ] `propose_hypothesis` tool
- [ ] Hypothesis tracking
- [ ] Source confidence scoring
- [ ] SKILL.md for research partner behavior

**Deliverable**: System actively searches and proposes hypotheses

### Phase 4: Pattern Detection (Week 4)

**Goal**: Finding non-obvious connections

Build:
- [ ] `query_patterns` tool
- [ ] Temporal correlation detection
- [ ] Cross-entity pattern analysis
- [ ] Hypothesis verification against new data
- [ ] App data importers (timeline, health)

**Deliverable**: System detects patterns in your data

### Phase 5: Polish (Week 5)

**Goal**: Production ready

Build:
- [ ] Comprehensive tests
- [ ] Migration from existing career project
- [ ] Multi-project support
- [ ] Performance optimization
- [ ] Documentation

**Deliverable**: Complete universal context graph

---

## Migration Path: Markdown Context Systems → Universal Graph

A well-designed markdown-based context system (decision logs with revisit triggers, categorized insights, normalized indexes, conversation archives) represents the upper bound of what's achievable without a graph database — essentially a hand-maintained knowledge graph in flat files. Migration to the universal context graph:

1. **Import decision logs** → Decision nodes with full structure (options, rationale, revisit triggers)
2. **Import insights/realizations** → Observation and Hypothesis nodes
3. **Import conversation archives** → Session nodes with extracted content
4. **Parse CLAUDE.md hierarchy** → Domain 2 reference structure
5. **Preserve cross-references** → Relationship edges

The markdown files remain as human-readable backup. The graph becomes the queryable substrate.

---

## Comparison: Original Plan vs. Universal Graph

| Aspect | Original EVENT_GRAPH_PLAN | Universal Context Graph |
|--------|--------------------------|------------------------|
| **Scope** | Software projects | Any complex domain |
| **Domain model** | Single (trajectories) | Two domains + bridges |
| **Knowledge source** | Git, conversations, docs | + Model KB, web search, apps |
| **Agent behavior** | Capture + query | + Active research, hypothesis |
| **Human-in-loop** | Implicit (corrections) | Explicit (bridge validation) |
| **Backfill** | Git, decision logs | + Conversation exports, app data |

The universal graph **subsumes** the original plan. Everything in EVENT_GRAPH_PLAN.md still applies — it's the Domain 1 structure. The universal graph adds Domain 2 and the bridge/research layer.

---

## Success Metrics (Revised)

### Primary: Reduced re-explanation

Same as original plan. Target: 50% reduction by week 6.

### Secondary: Bridge validation rate

Measure: What percentage of proposed bridges get validated?

- Too low (<30%) → proposals too speculative
- Too high (>90%) → proposals too obvious, not adding value
- Target: 50-70% validation rate

### Tertiary: Hypothesis usefulness

Measure: Do hypotheses lead to actionable insights?

- Track: Hypotheses proposed → tested → supported/refuted
- Target: 30% of hypotheses get tested within 30 days

### Cross-domain: Active research value

Measure: Does web search / model knowledge add value?

- Track: Knowledge gaps identified → searched → used
- Target: At least 2 useful research findings per week by week 6

---

## Example: Multi-Domain Session

```
User: "I had a rough week. Holiday gathering with extended family, didn't
sleep well for 3 nights. Some family dynamics were stressful. Now I'm behind
on the extraction service project and worried about the March deadline."

System processes:

DOMAIN 1 CAPTURE:
- Observation: Sleep disruption, 3 nights, during family event
- Observation: Family dynamics assessed as stressful
- Observation: Behind on project, March deadline concern
- Event: Family gathering (dates, people involved)

DOMAIN 2 QUERY:
- Bowen theory: Anxiety transmission in relationship systems
- Sleep research: Acute interpersonal stress effects
- Project context: March deadline, current status

BRIDGE PROPOSALS:
- Sleep disruption ↔ Interpersonal stress (literature match)
- Family stress ↔ Bowen "anxiety transmission" pattern

CROSS-PROJECT:
- March deadline + sleep disruption → productivity impact
- Career constraints → timeline pressure

RESPONSE:
"Logged the gathering and sleep disruption. The pattern of sleep problems
during high-stress family events has now occurred 3 times in your history.

From Bowen theory: Anxiety transmits in relationship systems. Your
physiological sensitivity (inflammatory profile) may amplify this.

Re: project — you're 3 weeks from March deadline with the extraction
service incomplete. Last session you were working on retry logic.
Given the sleep disruption, want to reassess the timeline or identify
what's truly critical path?"
```

---

## Theoretical Foundation

This architecture synthesizes insights from:

1. **"AI's trillion-dollar opportunity: Context graphs"** (Gupta & Garg, 2024)
   - Decision traces vs. state capture
   - The fragmentation tax
   - Systems of agents sitting in the execution path

2. **"How to build a context graph"** (Koratana, 2024)
   - The two clocks problem
   - Agents as informed walkers
   - Schema as output, not input
   - World models, not retrieval systems

3. **World Models** (Ha & Schmidhuber, 2018)
   - Simulation as the test of understanding
   - Learning compressed representations from trajectories

Key principles applied:
- **Event-sourced**: Append-only trajectory capture
- **Emergent ontology**: Structure discovered through walks
- **Precedent as first-class**: Exceptions and decisions are searchable
- **Simulation capability**: The test of understanding
- **Two-domain separation**: Your specifics vs. reference knowledge

---

## References

- [AI's trillion-dollar opportunity: Context graphs](https://foundationcapital.com/ais-trillion-dollar-opportunity-context-graphs/) — Gupta & Garg, Foundation Capital
- [How to build a context graph](https://akoratana.substack.com/p/how-to-build-a-context-graph) — Koratana
- [World Models](https://worldmodels.github.io/) — Ha & Schmidhuber
- [GraphRAG: Unlocking LLM discovery on narrative private data](https://www.microsoft.com/en-us/research/blog/graphrag-unlocking-llm-discovery-on-narrative-private-data/) — Microsoft Research
- [Personal Knowledge Graphs](https://doi.org/10.1007/978-3-030-33220-4_1) — Academic survey
- [Bowen Family Systems Theory](https://www.thebowencenter.org/) — For relationship domain modeling
- [Neo4j official MCP server](https://github.com/neo4j/mcp)
- [MCP specification](https://modelcontextprotocol.io)
- [node2vec: Scalable Feature Learning for Networks](https://arxiv.org/abs/1607.00653) — Graph embedding techniques
