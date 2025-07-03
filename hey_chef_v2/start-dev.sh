#!/bin/bash

# Hey Chef v2 Development Startup Script

echo "🍳 Starting Hey Chef v2 Development Environment..."

# Check if we're in the right directory
if [[ ! -d "backend" ]] || [[ ! -d "frontend" ]]; then
    echo "❌ Please run this script from the hey_chef_v2 directory"
    echo "   Current directory: $(pwd)"
    echo "   Expected: /path/to/hey_chef/hey_chef_v2"
    exit 1
fi

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
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ Servers stopped"
    exit 0
}

# Set trap to cleanup on Ctrl+C
trap cleanup SIGINT

# Wait for either process to finish
wait