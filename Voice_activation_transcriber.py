import os
import time
import threading
import queue
import logging
import argparse
import sounddevice as sd
import numpy as np
import webrtcvad
from scipy.io import wavfile
import tempfile
import sys

# Add parent directory to path to import from main module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lemonfox_transcriber import LemonFoxTranscriber
from config import load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('voice_activation')


class VoiceActivatedTranscriber:
    """Voice-activated transcription service using LemonFox API."""

    def __init__(self,
                 threshold=0.01,
                 sample_rate=16000,
                 frame_duration_ms=30,
                 silence_duration=1.0,
                 activation_phrase=None,
                 config=None):
        """
        Initialize the voice activation system.

        Args:
            threshold: Energy threshold for voice activity detection
            sample_rate: Audio sample rate in Hz
            frame_duration_ms: Frame duration in milliseconds
            silence_duration: Duration of silence (in seconds) to mark end of speech
            activation_phrase: Optional phrase to activate the system (not implemented yet)
            config: Configuration dictionary for LemonFox
        """
        self.threshold = threshold
        self.sample_rate = sample_rate
        self.frame_duration_ms = frame_duration_ms
        self.silence_duration = silence_duration
        self.activation_phrase = activation_phrase

        # Load config if not provided
        self.config = config or load_config()

        # Initialize LemonFox transcriber
        self.transcriber = LemonFoxTranscriber(config=self.config)

        # Initialize WebRTC VAD (Voice Activity Detection)
        self.vad = webrtcvad.Vad(3)  # Aggressiveness mode (0-3)

        # Calculate frame size
        self.frame_size = int(self.sample_rate * (self.frame_duration_ms / 1000.0))

        # Queues for audio processing
        self.audio_queue = queue.Queue()
        self.is_recording = False
        self.stop_requested = False

        # Buffer for storing audio data during recording
        self.audio_buffer = []

        # Counter for frames without voice
        self.silence_frames = 0
        self.max_silence_frames = int(self.silence_duration * (1000 / self.frame_duration_ms))

    def audio_callback(self, indata, frames, time_info, status):
        """Callback function for audio stream processing."""
        if status:
            logger.warning(f"Audio callback status: {status}")

        # Put the audio data in the queue
        self.audio_queue.put(indata.copy())

    def process_audio(self):
        """Process audio from the queue and detect voice activity."""
        last_active_time = 0

        while not self.stop_requested:
            try:
                # Get audio data from queue with timeout
                audio_data = self.audio_queue.get(timeout=0.5)

                # Convert float32 audio to int16 for VAD
                audio_int16 = (audio_data * 32767).astype(np.int16)

                # Process frames for voice activity detection
                for i in range(0, len(audio_int16) - self.frame_size, self.frame_size):
                    frame = audio_int16[i:i + self.frame_size].tobytes()

                    try:
                        # Check if frame contains voice
                        is_speech = self.vad.is_speech(frame, self.sample_rate)
                    except Exception as e:
                        logger.error(f"VAD error: {e}")
                        continue

                    # If in recording mode, append audio to buffer
                    if self.is_recording:
                        self.audio_buffer.append(audio_data[i:i + self.frame_size])

                        if is_speech:
                            # Reset silence counter if voice detected
                            self.silence_frames = 0
                            last_active_time = time.time()
                        else:
                            # Increment silence counter
                            self.silence_frames += 1

                            # Stop recording after silence threshold
                            if self.silence_frames >= self.max_silence_frames:
                                logger.info("Silence detected, stopping recording")
                                self.stop_recording()

                    # If not recording and voice detected, start recording
                    elif is_speech:
                        energy = np.mean(np.abs(audio_data))
                        if energy > self.threshold:
                            logger.info(f"Voice detected (energy: {energy:.6f}), starting recording")
                            self.start_recording()
                            self.audio_buffer.append(audio_data[i:i + self.frame_size])
                            last_active_time = time.time()

            except queue.Empty:
                # No audio data in queue
                pass

            # Check for timeout (if recording but no voice for a long time)
            if self.is_recording and time.time() - last_active_time > self.silence_duration * 2:
                logger.info("Recording timeout, stopping")
                self.stop_recording()

    def start_recording(self):
        """Start recording audio."""
        self.is_recording = True
        self.audio_buffer = []
        self.silence_frames = 0
        logger.info("Recording started")

    def stop_recording(self):
        """Stop recording and process the audio."""
        if not self.is_recording or not self.audio_buffer:
            return

        self.is_recording = False
        logger.info("Recording stopped, processing audio...")

        try:
            # Combine all audio frames
            audio_data = np.vstack(self.audio_buffer)

            # Save to temporary WAV file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_filename = temp_file.name
                wavfile.write(temp_filename, self.sample_rate, audio_data)

            logger.info(f"Audio saved to temporary file: {temp_filename}")

            # Transcribe the audio file
            try:
                response = self.transcriber.transcribe_file(temp_filename)

                # Save transcription to file
                output_file = self.transcriber.save_transcription(response)

                # Print transcription
                if "text" in response:
                    print("\n----- Transcription -----")
                    print(response["text"])
                    print("-------------------------\n")
                else:
                    print("\nNo text in transcription response")

                logger.info(f"Transcription saved to: {output_file}")

            except Exception as e:
                logger.error(f"Transcription error: {e}")

            # Clean up temporary file
            try:
                os.unlink(temp_filename)
            except:
                pass

        except Exception as e:
            logger.error(f"Error processing audio: {e}")

        # Clear audio buffer
        self.audio_buffer = []

    def run(self):
        """Run the voice-activated transcriber."""
        logger.info("Starting voice-activated transcriber")
        logger.info("Listening for voice input... (Press Ctrl+C to exit)")

        # Start audio processing thread
        processing_thread = threading.Thread(target=self.process_audio)
        processing_thread.daemon = True
        processing_thread.start()

        try:
            # Start audio stream
            with sd.InputStream(
                    samplerate=self.sample_rate,
                    channels=1,
                    callback=self.audio_callback,
                    blocksize=int(self.sample_rate * self.frame_duration_ms / 1000),
                    dtype='float32'
            ):
                print("\nVoice-activated transcriber is running...")
                print("Speak to start recording, silence to stop.")
                print("Press Ctrl+C to exit\n")

                # Keep the main thread alive
                while True:
                    time.sleep(0.1)

        except KeyboardInterrupt:
            logger.info("Keyboard interrupt, stopping...")
        except Exception as e:
            logger.error(f"Error in audio stream: {e}")
        finally:
            # Stop the processing thread
            self.stop_requested = True
            if self.is_recording:
                self.stop_recording()

            if processing_thread.is_alive():
                processing_thread.join(timeout=1.0)

            logger.info("Voice-activated transcriber stopped")


def main():
    """Main function to run the voice-activated transcriber."""
    parser = argparse.ArgumentParser(description="Voice-activated transcription using LemonFox API")
    parser.add_argument("--threshold", type=float, default=0.01, help="Voice activity detection threshold")
    parser.add_argument("--sample-rate", type=int, default=16000, help="Audio sample rate in Hz")
    parser.add_argument("--frame-duration", type=int, default=30, help="Frame duration in milliseconds")
    parser.add_argument("--silence-duration", type=float, default=1.5,
                        help="Silence duration to stop recording (seconds)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Load config
    config = load_config()

    # Create and run voice-activated transcriber
    transcriber = VoiceActivatedTranscriber(
        threshold=args.threshold,
        sample_rate=args.sample_rate,
        frame_duration_ms=args.frame_duration,
        silence_duration=args.silence_duration,
        config=config
    )

    transcriber.run()

if __name__ == "__main__":
    main()