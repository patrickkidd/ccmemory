# ccmemory-graph: Context Graph for Claude Code

## Executive Summary

A Claude Code plugin that builds an **event-clock context graph** from agent trajectories. Instead of extracting static entities, it captures **decision traces** — the reasoning, exceptions, precedents, and cross-system context that currently live in your head and die between sessions.

**The key insight**: Every Claude Code session is an *informed walk* through your project. The trajectory itself — files touched, decisions made, corrections given, exceptions granted — is the data. Accumulate enough walks and the organizational structure emerges. The schema is output, not input.

**What this enables**:
- "Why did we build it this way?" → Trace the decision chain
- "How did we handle this last time?" → Search precedent
- "What breaks if I change this?" → Simulate based on past trajectories
- "What's the context I need for this task?" → Relevant walks surface automatically

---

## The Problem: We Only Have Half of Time

### The Two Clocks Problem

Every system has two clocks:
- **State clock**: What's true right now
- **Event clock**: What happened, in what order, with what reasoning

We've built trillion-dollar infrastructure for state. The event clock barely exists.

| What State Clock Captures | What Event Clock Should Capture |
|---------------------------|--------------------------------|
| `timeout=30s` | "Tripled from 5s after cascading failures post-Gemini migration, based on auth-service precedent" |
| Component depends on service | The trajectory of discovering, debugging, and resolving that dependency |
| Decision: "Use F1 scoring" | Options considered, constraints evaluated, who approved, what precedent it sets |
| `CLAUDE.md` says "always use X" | Why that rule exists, what exception led to it, when it should be revisited |

### Why This Matters for Claude Code

Claude Code starts every session with zero context. The organizational brain — your accumulated understanding of why things work the way they do — exists only in your head.

Current solutions (CLAUDE.md, context files) capture state: "here's how things are." They don't capture:

1. **Exception logic**: "We always do X for healthcare customers because..." — tribal knowledge
2. **Precedent chains**: "We structured this like the auth refactor last month" — no link exists
3. **Cross-system synthesis**: You check three files, a Slack thread, and remember a conversation — the reasoning is never captured
4. **Approval context**: You say "yes, do that approach" — that's an approval that sets precedent, but it vanishes

---

## The Solution: Trajectories as the Event Clock

### Agents as Informed Walkers

When Claude Code works through a problem, it traverses your project. It reads files, makes decisions, asks questions, receives corrections. This trajectory is an **informed walk** through organizational state space.

Unlike random exploration, agent trajectories are **problem-directed**:
- Start broad: "What's the architecture here?"
- Narrow as evidence accumulates: "This file, this function, this pattern"
- Adapt based on what's found: corrections redirect, approvals confirm

**The trajectory IS the data.** We don't need to "extract entities" — we need to record the walk with full decision context.

### Schema Emerges from Walks

> "You don't need to understand a system to represent it. Traverse it enough times and the representation emerges."

Traditional approach (what v1 tried):
```
Predefine: Component, Decision, Constraint, Concept...
Extract: Parse conversation for entities
Store: Create nodes of predefined types
```

Trajectory approach:
```
Record: Every touch, decision, correction, exception
Accumulate: Thousands of walks through the project
Emerge: Co-occurrence patterns reveal structure
```

Files that always get touched together during auth issues → they're related.
Decisions that follow similar patterns → structural equivalence.
Exceptions that set precedent → searchable for future similar cases.

### From Knowledge Base to World Model

The goal isn't retrieval. It's **simulation**.

A context graph with enough accumulated trajectories becomes a **world model for organizational physics**:
- "What happens if I change this component?" → Based on past trajectories, here's the blast radius
- "Will this approach work?" → Similar decisions succeeded/failed in these contexts
- "What's the risk?" → Exception patterns suggest where problems emerge

> "Simulation is the test of understanding. If your context graph can't answer 'what if,' it's just a search index."

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User's Projects                           │
├──────────────────┬──────────────────┬───────────────────────────┤
│    btcopilot/    │  career-builder/ │     other-project/        │
│   Claude Code    │   Claude Code    │      Claude Code          │
└────────┬─────────┴────────┬─────────┴────────┬──────────────────┘
         │                  │                   │
         │    Trajectories  │                   │
         └──────────────────┼───────────────────┘
                            │
                     ┌──────▼──────┐
                     │  ccmemory   │
                     │   plugin    │
                     │  (hooks)    │
                     └──────┬──────┘
                            │
                     ┌──────▼──────┐
                     │ Context     │
                     │ Graph MCP   │
                     │ Server      │
                     └──────┬──────┘
                            │
                     ┌──────▼──────┐
                     │   Neo4j     │
                     │  (Docker)   │
                     │  + Volume   │
                     └─────────────┘
```

### Core Principle: Capture at Commit Time

The plugin sits in the **execution path**. It sees:
- What files were touched
- What decisions were made
- What corrections were given
- What exceptions were granted
- What reasoning connected observation to action

This happens **at commit time** — during the session, not reconstructed after via parsing.

---

## Data Model: Event-Sourced Trajectories

### Primary Structure: The Walk

```cypher
// A session is a walk through project space
(:Session {
  id: string,
  project: string,
  started_at: datetime,
  ended_at: datetime,
  summary: string,
  outcome: "completed" | "abandoned" | "errored"
})

