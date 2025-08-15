#!/bin/bash

# Concatly Development Startup Script with Logging
# This script starts both frontend and backend with proper logging

set -e

echo "🚀 Starting Concatly Development Environment"
echo "=============================================="

# Create logs directory if it doesn't exist
mkdir -p logs

# Function to cleanup background processes
cleanup() {
    echo "🛑 Shutting down services..."
    if [ -n "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ -n "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    exit 0
}

# Trap cleanup on script exit
trap cleanup EXIT INT TERM

# Check if ports are available
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port 8000 is already in use. Stopping existing process..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    sleep 2
fi

if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port 3000 is already in use. Next.js will use an alternative port."
fi

echo "📝 Log files will be created in: $(pwd)/logs/"
echo "📖 View logs with: python view_logs.py"
echo ""

# Start backend in background
echo "🔧 Starting Python backend (FastAPI)..."
cd /Users/chrissyd/DocJan
source .venv/bin/activate
python services/main.py > logs/backend_console.log 2>&1 &
BACKEND_PID=$!
echo "📱 Backend started (PID: $BACKEND_PID)"

# Wait a moment for backend to start
sleep 3

# Start frontend in background
echo "🎨 Starting Next.js frontend..."
cd /Users/chrissyd/DocJan/nextjs
npm run dev > ../logs/frontend_console.log 2>&1 &
FRONTEND_PID=$!
echo "🌐 Frontend started (PID: $FRONTEND_PID)"

echo ""
echo "✅ Development environment is ready!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌐 Frontend: http://localhost:3000 (or alternative port)"
echo "🔧 Backend:  http://localhost:8000"
echo "📊 Health:   http://localhost:8000/health"
echo "📝 Logs:     python view_logs.py"
echo "📝 Live logs: python view_logs.py --follow"
echo "📝 Errors:   python view_logs.py --errors"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for processes
wait
