#!/bin/bash

# Function to kill background processes on exit
cleanup() {
    echo "Stopping services..."
    kill $(jobs -p) 2>/dev/null
}
trap cleanup EXIT

set -e
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Starting Backend..."
if [ -x "${ROOT_DIR}/backend/venv/bin/python" ]; then
    PYTHON_BIN="${ROOT_DIR}/backend/venv/bin/python"
else
    PYTHON_BIN="$(command -v python3)"
fi

if [ -z "${PYTHON_BIN}" ]; then
    echo "No Python interpreter found."
    exit 1
fi

BACKEND_RELOAD_FLAG=""
if [ "${BACKEND_RELOAD:-0}" = "1" ]; then
    BACKEND_RELOAD_FLAG="--reload"
fi

cd "${ROOT_DIR}/backend" && "${PYTHON_BIN}" -m uvicorn app.main:app ${BACKEND_RELOAD_FLAG} --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo "Starting Frontend..."
cd "${ROOT_DIR}/frontend" && npm run dev -- --host 0.0.0.0 --port 5173

# Wait for backend to finish (if frontend exits)
wait $BACKEND_PID
