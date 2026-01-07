# Why Graphs? Deep Dive

This document expands on the [Why Graphs?](PROJECT_VISION.md#why-graphs-not-just-search) section in the project vision.

## The Core Question

Why use a graph database (Neo4j) instead of just a vector database for AI memory? After all, vector search is the standard approach for RAG systems.

## What Vector Search Does Well

Vector search excels at **discovery**: finding things that look similar to a query. You encode text as numbers (embeddings), then find the closest matches. This works for:

- "Find documents about authentication"
- "What have I seen that looks like this error?"
- "Show me similar code patterns"

## What Vector Search Cannot Do

### 1. Guarantee Completeness

Vector search returns the **top-k most similar** results. If you ask for "all decisions about authentication," you get the 10 (or 50) that scored highest. But what if decision #11 is critical? What if a decision used different terminology ("login" vs "auth") and scored lower?

Search is probabilistic. You get "probably relevant" results. For comprehensive review — audits, impact analysis, compliance — "probably" isn't good enough.

### 2. Count or Aggregate

"How many exceptions have we made to the 'always use middleware' rule?"

Vector search can't answer this. It can find things that *look like* exceptions, but it can't count them. It doesn't know what an "exception" is structurally — it just sees text similarity.

A graph query: `MATCH (r:Rule {name: 'always use middleware'})<-[:EXCEPTION_TO]-(e:Exception) RETURN count(e)` — gives you the exact number.

### 3. Trace Reasoning Chains

"Why did we decide to use JWT instead of sessions?"

The answer isn't in one document. It's a chain: there was a scaling requirement → that led to evaluating stateless options → JWT was chosen because X → but then we discovered Y → so we added Z as a workaround.

Vector search can find the final decision. It can't trace the path that led there. A graph traversal follows the actual relationships: `MATCH path = (d:Decision)-[:LED_TO|BASED_ON|CORRECTED_BY*]->(n) RETURN path`

### 4. Find Dependencies (Forward Tracing)

"What breaks if I change the auth system?"

Vector search might find things that *mention* auth. But what about things that don't mention auth explicitly but depend on a decision that depends on auth? The blast radius isn't about textual similarity — it's about structural dependency.

Graph traversal: `MATCH (d:Decision {topic: 'auth'})<-[:DEPENDS_ON*]-(dependent) RETURN dependent`

## Domain 1 vs Domain 2: Different Graph Value

### Domain 1: Your Specifics (Event-Sourced Graph)

Domain 1 stores your decisions, corrections, insights, exceptions, failed approaches. These have **explicit typed relationships**:

- Decision → CORRECTED_BY → Correction
- Rule → HAS_EXCEPTION → Exception
- Hypothesis → SUPPORTED_BY → Observation
- Decision → LED_TO → Decision (precedent chains)

The graph value here is **reasoning support**:
- Trace why a decision was made
- Count exceptions to validate/invalidate rules
- Follow precedent chains across projects
- Find blast radius of changes

Vector search alone would give you "similar-looking decisions" but miss the structural relationships.

### Domain 2: Reference Knowledge (Currently Partial)

Domain 2 currently has only Chunk nodes (text fragments from documents) with vector embeddings. This is essentially vector-search-only — no graph structure.

**The vision** (from PROJECT_VISION.md) includes:
- Concept nodes with relationships between concepts
- Claim nodes that SUPPORT or CONTRADICT each other
- Hypothesis nodes BASED_ON observations
- KnowledgeGap nodes for explicit unknowns
- Source tracking with confidence levels

**The bridge layer** connects Domain 1 observations to Domain 2 concepts:
- Observation -[:MAY_BE_INSTANCE_OF]-> Concept (proposed)
- Observation -[:INSTANCE_OF]-> Concept (validated)
- Decision -[:APPLIES_FRAMEWORK]-> Concept

This is where the two domains combine: your specific experience (Domain 1) gets connected to general knowledge (Domain 2), enabling questions like:
- "My observation X — does the literature say anything about this pattern?"
- "This framework concept — where have I actually applied it?"

## The Completeness Problem

This is the fundamental issue with vector-only approaches:

| Question Type | Vector Search | Graph |
|---------------|---------------|-------|
| "Find related" | Top-k by similarity | All connected nodes |
| "Find all X" | Can't guarantee completeness | Exhaustive by structure |
| "Count X" | Can't count | Exact count |
| "Why X?" | Can't trace reasoning | Follow relationship chain |
| "What depends on X?" | Textual similarity only | Structural dependencies |

**The proactive insights** that make ccmemory valuable require graph operations:
- "3 exceptions to the middleware rule" — exact count via relationship traversal
- "4 supporting data points for hypothesis" — count evidence edges
- "Monday deployments have 2x issues" — aggregate over deployment→outcome relationships

## ccmemory Uses Both

Vector search for **discovery**: "What's potentially relevant to this topic?"
Graph traversal for **reasoning**: "Given what's relevant, what can we infer?"

The cognitive multiplier comes from the graph — that's where "probably relevant" becomes "definitely complete."

## Why Not Just Write to CLAUDE.md?

An alternative to storing project facts in the graph: automatically append learned conventions to the target project's CLAUDE.md file. This is tempting because CLAUDE.md is already loaded at session start with zero latency.

| Dimension | Graph Storage | CLAUDE.md Auto-Write |
|-----------|---------------|---------------------|
| **Latency** | MCP query (~10-50ms) | Zero (already in context) |
| **Dependencies** | Neo4j + MCP server must run | Filesystem only |
| **Discoverability** | Requires tools to view/edit | Human-readable, git-tracked |
| **Semantic Search** | Yes - find related facts | No - exact text only |
| **Deduplication** | Embedding similarity (semantic) | String matching only |
| **Cross-Project** | Can share facts between projects | Per-project only |
| **Telemetry** | When learned, how often used | None |
| **Scalability** | Thousands of facts with indexing | ~10KB practical limit |

**Decision**: Graph storage chosen because:
1. Semantic deduplication prevents "uses pytest" and "we use pytest for testing" from being stored as separate facts
2. Cross-project learning enables "you used this pattern in ProjectX" insights
3. Telemetry supports the cognitive coefficient metric
4. Scalability matters for long-running projects with accumulated knowledge

**Tradeoff accepted**: Facts require MCP server running to be surfaced. If server is down, Claude Code falls back to stateless behavior.

### Project Facts Are Domain 1, Not Domain 2

A common confusion: "We use pytest" feels like reference knowledge (Domain 2). It's actually Domain 1:

| Characteristic | Domain 1 | Domain 2 |
|----------------|----------|----------|
| **Confidence** | High - user stated directly | Medium - needs validation |
| **Source** | Conversation | Imported docs, web search |
| **Entity resolution** | None needed | Bounded (concepts have stable definitions) |
| **Example** | "We use pytest" | "pytest is a Python testing framework" |

"We use pytest" is **your project's convention** - high confidence, stated directly, no ambiguity. The general knowledge that "pytest is a testing framework" would be Domain 2.

This matters for storage: Domain 1 facts don't need the bridge layer validation that Domain 2 concepts require. When you say "we use uv", that's immediately true for your project - no proposal/validation cycle needed.

## Current State vs Vision

**Implemented:**
- Domain 1 full graph structure (Session, Decision, Correction, Exception, Insight, Question, FailedApproach, Reference)
- Domain 2 Chunk nodes with vector embeddings (partial)
- Vector indexes on Domain 1 nodes for semantic search

**Not yet implemented:**
- Domain 2 Concept/Claim/Hypothesis/KnowledgeGap nodes
- Bridge layer relationships
- Full graph structure for Domain 2

The backfill system operates on the current implementation — it populates Domain 1 nodes and Domain 2 Chunks, not the full vision's Concept graph.