// Each touch in the walk
(:Touch {
  id: string,
  timestamp: datetime,
  file_path: string,
  action: "read" | "write" | "create" | "delete",
  context: string,  // Why this file was touched
  content_hash: string  // State at touch time
})

// Walks are sequences of touches
(Session)-[:CONTAINS {order: int}]->(Touch)
(Touch)-[:NEXT]->(Touch)

// Touches cluster into patterns
(Touch)-[:CO_OCCURS_WITH {frequency: int}]->(Touch)
```

### Decision Traces: The Event Clock

```cypher
// A decision made during a session
(:Decision {
  id: string,
  timestamp: datetime,
  description: string,
  options_considered: [string],
  choice: string,
  rationale: string,
  confidence: float
})

// Decisions happen in sessions
(Session)-[:DECIDED]->(Decision)

// Decisions affect files
(Decision)-[:AFFECTED]->(Touch)

// Decisions set or follow precedent
(Decision)-[:SETS_PRECEDENT_FOR {similarity: float}]->(Decision)
(Decision)-[:FOLLOWED_PRECEDENT]->(Decision)
```

### Corrections: High-Value Learning Events

```cypher
// When the user corrects Claude's understanding
(:Correction {
  id: string,
  timestamp: datetime,
  wrong_belief: string,
  right_belief: string,
  context: string,
  severity: "minor" | "significant" | "critical"
})

// Corrections are the most valuable data
(Session)-[:CORRECTION]->(Correction)
(Correction)-[:INVALIDATES]->(Decision)  // If a past decision was wrong
(Correction)-[:ESTABLISHES]->(Belief)    // New understanding
```

### Exceptions: Precedent for Future Cases

```cypher
// When a rule is broken with justification
(:Exception {
  id: string,
  timestamp: datetime,
  rule_broken: string,
  justification: string,
  approver: "user" | "implicit",
  outcome: string
})

// Exceptions set precedent
(Session)-[:EXCEPTION]->(Exception)
(Exception)-[:PRECEDENT_FOR]->(Exception)  // Future similar exceptions

// Exceptions can become rules
(Exception)-[:EVOLVED_INTO]->(:Rule)
```

### Emergent Structure: Schema as Output

```cypher
// Entities emerge from co-occurrence in trajectories
(:Entity {
  id: string,
  name: string,
  type: string,  // Discovered, not predefined
  first_seen: datetime,
  touch_count: int
})

// Relationships emerge from trajectory patterns
(:Entity)-[:RELATED_TO {
  strength: float,      // Co-occurrence frequency
  context: string,      // How they relate
  discovered_at: datetime
}]->(:Entity)

// Structural equivalence across projects
(:Entity)-[:STRUCTURALLY_EQUIVALENT {
  similarity: float,
  basis: string  // "similar role", "analogous patterns"
}]->(:Entity)
```

### Cross-Project: Shared Constraints and Patterns

```cypher
// Projects and their relationships
(:Project {name, path, description})
(Project)-[:RELATED_TO {type: "business" | "technical"}]->(Project)

// Constraints that span projects
(:Constraint {
  id: string,
  description: string,
  source: string,
  type: "financial" | "temporal" | "technical" | "business"
})
(Constraint)-[:APPLIES_TO]->(Project)
(Constraint)-[:CONSTRAINS]->(Decision)

// Example: RSU vesting affects both btcopilot timeline and career strategy
(:Constraint {description: "RSU vesting schedule", type: "financial"})
  -[:APPLIES_TO]->(:Project {name: "btcopilot"})
  -[:APPLIES_TO]->(:Project {name: "career-builder"})
```

---

## MCP Server Specification

### Tool: `record_trajectory`

Record the current session's trajectory. Called automatically by hooks.

```typescript
interface RecordTrajectoryParams {
  session_id: string;
  project: string;
  events: TrajectoryEvent[];
}

type TrajectoryEvent = 
  | { type: "touch"; file: string; action: string; context: string; }
  | { type: "decision"; description: string; options: string[]; choice: string; rationale: string; }
  | { type: "correction"; wrong: string; right: string; context: string; }
  | { type: "exception"; rule: string; justification: string; }
  | { type: "approval"; what: string; implicit: boolean; };

interface RecordTrajectoryResult {
  events_recorded: number;
  patterns_updated: number;
  precedents_linked: number;
}
```

### Tool: `query_context`

Get relevant context for current task based on trajectory patterns.

```typescript
interface QueryContextParams {
  current_files: string[];        // Files currently being worked on
  task_description: string;
  project: string;
  include_cross_project?: boolean;
}

interface QueryContextResult {
  relevant_trajectories: TrajectoryReference[];  // Past walks through similar territory
  applicable_decisions: Decision[];              // Precedent that applies
  active_exceptions: Exception[];                // Exceptions that might apply
  warnings: Warning[];                           // Contradictions, stale patterns
  suggested_approach: string;                    // Based on successful past trajectories
}
```

### Tool: `search_precedent`

Find past decisions and exceptions relevant to current situation.

```typescript
interface SearchPrecedentParams {
  situation: string;              // Natural language description
  decision_type?: string;         // "architecture", "implementation", "process"
  project?: string;               // Limit to project or search all
  include_exceptions?: boolean;
}

