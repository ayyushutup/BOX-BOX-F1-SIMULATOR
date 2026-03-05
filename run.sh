#!/bin/bash

# Function to kill background processes on exit
cleanup() {
    echo "Stopping services..."
    kill $(jobs -p) 2>/dev/null
}
trap cleanup EXIT

echo "Starting Backend..."
cd backend && /Library/Frameworks/Python.framework/Versions/3.14/bin/python3.14 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo "Starting Frontend..."
cd frontend && npm run dev -- --host 0.0.0.0 --port 5173

# Wait for backend to finish (if frontend exits)
wait $BACKEND_PID
