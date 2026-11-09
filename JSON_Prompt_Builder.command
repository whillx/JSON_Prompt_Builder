#!/bin/bash
# Launcher for macOS and Linux. Uses uv when available so the app runs on
# a uv-managed Python (with Tkinter included); otherwise falls back to the
# system python3.
cd "$(dirname "$0")" || exit 1

# Shells started by double-clicking may not load the user's profile,
# so add uv's default install locations to PATH.
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"

if command -v uv >/dev/null 2>&1; then
    exec uv run main.py
else
    exec python3 main.py
fi
