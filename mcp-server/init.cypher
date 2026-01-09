// === DOMAIN 1: Your Specifics ===
// Per doc/clarifications/1-DAG-with-CROSS-REFS.md: No sessions, organize by timestamp + project

// Constraints
CREATE CONSTRAINT decision_id IF NOT EXISTS FOR (d:Decision) REQUIRE d.id IS UNIQUE;
CREATE CONSTRAINT correction_id IF NOT EXISTS FOR (c:Correction) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT exception_id IF NOT EXISTS FOR (e:Exception) REQUIRE e.id IS UNIQUE;
CREATE CONSTRAINT insight_id IF NOT EXISTS FOR (i:Insight) REQUIRE i.id IS UNIQUE;
CREATE CONSTRAINT question_id IF NOT EXISTS FOR (q:Question) REQUIRE q.id IS UNIQUE;
CREATE CONSTRAINT failedapproach_id IF NOT EXISTS FOR (f:FailedApproach) REQUIRE f.id IS UNIQUE;
CREATE CONSTRAINT reference_id IF NOT EXISTS FOR (r:Reference) REQUIRE r.id IS UNIQUE;
CREATE CONSTRAINT projectfact_id IF NOT EXISTS FOR (pf:ProjectFact) REQUIRE pf.id IS UNIQUE;

// Primary indexes — project + timestamp for all node types
CREATE INDEX decision_project IF NOT EXISTS FOR (d:Decision) ON (d.project);
CREATE INDEX decision_time IF NOT EXISTS FOR (d:Decision) ON (d.timestamp);
CREATE INDEX decision_project_time IF NOT EXISTS FOR (d:Decision) ON (d.project, d.timestamp);
CREATE INDEX decision_status IF NOT EXISTS FOR (d:Decision) ON (d.status);
CREATE INDEX decision_project_status IF NOT EXISTS FOR (d:Decision) ON (d.project, d.status);

CREATE INDEX correction_project IF NOT EXISTS FOR (c:Correction) ON (c.project);
CREATE INDEX correction_time IF NOT EXISTS FOR (c:Correction) ON (c.timestamp);
CREATE INDEX correction_project_time IF NOT EXISTS FOR (c:Correction) ON (c.project, c.timestamp);

CREATE INDEX exception_project IF NOT EXISTS FOR (e:Exception) ON (e.project);
CREATE INDEX exception_time IF NOT EXISTS FOR (e:Exception) ON (e.timestamp);
CREATE INDEX exception_project_time IF NOT EXISTS FOR (e:Exception) ON (e.project, e.timestamp);

CREATE INDEX insight_project IF NOT EXISTS FOR (i:Insight) ON (i.project);
CREATE INDEX insight_time IF NOT EXISTS FOR (i:Insight) ON (i.timestamp);
CREATE INDEX insight_category IF NOT EXISTS FOR (i:Insight) ON (i.category);

CREATE INDEX question_project IF NOT EXISTS FOR (q:Question) ON (q.project);
CREATE INDEX question_time IF NOT EXISTS FOR (q:Question) ON (q.timestamp);

CREATE INDEX failedapproach_project IF NOT EXISTS FOR (f:FailedApproach) ON (f.project);
CREATE INDEX failedapproach_time IF NOT EXISTS FOR (f:FailedApproach) ON (f.timestamp);

CREATE INDEX reference_project IF NOT EXISTS FOR (r:Reference) ON (r.project);
CREATE INDEX reference_type IF NOT EXISTS FOR (r:Reference) ON (r.type);

CREATE INDEX projectfact_project IF NOT EXISTS FOR (pf:ProjectFact) ON (pf.project);
CREATE INDEX projectfact_category IF NOT EXISTS FOR (pf:ProjectFact) ON (pf.category);
CREATE INDEX projectfact_time IF NOT EXISTS FOR (pf:ProjectFact) ON (pf.timestamp);

// Full-text search indexes
CREATE FULLTEXT INDEX decision_search IF NOT EXISTS
  FOR (d:Decision) ON EACH [d.description, d.rationale, d.revisit_trigger];
CREATE FULLTEXT INDEX correction_search IF NOT EXISTS
  FOR (c:Correction) ON EACH [c.wrong_belief, c.right_belief];
CREATE FULLTEXT INDEX insight_search IF NOT EXISTS
  FOR (i:Insight) ON EACH [i.summary, i.detail, i.implications];
CREATE FULLTEXT INDEX question_search IF NOT EXISTS
  FOR (q:Question) ON EACH [q.question, q.answer, q.context];
CREATE FULLTEXT INDEX failedapproach_search IF NOT EXISTS
  FOR (f:FailedApproach) ON EACH [f.approach, f.outcome, f.lesson];
CREATE FULLTEXT INDEX reference_search IF NOT EXISTS
  FOR (r:Reference) ON EACH [r.uri, r.context, r.description];
CREATE FULLTEXT INDEX projectfact_search IF NOT EXISTS
  FOR (pf:ProjectFact) ON EACH [pf.fact, pf.context];
