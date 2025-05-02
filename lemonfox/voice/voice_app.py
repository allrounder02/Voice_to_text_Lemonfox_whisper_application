import os
import sys
import logging
import threading
import queue
import time
import signal

from .voice_recorder import VoiceRecorder
from .vad_processor import VADProcessor
from .keyboard_handler import KeyboardHandler
from .text_injector import TextInjector
from .tray_icon import TrayIcon

# Import your existing transcription service
from lemonfox.lemonfox_transcriber import LemonFoxTranscriber


class VoiceToTextApp:
    def __init__(self):
        self.logger = self._setup_logging()
        self.recorder = VoiceRecorder()
        self.vad_processor = VADProcessor()
        self.keyboard_handler = KeyboardHandler(
            on_toggle_recording=self.toggle_recording,
            on_start_listening=self.toggle_listening_mode
        )
        self.text_injector = TextInjector()
        self.tray_icon = TrayIcon(
            on_toggle_recording=self.toggle_recording,
            on_toggle_listening=self.toggle_listening_mode,
            on_quit=self.quit
        )

        # Initialize transcription service
        self.transcription_service = LemonFoxTranscriber()

        # State
        self.is_recording = False
        self.is_listening = False
        self.active_window = None
        self.running = True
        self.should_quit = False

        # Queues for processing
        self.audio_queue = queue.Queue()
        self.transcription_queue = queue.Queue()

        # Store original signal handler
        self.original_sigint_handler = signal.getsignal(signal.SIGINT)

    def _setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('lemonfox_voice.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        return logging.getLogger('VoiceToText')

    def start(self):
        """Start the application"""
        self.logger.info("Starting LemonFox Voice-to-Text...")

        # Start components
        self.keyboard_handler.start()
        self.tray_icon.start()

        # Start worker threads
        threading.Thread(target=self.audio_processor_worker, daemon=True).start()
        threading.Thread(target=self.transcription_worker, daemon=True).start()

        self.logger.info("Application started successfully")

    def toggle_recording(self):
        """Toggle recording state"""
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        """Start recording audio"""
        if not self.is_recording:
            self.is_recording = True
            self.active_window = self.text_injector.get_active_window()
            self.recorder.start_recording()
            self.tray_icon.update_status(recording=True)
            self.logger.info("Recording started")

    def stop_recording(self):
        """Stop recording and process audio"""
        if self.is_recording:
            self.is_recording = False
            audio_file = self.recorder.stop_recording()
            if audio_file:
                self.audio_queue.put(audio_file)
            self.tray_icon.update_status(recording=False)
            self.logger.info("Recording stopped")

    def toggle_listening_mode(self):
        """Toggle listening mode with VAD"""
        if not self.is_listening:
            self.start_listening_mode()
        else:
            self.stop_listening_mode()

    def start_listening_mode(self):
        """Start continuous listening with VAD"""
        if not self.is_listening:
            self.is_listening = True
            self.active_window = self.text_injector.get_active_window()
            threading.Thread(target=self.listening_loop, daemon=True).start()
            self.tray_icon.update_status(listening=True)
            self.logger.info("Listening mode started")

    def stop_listening_mode(self):
        """Stop listening mode"""
        if self.is_listening:
            self.is_listening = False
            self.tray_icon.update_status(listening=False)
            self.logger.info("Listening mode stopped")

    def listening_loop(self):
        """Main loop for listening mode with VAD"""
        # Start recording immediately
        self.recorder.start_recording()

        try:
            # Create a separate thread for VAD processing
            vad_thread = threading.Thread(
                target=self.vad_processor.process_stream,
                args=(self.recorder.audio_queue, self.handle_speech_detected),
                daemon=True
            )
            vad_thread.start()

            # Monitor listening state
            while self.is_listening and self.running:
                time.sleep(0.5)

        except Exception as e:
            self.logger.error(f"Error in listening loop: {e}")
        finally:
            # Stop recording when exiting
            if self.recorder.is_recording:
                self.recorder.stop_recording()
            # Signal VAD to stop processing
            self.recorder.audio_queue.put(None)

    def handle_speech_detected(self, audio_file):
        """Handle detected speech in listening mode"""
        if audio_file and self.is_listening:
            self.audio_queue.put(audio_file)

    def audio_processor_worker(self):
        """Worker thread for processing audio files"""
        while self.running and not self.should_quit:
            try:
                audio_file = self.audio_queue.get(timeout=2)
                if audio_file:
                    # Transcribe audio
                    response = self.transcription_service.transcribe_file(audio_file)
                    transcript = response.get('text', '') if isinstance(response, dict) else response
                    if transcript:
                        self.transcription_queue.put(transcript)

                    # Cleanup
                    try:
                        os.remove(audio_file)
                    except OSError as e:
                        # Log the specific error but don't crash the application
                        self.logger.warning(f"Failed to remove audio file {audio_file}: {e}")
                    except Exception as e:
                        self.logger.error(f"Unexpected error removing audio file {audio_file}: {e}")
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error in audio processor: {e}")

    def transcription_worker(self):
        """Worker thread for injecting transcriptions"""
        while self.running and not self.should_quit:
            try:
                transcript = self.transcription_queue.get(timeout=1)
                if transcript and self.active_window:
                    # Focus the original window and inject text
                    if self.text_injector.focus_window(self.active_window):
                        self.text_injector.inject_text(transcript)
                    else:
                        # Fallback to current active window
                        self.text_injector.inject_text(transcript)
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error in transcription worker: {e}")

    def quit(self):
        """Shutdown the application"""
        if self.should_quit:  # Prevent multiple shutdowns
            return

        self.logger.info("Shutting down...")
        self.should_quit = True
        self.running = False

        # Stop all components
        self.keyboard_handler.stop()
        self.tray_icon.stop()
        self.stop_recording()
        self.stop_listening_mode()

        # Give threads time to finish
        time.sleep(0.5)

        self.logger.info("Application shutdown complete")