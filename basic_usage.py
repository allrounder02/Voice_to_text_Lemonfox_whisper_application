import os
import sys
import json

# Add parent directory to path to import from main module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lemonfox_transcriber import LemonFoxTranscriber
from config import load_config


def main():
    """Example usage of the LemonFox Transcriber"""

    # Load configuration from .env file
    config = load_config()

    # Initialize transcriber with configuration
    transcriber = LemonFoxTranscriber(config=config)

    # Example 1: Transcribe from URL
    url = "https://output.lemonfox.ai/wikipedia_ai.mp3"
    print(f"Transcribing audio from URL: {url}")
    try:
        response = transcriber.transcribe_url(audio_url=url)
        print("\nTranscription result:")
        print(json.dumps(response, indent=2))

        # Save transcription to file
        output_file = transcriber.save_transcription(response)
        print(f"Saved transcription to: {output_file}")
    except Exception as e:
        print(f"Error transcribing URL: {e}")

    # Example 2: Transcribe local file (if exists)
    file_path = "examples/sample_audio.mp3"
    if os.path.exists(file_path):
        print(f"\nTranscribing local file: {file_path}")
        try:
            response = transcriber.transcribe_file(file_path=file_path)
            print("\nTranscription result:")
            print(json.dumps(response, indent=2))

            # Save transcription to file
            output_file = transcriber.save_transcription(response)
            print(f"Saved transcription to: {output_file}")
        except Exception as e:
            print(f"Error transcribing file: {e}")
    else:
        print(f"\nSkipping local file example: {file_path} not found")


if __name__ == "__main__":
    main()