interface SearchPrecedentResult {
  precedents: {
    decision: Decision;
    similarity: number;
    outcome: string;              // How it turned out
    trajectory_ref: string;       // Link to full context
  }[];
  exceptions: {
    exception: Exception;
    applicable: boolean;
    conditions: string;
  }[];
}
```

### Tool: `trace_decision`

Trace why something is the way it is.

```typescript
interface TraceDecisionParams {
  subject: string;                // File, component, pattern, or behavior
  question: "why" | "when" | "who" | "how";
}

interface TraceDecisionResult {
  chain: {
    event: Decision | Correction | Exception;
    timestamp: datetime;
    context: string;
    led_to: string;
  }[];
  narrative: string;              // LLM-generated explanation
  confidence: number;
  gaps: string[];                 // Where chain has missing links
}
```

### Tool: `simulate_change`

Predict impact of a change based on trajectory patterns.

```typescript
interface SimulateChangeParams {
  change_description: string;
  affected_files: string[];
  project: string;
}

interface SimulateChangeResult {
  predicted_impact: {
    files_likely_affected: string[];
    patterns_disrupted: string[];
    similar_past_changes: TrajectoryReference[];
  };
  risks: {
    description: string;
    basis: string;                // Which past trajectory suggests this
    severity: "low" | "medium" | "high";
  }[];
  recommendations: string[];
}
```

### Tool: `find_structural_equivalents`

Find structurally equivalent patterns across projects.

```typescript
interface FindEquivalentsParams {
  entity: string;                 // File, component, or pattern
  project: string;
  search_scope: "project" | "all";
}

interface FindEquivalentsResult {
  equivalents: {
    entity: string;
    project: string;
    similarity: number;
    basis: string;                // Why they're equivalent
    useful_precedent: Decision[];
  }[];
}
```

---

## Plugin Integration

### Hooks

#### `SessionStart`

```python
# Load relevant context based on:
# 1. Current working directory
# 2. Recently modified files
# 3. Past trajectories through this area

def on_session_start(project_path):
    # Query for relevant past trajectories
    context = mcp.query_context(
        current_files=get_recent_files(project_path),
        task_description="starting session",
        project=get_project_name(project_path),
        include_cross_project=True
    )
    
    # Surface relevant precedent
    if context.applicable_decisions:
        emit_context("Relevant precedent from past sessions...")
    
    # Warn about potential issues
    if context.warnings:
        emit_warnings(context.warnings)
```

#### `UserPromptSubmit` (The Critical Hook)

This is where trajectories are captured — at commit time, not after.

```python
def on_user_prompt(message, conversation_state):
    events = []
    
    # Detect decision points
    if is_decision_point(message, conversation_state):
        events.append({
            "type": "decision",
            "description": extract_decision(message),
            "options": conversation_state.options_discussed,
            "choice": extract_choice(message),
            "rationale": extract_rationale(message)
        })
    
    # Detect corrections (highest value!)
    if is_correction(message):
        events.append({
            "type": "correction",
            "wrong": conversation_state.claude_belief,
            "right": extract_correct_belief(message),
            "context": conversation_state.context
        })
    
    # Detect exceptions
    if is_exception_grant(message, conversation_state):
        events.append({
            "type": "exception",
            "rule": conversation_state.rule_in_question,
            "justification": extract_justification(message)
        })
    
    # Detect approvals (including implicit ones)
    if is_approval(message):
        events.append({
            "type": "approval",
            "what": conversation_state.proposed_action,
            "implicit": not is_explicit_approval(message)
        })
    
    # Record trajectory events
    if events:
        mcp.record_trajectory(
            session_id=conversation_state.session_id,
            project=conversation_state.project,
            events=events
        )
```

#### `Stop`

```python
def on_session_end(conversation_state):
    # Record final trajectory summary
    mcp.record_trajectory(
        session_id=conversation_state.session_id,
        project=conversation_state.project,
        events=[{
            "type": "session_end",
            "summary": generate_summary(conversation_state),
            "outcome": conversation_state.outcome,
            "files_touched": conversation_state.files_touched
        }]
    )
    
    # Trigger pattern analysis
    mcp.analyze_patterns(
        session_id=conversation_state.session_id,
        update_co_occurrence=True,
        link_precedents=True
    )
```

### Event Detection Prompts

#### Decision Detection

```markdown
Analyze this message in the context of the conversation.

CONVERSATION CONTEXT:
{recent_messages}

CURRENT MESSAGE:
{message}

Is this a decision point? Look for:
1. Explicit choices: "Let's go with X", "I'll use Y approach"
2. Implicit approval: "That sounds good", "Yes", "Do it"
3. Direction setting: "We should always...", "From now on..."
4. Trade-off resolution: Choosing between discussed options

If this is a decision:
- What was decided?
- What options were considered (even implicitly)?
- What's the rationale?
- Does this set precedent for future decisions?

Output JSON:
{
  "is_decision": boolean,
  "decision": {
    "description": string,
    "options_considered": [string],
    "choice": string,
    "rationale": string,
    "sets_precedent": boolean,
    "precedent_scope": string
  }
}
```

#### Correction Detection

```markdown
Analyze this message for corrections to Claude's understanding.

