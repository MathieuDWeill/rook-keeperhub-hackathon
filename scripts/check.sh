#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python -m pytest -q
python -m compileall -q apps scripts
if [[ -d contracts/node_modules ]]; then
  (cd contracts && npm test)
else
  echo "contracts/node_modules absent: run 'cd contracts && npm install' before contract tests" >&2
  exit 1
fi
