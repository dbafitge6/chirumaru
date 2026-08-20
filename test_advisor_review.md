# Test File for Advisor Review

This file is created to test whether Advisor correctly reviews actual changes.

## Changes Made
- Added test_advisor_review.md file
- Modified .claude/hooks/advisor_check.sh to include git diff/log

## Expected Behavior
Advisor should mention:
- test_advisor_review.md (this file)
- advisor_check.sh modification
- Should NOT mention any fictional files like agent.py, prisma, etc.
