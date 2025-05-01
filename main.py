#!/usr/bin/env python3
"""
Main entry point for the LemonFox Transcription Application.

This script provides a menu-driven interface for accessing different
transcription modes.
"""

import os
import sys
import argparse
import logging
import time  # Added for voice activation fix

# Configure logging - kept from original
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('lemonfox_main')

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import from the lemonfox package
from lemonfox import (
    load_config,
    LemonFoxTranscriber,
    VoiceActivationTranscriber,
    VOICE_AVAILABLE
)

# Import new voice module if available
if VOICE_AVAILABLE:
    from lemonfox.voice import VoiceToTextApp


def display_menu():
    """Display the main menu options."""
    print("\n=== LemonFox Transcription Application ===")
    print("1. Transcribe audio from URL")
    print("2. Transcribe local audio file")
    print("3. Start voice-activated transcription (continuous)")
    if VOICE_AVAILABLE:
        print("4. Voice Recording Mode (new)")
        print("5. Voice Listening Mode with VAD (new)")
    print("6. Exit")
    print("==========================================")


def get_user_choice():
    """Get and validate user choice."""
    while True:
        choice = input("\nEnter your choice (1-6): ").strip()
        if choice in ['1', '2', '3', '4', '5', '6']:
            return choice
        print("Invalid choice. Please enter a number between 1 and 6.")


def transcribe_url():
    """Handle URL transcription."""
    url = input("Enter the URL of the audio file: ").strip()
    if not url:
        print("URL cannot be empty.")
        return

    try:
        config = load_config()
        transcriber = LemonFoxTranscriber(config=config)
        response = transcriber.transcribe_url(url)

        # Display and save transcription
        if "text" in response:
            print(f"\nTranscription result:\n{response['text']}\n")
            output_file = transcriber.save_transcription(response)
            print(f"Transcription saved to: {output_file}")
        else:
            print("No text found in transcription response.")
    except Exception as e:
        logger.error(f"Error transcribing URL: {e}")


def transcribe_file():
    """Handle local file transcription."""
    file_path = input("Enter the path to the audio file: ").strip()
    if not file_path:
        print("File path cannot be empty.")
        return

    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    try:
        config = load_config()
        transcriber = LemonFoxTranscriber(config=config)
        response = transcriber.transcribe_file(file_path)

        # Display and save transcription
        if "text" in response:
            print(f"\nTranscription result:\n{response['text']}\n")
            output_file = transcriber.save_transcription(response)
            print(f"Transcription saved to: {output_file}")
        else:
            print("No text found in transcription response.")
    except Exception as e:
        logger.error(f"Error transcribing file: {e}")


def start_voice_activation():
    """Start voice-activated transcription mode."""
    print("Starting voice-activated transcription...")
    print("The system will now listen for voice input. Press Ctrl+C to return to menu.")

    try:
        transcriber = VoiceActivationTranscriber()  # Fixed: removed config parameter
        transcriber.start_voice_activation()
        transcriber.start_continuous_listening()

        # Keep the program running until interrupted
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            transcriber.stop_continuous_listening()
            transcriber.stop_voice_activation()
            print("\nReturning to main menu...")
    except Exception as e:
        logger.error(f"Error in voice activation: {e}")


def start_voice_recording():
    """Start voice recording mode."""
    if not VOICE_AVAILABLE:
        print("Voice recording module not available. Please install voice dependencies.")
        return

    print("\n=== Voice Recording Mode ===")
    print("Press Ctrl+Alt+V to start/stop recording")
    print("Press Enter to return to main menu")

    try:
        voice_app = VoiceToTextApp()
        voice_app.start()
        input()  # Wait for user to press Enter
    except Exception as e:
        logger.error(f"Error in voice recording: {e}")
        print(f"Error: {e}")
    finally:
        if 'voice_app' in locals():
            voice_app.quit()


def start_voice_listening():
    """Start voice listening mode with VAD."""
    if not VOICE_AVAILABLE:
        print("Voice listening module not available. Please install voice dependencies.")
        return

    print("\n=== Voice Listening Mode ===")
    print("Press Ctrl+Alt+L to start/stop listening")
    print("System will transcribe speech after pauses")
    print("Press Enter to return to main menu")

    try:
        voice_app = VoiceToTextApp()
        voice_app.start()
        voice_app.start_listening_mode()
        input()  # Wait for user to press Enter
    except Exception as e:
        logger.error(f"Error in voice listening: {e}")
        print(f"Error: {e}")
    finally:
        if 'voice_app' in locals():
            voice_app.quit()


def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(description="LemonFox Transcription Application")
    parser.add_argument('--direct', choices=['url', 'file', 'voice', 'voice-recording', 'voice-listening'],
                        help="Directly launch a specific mode without menu")
    parser.add_argument('--verbose', action='store_true', help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Check for API key in config
    try:
        config = load_config()
        if not config.get("api_key"):
            print("ERROR: LemonFox API key not found in configuration.")
            print("Please set LEMONFOX_API_KEY in your .env file or environment variables.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)

    # Handle direct launch mode
    if args.direct:
        if args.direct == 'url':
            transcribe_url()
        elif args.direct == 'file':
            transcribe_file()
        elif args.direct == 'voice':
            start_voice_activation()
        elif args.direct == 'voice-recording' and VOICE_AVAILABLE:
            start_voice_recording()
        elif args.direct == 'voice-listening' and VOICE_AVAILABLE:
            start_voice_listening()
        return

    # Main menu loop
    while True:
        display_menu()
        choice = get_user_choice()

        if choice == '1':
            transcribe_url()
        elif choice == '2':
            transcribe_file()
        elif choice == '3':
            start_voice_activation()
        elif choice == '4' and VOICE_AVAILABLE:
            start_voice_recording()
        elif choice == '5' and VOICE_AVAILABLE:
            start_voice_listening()
        elif choice == '6':
            print("Goodbye!")
            break


if __name__ == "__main__":
    main()