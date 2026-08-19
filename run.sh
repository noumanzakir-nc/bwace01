#!/usr/bin/env bash
set -euo pipefail

MIN_MAJOR=3
MIN_MINOR=11

if ! command -v python3 >/dev/null 2>&1; then
    echo "Python was not found on PATH. Install Python ${MIN_MAJOR}.${MIN_MINOR} or newer."
    exit 1
fi

PYVER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
FOUND_MAJOR=$(echo "$PYVER" | cut -d. -f1)
FOUND_MINOR=$(echo "$PYVER" | cut -d. -f2)

if [ "$FOUND_MAJOR" -lt "$MIN_MAJOR" ] || { [ "$FOUND_MAJOR" -eq "$MIN_MAJOR" ] && [ "$FOUND_MINOR" -lt "$MIN_MINOR" ]; }; then
    echo "Found Python ${PYVER}, but ${MIN_MAJOR}.${MIN_MINOR}+ is required."
    exit 1
fi

if [ ! -d .venv ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

if [ ! -f .venv/.provisioned ]; then
    echo "Installing dependencies..."
    .venv/bin/python -m pip install --quiet --upgrade pip
    .venv/bin/python -m pip install --quiet -e ".[dev]"
    touch .venv/.provisioned
fi

exec .venv/bin/streamlit run src/bwace/app/main.py
