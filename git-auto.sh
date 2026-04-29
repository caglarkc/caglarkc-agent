#!/usr/bin/env bash

set -euo pipefail

# Always run from the script's project directory.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

git add .
git commit -m "s"
git push
