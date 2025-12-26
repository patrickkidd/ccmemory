#!/bin/bash
# Analyze user prompt for memory capture triggers
# Outputs reminder if triggers detected

# Read the user's prompt from stdin
PROMPT=$(cat)

# Define trigger patterns (case-insensitive matching)
CORRECTION_PATTERNS=(
    "no,? that'?s wrong"
    "that'?s not how"
    "i already told you"
    "we discussed this"
    "stop doing"
    "don'?t assume"
    "the actual way"
    "it'?s actually"
    "you keep"
    "i said"
    "that'?s incorrect"
    "not like that"
)

DECISION_PATTERNS=(
    "i'?ve decided"
    "i decided"
    "i'?m going to"
    "i chose"
    "let'?s use"
    "we'?ll go with"
    "the approach will be"
    "i want to use"
)

PREFERENCE_PATTERNS=(
    "i prefer"
    "always use"
    "never use"
    "always do"
    "never do"
    "i like to"
    "i don'?t like"
    "make sure to"
    "don'?t ever"
)

FACT_PATTERNS=(
    "the way .* works"
    "how .* works"
    "this is because"
    "the reason is"
    "watch out for"
    "be careful with"
    "gotcha"
    "important:"
    "note:"
    "remember:"
    "fyi"
)

# Check for matches
PROMPT_LOWER=$(echo "$PROMPT" | tr '[:upper:]' '[:lower:]')

check_patterns() {
    local patterns=("$@")
    for pattern in "${patterns[@]}"; do
        if echo "$PROMPT_LOWER" | grep -qiE "$pattern"; then
            return 0
        fi
    done
    return 1
}

TRIGGERS=""

if check_patterns "${CORRECTION_PATTERNS[@]}"; then
    TRIGGERS="CORRECTION"
fi

if check_patterns "${DECISION_PATTERNS[@]}"; then
    TRIGGERS="${TRIGGERS:+$TRIGGERS, }DECISION"
fi

if check_patterns "${PREFERENCE_PATTERNS[@]}"; then
    TRIGGERS="${TRIGGERS:+$TRIGGERS, }PREFERENCE"
fi

if check_patterns "${FACT_PATTERNS[@]}"; then
    TRIGGERS="${TRIGGERS:+$TRIGGERS, }PROJECT_FACT"
fi

# Output reminder if any triggers detected
if [ -n "$TRIGGERS" ]; then
    echo ""
    echo "<ccmemory-trigger type=\"$TRIGGERS\">"
    echo "IMPORTANT: The user's message contains information that should be stored to memory."
    echo "After processing this message, use the memory service to store the key information."
    echo "Then confirm: \"Stored to memory: [brief description]\""
    echo "</ccmemory-trigger>"
fi