CLAUDE'S LAST RESPONSE:
{claude_response}

USER'S MESSAGE:
{message}

Is the user correcting a misunderstanding? Look for:
1. Direct correction: "No, that's not right", "Actually..."
2. Clarification that contradicts: "What I meant was..."
3. Factual correction: "It's X, not Y"
4. Context correction: "In this project we do it differently"

If this is a correction:
- What did Claude believe that was wrong?
- What is the correct understanding?
- How severe is this correction? (minor detail vs. fundamental misunderstanding)
- Does this invalidate any past reasoning?

Output JSON:
{
  "is_correction": boolean,
  "correction": {
    "wrong_belief": string,
    "right_belief": string,
    "severity": "minor" | "significant" | "critical",
    "invalidates_past": boolean,
    "context": string
  }
}
```

#### Exception Detection

```markdown
Analyze this message for exception grants.

CONVERSATION CONTEXT:
{context}

CURRENT MESSAGE:
{message}

Is the user granting an exception to normal rules/patterns? Look for:
1. Explicit exception: "In this case, let's skip X"
2. One-time deviation: "Just this once..."
3. Justified rule-breaking: "Because of Y, we should do Z instead"
4. Context-specific override: "For this customer/file/situation..."

If this is an exception:
- What rule or pattern is being broken?
- What's the justification?
- Is this a one-time exception or setting new precedent?
- What conditions make this exception valid?

Output JSON:
{
  "is_exception": boolean,
  "exception": {
    "rule_broken": string,
    "justification": string,
    "scope": "one-time" | "conditional" | "new-precedent",
    "conditions": string
  }
}
```

---

## Installation & Setup

### Prerequisites
- Docker and Docker Compose
- Claude Code CLI with plugin support

### Quick Start (< 5 minutes)

```bash
# 1. Install the plugin
claude plugin marketplace add patrickkidd/ccmemory-graph
claude plugin install ccmemory-graph

# 2. Start the context graph (auto-starts Neo4j in Docker)
ccmemory-graph start

# 3. That's it. Start using Claude Code normally.
```

The plugin auto-detects your project and begins capturing trajectories immediately.

### What Happens on First Run

1. Docker pulls Neo4j image (one-time, ~500MB)
2. Creates persistent volume for graph data
3. Initializes minimal schema (constraints only — structure emerges)
4. Registers MCP server with Claude Code
5. Begins capturing trajectories

### Configuration (Optional)

Create `~/.ccmemory-graph/config.yaml` for custom settings:

```yaml
# Neo4j connection (defaults work for local Docker)
neo4j:
  uri: bolt://localhost:7687
  username: neo4j
  password: ${CCMEMORY_NEO4J_PASSWORD:-ccmemory}

# Project relationships (optional — can also be discovered)
projects:
  btcopilot:
    path: ~/projects/btcopilot
    related_to: [career-builder]
  
  career-builder:
    path: ~/projects/career
    constraints:
      - "RSU vesting schedule affects timeline"

# Capture settings
capture:
  # What to capture automatically
  auto_detect_decisions: true
  auto_detect_corrections: true
  auto_detect_exceptions: true
  
  # Minimum confidence for pattern detection
  pattern_threshold: 0.7
  
  # Cross-project analysis
  cross_project: true

# Context surfacing
context:
  # How many past trajectories to consider
  max_trajectories: 20
  
  # Include structural equivalents from other projects
  include_equivalents: true
  
  # Warn about stale patterns (days)
  stale_threshold: 30
```

### CLI Commands

```bash
# Start/stop the context graph
ccmemory-graph start
ccmemory-graph stop
ccmemory-graph status

# Explore your graph
ccmemory-graph query "why is timeout set to 30s"
ccmemory-graph trace src/api/auth.py
ccmemory-graph precedent "error handling approach"

# Maintenance
ccmemory-graph backup ~/backups/
ccmemory-graph restore ~/backups/ccmemory-2024-01-15.dump
ccmemory-graph stats

# Debug
ccmemory-graph logs
ccmemory-graph inspect session-123
```

---

## Docker Configuration

### docker-compose.yml

```yaml
version: '3.8'

services:
  neo4j:
    image: neo4j:5-community
    container_name: ccmemory-graph-neo4j
    ports:
      - "7474:7474"   # Browser (optional, for debugging)
      - "7687:7687"   # Bolt protocol
    volumes:
      - ccmemory_data:/data
      - ccmemory_logs:/logs
    environment:
      - NEO4J_AUTH=neo4j/${CCMEMORY_NEO4J_PASSWORD:-ccmemory}
      - NEO4J_PLUGINS=["apoc"]
      - NEO4J_dbms_security_procedures_unrestricted=apoc.*
      - NEO4J_dbms_memory_heap_initial__size=256m
      - NEO4J_dbms_memory_heap_max__size=512m
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:7474"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    labels:
      - "ccmemory-graph=true"

volumes:
  ccmemory_data:
    name: ccmemory_graph_data
  ccmemory_logs:
    name: ccmemory_graph_logs
```

### Initialization (Minimal Schema)

```cypher
// Only constraints — structure emerges from trajectories

