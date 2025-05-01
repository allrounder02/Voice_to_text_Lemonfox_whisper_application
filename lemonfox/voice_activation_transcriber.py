#!/usr/bin/env python3
"""
Voice Activation Transcriber - Uses the new voice module capabilities
This file maintains backward compatibility with existing functionality
while integrating with the new voice module
"""

import logging
import os
from typing import Optional

# Try importing each component separately to identify which one fails
VOICE_MODULE_AVAILABLE = True
failed_imports = []

try:
    from voice.voice_app import VoiceToTextApp
except ImportError as e:
    failed_imports.append(f"VoiceToTextApp: {e}")
    VoiceToTextApp = None

try:
    from voice.voice_recorder import VoiceRecorder
except ImportError as e:
    failed_imports.append(f"VoiceRecorder: {e}")
    VoiceRecorder = None

try:
    from voice.vad_processor import VADProcessor
except ImportError as e:
    failed_imports.append(f"VADProcessor: {e}")
    VADProcessor = None

try:
    from voice.text_injector import TextInjector
except ImportError as e:
    failed_imports.append(f"TextInjector: {e}")
    TextInjector = None

# Set VOICE_MODULE_AVAILABLE to False if any import failed
if failed_imports:
    VOICE_MODULE_AVAILABLE = False
    logging.error("Failed to import some voice modules:")
    for failure in failed_imports:
        logging.error(f"  - {failure}")

# Use your actual LemonFoxTranscriber class and config functions
from lemonfox.lemonfox_transcriber import LemonFoxTranscriber
from lemonfox.config import load_config


class VoiceActivationTranscriber:
    """
    Voice Activation Transcriber - Wrapper for voice module functionality
    Maintains compatibility with existing interface
    """

    def __init__(self, verbose: bool = False):
        # Setup logging based on your main.py logging configuration
        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)

        self.logger = logging.getLogger(__name__)
        self.config = load_config()

        if VOICE_MODULE_AVAILABLE:
            # Check each module again to see which ones are available
            if VoiceToTextApp:
                self.voice_app = VoiceToTextApp()
            else:
                self.logger.error("VoiceToTextApp not available")
                self.voice_app = None

            if VoiceRecorder:
                self.recorder = VoiceRecorder()
            else:
                self.logger.error("VoiceRecorder not available")
                self.recorder = None

            if VADProcessor:
                self.vad_processor = VADProcessor()
            else:
                self.logger.error("VADProcessor not available")
                self.vad_processor = None

            if TextInjector:
                self.text_injector = TextInjector()
            else:
                self.logger.error("TextInjector not available")
                self.text_injector = None
        else:
            self.logger.error("Voice module not available. Please install dependencies.")
            self.logger.error(f"Failed imports: {', '.join(failed_imports)}")
            self.voice_app = None
            self.recorder = None
            self.vad_processor = None
            self.text_injector = None

    def start_voice_activation(self) -> None:
        """Start voice activation in the background"""
        if not self.voice_app:
            self.logger.error("Voice functionality not available")
            return

        try:
            self.voice_app.start()
            self.logger.info("Voice activation started")
        except Exception as e:
            self.logger.error(f"Failed to start voice activation: {e}")

    def stop_voice_activation(self) -> None:
        """Stop voice activation"""
        if self.voice_app:
            try:
                self.voice_app.quit()
                self.logger.info("Voice activation stopped")
            except Exception as e:
                self.logger.error(f"Failed to stop voice activation: {e}")

    def record_and_transcribe(self, duration_seconds: Optional[int] = None) -> Optional[str]:
        """
        Record audio and transcribe it

        Args:
            duration_seconds: Optional maximum duration in seconds

        Returns:
            Transcribed text or None if failed
        """
        if not self.recorder:
            self.logger.error("Voice recording not available")
            return None

        try:
            # Start recording
            self.recorder.start_recording()

            if duration_seconds:
                import time
                time.sleep(duration_seconds)
            else:
                input("Press Enter to stop recording...")

            # Stop recording and get file
            audio_file = self.recorder.stop_recording()

            if audio_file and os.path.exists(audio_file):
                try:
                    # Use LemonFoxTranscriber to transcribe the file
                    transcriber = LemonFoxTranscriber(config=self.config)
                    response = transcriber.transcribe_file(audio_file)

                    # Extract text from response if available
                    result = response.get("text", None) if isinstance(response, dict) else response

                    return result
                except FileNotFoundError:
                    self.logger.error(f"Audio file not found: {audio_file}")
                    return None
                except Exception as e:
                    self.logger.error(f"Transcription failed: {e}")
                    return None
                finally:
                    # Cleanup in finally block to ensure it always runs
                    if audio_file and os.path.exists(audio_file):
                        try:
                            os.remove(audio_file)
                            self.logger.debug(f"Cleaned up temporary file: {audio_file}")
                        except PermissionError:
                            self.logger.warning(f"Permission denied when trying to delete: {audio_file}")
                        except OSError as e:
                            self.logger.warning(f"Error deleting file {audio_file}: {e}")
            else:
                self.logger.error("No audio recorded")
                return None

        except Exception as e:
            self.logger.error(f"Recording and transcription failed: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
            return None

    def start_continuous_listening(self) -> None:
        """Start continuous listening with VAD"""
        if not self.voice_app:
            self.logger.error("Voice functionality not available")
            return

        try:
            self.voice_app.start_listening_mode()
            self.logger.info("Continuous listening started")
        except Exception as e:
            self.logger.error(f"Failed to start continuous listening: {e}")

    def stop_continuous_listening(self) -> None:
        """Stop continuous listening"""
        if self.voice_app:
            try:
                self.voice_app.stop_listening_mode()
                self.logger.info("Continuous listening stopped")
            except Exception as e:
                self.logger.error(f"Failed to stop continuous listening: {e}")

def main():
    """Standalone entry point for voice activation transcriber"""
    import argparse

    parser = argparse.ArgumentParser(description="Voice Activation Transcriber")
    parser.add_argument('--verbose', action='store_true', help="Enable verbose logging")
    parser.add_argument('--mode', choices=['record', 'listen'], default='record',
                        help="Mode: 'record' for single recording, 'listen' for continuous")
    parser.add_argument('--duration', type=int, help="Recording duration in seconds")

    args = parser.parse_args()

    # Setup basic logging since we don't have setup_logging function
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    transcriber = VoiceActivationTranscriber(verbose=args.verbose)

    try:
        if args.mode == 'record':
            result = transcriber.record_and_transcribe(args.duration)
            if result:
                print(f"\nTranscription: {result}")
        else:
            print("Starting continuous listening mode. Press Ctrl+C to stop.")
            transcriber.start_voice_activation()
            transcriber.start_continuous_listening()

            try:
                while True:
                    import time
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nStopping...")
            finally:
                transcriber.stop_continuous_listening()
                transcriber.stop_voice_activation()

    except Exception as e:
        logging.error(f"Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())