CREATE FULLTEXT INDEX exception_search IF NOT EXISTS
  FOR (e:Exception) ON EACH [e.rule_broken, e.justification];

// Vector indexes for semantic search (Neo4j 5.13+)
// Using 768 dimensions for Ollama nomic-embed-text embeddings
CREATE VECTOR INDEX decision_embedding IF NOT EXISTS FOR (d:Decision) ON d.embedding
  OPTIONS {indexConfig: {`vector.dimensions`: 768, `vector.similarity_function`: 'cosine'}};
CREATE VECTOR INDEX correction_embedding IF NOT EXISTS FOR (c:Correction) ON c.embedding
  OPTIONS {indexConfig: {`vector.dimensions`: 768, `vector.similarity_function`: 'cosine'}};
CREATE VECTOR INDEX insight_embedding IF NOT EXISTS FOR (i:Insight) ON i.embedding
  OPTIONS {indexConfig: {`vector.dimensions`: 768, `vector.similarity_function`: 'cosine'}};
CREATE VECTOR INDEX projectfact_embedding IF NOT EXISTS FOR (pf:ProjectFact) ON pf.embedding
  OPTIONS {indexConfig: {`vector.dimensions`: 768, `vector.similarity_function`: 'cosine'}};
CREATE VECTOR INDEX exception_embedding IF NOT EXISTS FOR (e:Exception) ON e.embedding
  OPTIONS {indexConfig: {`vector.dimensions`: 768, `vector.similarity_function`: 'cosine'}};
CREATE VECTOR INDEX failedapproach_embedding IF NOT EXISTS FOR (f:FailedApproach) ON f.embedding
  OPTIONS {indexConfig: {`vector.dimensions`: 768, `vector.similarity_function`: 'cosine'}};
CREATE VECTOR INDEX question_embedding IF NOT EXISTS FOR (q:Question) ON q.embedding
  OPTIONS {indexConfig: {`vector.dimensions`: 768, `vector.similarity_function`: 'cosine'}};

// === DOMAIN 2: Reference Knowledge Index ===

CREATE CONSTRAINT chunk_id IF NOT EXISTS FOR (ch:Chunk) REQUIRE ch.id IS UNIQUE;
CREATE INDEX chunk_source IF NOT EXISTS FOR (ch:Chunk) ON (ch.source_file);
CREATE INDEX chunk_project IF NOT EXISTS FOR (ch:Chunk) ON (ch.project);
CREATE FULLTEXT INDEX chunk_search IF NOT EXISTS
  FOR (ch:Chunk) ON EACH [ch.content, ch.section];
CREATE VECTOR INDEX chunk_embedding IF NOT EXISTS FOR (ch:Chunk) ON ch.embedding
  OPTIONS {indexConfig: {`vector.dimensions`: 768, `vector.similarity_function`: 'cosine'}};

// === DOMAIN 2: Concepts and Hypotheses (Roadmap) ===

CREATE CONSTRAINT concept_id IF NOT EXISTS FOR (c:Concept) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT hypothesis_id IF NOT EXISTS FOR (h:Hypothesis) REQUIRE h.id IS UNIQUE;
CREATE CONSTRAINT knowledge_gap_id IF NOT EXISTS FOR (kg:KnowledgeGap) REQUIRE kg.id IS UNIQUE;

CREATE INDEX concept_domain IF NOT EXISTS FOR (c:Concept) ON (c.domain);
CREATE INDEX hypothesis_status IF NOT EXISTS FOR (h:Hypothesis) ON (h.status);
CREATE FULLTEXT INDEX concept_search IF NOT EXISTS
  FOR (c:Concept) ON EACH [c.name, c.definition];
CREATE FULLTEXT INDEX hypothesis_search IF NOT EXISTS
  FOR (h:Hypothesis) ON EACH [h.statement, h.testable_prediction];

// === TELEMETRY ===

CREATE CONSTRAINT telemetry_event_id IF NOT EXISTS FOR (t:TelemetryEvent) REQUIRE t.id IS UNIQUE;
CREATE INDEX telemetry_type IF NOT EXISTS FOR (t:TelemetryEvent) ON (t.event_type);
CREATE INDEX telemetry_time IF NOT EXISTS FOR (t:TelemetryEvent) ON (t.timestamp);
CREATE INDEX telemetry_project IF NOT EXISTS FOR (t:TelemetryEvent) ON (t.project);

// === RETRIEVALS (telemetry, not core) ===

CREATE CONSTRAINT retrieval_id IF NOT EXISTS FOR (r:Retrieval) REQUIRE r.id IS UNIQUE;
CREATE INDEX retrieval_project IF NOT EXISTS FOR (r:Retrieval) ON (r.project);
CREATE INDEX retrieval_time IF NOT EXISTS FOR (r:Retrieval) ON (r.timestamp);

// === DEPRECATED: Session (kept for backward compat reads only) ===
// New code should NOT create Session nodes — organize by timestamp + project directly

CREATE CONSTRAINT session_id IF NOT EXISTS FOR (s:Session) REQUIRE s.id IS UNIQUE;
CREATE INDEX session_project IF NOT EXISTS FOR (s:Session) ON (s.project);
