#!/usr/bin/env python3
"""
Main entry point for the LemonFox Transcription Application.

This script provides a menu-driven interface for accessing different
transcription modes with system tray integration.
"""

import os
import sys
import argparse
import logging
import time
import msvcrt  # For clearing input buffer on Windows
import signal
import platform
import glob

# Fix TCL/TK paths before importing tkinter
if platform.system() == "Windows":
    try:
        python_dir = sys.prefix
        tcl_paths = glob.glob(os.path.join(python_dir, 'tcl', 'tcl*'))
        tk_paths = glob.glob(os.path.join(python_dir, 'tcl', 'tk*'))

        if tcl_paths:
            os.environ['TCL_LIBRARY'] = tcl_paths[0]
        if tk_paths:
            os.environ['TK_LIBRARY'] = tk_paths[0]
            os.environ['TKPATH'] = tk_paths[0]
    except Exception as e:
        logging.warning(f"Could not configure TCL/TK paths: {e}")

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
    from lemonfox.voice import VoiceToTextApp, TrayIcon

# Global flag for handling interrupts
interrupt_received = False


def signal_handler(signum, frame):
    """Global signal handler for SIGINT"""
    global interrupt_received
    interrupt_received = True
    logger.info("Interrupt signal received")


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
    """Get and validate user choice with proper encoding handling."""
    choice_bytes = None  # Initialize outside the try block

    while True:
        try:
            # Use sys.stdin.readline() instead of input()
            sys.stdout.write("\nEnter your choice (1-6): ")
            sys.stdout.flush()

            # Read line and handle encoding
            choice_bytes = sys.stdin.buffer.readline()
            choice = choice_bytes.decode('utf-8', errors='ignore').strip()

            if choice in ['1', '2', '3', '4', '5', '6']:
                return choice

            if choice:  # Only print error if something was actually entered
                print("Invalid choice. Please enter a number between 1 and 6.")
        except UnicodeDecodeError as e:
            logger.error(f"Encoding error: {e}")
            # Try again without decoding
            try:
                choice = choice_bytes.decode('latin-1').strip()
                if choice in ['1', '2', '3', '4', '5', '6']:
                    return choice
            except:
                continue
        except Exception as e:
            logger.error(f"Error reading input: {e}")
            continue


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
    """Start voice-activated transcription mode with tray icon."""
    global interrupt_received
    interrupt_received = False

    print("Starting voice-activated transcription...")
    print("The system will now listen for voice input. Check the system tray for status.")
    print("Press Ctrl+C to return to menu.")

    try:
        transcriber = VoiceActivationTranscriber()
        transcriber.start_voice_activation()
        transcriber.start_continuous_listening()

        # Create a simple tray icon for this mode
        tray_icon = TrayIcon(
            app_name="LemonFox Voice (Continuous)",
            on_toggle_recording=lambda: None,  # Not used in this mode
            on_toggle_listening=lambda: None,  # Not used in this mode
            on_quit=lambda: None
        )
        tray_icon.start()
        tray_icon.update_status(recording=False, listening=True)

        # Keep the program running until interrupted
        try:
            while not interrupt_received:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nCtrl+C detected. Stopping voice activation...")
        finally:
            transcriber.stop_continuous_listening()
            transcriber.stop_voice_activation()
            tray_icon.stop()
            print("Returning to main menu...")
            # Clear any remaining input buffer (Windows-specific)
            try:
                while msvcrt.kbhit():
                    msvcrt.getch()
            except:
                pass

    except Exception as e:
        logger.error(f"Error in voice activation: {e}")
        import traceback
        logger.debug(traceback.format_exc())


def start_voice_recording():
    """Start voice recording mode with tray icon."""
    global interrupt_received
    interrupt_received = False

    if not VOICE_AVAILABLE:
        print("Voice recording module not available. Please install voice dependencies.")
        return

    print("\n=== Voice Recording Mode ===")
    print("System tray icon is now active. Right-click for options.")
    print("Press Ctrl+Alt+V to start/stop recording")
    print("Press Enter to return to main menu")

    voice_app = None  # Initialize outside the try block

    try:
        voice_app = VoiceToTextApp()
        voice_app.start()

        # Use a proper input function that waits for Enter
        try:
            while not interrupt_received:
                if msvcrt.kbhit():
                    key = msvcrt.getch()
                    if key == b'\r':  # Enter key
                        break
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nCtrl+C detected. Returning to menu...")
    except Exception as e:
        logger.error(f"Error in voice recording: {e}")
        print(f"Error: {e}")
    finally:
        if 'voice_app' in locals():
            voice_app.quit()


def start_voice_listening():
    """Start voice listening mode with VAD, tray icon, and status window."""
    global interrupt_received
    interrupt_received = False

    if not VOICE_AVAILABLE:
        print("Voice listening module not available. Please install voice dependencies.")
        return

    print("\n=== Voice Listening Mode ===")
    print("System tray icon is now active with status window available.")
    print("Press Ctrl+Alt+L to start/stop listening")
    print("System will transcribe speech after pauses")
    print("Press Enter to return to main menu")

    voice_app = None  # Initialize outside the try block

    try:
        voice_app = VoiceToTextApp()
        voice_app.start()
        voice_app.start_listening_mode()

        # Show status window immediately when starting listening mode
        if hasattr(voice_app, 'tray_icon') and voice_app.tray_icon:
            voice_app.tray_icon.show_status_window(None, None)

        # Use a proper input function that waits for Enter
        try:
            while not interrupt_received:
                if msvcrt.kbhit():
                    key = msvcrt.getch()
                    if key == b'\r':  # Enter key
                        break
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nCtrl+C detected. Returning to menu...")
    except Exception as e:
        logger.error(f"Error in voice listening: {e}")
        print(f"Error: {e}")
    finally:
        if voice_app is not None:  # Check if voice_app was initialized
            voice_app.quit()


def main():
    """Main application entry point."""
    global interrupt_received

    # Set up global signal handler
    signal.signal(signal.SIGINT, signal_handler)

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
    while not interrupt_received:
        try:
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
        except KeyboardInterrupt:
            print("\nCtrl+C detected. Exiting...")
            break
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            print("An error occurred. Please try again.")


if __name__ == "__main__":
    main()