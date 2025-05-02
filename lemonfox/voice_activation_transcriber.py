#!/usr/bin/env python3
"""
Voice Activation Transcriber - Uses the new voice module capabilities
This file maintains backward compatibility with existing functionality
while integrating with the new voice module
"""

import logging
import os
import threading
import queue
import time
import signal
from typing import Optional

# Try importing each component separately to identify which one fails
VOICE_MODULE_AVAILABLE = True
failed_imports = []

try:
    from lemonfox.voice.voice_app import VoiceToTextApp
except ImportError as e:
    failed_imports.append(f"VoiceToTextApp: {e}")
    VoiceToTextApp = None

try:
    from lemonfox.voice.voice_recorder import VoiceRecorder
except ImportError as e:
    failed_imports.append(f"VoiceRecorder: {e}")
    VoiceRecorder = None

try:
    from lemonfox.voice.vad_processor import VADProcessor
except ImportError as e:
    failed_imports.append(f"VADProcessor: {e}")
    VADProcessor = None

try:
    from lemonfox.voice.text_injector import TextInjector
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
        self.running = False
        self.voice_app = None
        self._original_sigint_handler = None

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
            self.running = True
            # Start voice app without blocking
            # Don't install signal handlers in the voice app
            self.voice_app.start()
            self.logger.info("Voice activation started")
        except Exception as e:
            self.logger.error(f"Failed to start voice activation: {e}")

    def stop_voice_activation(self) -> None:
        """Stop voice activation"""
        if self.voice_app and self.running:
            try:
                self.running = False
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