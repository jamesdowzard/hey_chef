#!/bin/bash

# Hey Chef v2 Force Port Cleanup
# Nuclear option - kills all processes on development ports

echo "💥 Hey Chef v2 Force Port Cleanup"
echo "=================================="
echo ""
echo "⚠️  WARNING: This will forcefully kill ALL processes using development ports!"
echo "⚠️  This includes non-Hey Chef processes that might be using these ports."
echo ""

# Ask for confirmation
read -p "Are you sure you want to continue? (y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cleanup cancelled"
    exit 0
fi

echo "💥 Force killing all processes on development ports..."

# Function to force kill by port
force_kill_port() {
    local port=$1
    local service_name=$2
    
    echo "💥 Force killing port $port ($service_name)..."
    
    local pids=$(lsof -ti :$port 2>/dev/null)
    if [[ -n "$pids" ]]; then
        echo "   Found PIDs: $pids"
        echo "$pids" | xargs kill -9 2>/dev/null
        echo "   ✅ Port $port cleared"
    else
        echo "   ✅ Port $port was already free"
    fi
}

# Force kill all development ports
force_kill_port 3000 "Frontend"
force_kill_port 3001 "Frontend Backup"
force_kill_port 8000 "Backend"
force_kill_port 3333 "Notion MCP"

# Kill by process name patterns
echo ""
echo "💥 Killing Hey Chef processes by pattern..."

pkill -9 -f "hey_chef" 2>/dev/null && echo "   ✅ Hey Chef processes killed" || echo "   ✅ No Hey Chef processes found"
pkill -9 -f "hey-chef" 2>/dev/null && echo "   ✅ Hey-Chef processes killed" || echo "   ✅ No Hey-Chef processes found"

# Kill Node processes in the frontend directory
frontend_dir="/Users/jamesdowzard/Documents/code/gh/hey_chef/hey_chef_v2/frontend"
echo "💥 Killing Node processes in frontend directory..."
pkill -9 -f "node.*$frontend_dir" 2>/dev/null && echo "   ✅ Frontend Node processes killed" || echo "   ✅ No frontend Node processes found"

# Kill Python processes in the backend directory  
backend_dir="/Users/jamesdowzard/Documents/code/gh/hey_chef/hey_chef_v2/backend"
echo "💥 Killing Python processes in backend directory..."
pkill -9 -f "python.*$backend_dir" 2>/dev/null && echo "   ✅ Backend Python processes killed" || echo "   ✅ No backend Python processes found"

# Kill Uvicorn processes
echo "💥 Killing Uvicorn processes..."
pkill -9 -f "uvicorn" 2>/dev/null && echo "   ✅ Uvicorn processes killed" || echo "   ✅ No Uvicorn processes found"

# Kill Vite processes
echo "💥 Killing Vite processes..."
pkill -9 -f "vite" 2>/dev/null && echo "   ✅ Vite processes killed" || echo "   ✅ No Vite processes found"

echo ""
echo "🔍 Final verification..."

# Check if ports are now free
all_clear=true
for port in 3000 3001 8000 3333; do
    if lsof -ti :$port >/dev/null 2>&1; then
        echo "⚠️  Port $port is STILL in use:"
        lsof -i :$port
        all_clear=false
    else
        echo "✅ Port $port is free"
    fi
done

echo ""
if [[ "$all_clear" == true ]]; then
    echo "🎉 All development ports are now free!"
    echo "💡 You can now run: ./start-dev.sh"
else
    echo "⚠️  Some ports are still in use. You may need to manually kill those processes."
    echo "💡 Run './check-ports.sh' to see what's still running."
fi