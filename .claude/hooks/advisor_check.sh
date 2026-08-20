#!/bin/bash

# advisor_check.sh - Stop hook for work quality verification
# 1. Machine checks: git push status, Vercel deployment status
# 2. AI review: Anthropic API for code quality

set +e

REPO_ROOT="$(git rev-parse --show-toplevel)"
LOGS_DIR="$REPO_ROOT/logs"
LOG_FILE="$LOGS_DIR/advisor_checks.md"

mkdir -p "$LOGS_DIR"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

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

# ============================================================================
# PHASE 1: MACHINE CHECKS
# ============================================================================

# Check 1: Unpushed commits
git fetch github >/dev/null 2>&1
UNPUSHED=$(git log github/main..HEAD --oneline 2>/dev/null || echo "")
if [ -n "$UNPUSHED" ]; then
    ERROR_MSG="❌ UNPUSHED COMMITS detected:
$UNPUSHED

Run: git push github main"
    echo "$ERROR_MSG" >&2
    log_check "🔴 Unpushed Commits" "$ERROR_MSG"
    exit 2
fi

# Check 2: Vercel deployment status
if [ -n "$VERCEL_TOKEN" ] && [ -n "$VERCEL_PROJECT_ID" ]; then
    VERCEL_RESPONSE=$(curl -s "https://api.vercel.com/v6/deployments?projectId=$VERCEL_PROJECT_ID&limit=1" \
        -H "Authorization: Bearer $VERCEL_TOKEN")

    CURRENT_SHA=$(git rev-parse HEAD 2>/dev/null || echo "")
    DEPLOYED_SHA=$(echo "$VERCEL_RESPONSE" | jq -r '.deployments[0].meta.githubCommitSha // "UNKNOWN"' 2>/dev/null)
    READY_STATE=$(echo "$VERCEL_RESPONSE" | jq -r '.deployments[0].readyState // "UNKNOWN"' 2>/dev/null)

    if [ "$DEPLOYED_SHA" != "$CURRENT_SHA" ] || [ "$READY_STATE" != "READY" ]; then
        ERROR_MSG="❌ VERCEL DEPLOYMENT NOT READY
Current commit: $CURRENT_SHA
Deployed commit: $DEPLOYED_SHA
Deployment state: $READY_STATE

Wait for Vercel to finish deployment or push if needed."
        echo "$ERROR_MSG" >&2
        log_check "🔴 Vercel Not Ready" "$ERROR_MSG"
        exit 2
    fi
fi

# ============================================================================
# PHASE 2: AI REVIEW (only if machine checks pass)
# ============================================================================

if [ -n "$ANTHROPIC_API_KEY_ADVISOR" ]; then
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

    RESPONSE=$(curl -s https://api.anthropic.com/v1/messages \
        -H "x-api-key: $ANTHROPIC_API_KEY_ADVISOR" \
        -H "anthropic-version: 2023-06-01" \
        -H "content-type: application/json" \
        -d "$REQUEST_BODY" 2>&1)

    if echo "$RESPONSE" | grep -q '"error"'; then
        ERROR=$(echo "$RESPONSE" | jq -r '.error.message // "API error"' 2>/dev/null || echo "API call failed")
        log_check "⚠️ API Error (non-blocking)" "$ERROR"
        exit 0
    elif echo "$RESPONSE" | grep -q '"content"'; then
        ADVISOR_RESPONSE=$(echo "$RESPONSE" | jq -r '.content[0].text // empty' 2>/dev/null)
        if [ -n "$ADVISOR_RESPONSE" ]; then
            log_check "✅ Advisor Review" "" "$ADVISOR_RESPONSE"

            # If advisor detected issues, block with exit 2
            if echo "$ADVISOR_RESPONSE" | grep -qi "REVIEW NEEDED\|concern\|warning\|issue\|bug\|error"; then
                echo "⚠️ Advisor detected issues. Review logs/advisor_checks.md" >&2
                exit 2
            fi
            exit 0
        else
            log_check "✅ Advisor Check Completed" "" "Review processed successfully"
            exit 0
        fi
    else
        log_check "⚠️ API Response (non-blocking)" "Unexpected response format"
        exit 0
    fi
else
    log_check "⏭️ AI Review Skipped" "ANTHROPIC_API_KEY_ADVISOR not set"
    exit 0
fi

exit 0
