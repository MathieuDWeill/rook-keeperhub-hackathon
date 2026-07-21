#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
fail=0
for cmd in python3 node npm; do command -v "$cmd" >/dev/null || { echo "Missing: $cmd"; fail=1; }; done
[[ -f .env ]] || echo "INFO: .env absent; bootstrap will copy .env.example"
grep -RInE '(PRIVATE_KEY|API_KEY)=[^[:space:]]+' \
  --exclude='.env' \
  --exclude='.env.example' \
  --exclude-dir='.git' \
  --exclude-dir='.venv' \
  --exclude-dir='node_modules' \
  . | grep -v '\.\.\.' && { echo "Possible committed secret above"; fail=1; } || true
find . -type f -size +20M \
  -not -path './.git/*' \
  -not -path './.venv/*' \
  -not -path './contracts/node_modules/*' \
  -not -path './scripts/video/node_modules/*' \
  -not -path './artifacts/video/*' \
  -not -path './artifacts/*.mp4' \
  -not -path './artifacts/*.webm' \
  -print | grep . && { echo "Large files found"; fail=1; } || true
exit "$fail"
