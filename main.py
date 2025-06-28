#!/usr/bin/env python3
"""
Hey Chef - Voice-Controlled Cooking Assistant

Main entry point for the application. Runs the Streamlit interface.

Usage:
    python main.py
    or
    streamlit run main.py
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path for imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def main():
    """Main entry point for Hey Chef."""
    try:
        from src.ui.app import main as app_main
        app_main()
    except ImportError as e:
        print(f"Error importing application: {e}")
        print("Make sure all dependencies are installed: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 