// Uniqueness
CREATE CONSTRAINT session_id IF NOT EXISTS FOR (s:Session) REQUIRE s.id IS UNIQUE;
CREATE CONSTRAINT decision_id IF NOT EXISTS FOR (d:Decision) REQUIRE d.id IS UNIQUE;
CREATE CONSTRAINT correction_id IF NOT EXISTS FOR (c:Correction) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT exception_id IF NOT EXISTS FOR (e:Exception) REQUIRE e.id IS UNIQUE;
CREATE CONSTRAINT project_name IF NOT EXISTS FOR (p:Project) REQUIRE p.name IS UNIQUE;

// Indexes for common queries
CREATE INDEX session_project IF NOT EXISTS FOR (s:Session) ON (s.project);
CREATE INDEX session_time IF NOT EXISTS FOR (s:Session) ON (s.started_at);
CREATE INDEX touch_file IF NOT EXISTS FOR (t:Touch) ON (t.file_path);
CREATE INDEX decision_time IF NOT EXISTS FOR (d:Decision) ON (d.timestamp);

// Full-text search
CREATE FULLTEXT INDEX decision_search IF NOT EXISTS 
  FOR (d:Decision) ON EACH [d.description, d.rationale];
CREATE FULLTEXT INDEX correction_search IF NOT EXISTS 
  FOR (c:Correction) ON EACH [c.wrong_belief, c.right_belief];
