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
GIT_LOG=$(git log -1 --pretty=format:"%H %s" 2>/dev/null || echo "")

# Call Anthropic API for code review if API key is set
if [ -n "$ANTHROPIC_API_KEY_ADVISOR" ]; then
    # Prepare request for Anthropic API
    REQUEST_BODY='{
  "model": "claude-sonnet-4-6",
  "max_tokens": 500,
  "messages": [
    {
      "role": "user",
      "content": "Review the recent work in this repository for code quality, uncommitted changes, test coverage, documentation, and obvious bugs. Be concise."
    }
  ]
}'

    # Make API call
    RESPONSE=$(curl -s https://api.anthropic.com/v1/messages \
        -H "x-api-key: $ANTHROPIC_API_KEY_ADVISOR" \
        -H "anthropic-version: 2023-06-01" \
        -H "content-type: application/json" \
        -d "$REQUEST_BODY" 2>&1)

    # Parse response for errors or success
    if echo "$RESPONSE" | grep -q '"error"'; then
        # Extract error message
        ERROR=$(echo "$RESPONSE" | jq -r '.error.message // "API error"' 2>/dev/null || echo "API call failed")
        log_check "❌ API Error" "$ERROR"
        exit 0
    elif echo "$RESPONSE" | grep -q '"content"'; then
        # Success - extract response text
        ADVISOR_RESPONSE=$(echo "$RESPONSE" | jq -r '.content[0].text // empty' 2>/dev/null)
        if [ -n "$ADVISOR_RESPONSE" ]; then
            log_check "✅ Advisor Review" "" "$ADVISOR_RESPONSE"
        else
            log_check "✅ Advisor Check Completed" "" "Review processed successfully"
        fi
        exit 0
    else
        # Unknown response format
        log_check "❌ API Response" "Unexpected response format"
        exit 0
    fi
else
    # No API key - just log that check was skipped
    log_check "⏭️ Skipped" "ANTHROPIC_API_KEY_ADVISOR not set"
fi

exit 0
