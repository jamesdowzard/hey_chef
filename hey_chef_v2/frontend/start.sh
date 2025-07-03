#!/bin/bash

# Hey Chef Frontend Startup Script

echo "🍳 Starting Hey Chef Frontend..."
echo ""

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
    echo ""
fi

# Check if backend is running
echo "🔗 Checking backend connection..."
if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
    echo "✅ Backend is running on port 8000"
else
    echo "⚠️  Backend is not running on port 8000"
    echo "   Please start the FastAPI backend first:"
    echo "   cd ../backend && python main.py"
fi

echo ""
echo "🚀 Starting development server on http://localhost:3000"
echo ""

# Start the development server
npm run dev