#!/bin/bash

# Hey Chef v2 Development Startup Script

echo "🍳 Starting Hey Chef v2 Development Environment..."

# Check if we're in the right directory
if [[ ! -d "backend" ]] || [[ ! -d "frontend" ]]; then
    echo "❌ Please run this script from the hey_chef root directory"
    echo "   Current directory: $(pwd)"
    echo "   Expected: /path/to/hey_chef"
    exit 1
fi

# Function to kill processes by port safely
cleanup_port() {
    local port=$1
    local service_name=$2
    
    local pids=$(lsof -ti :$port 2>/dev/null)
    if [[ -n "$pids" ]]; then
        echo "🧹 Cleaning up existing $service_name processes on port $port..."
        kill $pids 2>/dev/null
        sleep 1
        
        # Force kill if still running
        local remaining_pids=$(lsof -ti :$port 2>/dev/null)
        if [[ -n "$remaining_pids" ]]; then
            kill -9 $remaining_pids 2>/dev/null
        fi
        echo "✅ Port $port cleaned up"
    fi
}

# Pre-startup cleanup
echo "🧹 Cleaning up any existing processes..."
cleanup_port 3000 "Frontend"
cleanup_port 3001 "Frontend (backup)"
cleanup_port 8000 "Backend"

# Additional cleanup for any hanging processes
pkill -f "hey_chef.*main\.py" 2>/dev/null || true
pkill -f "vite.*hey-chef-v2-frontend" 2>/dev/null || true

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check dependencies
echo "📋 Checking dependencies..."

if ! command_exists python3; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

if ! command_exists node; then
    echo "❌ Node.js is required but not installed"
    exit 1
fi

if ! command_exists npm; then
    echo "❌ npm is required but not installed"
    exit 1
fi

# Check environment variables
echo "🔑 Checking environment variables..."

if [[ -z "$OPENAI_API_KEY" ]]; then
    echo "⚠️  Warning: OPENAI_API_KEY not set. Voice features may not work."
    echo "   Set it with: export OPENAI_API_KEY=your_key_here"
fi

if [[ -z "$PICO_ACCESS_KEY" ]]; then
    echo "⚠️  Warning: PICO_ACCESS_KEY not set. Wake word detection may not work."
    echo "   Set it with: export PICO_ACCESS_KEY=your_key_here"
fi

# Start backend
echo "🚀 Starting FastAPI backend..."
cd backend

# Install backend dependencies if needed
if [[ ! -d "venv" ]]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt

# Start backend in background
python main.py &
BACKEND_PID=$!

echo "✅ Backend started (PID: $BACKEND_PID)"

# Start frontend
echo "🎨 Starting React frontend..."
cd ../frontend

# Install frontend dependencies if needed
if [[ ! -d "node_modules" ]]; then
    echo "📦 Installing npm dependencies..."
    npm install
fi

# Start frontend
echo "✅ Starting frontend development server..."
npm run dev &
FRONTEND_PID=$!

echo ""
echo "🎉 Hey Chef v2 is starting up!"
echo ""
echo "📍 Frontend: http://localhost:3000"
echo "📍 Backend API: http://localhost:8000"
echo "📍 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down Hey Chef v2..."
    
    # Kill the specific PIDs we started
    if [[ -n "$BACKEND_PID" ]] && kill -0 $BACKEND_PID 2>/dev/null; then
        echo "⏹️  Stopping backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null
        sleep 2
        # Force kill if still running
        if kill -0 $BACKEND_PID 2>/dev/null; then
            kill -9 $BACKEND_PID 2>/dev/null
        fi
    fi
    
    if [[ -n "$FRONTEND_PID" ]] && kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "⏹️  Stopping frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID 2>/dev/null
        sleep 2
        # Force kill if still running
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            kill -9 $FRONTEND_PID 2>/dev/null
        fi
    fi
    
    # Additional cleanup for any remaining processes
    cleanup_port 3000 "Frontend"
    cleanup_port 3001 "Frontend (backup)"
    cleanup_port 8000 "Backend"
    
    echo "✅ Hey Chef v2 development environment stopped"
    echo "💡 If you still see port conflicts, run: ./stop-dev.sh"
    exit 0
}

# Set trap to cleanup on Ctrl+C
trap cleanup SIGINT

# Wait for either process to finish
wait