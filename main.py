#!/usr/bin/env python3
"""
Hey Chef - Voice-Controlled Cooking Assistant

Main entry point for the application. Runs the Streamlit interface.

Usage:
    streamlit run main.py
"""

import sys
import os
from pathlib import Path

def main():
    """Main entry point for Hey Chef."""
    
    # Check if running directly vs through streamlit
    if len(sys.argv) == 1 and 'streamlit' not in sys.modules:
        print("🍳 Hey Chef - Voice-Controlled Cooking Assistant")
        print("=" * 50)
        print()
        print("⚠️  This is a Streamlit web application.")
        print("   To run it properly, use:")
        print()
        print("   streamlit run main.py")
        print()
        print("   Then open your browser to the URL shown.")
        print()
        print("🚀 Starting with streamlit run for you...")
        print()
        
        # Try to launch with streamlit
        try:
            import subprocess
            subprocess.run([sys.executable, "-m", "streamlit", "run", __file__])
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
        except Exception as e:
            print(f"❌ Error launching streamlit: {e}")
            print("Please run manually: streamlit run main.py")
        return
    
    # Add src directory to Python path for imports
    src_path = Path(__file__).parent / "src"
    sys.path.insert(0, str(src_path))
    
    try:
        from src.ui.app import main as app_main
        app_main()
    except ImportError as e:
        print(f"❌ Error importing application: {e}")
        print("Make sure all dependencies are installed: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 