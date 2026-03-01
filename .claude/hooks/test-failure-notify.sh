#!/usr/bin/env bash
set -uo pipefail
INPUT=$(cat 2>/dev/null || echo "{}")
CMD=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)
EXIT_CODE=$(echo "$INPUT" | jq -r '.tool_response.exit_code // 0' 2>/dev/null)
case "$CMD" in
    *pytest*|*"make test"*|*"npm test"*|*"pnpm test"*|*"npx tsc"*|*"cargo test"*|*"make lint"*|*"make typecheck"*|*"ruff check"*|*"mypy"*)
        ;;
    *) exit 0 ;;
esac
if [ "$EXIT_CODE" != "0" ]; then
    echo "{\"additionalContext\": \"Tests/checks just failed (exit code $EXIT_CODE). Consider using /log-bug to capture this.\"}"
fi
exit 0
