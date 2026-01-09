"""Unified detection prompt for context extraction."""

DETECTION_PROMPT = """Analyze this conversation exchange and extract any memorable context.

CONTEXT (recent conversation):
{context}

CLAUDE'S RESPONSE:
{claude_response}

USER'S MESSAGE:
{user_message}

═══════════════════════════════════════════════════════════════════════════════
DETECTION TYPES
═══════════════════════════════════════════════════════════════════════════════

Extract items into these categories. Most exchanges yield NOTHING — only extract
when clearly present. Each item needs a confidence score (0.0-1.0).

**DECISION**: User makes an explicit choice between options or sets task direction.
- "Let's go with X", "I'll use Y", "That sounds good, do it"
- Choosing between alternatives for the current task
- NOT: Questions, hypotheticals, or Claude's suggestions
- NOT: Establishing project-wide rules (use PROJECT_FACT)

**CORRECTION**: User corrects Claude's misunderstanding.
- "No, that's wrong", "Actually...", "It's X not Y"
- Must identify what Claude believed vs what's true
- NOT: New information that doesn't contradict Claude

**EXCEPTION**: User grants a one-time exception to normal rules.
- "In this case, skip X", "Just this once...", "Because of Y, do Z instead"
- Must reference a rule being broken and why
- NOT: General preferences or new rules

**INSIGHT**: Significant realization emerges from the exchange.
- Pattern recognition, strategic conclusions, synthesized understanding
- Must be non-obvious and worth remembering
- NOT: Routine observations or basic facts

**QUESTION**: Claude asked something and got a substantive answer.
- Preference elicitation with meaningful response
- Constraint discovery, requirement clarification
- NOT: Rhetorical questions, yes/no answers, routine confirmations

**FAILED_APPROACH**: Something was tried and didn't work.
- "That didn't work", "Let's try something else"
- "Turns out X causes Y problem"
- Must capture what failed and why
- NOT: Hypothetical problems or general concerns

**PROJECT_FACT**: User states a project convention, rule, requirement, or pattern.
- "We use X", "This project uses Y", "Our convention is..."
- "Tests are in the tests/ folder", "We always use camelCase"
- "All changes must include tests", "Never commit without passing tests"
- Project-wide rules and requirements that apply going forward
- Categories: tool, pattern, convention, environment, constraint, workflow
- KEY DISTINCTION from DECISION:
  * DECISION: "Let's use pytest for this" (choosing for current task)
  * PROJECT_FACT: "We use pytest" or "All code must have tests" (project rule)
- NOT: Personal preferences, Claude's observations, or hypotheticals

═══════════════════════════════════════════════════════════════════════════════
EXTRACTION RULES
═══════════════════════════════════════════════════════════════════════════════

1. **DETECT WHEN PRESENT**: Extract items when they clearly match. Don't
   force-fit marginal cases, but do capture clear statements of rules,
   conventions, decisions, or corrections.

2. **CONFIDENCE**: Use >= 0.7 for clear matches, >= 0.8 for very explicit ones.

3. **NO DUPLICATES**: One item per distinct piece of information. Don't extract
   the same thing as both a decision and an insight.

4. **REQUIRED FIELDS**: Each type has required fields that must be filled:
   - Decision: description (what was decided)
   - Correction: wrongBelief, rightBelief (what changed)
   - Exception: ruleBroken, justification (what and why)
   - Insight: summary (the insight itself)
   - Question: question, answer (the Q&A pair)
   - FailedApproach: approach, outcome (what failed and result)
   - ProjectFact: fact, category (the convention and its type)

5. **TOPICS**: Each item should include a `topics` list identifying which
   components/areas it relates to. Examples: ["auth", "api"], ["database"],
   ["ui", "forms"], ["testing"]. Use short, lowercase tags. Empty list if
   no specific topic applies.

6. **DECISION RELATIONSHIPS**: For decisions, identify relationships to prior
   decisions when the conversation references them:
   - SUPERSEDES: This decision replaces/updates a prior decision
   - DEPENDS_ON: This decision requires a prior decision to hold
   - CONSTRAINS: This decision limits options for another area
   - CONFLICTS_WITH: This decision contradicts a prior decision
   - IMPACTS: This decision affects another area

   Include as `relatedDecisions` with description of the prior decision,
   relationship type, and reason. Only include if explicitly referenced.

═══════════════════════════════════════════════════════════════════════════════
EXAMPLES
═══════════════════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────────────────────
# [EMPTY_OUTPUT_ROUTINE_EXCHANGE]
# Most exchanges don't contain memorable context
# ─────────────────────────────────────────────────────────────────────────────

Claude: "I'll read the config file to understand the setup."
User: "Sounds good."

❌ WRONG (forced detection):
{{"decisions": [{{"confidence": 0.8, "description": "Proceed with reading config"}}]}}

WHY WRONG: "Sounds good" is routine acknowledgment, not a memorable decision.
The user isn't choosing between alternatives or setting direction.

✅ CORRECT:
{{"decisions": [], "corrections": [], "exceptions": [], "insights": [], "questions": [], "failedApproaches": [], "projectFacts": []}}

# ─────────────────────────────────────────────────────────────────────────────
# [DECISION_EXPLICIT_CHOICE]
# User makes clear choice between alternatives
# ─────────────────────────────────────────────────────────────────────────────

Claude: "Should we use Redis or PostgreSQL for caching?"
User: "Let's go with Redis. It's simpler for our use case and we don't need persistence."

✅ CORRECT:
{{
  "decisions": [{{
    "confidence": 0.9,
    "description": "Use Redis for caching instead of PostgreSQL",
    "rationale": "Simpler, persistence not needed",
    "topics": ["caching", "infrastructure"]
  }}],
  "corrections": [], "exceptions": [], "insights": [], "questions": [], "failedApproaches": [], "projectFacts": []
}}

# ─────────────────────────────────────────────────────────────────────────────
# [PROJECT_FACT_SETTING_RULE]
# User establishes a project-wide rule or requirement
# ─────────────────────────────────────────────────────────────────────────────

Claude: "I'm ready to help with your project."
User: "All changes must include tests and those tests must pass before claiming done."

✅ CORRECT:
{{
  "projectFacts": [{{
    "confidence": 0.85,
    "category": "workflow",
    "fact": "All changes require passing tests before completion"
  }}],
  "decisions": [], "corrections": [], "exceptions": [], "insights": [], "questions": [], "failedApproaches": []
}}

# ─────────────────────────────────────────────────────────────────────────────
# [CORRECTION_FACTUAL_FIX]
# User corrects Claude's misunderstanding
# ─────────────────────────────────────────────────────────────────────────────

Claude: "I'll update the User model in models/user.py..."
User: "No, users are defined in auth/accounts.py, not models/user.py. We don't have a models directory."

✅ CORRECT:
{{
  "corrections": [{{
    "confidence": 0.95,
    "wrongBelief": "User model is in models/user.py",
    "rightBelief": "User model is in auth/accounts.py, no models directory exists",
    "severity": "significant",
    "topics": ["auth", "models"]
  }}],
  "decisions": [], "exceptions": [], "insights": [], "questions": [], "failedApproaches": [], "projectFacts": []
}}

# ─────────────────────────────────────────────────────────────────────────────
# [CORRECTION_VS_NEW_INFO]
# New information is NOT a correction
# ─────────────────────────────────────────────────────────────────────────────

Claude: "I'll add the new endpoint to the API."
User: "By the way, we also need to add rate limiting to it."

❌ WRONG (treating new info as correction):
{{"corrections": [{{"wrongBelief": "No rate limiting needed", "rightBelief": "Rate limiting required"}}]}}

WHY WRONG: Claude didn't claim rate limiting wasn't needed. This is new
information/requirement, not a correction of a false belief.

✅ CORRECT:
{{"decisions": [], "corrections": [], "exceptions": [], "insights": [], "questions": [], "failedApproaches": [], "projectFacts": []}}

# ─────────────────────────────────────────────────────────────────────────────
# [EXCEPTION_ONE_TIME_OVERRIDE]
# User grants exception to normal practice
# ─────────────────────────────────────────────────────────────────────────────

Claude: "I'll add unit tests for this new function."
User: "Skip tests for now — this is just a quick prototype we're throwing away next week."

✅ CORRECT:
{{
  "exceptions": [{{
    "confidence": 0.85,
    "ruleBroken": "Add unit tests for new functions",
    "justification": "Quick prototype being discarded next week",
    "scope": "one-time",
    "topics": ["testing"]
  }}],
  "decisions": [], "corrections": [], "insights": [], "questions": [], "failedApproaches": [], "projectFacts": []
}}

# ─────────────────────────────────────────────────────────────────────────────
# [QUESTION_SUBSTANTIVE_ANSWER]
# Claude's question gets meaningful answer
# ─────────────────────────────────────────────────────────────────────────────

Claude: "What authentication method does your API use?"
User: "We use JWT tokens with RS256 signing. Tokens expire after 1 hour and refresh tokens last 30 days."

✅ CORRECT:
{{
  "questions": [{{
    "confidence": 0.9,
    "question": "What authentication method does the API use?",
    "answer": "JWT tokens with RS256 signing, 1hr expiry, 30-day refresh tokens",
    "context": "API authentication",
    "topics": ["auth", "api"]
  }}],
  "decisions": [], "corrections": [], "exceptions": [], "insights": [], "failedApproaches": [], "projectFacts": []
}}

# ─────────────────────────────────────────────────────────────────────────────
# [QUESTION_TRIVIAL_NOT_EXTRACTED]
# Trivial yes/no answers aren't worth storing
# ─────────────────────────────────────────────────────────────────────────────

Claude: "Should I proceed?"
User: "Yes."

❌ WRONG:
{{"questions": [{{"question": "Should I proceed?", "answer": "Yes"}}]}}

WHY WRONG: This is a trivial confirmation, not substantive Q&A worth remembering.

✅ CORRECT:
{{"decisions": [], "corrections": [], "exceptions": [], "insights": [], "questions": [], "failedApproaches": [], "projectFacts": []}}

# ─────────────────────────────────────────────────────────────────────────────
# [FAILED_APPROACH_CONCRETE]
# Something specific was tried and failed
# ─────────────────────────────────────────────────────────────────────────────

User: "That regex approach didn't work — it times out on large files. We need to use streaming instead."

✅ CORRECT:
{{
  "failedApproaches": [{{
    "confidence": 0.9,
    "approach": "Regex parsing",
    "outcome": "Times out on large files",
    "lesson": "Use streaming for large file handling",
    "topics": ["parsing", "performance"]
  }}],
  "decisions": [], "corrections": [], "exceptions": [], "insights": [], "questions": [], "projectFacts": []
}}

# ─────────────────────────────────────────────────────────────────────────────
# [INSIGHT_PATTERN_RECOGNITION]
# Non-obvious realization worth remembering
# ─────────────────────────────────────────────────────────────────────────────

Claude: "Looking at these errors, they all happen during the nightly batch job."
User: "Oh interesting — they correlate with when marketing sends their email blasts. The DB load spikes."

✅ CORRECT:
{{
  "insights": [{{
    "confidence": 0.85,
    "category": "analysis",
    "summary": "Nightly errors correlate with marketing email blasts causing DB load spikes",
    "implications": "May need to schedule batch jobs to avoid email blast times",
    "topics": ["database", "batch-jobs", "performance"]
  }}],
  "decisions": [], "corrections": [], "exceptions": [], "questions": [], "failedApproaches": [], "projectFacts": []
}}

# ─────────────────────────────────────────────────────────────────────────────
# [MULTIPLE_DETECTIONS]
# Single exchange can contain multiple items
# ─────────────────────────────────────────────────────────────────────────────

Claude: "I'll use the standard REST pattern with /api/v1/users endpoint."
User: "Actually we use GraphQL here, not REST. And let's put it under /graphql not /api. Also skip the authentication middleware for now since this is internal-only."

✅ CORRECT:
{{
  "corrections": [{{
    "confidence": 0.95,
    "wrongBelief": "Project uses REST API pattern",
    "rightBelief": "Project uses GraphQL",
    "severity": "significant",
    "topics": ["api"]
  }}],
  "decisions": [{{
    "confidence": 0.85,
    "description": "Use /graphql endpoint path",
    "rationale": "Project convention",
    "topics": ["api", "routing"]
  }}],
  "exceptions": [{{
    "confidence": 0.8,
    "ruleBroken": "Authentication middleware required",
    "justification": "Internal-only endpoint",
    "scope": "conditional",
    "topics": ["auth", "api"]
  }}],
  "insights": [], "questions": [], "failedApproaches": [], "projectFacts": []
}}

# ─────────────────────────────────────────────────────────────────────────────
# [PROJECT_FACT_STATING_CONVENTION]
# User states existing project convention
# ─────────────────────────────────────────────────────────────────────────────

Claude: "I'll run the tests with unittest."
User: "We use pytest here, not unittest."

✅ CORRECT:
{{
  "projectFacts": [{{
    "confidence": 0.9,
    "category": "tool",
    "fact": "Uses pytest for testing",
    "topics": ["testing"]
  }}],
  "corrections": [{{
    "confidence": 0.85,
    "wrongBelief": "Project uses unittest",
    "rightBelief": "Project uses pytest",
    "severity": "minor",
    "topics": ["testing"]
  }}],
  "decisions": [], "exceptions": [], "insights": [], "questions": [], "failedApproaches": []
}}

NOTE: Both ProjectFact AND Correction — the user corrected Claude while also
stating a project convention.

# ─────────────────────────────────────────────────────────────────────────────
# [PROJECT_FACT_VS_DECISION]
# Stating existing fact vs making new decision
# ─────────────────────────────────────────────────────────────────────────────

Example A - PROJECT_FACT:
User: "By the way, we use uv for all Python commands in this project."

✅ CORRECT:
{{
  "projectFacts": [{{
    "confidence": 0.9,
    "category": "tool",
    "fact": "Uses uv for Python package management"
  }}],
  "decisions": [], "corrections": [], "exceptions": [], "insights": [], "questions": [], "failedApproaches": []
}}

Example B - DECISION (not PROJECT_FACT):
User: "Let's switch to using uv instead of pip."

✅ CORRECT:
{{
  "decisions": [{{
    "confidence": 0.85,
    "description": "Switch to uv from pip for package management"
  }}],
  "projectFacts": [], "corrections": [], "exceptions": [], "insights": [], "questions": [], "failedApproaches": []
}}

WHY: Example A states existing convention. Example B makes new decision.

# ─────────────────────────────────────────────────────────────────────────────
# [PROJECT_FACT_MULTIPLE]
# Multiple facts from one statement
# ─────────────────────────────────────────────────────────────────────────────

User: "This project uses Python 3.11, tests are in the tests/ directory, and we use black for formatting."

✅ CORRECT:
{{
  "projectFacts": [
    {{"confidence": 0.9, "category": "environment", "fact": "Uses Python 3.11"}},
    {{"confidence": 0.9, "category": "pattern", "fact": "Tests located in tests/ directory"}},
    {{"confidence": 0.9, "category": "tool", "fact": "Uses black for code formatting"}}
  ],
  "decisions": [], "corrections": [], "exceptions": [], "insights": [], "questions": [], "failedApproaches": []
}}

═══════════════════════════════════════════════════════════════════════════════
OUTPUT FORMAT
═══════════════════════════════════════════════════════════════════════════════

Return a JSON object with these fields (all lists, empty if nothing detected):
- decisions: list of Decision objects
- corrections: list of Correction objects
- exceptions: list of Exception_ objects
- insights: list of Insight objects
- questions: list of Question objects
- failedApproaches: list of FailedApproach objects
- projectFacts: list of ProjectFact objects"""
