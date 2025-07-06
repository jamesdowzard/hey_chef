#!/bin/bash

# Hey Chef v2 Port Status Checker
# Shows what's running on the development ports

echo "🔍 Hey Chef v2 Port Status Check"
echo "================================="

# Function to check a specific port
check_port() {
    local port=$1
    local service_name=$2
    
    echo ""
    echo "📍 Port $port ($service_name):"
    
    if lsof -i :$port >/dev/null 2>&1; then
        echo "🟢 IN USE"
        lsof -i :$port | head -1
        lsof -i :$port | grep -v COMMAND | while read line; do
            echo "   $line"
        done
    else
        echo "🟡 FREE"
    fi
}

# Check all development ports
check_port 3000 "Frontend (Primary)"
check_port 3001 "Frontend (Backup)" 
check_port 8000 "Backend API"
check_port 3333 "Notion MCP Server"

echo ""
echo "🔍 Hey Chef Related Processes:"
echo "============================="

# Check for Hey Chef processes
chef_processes=$(ps aux | grep -E "(hey_chef|hey-chef)" | grep -v grep | grep -v check-ports)

if [[ -n "$chef_processes" ]]; then
    echo "🟢 Found Hey Chef processes:"
    echo "$chef_processes" | while read line; do
        echo "   $line"
    done
else
    echo "🟡 No Hey Chef processes found"
fi

echo ""
echo "🔍 Node.js Development Servers:"
echo "==============================="

# Check for Node/Vite processes
node_processes=$(ps aux | grep -E "(node.*vite|vite)" | grep -v grep)

if [[ -n "$node_processes" ]]; then
    echo "🟢 Found Node/Vite processes:"
    echo "$node_processes" | while read line; do
        echo "   $line"
    done
else
    echo "🟡 No Node/Vite processes found"
fi

echo ""
echo "🔍 Python Development Servers:"
echo "=============================="

# Check for Python/Uvicorn processes
python_processes=$(ps aux | grep -E "(python.*main|uvicorn)" | grep -v grep)

if [[ -n "$python_processes" ]]; then
    echo "🟢 Found Python/Uvicorn processes:"
    echo "$python_processes" | while read line; do
        echo "   $line"
    done
else
    echo "🟡 No Python/Uvicorn processes found"
fi

echo ""
echo "💡 Commands:"
echo "============"
echo "• Start development: ./start-dev.sh"
echo "• Stop development:  ./stop-dev.sh"
echo "• Force cleanup:     ./cleanup-ports.sh"
echo "• Check status:      ./check-ports.sh"