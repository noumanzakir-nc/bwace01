#!/usr/bin/env bash
# BW-ACE — Docker convenience launcher for Linux / macOS
# Builds the image if it does not exist, then starts the container.
# Usage: ./docker-run.sh [--build]
set -euo pipefail

IMAGE="bwace:latest"
CONTAINER="bwace"

# Check Docker is available
if ! command -v docker >/dev/null 2>&1; then
    echo "Docker was not found on PATH."
    echo "Install Docker Engine: https://docs.docker.com/engine/install/"
    exit 1
fi

# Force a (re)build when --build is passed
if [ "${1:-}" = "--build" ]; then
    echo "Building Docker image..."
    docker build -t "$IMAGE" .
    BUILD_DONE=1
fi

# Build only if the image does not yet exist
if [ "${BUILD_DONE:-0}" = "0" ] && ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
    echo "Image not found — building for the first time..."
    docker build -t "$IMAGE" .
fi

# Remove a stopped container with the same name, if any
docker rm -f "$CONTAINER" >/dev/null 2>&1 || true

# Resolve env-file flag (optional)
ENVFLAG=""
if [ -f .env ]; then
    ENVFLAG="--env-file .env"
fi

echo "Starting BW-ACE …"
echo "Open http://localhost:8501 in your browser."
echo "Press Ctrl+C to stop."
echo ""

# shellcheck disable=SC2086
docker run --rm --name "$CONTAINER" -p 8501:8501 $ENVFLAG "$IMAGE"
