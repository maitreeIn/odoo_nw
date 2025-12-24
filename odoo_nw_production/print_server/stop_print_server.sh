#!/bin/bash
# Stop Print Server

# Find PID of python3 app.py
PID=$(pgrep -f "python3 app.py")

if [ -z "$PID" ]; then
    echo "Print Server is not running."
else
    echo "Stopping Print Server (PID: $PID)..."
    kill $PID
    echo "Print Server stopped."
fi
