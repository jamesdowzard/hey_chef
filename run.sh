#!/bin/bash

# Hey Chef - Voice-Controlled Cooking Assistant
# Convenience script to run both the Notion MCP server and the Streamlit UI

echo "🍳 Starting Hey Chef..."
echo ""

# Ensure dependencies are installed (Streamlit, Uvicorn)
if ! command -v streamlit &> /dev/null || ! command -v uvicorn &> /dev/null; then
    echo "❌ Required tools not found. Installing dependencies..."
    pip install -r requirements.txt
fi

# Start the Notion MCP server in the background
echo "🚀 Starting Notion MCP server at http://localhost:3333"
uvicorn notion_api:app --reload --port 3333 &
API_PID=$!

# Start the Streamlit UI (foreground)
echo "🍳 Launching Streamlit UI..."
streamlit run main.py

# When Streamlit exits, shut down the MCP server
echo "🛑 Shutting down Notion MCP server (pid $API_PID)"
kill $API_PID 