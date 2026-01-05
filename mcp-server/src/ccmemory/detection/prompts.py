"""Detection prompt templates for LLM-based context extraction."""

DECISION_PROMPT = """Analyze if this user message contains a decision.

CONTEXT:
{context}

CLAUDE'S RESPONSE:
{claude_response}

USER'S MESSAGE:
{user_message}

Is this a decision? Look for:
- Explicit choices: "Let's go with X", "I'll use Y"
- Approvals: "That sounds good", "Yes, do it"
- Direction setting: "We should always...", "From now on..."

Output JSON:
{{"is_decision": true/false, "confidence": 0.0-1.0, "description": "...", "rationale": "...", "revisit_trigger": "..."}}"""

CORRECTION_PROMPT = """Analyze if this user message corrects Claude's understanding.

CLAUDE'S RESPONSE:
{claude_response}

USER'S MESSAGE:
{user_message}

Is this a correction? Look for:
- Direct correction: "No, that's not right", "Actually..."
- Factual fix: "It's X, not Y"
- Context correction: "In this project we do it differently"

Output JSON:
{{"is_correction": true/false, "confidence": 0.0-1.0, "wrong_belief": "...", "right_belief": "...", "severity": "minor/significant/critical"}}"""

EXCEPTION_PROMPT = """Analyze if this user message grants an exception to normal rules.

CONTEXT:
{context}

USER'S MESSAGE:
{user_message}

Is this an exception? Look for:
- "In this case, skip X"
- "Just this once..."
- "Because of Y, we should do Z instead"

Output JSON:
{{"is_exception": true/false, "confidence": 0.0-1.0, "rule_broken": "...", "justification": "...", "scope": "one-time/conditional/new-precedent"}}"""

INSIGHT_PROMPT = """Analyze if this exchange contains a significant insight.

CONTEXT:
{context}

CLAUDE'S RESPONSE:
{claude_response}

USER'S MESSAGE:
{user_message}

Is there an insight? Look for:
- Realizations about situation/patterns
- Strategic conclusions
- Synthesized understanding

Output JSON:
{{"is_insight": true/false, "confidence": 0.0-1.0, "category": "realization/analysis/strategy/personal/synthesis", "summary": "...", "implications": "..."}}"""

QUESTION_PROMPT = """Analyze if Claude asked a question that got a substantive answer.

CLAUDE'S RESPONSE:
{claude_response}

USER'S MESSAGE:
{user_message}

Is this meaningful Q&A? Look for:
- Answered questions with useful info
- Preference elicitation with response
- Constraint discovery

NOT meaningful: rhetorical questions, simple yes/no

Output JSON:
{{"is_question": true/false, "confidence": 0.0-1.0, "question": "...", "answer": "...", "context": "..."}}"""

FAILED_APPROACH_PROMPT = """Analyze if something was tried and didn't work.

CONTEXT:
{context}

USER'S MESSAGE:
{user_message}

Is this a failed approach? Look for:
- "That didn't work"
- "Let's try something else"
- "Turns out X causes Y problem"

Output JSON:
{{"is_failed_approach": true/false, "confidence": 0.0-1.0, "approach": "...", "outcome": "...", "lesson": "..."}}"""
