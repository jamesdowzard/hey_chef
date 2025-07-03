# test/tts_engine_test_debug.py

import os
import sys
import subprocess
import shutil

# 1) Ensure we can import tts_engine from the project root
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from tts_engine import TTSEngine

def which_or_none(prog):
    """Return the full path of prog if it exists, or None otherwise."""
    path = shutil.which(prog)
    return path if path else None

def main():
    print("🔍 Python executable:", sys.executable)
    print("🔍 Current working directory:", os.getcwd())
    print("🔍 Checking for 'say' binary at:", which_or_none("say"))
    print("🔍 Checking for 'afplay' binary at:", which_or_none("afplay"))

    # 2) List the first 10 lines of audio devices (for context)
    print("\n🔍 Listing first 10 lines of AUDIO devices via `system_profiler SPAudioDataType`:")
    try:
        out = subprocess.check_output(["system_profiler", "SPAudioDataType"], text=True)
        for line in out.splitlines()[:10]:
            print("   ", line)
    except subprocess.CalledProcessError as e:
        print("⚠️ Failed to run system_profiler:", e)

    # 3) Invoke TTSEngine.say(...) to generate and play an AIFF using 'Alex'
    print("\n🔊 Now invoking TTSEngine.say(...) with the Alex voice")
    tts = TTSEngine(voice_id="Alex")
    try:
        tts.say("Hello from ChefBot TTS engine. If you hear this, TTSEngine.say worked.")
        print("✅ tts.say() completed without throwing an exception.")
    except Exception as e:
        print("❌ Exception raised inside tts.say():", e)

    # 4) Directly call say -v Alex from Python to confirm it works
    print("\n🔊 Directly calling subprocess.run(['say', '-v', 'Alex', 'Test from subprocess']):")
    try:
        ret = subprocess.run(["say", "-v", "Alex", "Test from subprocess"], check=True)
        print("✅ subprocess say returned with code", ret.returncode)
    except subprocess.CalledProcessError as e:
        print("❌ subprocess.run(['say', '-v', 'Alex', ...]) failed:", e)

    # 5) Directly call afplay on the built-in Ping.aiff
    print("\n🔊 Directly calling subprocess.run(['afplay', '/System/Library/Sounds/Ping.aiff']):")
    try:
        ret = subprocess.run(["afplay", "/System/Library/Sounds/Ping.aiff"], check=True)
        print("✅ afplay returned with code", ret.returncode)
    except subprocess.CalledProcessError as e:
        print("❌ subprocess.run(['afplay', ...]) failed:", e)

    # 6) Print environment variables that might influence audio
    print("\n🔍 Environment variables related to audio:")
    for var in ["AUDIODEV", "SOUND_PREFERENCE_ORDER"]:
        print(f"   {var} =", os.getenv(var))

    # 7) Provide a manual command for reference
    print(
        "\n🔄 If the above TTSEngine.say() worked, "
        "you can manually run:\n"
        "    say -v Alex -o /tmp/manual_test.aiff \"Hello from manual test\"\n"
        "    afplay /tmp/manual_test.aiff\n"
    )

if __name__ == "__main__":
    main()