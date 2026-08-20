#!/bin/bash

# pre-commit-settings-check.sh - Prevent committing without updating .claude/settings.json
# if it has been modified locally. This avoids settings loss in future sessions.

# Check if .claude/settings.json has been modified (unstaged or staged changes)
SETTINGS_FILE=".claude/settings.json"

if [ -f "$SETTINGS_FILE" ]; then
    # Check if settings.json is in the staging area (being committed)
    if git diff --cached --name-only | grep -q "^$SETTINGS_FILE$"; then
        exit 0  # File is staged for commit, allow it
    fi

    # Check if settings.json has unstaged changes
    if git diff --name-only | grep -q "^$SETTINGS_FILE$"; then
        echo "⚠️  Warning: $SETTINGS_FILE has unstaged changes but is NOT being committed."
        echo "This could cause settings to be lost in future sessions."
        echo ""
        echo "To fix this, run:"
        echo "  git add .claude/settings.json"
        echo "  git commit --amend --no-edit"
        echo ""
        echo "Continuing without these changes — but consider committing them!"
        exit 0  # Don't block, just warn
    fi
fi

exit 0
