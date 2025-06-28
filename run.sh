#!/bin/bash

# Hey Chef - Voice-Controlled Cooking Assistant
# Convenience script to run the application

echo "🍳 Starting Hey Chef..."
echo "Opening in your default browser..."
echo ""

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "❌ Streamlit not found. Installing dependencies..."
    pip install -r requirements.txt
fi

# Run the app
streamlit run main.py 