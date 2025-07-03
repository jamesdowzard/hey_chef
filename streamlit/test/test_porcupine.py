# test_porcupine.py
#
# Simple script to test that Porcupine detects "Hey Chef".
# Now updated to import wake_porcupine from the parent directory.

import os
import sys
from dotenv import load_dotenv

# ──────────────────────────────────────────────────────────
# 1) Make sure Python can import wake_porcupine from the project root
#    (since this test script lives in hey_chef/test/)
test_dir = os.path.dirname(os.path.abspath(__file__))      # .../hey_chef/test
project_root = os.path.dirname(test_dir)                    # .../hey_chef
sys.path.append(project_root)

# 2) Load .env so PICO_ACCESS_KEY is available
load_dotenv(os.path.join(project_root, ".env"))

# 3) Import our WakeWordDetector from wake_porcupine.py
from wake_porcupine import WakeWordDetector

def main():
    # 4) Ensure PICO_ACCESS_KEY is set
    pico_key = os.getenv("PICO_ACCESS_KEY")
    if not pico_key:
        print("❌ ERROR: PICO_ACCESS_KEY not found in environment. Add it to your .env file.")
        return

    # 5) Path to your Porcupine model file (relative to project root)
    keyword_model = os.path.join(project_root, "porcupine_models", "hey_chef.ppn")
    if not os.path.exists(keyword_model):
        print(f"❌ ERROR: Could not find keyword model at '{keyword_model}'")
        return

    # 6) Create the detector (using default sensitivity of 0.7)
    detector = WakeWordDetector(
        keyword_path=keyword_model,
        sensitivity=0.7
    )

    print("👂 Listening for wake word “Hey Chef” (Porcupine).")
    print("    Speak clearly into your microphone...")

    try:
        # 7) This will block until Porcupine hears the wake word
        detected = detector.detect_once()
        if detected:
            print("✅ Porcupine detected ‘Hey Chef’!\n")
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user (Ctrl+C). Exiting.")
    finally:
        detector.cleanup()

if __name__ == "__main__":
    main()