```

---

## Repository Structure

```
ccmemory-graph/
├── .claude-plugin/
│   └── manifest.json
├── docker/
│   ├── docker-compose.yml
│   └── init.cypher
├── mcp-server/
│   ├── pyproject.toml
│   └── src/
│       └── ccmemory_graph/
│           ├── __init__.py
│           ├── server.py           # MCP server
│           ├── tools/
│           │   ├── record.py       # record_trajectory
│           │   ├── query.py        # query_context
│           │   ├── precedent.py    # search_precedent
│           │   ├── trace.py        # trace_decision
│           │   └── simulate.py     # simulate_change
│           ├── detection/
│           │   ├── decisions.py    # Decision detection
│           │   ├── corrections.py  # Correction detection
│           │   └── exceptions.py   # Exception detection
│           ├── patterns/
│           │   ├── cooccurrence.py # Co-occurrence analysis
│           │   ├── structural.py   # Structural equivalence
│           │   └── precedent.py    # Precedent linking
│           └── graph/
│               ├── client.py       # Neo4j connection
│               └── queries.py      # Cypher templates
├── hooks/
│   ├── hooks.json
│   ├── session_start.py
│   ├── user_prompt.py
│   └── session_end.py
├── prompts/
│   ├── detect_decision.md
│   ├── detect_correction.md
│   └── detect_exception.md
├── skills/
│   └── context-graph/
│       └── SKILL.md
├── cli/
│   └── ccmemory_graph_cli.py
├── scripts/
│   ├── install.sh
│   ├── start.sh
│   ├── stop.sh
│   └── backup.sh
├── tests/
│   ├── test_detection.py
│   ├── test_patterns.py
│   └── test_queries.py
├── CLAUDE.md
├── README.md
└── LICENSE
```

---

## Implementation Phases

There are three interrelated timelines to understand:

1. **Development phases**: What gets built and when
2. **Graph maturity stages**: When each capability becomes genuinely useful
3. **Backfilling**: How to bootstrap value from existing data

---

### Development Phases

#### Phase 1: Foundation + Backfill Infrastructure (Week 1)

**Goal**: Working trajectory capture AND import pipeline

Build:
- [ ] Docker compose with Neo4j
- [ ] Minimal schema (constraints only)
- [ ] MCP server skeleton
- [ ] `record_trajectory` tool (basic events)
- [ ] Session start/end hooks
- [ ] Basic CLI (start/stop/status)
- [ ] **Backfill pipeline architecture** (importers as plugins)
- [ ] **Decision log importer** (markdown → Decision nodes)
- [ ] **Conversation log importer** (if you have raw logs)

**Deliverable**: Can capture new sessions AND import existing decision logs

**Why backfill in Phase 1**: The graph is only useful with data. Starting with backfill means you have something to query immediately, and you validate the data model against real decisions you've already made.

#### Phase 2: Decision Capture + Git Backfill (Week 2)

**Goal**: Detect decisions in real-time AND mine git history

Build:
- [ ] Decision detection prompt + parser
- [ ] Correction detection prompt + parser  
- [ ] Exception detection prompt + parser
- [ ] `UserPromptSubmit` hook with detection
- [ ] Decision/Correction/Exception node creation
- [ ] Basic relationship linking
- [ ] **Git history importer** (commits → Touch events, with file co-occurrence)
- [ ] **Commit message analyzer** (extract decisions/rationale from commits)

**Deliverable**: Live capture working + git history providing trajectory skeleton

#### Phase 3: Pattern Emergence (Week 3)

**Goal**: Co-occurrence patterns and precedent linking

Build:
- [ ] Touch co-occurrence analysis
- [ ] Decision pattern similarity
- [ ] Precedent chain detection
- [ ] Structural equivalence (within project)
- [ ] Background pattern update job
- [ ] `query_context` tool
- [ ] **Pattern bootstrap from backfilled data**

**Deliverable**: Context surfacing works, bootstrapped by historical data

#### Phase 4: Cross-Project Intelligence (Week 4)

**Goal**: Cross-project patterns and simulation

Build:
- [ ] Project relationship configuration
- [ ] Cross-project structural equivalence
- [ ] Shared constraint handling
- [ ] `search_precedent` tool
- [ ] `trace_decision` tool
- [ ] `simulate_change` tool (basic)
- [ ] **Cross-project backfill linking** (find connections in imported data)

**Deliverable**: Cross-project context and precedent search

#### Phase 5: Polish & World Model (Week 5)

**Goal**: Production ready with simulation capability

Build:
- [ ] Comprehensive tests
- [ ] Documentation
- [ ] Simulation refinement
- [ ] Performance optimization
- [ ] Migration from ccmemory
- [ ] `find_structural_equivalents` tool
- [ ] **Backfill quality report** (gaps, low-confidence imports, suggested manual review)

**Deliverable**: Complete context graph with "what if" capability

---

### Graph Maturity Stages

The graph evolves through distinct stages. Each stage unlocks different capabilities.

#### Stage 0: Empty → Backfilled (Day 1)

**Data**: Imported decision logs, conversation logs, git history
**Node count**: 50-500 depending on project history
**What works**:
- Basic search over imported decisions
- File co-occurrence from git (which files change together)
- Keyword search on decision rationale

**What doesn't work yet**:
- Precedent chains (need live decisions to link)
- Corrections (must be captured live)
- Exception patterns (must be captured live)

**User experience**: "I can search my past decisions, but context isn't surfaced automatically yet."

#### Stage 1: Sparse Live Data (Sessions 1-20)

**Data**: Backfill + first few weeks of live capture
**Node count**: 100-700
**What works**:
- Live decisions linking to backfilled precedent
- Corrections being recorded (high value!)
- Basic "what was I working on" queries
- File touch patterns starting to form

**What doesn't work yet**:
- Co-occurrence patterns too sparse for reliable inference
- Structural equivalence unreliable
- Simulation not meaningful

**User experience**: "Claude remembers corrections and recent decisions. Starting to feel useful."

#### Stage 2: Pattern Formation (Sessions 20-50)

**Data**: Enough trajectories for statistical patterns
**Node count**: 300-1500
**What works**:
- Co-occurrence patterns become reliable
- `query_context` starts surfacing relevant past work
- Precedent search finds meaningful matches
- Decision traces become followable

**What doesn't work yet**:
- Cross-project patterns (unless both projects have 20+ sessions)
- Simulation still low confidence
- Structural equivalence within project only

**User experience**: "Context surfacing is noticeably helpful. I'm repeating myself less."

#### Stage 3: Mature Graph (Sessions 50-100)

**Data**: Rich trajectory history
**Node count**: 1000-5000
**What works**:
- Reliable precedent chains
- Cross-project structural equivalence
- `trace_decision` gives meaningful provenance
- Exception patterns are searchable
- `simulate_change` becomes useful (medium confidence)

**User experience**: "The graph knows why things are the way they are. Cross-project insights are appearing."

#### Stage 4: World Model (Sessions 100+)

**Data**: Deep organizational memory
**Node count**: 3000+
**What works**:
- High-confidence simulation
- "What if" queries are reliable
- Structural equivalence finds non-obvious connections
- Exception → Rule evolution is trackable
- The graph is genuinely a world model

**User experience**: "I trust the graph's predictions. It knows things I've forgotten."

---

### Backfilling Strategy

Backfilling is critical for bootstrapping value. Without it, the graph is empty for weeks while you wait for live data to accumulate.

#### What Can Be Backfilled

| Source | What it provides | Confidence | Effort |
|--------|-----------------|------------|--------|
| **Decision logs** (markdown) | Decision nodes with rationale | High | Low |
| **Conversation logs** | Sessions, some decisions/corrections | Medium | Medium |
| **Git history** | Touch events, file co-occurrence | High | Low |
| **Commit messages** | Decision hints, rationale fragments | Medium | Low |
| **CLAUDE.md / docs** | Rules, constraints, some decisions | Medium | Medium |
| **Slack/notes export** | Exception context, tribal knowledge | Low-Medium | High |

#### Decision Log Importer

Your existing decision logs are the highest-value backfill source.

```python
# Input: Your decision log markdown
"""
## 2024-01-15: Use F1 scoring for extraction accuracy

**Context**: Need to measure how well the LLM extracts family systems data

**Options considered**:
- Exact match (too strict)
- BLEU score (designed for translation)
- F1 score (precision/recall balance)

**Decision**: F1 score with entity-level matching

**Rationale**: Handles partial extractions well, standard in NER literature
"""

# Output: Decision node
(:Decision {
  id: "decision-2024-01-15-f1-scoring",
  timestamp: datetime("2024-01-15"),
  description: "Use F1 scoring for extraction accuracy",
  options_considered: ["Exact match", "BLEU score", "F1 score"],
  choice: "F1 score with entity-level matching",
  rationale: "Handles partial extractions well, standard in NER literature",
  source: "backfill:decision-log",
  confidence: 0.9
})
```

#### Conversation Log Importer

If you have raw conversation logs from Claude Code sessions:

```python
# Parse conversation for:
# 1. Session boundaries
# 2. Files mentioned/touched
# 3. Decision-like exchanges
# 4. Correction patterns (user contradicting Claude)

