#!/bin/bash
# FFQ Dev Launcher - starts both backend and frontend

echo "🥗 Starting FFQ Manager..."

# Start FastAPI backend in background
cd backend
uv venv
uv pip install -r requirements.txt -q
uv run uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!
echo "✅ Backend running at http://localhost:8000"

# Start React frontend
cd ../frontend
npm install -q
npm run dev &
FRONTEND_PID=$!
echo "✅ Frontend running at http://localhost:5173"

echo ""
echo "📋 Open http://localhost:5173 in your browser"
echo "📋 API docs at http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers."

# Cleanup on exit
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo 'Stopped.'" EXIT
wait
