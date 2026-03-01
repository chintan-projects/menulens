#!/usr/bin/env bash
set -uo pipefail
cat > /dev/null 2>&1 || true
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
    echo 'export PYTHONPATH="."' >> "$CLAUDE_ENV_FILE"
fi
DIR="${CLAUDE_PROJECT_DIR:-.}"
echo "=== SESSION STATE (active only — archive in PROGRESS-archive.yaml) ==="
if [ -f "$DIR/PROGRESS.yaml" ]; then
    echo "--- PROGRESS.yaml ---"
    cat "$DIR/PROGRESS.yaml"
fi
if [ -f "$DIR/BUGS.yaml" ]; then
    OPEN_BUGS=$(grep -c 'status: open' "$DIR/BUGS.yaml" 2>/dev/null || echo "0")
    if [ "$OPEN_BUGS" -gt 0 ]; then
        echo "--- BUGS.yaml ($OPEN_BUGS open) ---"
        cat "$DIR/BUGS.yaml"
    else
        echo "--- BUGS: none open ---"
    fi
fi
echo "--- Recent commits ---"
git -C "$DIR" log --oneline -5 2>/dev/null || echo "(no git history)"
CHANGES=$(git -C "$DIR" diff --name-only 2>/dev/null)
if [ -n "$CHANGES" ]; then
    echo "--- Uncommitted changes ---"
    echo "$CHANGES"
fi
exit 0
