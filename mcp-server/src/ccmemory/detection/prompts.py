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

**DECISION**: User makes an explicit choice or sets direction.
- "Let's go with X", "I'll use Y", "That sounds good, do it"
- "We should always...", "From now on..."
- NOT: Questions, hypotheticals, or Claude's suggestions

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

═══════════════════════════════════════════════════════════════════════════════
EXTRACTION RULES
═══════════════════════════════════════════════════════════════════════════════

1. **SPARSE OUTPUT**: Return empty lists when nothing matches. Most exchanges
   have no detections. Don't force-fit marginal cases.

2. **HIGH BAR**: Only extract items with confidence >= 0.7. If unsure, don't
   include it.

3. **NO DUPLICATES**: One item per distinct piece of information. Don't extract
   the same thing as both a decision and an insight.

4. **REQUIRED FIELDS**: Each type has required fields that must be filled:
   - Decision: description (what was decided)
   - Correction: wrongBelief, rightBelief (what changed)
   - Exception: ruleBroken, justification (what and why)
   - Insight: summary (the insight itself)
   - Question: question, answer (the Q&A pair)
   - FailedApproach: approach, outcome (what failed and result)

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
{{"decisions": [], "corrections": [], "exceptions": [], "insights": [], "questions": [], "failedApproaches": []}}

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
    "rationale": "Simpler, persistence not needed"
  }}],
  "corrections": [], "exceptions": [], "insights": [], "questions": [], "failedApproaches": []
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
    "severity": "significant"
  }}],
  "decisions": [], "exceptions": [], "insights": [], "questions": [], "failedApproaches": []
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
{{"decisions": [], "corrections": [], "exceptions": [], "insights": [], "questions": [], "failedApproaches": []}}

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
    "scope": "one-time"
  }}],
  "decisions": [], "corrections": [], "insights": [], "questions": [], "failedApproaches": []
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
    "context": "API authentication"
  }}],
  "decisions": [], "corrections": [], "exceptions": [], "insights": [], "failedApproaches": []
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
{{"decisions": [], "corrections": [], "exceptions": [], "insights": [], "questions": [], "failedApproaches": []}}

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
    "lesson": "Use streaming for large file handling"
  }}],
  "decisions": [], "corrections": [], "exceptions": [], "insights": [], "questions": []
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
    "implications": "May need to schedule batch jobs to avoid email blast times"
  }}],
  "decisions": [], "corrections": [], "exceptions": [], "questions": [], "failedApproaches": []
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
    "severity": "significant"
  }}],
  "decisions": [{{
    "confidence": 0.85,
    "description": "Use /graphql endpoint path",
    "rationale": "Project convention"
  }}],
  "exceptions": [{{
    "confidence": 0.8,
    "ruleBroken": "Authentication middleware required",
    "justification": "Internal-only endpoint",
    "scope": "conditional"
  }}],
  "insights": [], "questions": [], "failedApproaches": []
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
- failedApproaches: list of FailedApproach objects"""
