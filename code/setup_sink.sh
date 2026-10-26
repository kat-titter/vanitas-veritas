#!/bin/bash
# setup_sink.sh: everything the sink's MacBook Pro needs, once. Safe to run again: it skips what is already there.
#   bash code/setup_sink.sh          install, then dream two test frames (about 25 min the first time, mostly downloads)
#   bash code/setup_sink.sh --test   only the test
# Downloads (first run): Python packages about 2.5 GB, Stable Diffusion 1.5 about 4 GB, LCM-LoRA 135 MB, Real-ESRGAN 64 MB,
# cloudflared about 20 MB.
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT=$(pwd); VENV="$ROOT/.venv"; PY="$VENV/bin/python"
say() { printf '\n\033[1m%s\033[0m\n' "$1"; }

if [ "${1:-}" != "--test" ]; then
  say "1/6  Python"
  command -v python3 >/dev/null || { echo "Install the Xcode command line tools first: xcode-select --install"; exit 1; }
  [ -x "$PY" ] || python3 -m venv "$VENV"
  "$PY" -m pip install --quiet --upgrade pip

  say "2/6  packages (pinned to the versions the piece was made with)"
  "$PY" -m pip install --quiet torch==2.8.0 diffusers==0.36.0 transformers==4.57.6 accelerate==1.10.1 peft==0.17.1 \
    safetensors==0.7.0 pillow==11.3.0 numpy==2.0.2 coremltools==9.0 spandrel==0.4.1 opencv-python==4.13.0.92

  say "3/6  the upscaler"
  mkdir -p code/models
  [ -s code/models/RealESRGAN_x4plus.pth ] || curl -fL --retry 3 -o code/models/RealESRGAN_x4plus.pth \
    https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth
  [ -d code/models/RealESRGAN_x4plus_640x480.mlpackage ] || "$PY" code/upscale.py

  say "4/6  the moodboard"
  mkdir -p source/moodboard source/mj_inbox
  if ! ls source/moodboard/*.webp >/dev/null 2>&1; then cp documents/assets/mood[1-8].webp source/moodboard/; fi
  echo "$(ls source/moodboard | wc -l | tr -d ' ') pictures in source/moodboard"

  say "5/6  the public address (cloudflared, and the key that points the public basin here)"
  mkdir -p "$HOME/.local/bin" spring_feed
  [ -x "$HOME/.local/bin/cloudflared" ] || curl -fsL --retry 3 \
    https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-arm64.tgz | tar -xz -C "$HOME/.local/bin" cloudflared
  if [ -s spring_feed/github_token ]; then echo "key in spring_feed/github_token"
  else echo "No key yet: save a fine-grained GitHub token (this repository only, Contents: read and write) in spring_feed/github_token."
       echo "Without it the piece runs, but the public address only shows in the log."; fi
fi

say "6/6  test: two dreams (the models download now if this is the first run)"
HF_HUB_OFFLINE=0 "$PY" code/sink.py --sheet 2 --out "$ROOT/spring_feed/test"   # online once: the models download here
echo; echo "Done. The contact sheet is spring_feed/test/sheet.jpg. Next: bash code/sink.sh install"
