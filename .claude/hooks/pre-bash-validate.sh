#!/usr/bin/env bash
set -uo pipefail
INPUT=$(cat 2>/dev/null || echo "{}")
CMD=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)
[ -z "$CMD" ] && exit 0
deny() {
    jq -n --arg reason "$1" \
      '{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": $reason}}'
    exit 0
}
echo "$CMD" | grep -qiE 'rm\s+-rf\s+/' && deny "Blocked: recursive delete at filesystem root"
echo "$CMD" | grep -qiE 'rm\s+-rf\s+~' && deny "Blocked: recursive delete of home directory"
echo "$CMD" | grep -qiE 'rm\s+-rf\s+\.' && deny "Blocked: recursive delete of current directory"
echo "$CMD" | grep -qiE '>\s*/dev/sd' && deny "Blocked: writing to block device"
echo "$CMD" | grep -qiE 'mkfs\.' && deny "Blocked: filesystem format command"
echo "$CMD" | grep -qiE 'dd\s+.*of=/' && deny "Blocked: dd to device"
echo "$CMD" | grep -qiE 'git\s+push\s+.*--force' && deny "Blocked: force push. Use --force-with-lease."
echo "$CMD" | grep -qiE 'git\s+reset\s+--hard' && deny "Blocked: hard reset. Use git stash or soft reset."
echo "$CMD" | grep -qiE 'git\s+clean\s+-fd' && deny "Blocked: git clean removes untracked files permanently."
echo "$CMD" | grep -qiE '^sudo\s+' && deny "Blocked: sudo not permitted."
echo "$CMD" | grep -qiE 'chmod\s+777' && deny "Blocked: world-writable permissions."
echo "$CMD" | grep -qiE 'curl.*production' && deny "Blocked: direct production access."
echo "$CMD" | grep -qiE 'deploy.*prod' && deny "Blocked: production deployment requires manual approval."
exit 0
