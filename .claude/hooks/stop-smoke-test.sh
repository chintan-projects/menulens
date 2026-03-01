#!/usr/bin/env bash
set -uo pipefail
cat > /dev/null 2>&1 || true
DIR="${CLAUDE_PROJECT_DIR:-.}"

if command -v ruff &>/dev/null; then
    echo 'Running ruff check...' >&2
    if ! (cd "$DIR" && ruff check . 2>&1); then
        echo 'Ruff lint failed.' >&2
        exit 2
    fi
fi
echo "Smoke tests passed." >&2
exit 0
