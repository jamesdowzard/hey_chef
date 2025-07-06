#!/bin/bash

# Hey Chef v2 - Comprehensive Test Runner
# This script runs all tests with error detection and feedback loops

set -e

echo "🧪 Hey Chef v2 - Comprehensive Test Suite"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if a service is running
check_service() {
    local service_name=$1
    local url=$2
    local max_attempts=10
    local attempt=1
    
    print_status "Checking $service_name at $url..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$url/health" > /dev/null 2>&1; then
            print_status "$service_name is running ✅"
            return 0
        fi
        
        print_warning "$service_name not ready (attempt $attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done
    
    print_error "$service_name is not running after $max_attempts attempts"
    return 1
}

# Function to start a service in the background
start_service() {
    local service_name=$1
    local command=$2
    local pidfile=$3
    
    print_status "Starting $service_name..."
    
    # Kill existing process if running
    if [ -f "$pidfile" ]; then
        local pid=$(cat "$pidfile")
        if kill -0 "$pid" 2>/dev/null; then
            print_warning "Stopping existing $service_name process (PID: $pid)"
            kill "$pid"
            sleep 2
        fi
        rm -f "$pidfile"
    fi
    
    # Start the service
    eval "$command" &
    local pid=$!
    echo "$pid" > "$pidfile"
    
    print_status "$service_name started with PID: $pid"
    sleep 3
}

# Function to stop a service
stop_service() {
    local service_name=$1
    local pidfile=$2
    
    if [ -f "$pidfile" ]; then
        local pid=$(cat "$pidfile")
        if kill -0 "$pid" 2>/dev/null; then
            print_status "Stopping $service_name (PID: $pid)..."
            kill "$pid"
            sleep 2
            
            # Force kill if still running
            if kill -0 "$pid" 2>/dev/null; then
                print_warning "Force killing $service_name"
                kill -9 "$pid"
            fi
        fi
        rm -f "$pidfile"
    fi
}

# Function to cleanup on exit
cleanup() {
    print_status "Cleaning up services..."
    stop_service "Backend API" "backend.pid"
    stop_service "Frontend" "frontend.pid"
    stop_service "Notion MCP" "notion.pid"
    
    # Clean up any remaining processes
    pkill -f "hey_chef_v2_api" 2>/dev/null || true
    pkill -f "notion_mcp_server" 2>/dev/null || true
    pkill -f "npm run dev" 2>/dev/null || true
    
    print_status "Cleanup complete"
}

# Set up cleanup trap
trap cleanup EXIT

# Create logs directory
mkdir -p logs

# Install testing dependencies
print_status "Installing testing dependencies..."
pip install -r testing/requirements.txt

# Start services
print_status "Starting Hey Chef v2 services..."

# Start Backend API
start_service "Backend API" "cd backend && python main.py > ../logs/backend.log 2>&1" "backend.pid"

# Start Frontend
start_service "Frontend" "cd frontend && npm run dev > ../logs/frontend.log 2>&1" "frontend.pid"

# Start Notion MCP Server
start_service "Notion MCP" "python notion_mcp_server.py > logs/notion.log 2>&1" "notion.pid"

# Wait for services to be ready
print_status "Waiting for services to be ready..."
sleep 5

# Check if services are running
print_status "Verifying services..."
services_ready=true

if ! check_service "Backend API" "http://localhost:8000"; then
    services_ready=false
fi

if ! check_service "Frontend" "http://localhost:5173"; then
    services_ready=false
fi

if ! check_service "Notion MCP" "http://localhost:3333"; then
    services_ready=false
fi

if [ "$services_ready" = false ]; then
    print_error "Some services are not ready. Check logs in the logs/ directory."
    exit 1
fi

print_status "All services are ready! 🚀"

# Run comprehensive test suite
print_status "Running comprehensive test suite..."
python testing/comprehensive_test_suite.py

# Check test results
if [ $? -eq 0 ]; then
    print_status "All tests passed! 🎉"
else
    print_error "Some tests failed. Check the test report for details."
    exit 1
fi

print_status "Test suite completed successfully!"