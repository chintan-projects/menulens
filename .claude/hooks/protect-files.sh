#!/usr/bin/env bash
set -uo pipefail
INPUT=$(cat 2>/dev/null || echo "{}")
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null)
[ -z "$FILE" ] && exit 0
BASENAME=$(basename "$FILE")
deny_edit() {
    jq -n --arg reason "$1" \
      '{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": $reason}}'
    exit 0
}
case "$BASENAME" in
    package-lock.json) deny_edit "Protected: auto-generated. Run npm install instead." ;;
    pnpm-lock.yaml)    deny_edit "Protected: auto-generated. Run pnpm install instead." ;;
    uv.lock)           deny_edit "Protected: auto-generated. Run uv sync instead." ;;
    Cargo.lock)        deny_edit "Protected: auto-generated. Run cargo build instead." ;;
    Package.resolved)  deny_edit "Protected: auto-generated. Run swift package resolve instead." ;;
    .env|.env.local|.env.production) deny_edit "Protected: contains secrets. Edit manually." ;;
esac
echo "$FILE" | grep -q '\.git/' && deny_edit "Protected: .git internals."
echo "$FILE" | grep -q 'node_modules/' && deny_edit "Protected: managed by package manager."
exit 0
