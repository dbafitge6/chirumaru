#!/bin/bash

# advisor_check.sh - Stop hook that verifies work quality before task completion
# Calls the Anthropic API to perform a code/work quality review
# Logs results to logs/advisor_checks.md

set -e

REPO_ROOT="$(git rev-parse --show-toplevel)"
LOGS_DIR="$REPO_ROOT/logs"
LOG_FILE="$LOGS_DIR/advisor_checks.md"

# Ensure logs directory exists
mkdir -p "$LOGS_DIR"

# Get timestamp
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Function to log advisor check result
log_check() {
    local status="$1"
    local error_msg="${2:-}"
    local response="${3:-}"

    {
        echo "# Advisor Check: $TIMESTAMP"
        echo "**Status**: $status"
        if [ -n "$error_msg" ]; then
            echo "**Error**: $error_msg"
        fi
        if [ -n "$response" ]; then
            echo ""
            echo "## Advisor Response"
            echo "$response"
        fi
        echo ""
        echo "---"
        echo ""
    } >> "$LOG_FILE"
}

# Try to get recent git changes for context
GIT_DIFF=$(git diff HEAD~1 HEAD 2>/dev/null || echo "")
GIT_LOG=$(git log -1 --pretty=format:"%H %s" 2>/dev/null || echo "")

# Call Anthropic API for code review if API key is set
if [ -n "$ANTHROPIC_API_KEY" ]; then
    PROMPT="Review the recent work in this repository. Check for:
1. Code quality and correctness
2. Uncommitted changes that should be committed
3. Test coverage for new code
4. Documentation updates
5. Any obvious bugs or issues

Recent changes:
$GIT_LOG

Reply with: ✅ APPROVED if the work is ready, or ⚠️ REVIEW NEEDED with specific concerns."

    # Make API call
    RESPONSE=$(curl -s https://api.anthropic.com/v1/messages \
        -H "x-api-key: $ANTHROPIC_API_KEY" \
        -H "anthropic-version: 2023-06-01" \
        -H "content-type: application/json" \
        -d "{
            \"model\": \"claude-opus-4-20250805\",
            \"max_tokens\": 500,
            \"messages\": [
                {
                    \"role\": \"user\",
                    \"content\": \"$PROMPT\"
                }
            ]
        }" 2>&1)

    # Check if response contains error
    if echo "$RESPONSE" | grep -q '"error"'; then
        ERROR=$(echo "$RESPONSE" | grep -o '"message":"[^"]*' | sed 's/"message":"//')
        log_check "❌ API Error" "$ERROR"
        exit 0  # Don't block on API errors
    else
        # Extract text from response
        ADVISOR_RESPONSE=$(echo "$RESPONSE" | grep -o '"text":"[^"]*"' | head -1 | sed 's/"text":"//' | sed 's/"$//')
        log_check "✅ Checked" "" "$ADVISOR_RESPONSE"

        # Check if response contains warning keywords
        if echo "$ADVISOR_RESPONSE" | grep -qi "⚠️\|REVIEW NEEDED\|concern\|issue\|bug"; then
            echo "⚠️ Advisor has concerns. Check logs/advisor_checks.md for details."
            exit 0  # Still allow completion, but inform user
        fi
    fi
else
    # No API key - just log that check was skipped
    log_check "⏭️ Skipped" "ANTHROPIC_API_KEY not set"
fi

exit 0
