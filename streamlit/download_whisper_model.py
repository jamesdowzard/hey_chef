# download_whisper_model.py
"""
Simple script to pre-download and cache a Whisper model locally, bypassing SSL certificate checks.
Usage:
    python download_whisper_model.py [model_size]

If model_size is not provided, defaults to "tiny".
"""
import sys
import ssl

# Disable SSL verification (use only if you trust the source)
ssl._create_default_https_context = ssl._create_unverified_context


def main():
    model_size = sys.argv[1] if len(sys.argv) > 1 else "tiny"
    try:
        import whisper
    except ImportError:
        print("Error: 'whisper' package not installed. Install with `pip install git+https://github.com/openai/whisper.git`. ")
        sys.exit(1)

    print(f"Downloading Whisper model '{model_size}' into cache (SSL verification disabled)...")
    try:
        # This will download and cache weights to ~/.cache/whisper/{model_size}.pt
        whisper.load_model(model_size)
        print(f"Success! Model '{model_size}' cached at ~/.cache/whisper/{model_size}.pt")
    except Exception as e:
        print(f"Failed to download model '{model_size}': {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()