#!/bin/bash

set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Function to kill background processes on exit
cleanup() {
    echo "Stopping services..."
    kill $(jobs -p) 2>/dev/null || true
}
trap cleanup EXIT

is_port_in_use() {
    local port="$1"
    if command -v lsof >/dev/null 2>&1; then
        lsof -nP -iTCP:"${port}" -sTCP:LISTEN >/dev/null 2>&1
    else
        return 1
    fi
}

find_free_port() {
    local preferred="$1"
    local max_tries="${2:-20}"
    local port="$preferred"
    local tries=0

    while [ "$tries" -le "$max_tries" ]; do
        if ! is_port_in_use "$port"; then
            echo "$port"
            return 0
        fi
        port=$((port + 1))
        tries=$((tries + 1))
    done

    echo ""
    return 1
}

echo "Resolving runtime configuration..."
if [ -x "${ROOT_DIR}/backend/venv/bin/python" ]; then
    PYTHON_BIN="${ROOT_DIR}/backend/venv/bin/python"
else
    PYTHON_BIN="$(command -v python3 || true)"
fi

if [ -z "${PYTHON_BIN}" ]; then
    echo "No Python interpreter found."
    exit 1
fi

BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
FRONTEND_HOST="${FRONTEND_HOST:-127.0.0.1}"
REQUESTED_BACKEND_PORT="${BACKEND_PORT:-8000}"
REQUESTED_FRONTEND_PORT="${FRONTEND_PORT:-5173}"

BACKEND_PORT="$(find_free_port "$REQUESTED_BACKEND_PORT" 20)"
if [ -z "${BACKEND_PORT}" ]; then
    echo "Unable to find a free backend port near ${REQUESTED_BACKEND_PORT}."
    exit 1
fi
if [ "${BACKEND_PORT}" != "${REQUESTED_BACKEND_PORT}" ]; then
    echo "Port ${REQUESTED_BACKEND_PORT} is busy. Using backend port ${BACKEND_PORT}."
fi

FRONTEND_PORT="$(find_free_port "$REQUESTED_FRONTEND_PORT" 20)"
if [ -z "${FRONTEND_PORT}" ]; then
    echo "Unable to find a free frontend port near ${REQUESTED_FRONTEND_PORT}."
    exit 1
fi
if [ "${FRONTEND_PORT}" != "${REQUESTED_FRONTEND_PORT}" ]; then
    echo "Port ${REQUESTED_FRONTEND_PORT} is busy. Using frontend port ${FRONTEND_PORT}."
fi

BACKEND_RELOAD_FLAG=""
if [ "${BACKEND_RELOAD:-0}" = "1" ]; then
    BACKEND_RELOAD_FLAG="--reload"
fi

echo "Starting Backend on ${BACKEND_HOST}:${BACKEND_PORT}..."
cd "${ROOT_DIR}/backend" && "${PYTHON_BIN}" -m uvicorn app.main:app ${BACKEND_RELOAD_FLAG} --host "${BACKEND_HOST}" --port "${BACKEND_PORT}" &
BACKEND_PID=$!

echo "Starting Frontend on ${FRONTEND_HOST}:${FRONTEND_PORT}..."
cd "${ROOT_DIR}/frontend"
if ! npm run dev -- --host "${FRONTEND_HOST}" --port "${FRONTEND_PORT}"; then
    FALLBACK_HOST="127.0.0.1"
    FALLBACK_PORT="$(find_free_port "$((FRONTEND_PORT + 1))" 20)"
    if [ -z "${FALLBACK_PORT}" ]; then
        echo "Frontend failed to start and no fallback port is available."
        exit 1
    fi
    echo "Retrying frontend on ${FALLBACK_HOST}:${FALLBACK_PORT}..."
    npm run dev -- --host "${FALLBACK_HOST}" --port "${FALLBACK_PORT}"
fi

# Wait for backend to finish (if frontend exits)
wait "${BACKEND_PID}"
