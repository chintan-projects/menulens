#!/usr/bin/env bash
set -uo pipefail
cat > /dev/null 2>&1 || true
DIR="${CLAUDE_PROJECT_DIR:-.}"
BUGS_FILE="$DIR/BUGS.yaml"
if [ -f "$BUGS_FILE" ]; then
    CRITICAL_COUNT=$(python3 -c "
import yaml, sys
try:
    with open('$BUGS_FILE') as f:
        bugs = yaml.safe_load(f)
    if not bugs or not isinstance(bugs, list):
        print(0)
    else:
        count = sum(1 for b in bugs if b.get('severity') == 'critical' and b.get('status') == 'open')
        print(count)
except Exception:
    print(0)
" 2>/dev/null)
    if [ "${CRITICAL_COUNT:-0}" -gt 0 ]; then
        echo "Cannot complete task: $CRITICAL_COUNT critical bug(s) still open." >&2
        exit 2
    fi
fi
exit 0
