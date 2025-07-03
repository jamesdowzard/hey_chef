# sounddevice_test.py

import sounddevice as sd
sd.check_input_settings(samplerate=16000, channels=1, dtype="int16")