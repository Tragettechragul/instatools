#!/usr/bin/env bash
# One-time setup: Python env, browser, speech-to-text, Instagram login.
set -e
cd "$(dirname "$0")"
command -v ffmpeg >/dev/null || { echo "Install ffmpeg first (brew install ffmpeg / sudo apt install ffmpeg)"; exit 1; }
python3 -m venv .venv
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -e ".[transcribe]"
.venv/bin/playwright install chromium
if [ -z "$ANTHROPIC_API_KEY" ]; then
  read -rp "Anthropic API key (sk-ant-...): " KEY
  echo "export ANTHROPIC_API_KEY=$KEY" >> ~/.bashrc; export ANTHROPIC_API_KEY=$KEY
fi
mkdir -p ~/.local/bin && ln -sf "$PWD/.venv/bin/instatools" ~/.local/bin/instatools
.venv/bin/instatools login
echo "Done. Try: instatools analyze <instagram link>"
