#!/bin/bash

# advisor_check.sh - Stop hook for work quality verification
# 1. Machine checks: git push status, Vercel deployment status
# 2. AI review: Anthropic API for code quality

set +e

REPO_ROOT="$(git rev-parse --show-toplevel)"
LOGS_DIR="$REPO_ROOT/logs"
LOG_FILE="$LOGS_DIR/advisor_checks.md"
LOG_MAX_SIZE=50000  # Rotate log if it exceeds ~50KB
ARCHIVE_RETENTION=5  # Keep last N archive files

mkdir -p "$LOGS_DIR"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Rotate log if it exceeds max size
if [ -f "$LOG_FILE" ]; then
    FILE_SIZE=$(stat -f%z "$LOG_FILE" 2>/dev/null || stat -c%s "$LOG_FILE" 2>/dev/null)
    if [ -z "$FILE_SIZE" ]; then
        # stat failed; skip rotation to avoid data loss on filesystem errors
        FILE_SIZE=0
    fi

    if [ "$FILE_SIZE" -gt "$LOG_MAX_SIZE" ]; then
        ARCHIVE="$LOGS_DIR/advisor_checks.archive.$(date -u +"%Y%m%d_%H%M%S").md"
        # Atomic rotation: create new log first, then move old to archive
        touch "$ARCHIVE"
        mv "$LOG_FILE" "$ARCHIVE" || exit 2

        # Clean up old archives, keep only the last N
        # Use find + while read to safely handle filenames with spaces/newlines
        ARCHIVE_COUNT=0
        find "$LOGS_DIR" -maxdepth 1 -name 'advisor_checks.archive.*.md' -print0 2>/dev/null | \
            xargs -0 ls -1t 2>/dev/null | while IFS= read -r archive_file; do
                ARCHIVE_COUNT=$((ARCHIVE_COUNT + 1))
                if [ "$ARCHIVE_COUNT" -gt "$ARCHIVE_RETENTION" ]; then
                    rm -f "$archive_file"
                fi
            done
    fi
fi

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
    # Gather actual git diff and log
    GIT_DIFF=$(git diff HEAD~3 HEAD 2>/dev/null || echo "No recent changes")
    GIT_LOG=$(git log -5 --stat 2>/dev/null || echo "No git log available")

    # Use a test model ID if ADVISOR_TEST_MODEL is set (for testing API error handling)
    TEST_MODEL="${ADVISOR_TEST_MODEL:-claude-sonnet-4-6}"

    # Build prompt with actual git data, using jq for safe JSON encoding
    PROMPT=$(cat <<'EOF'
Review the following actual git changes in this repository.
This is real git diff and git log output - do NOT imagine or fabricate files/changes.
Base your review ONLY on what is shown below.

RECENT GIT LOG (5 commits):
EOF
)
    PROMPT="$PROMPT
$GIT_LOG

RECENT GIT DIFF (last 3 commits):
$GIT_DIFF

Please review for:
1. Code quality and correctness
2. Uncommitted changes that should be committed
3. Test coverage for new code
4. Documentation updates
5. Obvious bugs or issues

Be concise. Reference actual changed files from the diff above."

    # Build request using jq for safe JSON encoding
    REQUEST_BODY=$(jq -n \
        --arg model "$TEST_MODEL" \
        --arg prompt "$PROMPT" \
        '{
            "model": $model,
            "max_tokens": 600,
            "messages": [
                {
                    "role": "user",
                    "content": $prompt
                }
            ]
        }')

    RESPONSE=$(curl -s https://api.anthropic.com/v1/messages \
        -H "x-api-key: $ANTHROPIC_API_KEY_ADVISOR" \
        -H "anthropic-version: 2023-06-01" \
        -H "content-type: application/json" \
        -d "$REQUEST_BODY" 2>&1)

    if echo "$RESPONSE" | grep -q '"error"'; then
        ERROR=$(echo "$RESPONSE" | jq -r '.error.message // "API error"' 2>/dev/null || echo "API call failed")
        ERROR_MSG="❌ ADVISOR API FAILED
$ERROR

Cannot complete AI review. Task completion blocked."
        echo "$ERROR_MSG" >&2
        log_check "🔴 API Error" "$ERROR_MSG"
        exit 2
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
        ERROR_MSG="❌ ADVISOR API FAILED
Unexpected response format from Anthropic API.

Cannot complete AI review. Task completion blocked."
        echo "$ERROR_MSG" >&2
        log_check "🔴 API Response Failed" "$ERROR_MSG"
        exit 2
    fi
else
    log_check "⏭️ AI Review Skipped" "ANTHROPIC_API_KEY_ADVISOR not set"
    exit 0
fi

exit 0
