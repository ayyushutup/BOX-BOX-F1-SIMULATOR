#!/bin/bash

# Function to kill background processes on exit
cleanup() {
    echo "Stopping services..."
    kill $(jobs -p) 2>/dev/null
}
trap cleanup EXIT

echo "Starting Backend..."
cd backend && uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!

echo "Starting Frontend..."
cd frontend && npm run dev

# Wait for backend to finish (if frontend exits)
wait $BACKEND_PID
