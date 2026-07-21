#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

mkdir -p artifacts/video

VOICE="${ROOK_VOICE:-Samantha}"
RATE="${ROOK_VOICE_RATE:-170}"
TEXT="scripts/video/narration.txt"
AIFF="artifacts/video/voiceover.aiff"
WAV="artifacts/video/voiceover.wav"

if ! say -v "$VOICE" "voice check" >/dev/null 2>&1; then
  VOICE="$(say -v '?' | awk 'NR==1 {print $1}')"
fi

say -v "$VOICE" -r "$RATE" -f "$TEXT" -o "$AIFF"
ffmpeg -y -hide_banner -loglevel error -i "$AIFF" -ar 48000 -ac 2 "$WAV"

echo "$WAV"
