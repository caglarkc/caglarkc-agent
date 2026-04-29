#!/usr/bin/env bash

set -euo pipefail

# Always run from the script's project directory.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if ! command -v inotifywait >/dev/null 2>&1; then
  echo "Missing dependency: inotifywait"
  echo "Install with: sudo apt-get install inotify-tools"
  exit 1
fi

echo "Auto push watcher started in: $SCRIPT_DIR"
echo "Press Ctrl+C to stop."

while true; do
  inotifywait -qq -r \
    -e modify,create,delete,move \
    --exclude '(\.git/|node_modules/|\.venv/|dist/|build/|\.next/)' \
    "$SCRIPT_DIR"

  # Small debounce to merge burst writes from editors.
  sleep 1

  git add -A

  # Skip commit/push if there is no staged diff.
  if git diff --cached --quiet; then
    continue
  fi

  COMMIT_MSG="auto: sync $(date '+%Y-%m-%d %H:%M:%S')"
  git commit -m "$COMMIT_MSG"
  git push

  echo "Pushed: $COMMIT_MSG"
done
