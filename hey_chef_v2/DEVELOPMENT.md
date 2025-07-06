# Hey Chef v2 Development Guide

## Port Management Scripts

This directory contains several scripts to help manage the development environment and prevent port conflicts.

### Available Scripts

#### 🚀 `./start-dev.sh`
**Primary development startup script**
- Automatically cleans up any existing processes before starting
- Starts both backend (port 8000) and frontend (port 3000)
- Includes proper signal handling for Ctrl+C cleanup
- Shows helpful URLs when started

```bash
./start-dev.sh
```

#### 🛑 `./stop-dev.sh`
**Clean shutdown script**
- Gracefully stops all Hey Chef development processes
- Tries graceful shutdown first, then force-kills if needed
- Cleans up all relevant ports (3000, 3001, 8000)
- Verifies cleanup was successful

```bash
./stop-dev.sh
```

#### 🔍 `./check-ports.sh`
**Status checker**
- Shows what's running on all development ports
- Lists Hey Chef related processes
- Displays Node.js and Python development servers
- Helpful for debugging port conflicts

```bash
./check-ports.sh
```

#### 💥 `./cleanup-ports.sh`
**Nuclear option - force cleanup**
- **WARNING**: Forcefully kills ALL processes on development ports
- Use only when normal cleanup fails
- Requires confirmation before running
- Verifies all ports are freed

```bash
./cleanup-ports.sh
```

## Common Port Conflict Solutions

### Problem: "Port 3000 is in use, trying another one..."

**Cause**: Previous frontend process didn't shut down properly

**Quick Fix**:
```bash
./stop-dev.sh
./start-dev.sh
```

**If that doesn't work**:
```bash
./cleanup-ports.sh
./start-dev.sh
```

### Problem: "ERROR: [Errno 48] Address already in use" (Backend)

**Cause**: Previous backend process is still running on port 8000

**Quick Fix**:
```bash
./stop-dev.sh
./start-dev.sh
```

### Problem: Services start on wrong ports (3001, etc.)

**Cause**: Multiple instances running, ports getting shifted

**Solution**:
```bash
./cleanup-ports.sh  # Force clean everything
./start-dev.sh      # Start fresh
```

## Development Workflow

### Normal Development
```bash
# Start development environment
./start-dev.sh

# Work on your code...
# Both services auto-reload on file changes

# Stop when done (Ctrl+C or)
./stop-dev.sh
```

### Troubleshooting Workflow
```bash
# Check what's running
./check-ports.sh

# If you see conflicts, clean up
./stop-dev.sh

# If problems persist, force cleanup
./cleanup-ports.sh

# Start fresh
./start-dev.sh
```

### Emergency Reset
```bash
# Nuclear option - kills everything
./cleanup-ports.sh

# Verify everything is clean
./check-ports.sh

# Start fresh
./start-dev.sh
```

## Service URLs

When everything is running correctly:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **WebSocket**: ws://localhost:8000/ws/audio

## Port Reference

| Port | Service | Purpose |
|------|---------|---------|
| 3000 | Frontend (Vite) | React development server |
| 3001 | Frontend (Backup) | Vite fallback when 3000 is busy |
| 8000 | Backend (FastAPI) | Python API server |
| 3333 | Notion MCP | Recipe management (optional) |

## Environment Variables

Make sure these are set for full functionality:

```bash
export OPENAI_API_KEY="your_openai_key_here"
export PICO_ACCESS_KEY="your_picovoice_key_here"
```

Optional:
```bash
export RECIPE_API_URL="http://localhost:3333"  # For Notion integration
```

## Tips

1. **Always use the scripts** instead of manually starting services
2. **Use Ctrl+C** to stop the development environment (signal handling is improved)
3. **Run `./check-ports.sh`** if you're unsure what's running
4. **Use `./cleanup-ports.sh`** as a last resort only
5. **The scripts are safe to run multiple times** - they won't break anything

## Troubleshooting Commands

```bash
# See what's using specific ports
lsof -i :3000
lsof -i :8000

# Kill specific process by PID
kill <PID>
kill -9 <PID>  # Force kill

# Kill all Node processes (dangerous!)
pkill -f node

# Kill all Python processes (dangerous!)
pkill -f python
```

**Note**: Use the provided scripts instead of manual commands when possible.