def import_conversation(log_path):
    conversations = parse_conversations(log_path)
    
    for conv in conversations:
        # Create session node
        session = create_session(conv.timestamp, conv.project)
        
        # Extract file touches
        for file_mention in extract_file_mentions(conv):
            create_touch(session, file_mention)
        
        # Attempt decision extraction (lower confidence than live)
        for exchange in conv.exchanges:
            if looks_like_decision(exchange):
                create_decision(
                    session, 
                    exchange,
                    confidence=0.6,  # Lower than live capture
                    source="backfill:conversation"
                )
            
            if looks_like_correction(exchange):
                create_correction(
                    session,
                    exchange,
                    confidence=0.7,
                    source="backfill:conversation"
                )
```

#### Git History Importer

Git provides a rich source of trajectory data:

```python
def import_git_history(repo_path, since=None):
    commits = get_commits(repo_path, since=since)
    
    for commit in commits:
        # Each commit is like a mini-session
        session = create_session(
            timestamp=commit.timestamp,
            source="backfill:git",
            summary=commit.message
        )
        
        # Files changed = touches
        for file in commit.files_changed:
            create_touch(session, file, action=file.change_type)
        
        # Co-occurrence: files changed together
        for file_a, file_b in combinations(commit.files_changed, 2):
            increment_cooccurrence(file_a, file_b)
        
        # Try to extract decision from commit message
        if commit.message_suggests_decision():
            create_decision(
                session,
                description=extract_decision_from_message(commit.message),
                confidence=0.5,  # Commit messages are terse
                source="backfill:git"
            )
```

**Co-occurrence from git is particularly valuable**: Files that frequently change together in commits are related. This gives you structural patterns immediately, before any live sessions.

#### CLAUDE.md / Documentation Importer

Your existing context files contain embedded decisions and rules:

```python
def import_claude_md(file_path, project):
    content = parse_markdown(file_path)
    
    for section in content.sections:
        # Rules become constraints or codified exceptions
        if section.looks_like_rule():
            create_rule(
                description=section.content,
                source="backfill:claude-md",
                confidence=0.8
            )
        
        # "We do X because Y" patterns are decisions
        if section.contains_rationale():
            create_decision(
                description=section.extract_decision(),
                rationale=section.extract_rationale(),
                source="backfill:claude-md",
                confidence=0.7
            )
```

#### Backfill Quality and Confidence

All backfilled data gets marked with:
- `source`: Where it came from (e.g., "backfill:decision-log", "backfill:git")
- `confidence`: How reliable the extraction is
- `needs_review`: Flag for human verification

```cypher
// Query for low-confidence backfilled data that needs review
MATCH (d:Decision)
WHERE d.source STARTS WITH "backfill:" 
  AND d.confidence < 0.7
