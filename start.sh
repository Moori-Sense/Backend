#!/bin/bash

# Start the backend server
echo "Starting backend server..."
cd /home/user/webapp/src
python3 main.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start the frontend development server
echo "Starting frontend server..."
cd /home/user/webapp/frontend
npm run dev &
FRONTEND_PID=$!

echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"

# Keep script running
wait $BACKEND_PID $FRONTEND_PID