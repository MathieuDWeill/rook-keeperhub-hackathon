#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
[[ -d .venv ]] || { echo "Run ./scripts/bootstrap.sh first"; exit 1; }
cp -n .env.example .env 2>/dev/null || true
. .venv/bin/activate
python scripts/demo_smoke.py
printf '\nRook local proof passed. Start the judge UI with:\n  make run-api\n  make run-demo\n'