RETURN d.description, d.source, d.confidence
ORDER BY d.confidence ASC
```

#### Backfill CLI Commands

```bash
# Import decision logs
ccmemory-graph backfill decisions ./decisions/*.md --project btcopilot

# Import from git history
ccmemory-graph backfill git ~/projects/btcopilot --since 2024-01-01

# Import conversation logs
ccmemory-graph backfill conversations ~/.claude/logs/ --project btcopilot

# Import existing CLAUDE.md and docs
ccmemory-graph backfill docs ~/projects/btcopilot --include "CLAUDE.md,docs/*.md"

# See backfill status and quality
ccmemory-graph backfill status

# Review low-confidence imports
ccmemory-graph backfill review --confidence-below 0.7
```

#### Bootstrapping Sequence

Recommended order for a new project:

1. **Git history first**: Gives you file co-occurrence patterns immediately
2. **Decision logs**: High-value, high-confidence decisions
3. **CLAUDE.md / docs**: Captures codified rules and constraints  
4. **Conversation logs** (if available): Lower confidence but adds trajectory data
5. **Start live capture**: New sessions link to backfilled precedent

After backfill, run pattern analysis:

```bash
# Analyze patterns in backfilled data
ccmemory-graph analyze --rebuild-cooccurrence --link-precedents

# Generate backfill quality report
ccmemory-graph backfill report > backfill-quality.md
```

---

### Capability × Maturity Matrix

| Capability | Stage 0 (Backfill) | Stage 1 (Sparse) | Stage 2 (Forming) | Stage 3 (Mature) | Stage 4 (World Model) |
|------------|-------------------|------------------|-------------------|------------------|----------------------|
| Search decisions | ✅ Works | ✅ Works | ✅ Works | ✅ Works | ✅ Works |
| File co-occurrence | ✅ From git | ✅ Improving | ✅ Reliable | ✅ Reliable | ✅ Reliable |
| Correction memory | ❌ N/A | ✅ Recording | ✅ Useful | ✅ Valuable | ✅ Valuable |
| `query_context` | ⚠️ Basic | ⚠️ Sparse | ✅ Useful | ✅ Good | ✅ Excellent |
| `search_precedent` | ⚠️ Backfill only | ✅ Improving | ✅ Useful | ✅ Good | ✅ Excellent |
| `trace_decision` | ⚠️ Gaps | ⚠️ Partial | ✅ Mostly works | ✅ Reliable | ✅ Complete |
| Cross-project | ❌ | ❌ | ⚠️ Starting | ✅ Useful | ✅ Valuable |
| `simulate_change` | ❌ | ❌ | ⚠️ Low confidence | ✅ Medium | ✅ High confidence |
| Structural equivalence | ❌ | ❌ | ⚠️ Within project | ✅ Cross-project | ✅ Non-obvious finds |

---

## Success Metrics

### Primary: Does it reduce re-explanation?

Measure: How often does the user have to explain the same thing twice?

- **Baseline**: Track corrections and re-explanations in first 2 weeks
- **Target**: 50% reduction by week 6

### Secondary: Decision trace completeness

Measure: Can we answer "why is it this way?" for code and architecture?

- **Test**: Random sample of 10 files/decisions per week
- **Target**: Traceable provenance for 70% by week 6

### Tertiary: Simulation usefulness

Measure: Do `simulate_change` predictions match reality?

- **Test**: Compare predictions vs. actual outcomes
- **Target**: 60% accuracy on blast radius by week 8

### Cross-Project Value

Measure: Does precedent from project A help project B?

- **Test**: Track when cross-project context is surfaced and used
- **Target**: At least 1 useful cross-project insight per week by week 6

---

## Example: Patrick's Use Case

### Scenario 1: Starting Work on btcopilot

```
Session starts...

Context Graph surfaces:
- Last session: Working on extraction service retry logic
- Relevant precedent: Similar retry pattern used in auth-service (Decision #47)
- Active exception: "Using synchronous calls for clinical model (Exception #12, 
  justification: race conditions in async caused data corruption)"
- Cross-project: RSU vesting in 6 months (Constraint #3) affects launch timeline

Claude begins with this context automatically loaded.
```

### Scenario 2: User Corrects Claude

```
Claude: "I'll add the retry logic with exponential backoff..."
User: "No, we tried that and it caused cascading failures. Use fixed delays with jitter."

Correction detected:
- Wrong belief: "Exponential backoff is appropriate here"
- Right belief: "Fixed delays with jitter, because exponential caused cascading failures"
- Severity: significant
- Context: extraction-service, retry logic

This correction is now searchable. Next time retry logic comes up anywhere,
this precedent surfaces.
```

### Scenario 3: Querying Precedent

```
User: "How did we handle error recovery in similar services?"

search_precedent("error recovery patterns")

Results:
1. Decision #47 (auth-service): "Fixed retry with circuit breaker"
   - Outcome: Successful, reduced incidents by 80%
   - Trajectory: 3 sessions, involved files X, Y, Z
   
2. Exception #12 (clinical-model): "Sync instead of async"
   - Justification: Race conditions in async
   - Still active, conditions: "any clinical data operations"
   
3. Decision #89 (career-builder): "Graceful degradation for API calls"
   - Structural equivalent: Similar service architecture
   - Outcome: Working well
```

### Scenario 4: Simulating a Change

```
User: "What if we switch the extraction service to async?"

simulate_change("switch extraction-service to async")

Prediction:
- Files likely affected: extraction.py, clinical_model.py, tests/
- Patterns disrupted: Sync-only pattern established in Exception #12
- Similar past change: Decision #23 (attempted async, rolled back)
  
Risks:
- HIGH: Race conditions in clinical data (basis: Exception #12, Correction #34)
- MEDIUM: Test suite assumes sync behavior (basis: trajectory patterns)

Recommendation: If async needed, address race conditions first. 
See Exception #12 for original justification.
```

---

## Migration from ccmemory

### Automatic Import

```bash
ccmemory-graph migrate --from ~/.ccmemory/
```

This will:
1. Parse existing markdown files
2. Create initial trajectory events (as "imported" type)
3. Attempt to link decisions and patterns
4. Preserve session history

### Coexistence

ccmemory-graph can run alongside ccmemory during transition:
- Both capture data
- Graph is primary source of truth
- Markdown files remain as human-readable backup

---

## Theoretical Foundation

This architecture is based on insights from:

1. **"AI's trillion-dollar opportunity: Context graphs"** (Gupta & Garg)
   - Decision traces vs. state capture
   - The fragmentation tax
   - Systems of agents sitting in the execution path

2. **"How to build a context graph"** (Koratana)
   - The two clocks problem
   - Agents as informed walkers  
   - Schema as output, not input
   - World models, not retrieval systems

Key principles applied:
- **Event-sourced**: Append-only trajectory capture
- **Emergent ontology**: Structure discovered through walks
- **Precedent as first-class**: Exceptions and decisions are searchable
- **Simulation capability**: The test of understanding

---

## References

- [AI's trillion-dollar opportunity: Context graphs](https://foundationcapital.com) — Gupta & Garg
- [How to build a context graph](https://akoratana.com) — Koratana  
- [Neo4j official MCP server](https://github.com/neo4j/mcp)
- [MCP specification](https://modelcontextprotocol.io)
- [ccmemory](https://github.com/patrickkidd/ccmemory)
- [node2vec: Scalable Feature Learning for Networks](https://arxiv.org/abs/1607.00653)
- [World Models](https://worldmodels.github.io/) — Ha & Schmidhuber