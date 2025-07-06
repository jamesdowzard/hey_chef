#!/bin/bash

# Hey Chef v2 Development Stop Script
# Safely stops all development servers and cleans up processes

echo "🛑 Stopping Hey Chef v2 Development Environment..."

# Function to kill processes by port
kill_by_port() {
    local port=$1
    local service_name=$2
    
    echo "🔍 Checking for processes on port $port ($service_name)..."
    
    # Find processes using the port
    local pids=$(lsof -ti :$port 2>/dev/null)
    
    if [[ -n "$pids" ]]; then
        echo "📝 Found processes on port $port: $pids"
        
        # Try graceful shutdown first
        echo "⏹️  Attempting graceful shutdown..."
        kill $pids 2>/dev/null
        
        # Wait a moment for graceful shutdown
        sleep 2
        
        # Check if processes are still running
        local remaining_pids=$(lsof -ti :$port 2>/dev/null)
        
        if [[ -n "$remaining_pids" ]]; then
            echo "💥 Force killing remaining processes: $remaining_pids"
            kill -9 $remaining_pids 2>/dev/null
        fi
        
        echo "✅ Port $port ($service_name) cleaned up"
    else
        echo "✅ Port $port ($service_name) is already free"
    fi
}

# Function to kill processes by name pattern
kill_by_pattern() {
    local pattern=$1
    local service_name=$2
    
    echo "🔍 Checking for $service_name processes..."
    
    # Find processes matching the pattern
    local pids=$(ps aux | grep -E "$pattern" | grep -v grep | awk '{print $2}')
    
    if [[ -n "$pids" ]]; then
        echo "📝 Found $service_name processes: $pids"
        
        # Try graceful shutdown first
        echo "⏹️  Attempting graceful shutdown..."
        echo "$pids" | xargs kill 2>/dev/null
        
        # Wait a moment for graceful shutdown
        sleep 2
        
        # Check if processes are still running
        local remaining_pids=$(ps aux | grep -E "$pattern" | grep -v grep | awk '{print $2}')
        
        if [[ -n "$remaining_pids" ]]; then
            echo "💥 Force killing remaining processes: $remaining_pids"
            echo "$remaining_pids" | xargs kill -9 2>/dev/null
        fi
        
        echo "✅ $service_name processes cleaned up"
    else
        echo "✅ No $service_name processes found"
    fi
}

# Kill by specific ports
kill_by_port 3000 "Frontend (Vite)"
kill_by_port 3001 "Frontend (Vite backup)"
kill_by_port 8000 "Backend (FastAPI)"

# Kill by process patterns
kill_by_pattern "hey_chef.*main\.py" "Hey Chef Backend"
kill_by_pattern "vite.*hey-chef-v2-frontend" "Hey Chef Frontend"
kill_by_pattern "uvicorn.*main:" "Uvicorn Server"

# Additional cleanup for any Node processes in the frontend directory
echo "🔍 Checking for Node processes in Hey Chef frontend directory..."
frontend_dir="/Users/jamesdowzard/Documents/code/gh/hey_chef/hey_chef_v2/frontend"
node_pids=$(ps aux | grep "node.*$frontend_dir" | grep -v grep | awk '{print $2}')

if [[ -n "$node_pids" ]]; then
    echo "📝 Found Node processes in frontend directory: $node_pids"
    echo "$node_pids" | xargs kill -9 2>/dev/null
    echo "✅ Frontend Node processes cleaned up"
fi

# Additional cleanup for any Python processes in the backend directory
echo "🔍 Checking for Python processes in Hey Chef backend directory..."
backend_dir="/Users/jamesdowzard/Documents/code/gh/hey_chef/hey_chef_v2/backend"
python_pids=$(ps aux | grep "python.*$backend_dir" | grep -v grep | awk '{print $2}')

if [[ -n "$python_pids" ]]; then
    echo "📝 Found Python processes in backend directory: $python_pids"
    echo "$python_pids" | xargs kill -9 2>/dev/null
    echo "✅ Backend Python processes cleaned up"
fi

# Final verification
echo ""
echo "🔍 Final verification..."

# Check if ports are now free
for port in 3000 3001 8000; do
    if lsof -ti :$port >/dev/null 2>&1; then
        echo "⚠️  Warning: Port $port is still in use"
        lsof -i :$port
    else
        echo "✅ Port $port is free"
    fi
done

echo ""
echo "🎉 Hey Chef v2 development environment stopped successfully!"
echo ""
echo "💡 To start again: ./start-dev.sh"
echo "💡 To check what's running: ./check-ports.sh"