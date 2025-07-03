#!/usr/bin/env python3
"""
Simple test script to verify the new logging system works correctly.
Run this to test logging before starting the full application.
"""
import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_logging_system():
    """Test the logging system functionality."""
    print("🧪 Testing Hey Chef Logging System...")
    
    try:
        from src.utils.logger import get_logger, setup_logging
        print("✅ Logger import successful")
        
        # Setup logging
        logger = setup_logging(".")
        print("✅ Logger setup successful")
        
        # Test session logging
        logger.start_session("normal", "test_recipe", True)
        print("✅ Session start logging successful")
        
        # Test various log types
        logger.log_audio_event("TEST_AUDIO", "Audio test event", 12345)
        print("✅ Audio event logging successful")
        
        logger.log_error("TEST_ERROR", "Test error message", "Test context")
        print("✅ Error logging successful")
        
        logger.log_state_change("idle", "testing", "Test state change")
        print("✅ State change logging successful")
        
        logger.log_user_action("TEST_ACTION", "User clicked test button")
        print("✅ User action logging successful")
        
        # End session
        logger.end_session(success=True)
        print("✅ Session end logging successful")
        
        # Check if log file was created
        if os.path.exists("hey_chef.log"):
            print("✅ Master log file created successfully")
            
            # Read and display first few lines
            with open("hey_chef.log", "r") as f:
                content = f.read()
                lines = content.split('\n')[:10]  # First 10 lines
                print("\n📄 Sample log content:")
                for line in lines:
                    if line.strip():
                        print(f"   {line}")
        else:
            print("❌ Master log file not created")
        
        # Check logs directory
        if os.path.exists("logs"):
            print("✅ Logs directory structure created")
            subdirs = ["sessions", "audio", "streamlit", "archived"]
            for subdir in subdirs:
                if os.path.exists(f"logs/{subdir}"):
                    print(f"✅ {subdir} directory exists")
                else:
                    print(f"❌ {subdir} directory missing")
        else:
            print("❌ Logs directory not created")
            
        print("\n🎉 Logging system test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Logging system test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_logging_system()
    sys.exit(0 if success else 1)