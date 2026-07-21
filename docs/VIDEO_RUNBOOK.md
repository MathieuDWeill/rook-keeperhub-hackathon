# Rook DoraHacks Video Runbook

This runbook generates the final submission video from the local live proof.

## Prerequisites

- `.env` is present locally and contains the live KeeperHub/Sepolia configuration.
- `artifacts/deployment.json` exists from `make deploy`.
- `artifacts/live-proof.json` exists from the live KeeperHub execution.
- `ffmpeg`, `ffprobe`, `node`, `npm`, and macOS `say` are available.

The video scripts do not print `.env` and do not show terminals in the recording.

## Render

```bash
scripts/video/render_video.sh
```

The render script starts the API and Streamlit app, waits for readiness, records a clean browser session with Playwright, generates the voiceover, and writes:

- `artifacts/rook-demo-final.mp4`
- `artifacts/rook-demo-no-voice.mp4`
- `artifacts/rook-demo-thumbnail.png`

## Validation

```bash
ffprobe -v error -show_entries format=duration,size -show_entries stream=codec_name,codec_type,width,height,r_frame_rate -of json artifacts/rook-demo-final.mp4
ffmpeg -hide_banner -loglevel info -i artifacts/rook-demo-final.mp4 -vf "blackdetect=d=0.5:pix_th=0.10" -an -f null -
```

The final video should be 1920x1080, H.264, 30 fps, with AAC audio. The approved screen must show the real KeeperHub execution proof, and the blocked scenario must show `Payment safely blocked — client acceptance missing`.

## Live Proof Used

The recording reads the live proof from `artifacts/live-proof.json`; it does not submit a second approved transaction while recording. The blocked scenario is exercised through the API and must remain blocked before any KeeperHub execution attempt.
