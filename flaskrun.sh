#!/bin/bash

PORT=5000  # Change to your Flask port if different

# Find the process using the specified port and kill it
PID=$(lsof -t -i:$PORT)
if [ ! -z "$PID" ]; then
    echo "Killing process $PID using port $PORT"
    kill -9 $PID
fi

# Run the Flask application
flask run --port=$PORT -h 0.0.0.0