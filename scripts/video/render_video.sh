#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

mkdir -p artifacts/video

WEBM="artifacts/video/rook-demo-no-voice.webm"
NO_VOICE="artifacts/rook-demo-no-voice.mp4"
FINAL="artifacts/rook-demo-final.mp4"
VOICE="artifacts/video/voiceover.wav"
SUBTITLES="scripts/video/subtitles.srt"

npm ci --prefix scripts/video
npm exec --prefix scripts/video -- playwright install chromium
node scripts/video/record_demo.mjs

ffmpeg -y -hide_banner -loglevel error \
  -i "$WEBM" \
  -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=#fbf7ef,fps=30,format=yuv420p" \
  -c:v libx264 -preset veryfast -crf 18 -movflags +faststart \
  -an "$NO_VOICE"

scripts/video/generate_voiceover.sh >/dev/null

ffmpeg -y -hide_banner -loglevel error \
  -i "$NO_VOICE" \
  -i "$VOICE" \
  -i "$SUBTITLES" \
  -filter_complex "[1:a]apad[a]" \
  -map 0:v:0 -map "[a]" -map 2:0 \
  -c:v copy \
  -c:a aac -b:a 160k -ar 48000 -ac 2 \
  -c:s mov_text \
  -metadata:s:s:0 language=eng \
  -shortest \
  -movflags +faststart \
  "$FINAL"

ffmpeg -y -hide_banner -loglevel error \
  -ss 00:00:04 \
  -i "$FINAL" \
  -frames:v 1 \
  -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=#fbf7ef" \
  artifacts/rook-demo-thumbnail.png

echo "$FINAL"
