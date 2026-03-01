#!/usr/bin/env bash
set -uo pipefail
INPUT=$(cat 2>/dev/null || echo "{}")
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null)
[ -z "$FILE" ] && exit 0
[ ! -f "$FILE" ] && exit 0
BASENAME=$(basename "$FILE")
DIR="${CLAUDE_PROJECT_DIR:-.}"
case "$FILE" in
    *.py)
        black --line-length=100 --quiet "$FILE" 2>/dev/null
        ruff check --fix --quiet "$FILE" 2>/dev/null
        echo "{\"systemMessage\": \"Auto-formatted $BASENAME (black + ruff)\"}"
        ;;
esac
exit 0
