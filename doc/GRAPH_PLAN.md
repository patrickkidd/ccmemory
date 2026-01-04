# ccmemory: Automatic Knowledge Graph Memory for Claude Code

## Executive Summary

An extension to [ccmemory](https://github.com/patrickkidd/ccmemory) that replaces flat markdown context files with an LLM-populated Neo4j knowledge graph. The graph automatically captures relationships, patterns, and connections that humans wouldn't think to encode, and surfaces relevant context across multiple related projects.

**Key differentiator**: The LLM both builds AND consumes the graph—it captures subtle relationships (implicit dependencies, terminology drift, unstated assumptions) that manual documentation misses.

---

## Problem Statement

### Current ccmemory limitations

1. **Meta-complexity**: The system designed to help Claude remember has itself become too complex to remember. Users need an external brain to manage the external brain.

2. **Flat file blindness**: Markdown files can't encode relationships. Connections between decisions, components, and constraints are implicit at best.

3. **Manual relevance filtering**: Users must decide which context files to load. They can't hold all the connections in their heads, so Claude often works with incomplete context.

4. **No cross-project awareness**: Two related projects (e.g., app code + business strategy) can't share context or surface patterns that span both.

5. **Contradiction hiding**: A decision in `decisions/auth.md` that conflicts with `architecture/api-design.md` remains invisible because the connection isn't explicit.

### What a knowledge graph solves

- **Relational queries**: "What components depend on the extraction service?" becomes traversable
- **Emergent context surfacing**: Working on component X automatically surfaces related decisions, gotchas, and dependencies
- **Temporal reasoning**: "What changed since I last touched this module?" becomes queryable
- **Cross-project patterns**: Shared architectural lessons, business constraints affecting technical decisions
- **Contradiction detection**: Typed relationships can surface conflicts
- **Provenance chains**: component → decision → constraint → business requirement

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     User's Projects                          │
├─────────────────┬─────────────────┬─────────────────────────┤
│   btcopilot/    │  career-builder/│    other-project/       │
│   Claude Code   │   Claude Code   │      Claude Code        │
└────────┬────────┴────────┬────────┴────────┬────────────────┘
         │                 │                  │
         └─────────────────┼──────────────────┘
                           │
                    ┌──────▼──────┐
                    │  ccmemory   │
                    │   plugin    │
                    │  (hooks)    │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  Neo4j MCP  │
                    │   Server    │
                    │  (custom)   │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   Neo4j     │
                    │  (Docker)   │
                    │  + Volume   │
                    └─────────────┘
```

### Components

1. **Neo4j in Docker**: Persistent graph storage with APOC plugins
2. **Custom MCP Server**: Knowledge-graph-specific operations (not just raw Cypher)
3. **ccmemory Plugin Extension**: Hooks that trigger graph updates and queries
4. **LLM Graph Builder**: Prompts that extract entities and relationships from conversations

---

## Technology Decisions

### Why Neo4j (not SQLite or JSON)

| Requirement | JSON | SQLite | Neo4j |
|-------------|------|--------|-------|
| Multi-hop traversal | ❌ Manual | ⚠️ Recursive CTEs | ✅ Native |
| Cross-project queries | ❌ File merging | ⚠️ Attached DBs | ✅ Labels/namespaces |
| Relationship types | ❌ Manual encoding | ⚠️ Join tables | ✅ First-class |
| Pattern matching | ❌ Code | ⚠️ Complex SQL | ✅ Cypher |
| Contradiction detection | ❌ Manual | ⚠️ Triggers | ✅ Graph algorithms |
| Scale to 1000s of nodes | ⚠️ Context limits | ✅ | ✅ |

### Why custom MCP server (not official neo4j-mcp)

The official `mcp-neo4j-cypher` server is great for raw database access, but we need higher-level operations:

- `ingest_insight`: Parse conversation, extract entities/relationships, merge into graph
- `get_relevant_context`: Given current task, return subgraph of related nodes
- `detect_contradictions`: Find conflicting information across projects
- `trace_provenance`: Follow decision chains backward to constraints/requirements
- `suggest_connections`: Surface nodes that might be related but aren't linked

### Why Docker with volume

- **Zero-config persistence**: Volume survives container restarts
- **Isolation**: Doesn't pollute user's system
- **Portability**: Same setup works everywhere
- **Easy backup**: `docker cp` or volume backup
- **Version pinning**: Consistent Neo4j version across users

---

## Data Model

### Node Types

```cypher
// Core entities
(:Project {name, path, description})
(:Component {name, type, path, project})
(:Decision {id, title, rationale, date, status})
(:Constraint {type, description, source})
(:Concept {name, definition, domain})

// Knowledge entities
(:Insight {content, confidence, source_conversation, timestamp})
(:Pattern {name, description, occurrences})
(:Assumption {content, explicit: boolean, validated: boolean})
(:Gotcha {description, severity, affected_components})

// Session entities
(:Conversation {id, project, timestamp, summary})
(:Task {description, status, related_files})
```

### Relationship Types

```cypher
// Structural
(Component)-[:BELONGS_TO]->(Project)
(Component)-[:DEPENDS_ON {type: "runtime|build|optional"}]->(Component)
(Component)-[:IMPLEMENTS]->(Concept)

// Decisional
(Decision)-[:AFFECTS]->(Component)
(Decision)-[:CONSTRAINED_BY]->(Constraint)
(Decision)-[:SUPERSEDES]->(Decision)
(Decision)-[:INFORMED_BY]->(Insight)

// Knowledge
(Insight)-[:EXTRACTED_FROM]->(Conversation)
(Insight)-[:RELATES_TO]->(Component|Decision|Concept)
(Insight)-[:CONTRADICTS {confidence}]->(Insight)
(Assumption)-[:UNDERLIES]->(Component|Decision)
(Gotcha)-[:AFFECTS]->(Component)
(Pattern)-[:OBSERVED_IN]->(Project)

// Cross-project
(Project)-[:RELATED_TO {type: "business|technical|shared_resource"}]->(Project)
(Constraint)-[:APPLIES_TO]->(Project)  // e.g., RSU vesting affects both projects
```

### Example: Patrick's use case

```cypher
// btcopilot app
CREATE (bt:Project {name: "btcopilot", path: "/path/to/btcopilot"})
CREATE (ext:Component {name: "extraction-service", type: "service"})
CREATE (f1:Component {name: "f1-scoring", type: "module"})
CREATE (clinical:Concept {name: "Bowen family systems", domain: "psychology"})

// Career builder
CREATE (cb:Project {name: "career-builder", path: "/path/to/career"})
CREATE (rsu:Constraint {type: "financial", description: "RSU vesting schedule"})
CREATE (timeline:Constraint {type: "temporal", description: "App store launch timeline"})

// Cross-project relationships
CREATE (bt)-[:RELATED_TO {type: "business"}]->(cb)
CREATE (timeline)-[:APPLIES_TO]->(bt)
CREATE (rsu)-[:CONSTRAINS]->(timeline)

// Insight example
CREATE (i:Insight {
  content: "Extraction prompt changes require F1 baseline updates",
  confidence: 0.9,
  timestamp: datetime()
})
CREATE (i)-[:RELATES_TO]->(ext)
CREATE (i)-[:RELATES_TO]->(f1)
```

---

## MCP Server Specification

### Tools

#### `graph_ingest`
Extract entities and relationships from conversation content and merge into graph.

```typescript
interface GraphIngestParams {
  conversation_id: string;
  content: string;           // The conversation text to analyze
  project: string;           // Current project context
  extraction_mode: "auto" | "correction" | "decision" | "insight";
}

interface GraphIngestResult {
  nodes_created: number;
  nodes_updated: number;
  relationships_created: number;
  entities_extracted: Entity[];
  confidence_scores: Record<string, number>;
}
```

#### `graph_query_context`
Get relevant context for current task.

```typescript
interface QueryContextParams {
  task_description: string;
  current_file?: string;
  project: string;
  max_hops?: number;         // Default: 2
  include_cross_project?: boolean;
}

interface QueryContextResult {
  relevant_nodes: Node[];
  relevant_relationships: Relationship[];
  suggested_files: string[];
  warnings: string[];        // Contradictions, stale info, etc.
}
```

#### `graph_detect_issues`
Find contradictions, stale information, and gaps.

```typescript
interface DetectIssuesParams {
  scope: "project" | "all";
  project?: string;
  issue_types?: ("contradiction" | "stale" | "orphan" | "cycle")[];
}

interface DetectIssuesResult {
  contradictions: Contradiction[];
  stale_nodes: Node[];
  orphan_nodes: Node[];      // Unconnected information
  circular_dependencies: Path[];
}
```

#### `graph_trace_provenance`
Follow the chain from a component back to its origins.

```typescript
interface TraceProvenanceParams {
  node_id: string;
  direction: "upstream" | "downstream" | "both";
  max_depth?: number;
}

interface TraceProvenanceResult {
  path: Node[];
  relationships: Relationship[];
  narrative: string;         // LLM-generated explanation of the chain
}
```

#### `graph_suggest_connections`
Surface potential relationships that aren't yet encoded.

```typescript
interface SuggestConnectionsParams {
  node_id?: string;          // Specific node, or null for global
  project?: string;
  min_confidence?: number;
}

interface SuggestConnectionsResult {
  suggestions: {
    source: Node;
    target: Node;
    suggested_relationship: string;
    confidence: number;
    reasoning: string;
  }[];
}
```

### Resources

#### `graph://schema`
Current graph schema (node types, relationship types, counts).

#### `graph://project/{name}`
Summary of a specific project's graph.

#### `graph://stats`
Overall graph statistics.

---

## Plugin Integration

### Hook Updates

Extend ccmemory's existing hooks:

#### `SessionStart`
```
1. Load session.md (existing behavior)
2. NEW: Query graph for relevant context based on:
   - Recent conversation topics
   - Current working directory
   - Open files (if detectable)
3. NEW: Surface any detected issues (contradictions, stale info)
```

#### `UserPromptSubmit`
```
1. Executive oversight analysis (existing behavior)
2. NEW: If important information detected:
   - Call graph_ingest to extract and store
   - Update relationships to existing nodes
   - Flag low-confidence extractions for user review
3. NEW: If correction detected:
   - Higher priority ingestion
   - Mark contradicted information as superseded
```

#### `Stop`
```
1. Log session (existing behavior)
2. NEW: Call graph_ingest on full conversation
3. NEW: Create Conversation node with summary
4. NEW: Run graph_detect_issues, log any new problems
```

### New Skill: `knowledge-graph`

```markdown
---
name: knowledge-graph
description: Manage and query the project knowledge graph for context, relationships, and insights
---

# Knowledge Graph Skill

## When to Use
- Starting work on a component (get relevant context)
- Making architectural decisions (check for conflicts)
- Investigating why something is built a certain way (trace provenance)
- After learning something important (ensure it's captured)

## Available Operations

### Get Context
Before starting any significant task, query for relevant context:
```
Use graph_query_context with task description and current file
```

### Record Important Information
When the user tells you something important:
```
Use graph_ingest with extraction_mode appropriate to content type
```

### Check for Issues
Periodically, especially before major changes:
```
Use graph_detect_issues to surface contradictions or stale info
```

### Understand History
When you need to know why something exists:
```
Use graph_trace_provenance to follow the decision chain
```
```

---

## Extraction Prompts

### Entity Extraction Prompt

```markdown
Analyze this conversation and extract structured knowledge.

CONVERSATION:
{conversation_content}

PROJECT CONTEXT:
{project_name} - {project_description}

Extract the following if present:

1. COMPONENTS: Software components, modules, services mentioned
   - name, type (service|module|component|config), relationships to other components

2. DECISIONS: Architectural or design decisions made or discussed
   - title, rationale, affected components, constraints considered

3. CONSTRAINTS: Limitations, requirements, rules that affect decisions
   - type (technical|business|regulatory|temporal|financial), description, source

4. INSIGHTS: Important realizations, learnings, or discoveries
   - content, confidence (0-1), what it relates to

5. ASSUMPTIONS: Things being assumed true (especially implicit ones)
   - content, explicit (true/false), validated (true/false)

6. GOTCHAS: Pitfalls, edge cases, things that trip people up
   - description, severity (low|medium|high), affected components

7. CORRECTIONS: If the user corrected Claude's understanding
   - what was wrong, what is correct, what nodes need updating

For each entity, also identify RELATIONSHIPS to:
- Other entities in this extraction
- Entities likely already in the graph (reference by name)

Output as JSON:
{
  "entities": [...],
  "relationships": [...],
  "confidence_notes": "..."
}
```

### Relationship Inference Prompt

```markdown
Given these existing graph nodes and a new insight, suggest relationships.

EXISTING NODES (sample):
{relevant_existing_nodes}

NEW INSIGHT:
{new_insight}

For each potential relationship:
1. Source and target nodes
2. Relationship type (from allowed types: DEPENDS_ON, AFFECTS, IMPLEMENTS, etc.)
3. Confidence score (0-1)
4. Reasoning for the connection

Also flag:
- Potential contradictions with existing information
- Nodes that might need updating based on this insight
- Implicit assumptions this reveals
```

---

## Docker Configuration

### docker-compose.yml

```yaml
version: '3.8'

services:
  neo4j:
    image: neo4j:5-community
    container_name: ccmemory-neo4j
    ports:
      - "7474:7474"   # HTTP browser
      - "7687:7687"   # Bolt protocol
    volumes:
      - ccmemory_data:/data
      - ccmemory_logs:/logs
      - ./neo4j/plugins:/plugins
      - ./neo4j/conf:/conf
    environment:
      - NEO4J_AUTH=neo4j/${NEO4J_PASSWORD:-ccmemory}
      - NEO4J_PLUGINS=["apoc"]
      - NEO4J_dbms_security_procedures_unrestricted=apoc.*
      - NEO4J_dbms_memory_heap_initial__size=512m
      - NEO4J_dbms_memory_heap_max__size=1G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:7474"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

volumes:
  ccmemory_data:
    name: ccmemory_neo4j_data
  ccmemory_logs:
    name: ccmemory_neo4j_logs
```

### Initialization Script

```cypher
// constraints.cypher - Run on first startup

// Uniqueness constraints
CREATE CONSTRAINT project_name IF NOT EXISTS FOR (p:Project) REQUIRE p.name IS UNIQUE;
CREATE CONSTRAINT component_id IF NOT EXISTS FOR (c:Component) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT decision_id IF NOT EXISTS FOR (d:Decision) REQUIRE d.id IS UNIQUE;
CREATE CONSTRAINT conversation_id IF NOT EXISTS FOR (c:Conversation) REQUIRE c.id IS UNIQUE;

// Indexes for common queries
CREATE INDEX component_name IF NOT EXISTS FOR (c:Component) ON (c.name);
CREATE INDEX component_project IF NOT EXISTS FOR (c:Component) ON (c.project);
CREATE INDEX insight_timestamp IF NOT EXISTS FOR (i:Insight) ON (i.timestamp);
CREATE INDEX decision_date IF NOT EXISTS FOR (d:Decision) ON (d.date);

// Full-text search indexes
CREATE FULLTEXT INDEX insight_content IF NOT EXISTS FOR (i:Insight) ON EACH [i.content];
CREATE FULLTEXT INDEX decision_search IF NOT EXISTS FOR (d:Decision) ON EACH [d.title, d.rationale];
```

---

## Installation & Setup

### Prerequisites
- Docker and Docker Compose
- Claude Code CLI with plugin support
- Python 3.8+ (for MCP server)

### Quick Start

```bash
# 1. Clone the repository
git clone git@github.com:patrickkidd/ccmemory.git
cd ccmemory

# 2. Start Neo4j
docker-compose up -d

# 3. Wait for Neo4j to be ready
./scripts/wait-for-neo4j.sh

# 4. Initialize the database schema
./scripts/init-db.sh

# 5. Install the Claude Code plugin
claude plugin marketplace add patrickkidd/ccmemory
claude plugin install ccmemory

# 6. Restart Claude Code
```

### Configuration

Create `~/.ccmemory/config.yaml`:

```yaml
neo4j:
  uri: bolt://localhost:7687
  username: neo4j
  password: ccmemory  # Change this!

projects:
  - name: btcopilot
    path: /path/to/btcopilot
    description: "Relationship counseling app with family systems model"
  
  - name: career-builder
    path: /path/to/career
    description: "Career strategy, finances, RSU tracking"
    related_to:
      - btcopilot  # Cross-project relationship

extraction:
  auto_ingest: true
  min_confidence: 0.7
  prompt_for_low_confidence: true

context:
  max_hops: 2
  include_cross_project: true
  max_context_nodes: 50
```

---

## Repository Structure

```
ccmemory/
├── .claude-plugin/
│   └── manifest.json
├── docker/
│   ├── docker-compose.yml
│   └── neo4j/
│       ├── conf/
│       │   └── neo4j.conf
│       └── init/
│           └── constraints.cypher
├── mcp-server/
│   ├── pyproject.toml
│   ├── src/
│   │   └── ccmemory/
│   │       ├── __init__.py
│   │       ├── server.py          # MCP server implementation
│   │       ├── tools/
│   │       │   ├── ingest.py
│   │       │   ├── query.py
│   │       │   ├── detect.py
│   │       │   └── trace.py
│   │       ├── extraction/
│   │       │   ├── prompts.py
│   │       │   └── parser.py
│   │       └── graph/
│   │           ├── client.py      # Neo4j connection
│   │           ├── schema.py      # Node/relationship types
│   │           └── queries.py     # Cypher query templates
│   └── tests/
├── hooks/
│   ├── hooks.json
│   ├── session-start.sh
│   ├── user-prompt.sh
│   └── stop.sh
├── prompts/
│   ├── extract-entities.md
│   ├── infer-relationships.md
│   └── analyze-message.md
├── skills/
│   └── knowledge-graph/
│       └── SKILL.md
├── scripts/
│   ├── wait-for-neo4j.sh
│   ├── init-db.sh
│   ├── backup.sh
│   └── restore.sh
├── templates/
│   └── config.yaml.template
├── examples/
│   ├── sample-graph.cypher
│   └── demo-queries.md
├── CLAUDE.md
├── README.md
├── LICENSE
└── ccmemory.code-workspace
```

---

## Implementation Phases

### Phase 1: Foundation (Week 1)

**Goal**: Working Neo4j + MCP server with basic ingest/query

- [ ] Docker compose setup with Neo4j
- [ ] Database schema and constraints
- [ ] Basic MCP server skeleton (Python + mcp SDK)
- [ ] `graph_ingest` tool (manual JSON input)
- [ ] `graph_query_context` tool (simple Cypher)
- [ ] Test with Claude Desktop before Claude Code integration

### Phase 2: Extraction (Week 2)

**Goal**: LLM-powered entity extraction from conversations

- [ ] Entity extraction prompts
- [ ] Relationship inference prompts
- [ ] Parser for LLM extraction output
- [ ] Confidence scoring
- [ ] Merge logic (update vs. create)
- [ ] Handle corrections (mark superseded)

### Phase 3: Plugin Integration (Week 3)

**Goal**: Integrate with ccmemory hooks

- [ ] Extend SessionStart hook
- [ ] Extend UserPromptSubmit hook
- [ ] Extend Stop hook
- [ ] Knowledge-graph skill
- [ ] Configuration file support
- [ ] Cross-project relationship setup

### Phase 4: Intelligence (Week 4)

**Goal**: Advanced graph operations

- [ ] `graph_detect_issues` tool
- [ ] `graph_trace_provenance` tool
- [ ] `graph_suggest_connections` tool
- [ ] Automatic relevance scoring
- [ ] Context window optimization (don't load too much)

### Phase 5: Polish (Week 5)

**Goal**: Production ready

- [ ] Comprehensive tests
- [ ] Documentation
- [ ] Example configurations
- [ ] Migration guide from ccmemory
- [ ] Backup/restore scripts
- [ ] Performance tuning

---

## Testing Strategy

### Unit Tests
- Entity extraction from sample conversations
- Cypher query generation
- Merge logic correctness

### Integration Tests
- MCP server tool invocations
- Neo4j connection handling
- Hook trigger -> graph update flow

### End-to-End Tests
- Full conversation -> extraction -> storage -> retrieval
- Cross-project context surfacing
- Contradiction detection

### Manual Testing Scenarios
1. Start new project, have conversation about architecture
2. Verify components and decisions appear in graph
3. Start second project, reference first
4. Verify cross-project relationships
5. Make contradictory statement
6. Verify contradiction is detected

---

## Migration from ccmemory

### Automatic Migration Script

For existing ccmemory users:

```bash
./scripts/migrate-from-ccmemory.sh /path/to/project
```

This will:
1. Parse existing `.ccmemory/` files
2. Extract entities from markdown
3. Create graph nodes and relationships
4. Preserve session history

### Coexistence

The graph can run alongside flat markdown files:
- Graph is the primary source of truth
- Markdown files remain as human-readable backup
- Hooks call both systems during transition

---

## Security Considerations

1. **Neo4j credentials**: Use environment variables, not config files
2. **MCP transport**: Local STDIO only (no remote by default)
3. **Conversation content**: Stored in graph, consider sensitivity
4. **Backup encryption**: Optional encrypted backups

---

## Future Enhancements

1. **Web UI**: Browser-based graph visualization
2. **Team sharing**: Shared Neo4j instance for team knowledge
3. **RAG integration**: Use graph for retrieval-augmented generation
4. **Embeddings**: Vector similarity for semantic relationships
5. **Temporal queries**: "What did we know about X on date Y?"
6. **Export**: Generate documentation from graph

---

## Success Metrics

1. **Reduced re-explanation**: Measure how often user has to repeat context
2. **Context accuracy**: Does Claude apply correct, relevant context?
3. **Contradiction catch rate**: How many conflicts detected before causing issues?
4. **Cross-project value**: Do insights from one project help another?
5. **Graph growth**: Is knowledge accumulating over time?

---

## References

- [Neo4j official MCP server](https://github.com/neo4j/mcp)
- [Neo4j MCP memory server](https://github.com/neo4j-contrib/mcp-neo4j)
- [MCP specification](https://modelcontextprotocol.io)
- [ccmemory](https://github.com/patrickkidd/ccmemory)
- [Claude Code plugins](https://docs.anthropic.com/claude-code/plugins)