import webrtcvad
import collections
import wave
import tempfile
from datetime import datetime
import os
import logging
import numpy as np
import queue


class VADProcessor:
    def __init__(self, aggressiveness=3, silence_threshold=3, frame_duration_ms=30):
        """
        aggressiveness: 0-3, where 3 is most aggressive in filtering out non-speech
        silence_threshold: seconds of silence before considering speech ended
        frame_duration_ms: 10, 20, or 30 ms
        """
        self.vad = webrtcvad.Vad(aggressiveness)
        self.silence_threshold = silence_threshold
        self.frame_duration_ms = frame_duration_ms
        self.sample_rate = 16000  # WebRTC VAD requires 8000, 16000, 32000, or 48000 Hz
        self.frame_size = int(self.sample_rate * frame_duration_ms / 1000) * 2  # 2 bytes per sample for 16-bit audio
        self.temp_dir = os.path.join(tempfile.gettempdir(), 'lemonfox_vad')
        os.makedirs(self.temp_dir, exist_ok=True)
        self.logger = logging.getLogger(__name__)

    def process_stream(self, audio_queue, callback):
        """Process audio from a queue with VAD"""
        frame_buffer = collections.deque(maxlen=int(self.silence_threshold * 1000 / self.frame_duration_ms))
        is_speech = False
        speech_frames = []
        silence_frames = 0

        try:
            while True:
                try:
                    # Get audio data from queue with timeout
                    audio_chunk = audio_queue.get(timeout=1)

                    if audio_chunk is None:  # End signal
                        break

                    # Convert to bytes if necessary
                    if isinstance(audio_chunk, np.ndarray):
                        # Ensure it's 16-bit PCM
                        if audio_chunk.dtype != np.int16:
                            audio_chunk = (audio_chunk * 32767).astype(np.int16)
                        audio_bytes = audio_chunk.tobytes()
                    else:
                        audio_bytes = audio_chunk

                    # Process frames from the audio chunk
                    for frame in self._frame_generator(audio_bytes):
                        try:
                            # Validate frame size
                            if len(frame) != self.frame_size:
                                # Pad frame to correct size if needed
                                if len(frame) < self.frame_size:
                                    frame = frame + b'\x00' * (self.frame_size - len(frame))
                                else:
                                    # Truncate frame if too long
                                    frame = frame[:self.frame_size]

                            # Additional check: ensure frame has proper sample count
                            expected_samples = self.frame_size // 2  # 2 bytes per sample
                            actual_samples = len(frame) // 2

                            if actual_samples != expected_samples:
                                self.logger.warning(
                                    f"Frame sample count mismatch: expected {expected_samples}, got {actual_samples}")
                                continue

                            is_speech_frame = self.vad.is_speech(frame, self.sample_rate)
                            frame_buffer.append((frame, is_speech_frame))

                            if is_speech_frame:
                                if not is_speech:
                                    # Speech started
                                    is_speech = True
                                    silence_frames = 0
                                    speech_frames = []

                                speech_frames.append(frame)
                                silence_frames = 0
                            else:
                                if is_speech:
                                    silence_frames += 1
                                    speech_frames.append(frame)

                                    if silence_frames * self.frame_duration_ms >= self.silence_threshold * 1000:
                                        # Speech ended after silence threshold
                                        is_speech = False
                                        if speech_frames:
                                            audio_file = self._save_speech(speech_frames)
                                            callback(audio_file)
                                        silence_frames = 0
                                        speech_frames = []
                        except Exception as e:
                            self.logger.error(f"Error processing frame: {e}")
                            # Log frame details for debugging
                            self.logger.debug(f"Frame details: length={len(frame)}, expected={self.frame_size}")
                            continue

                except queue.Empty:
                    continue
                except Exception as e:
                    self.logger.error(f"Error processing audio chunk: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Error in VAD processing: {e}")
        finally:
            # Process any remaining speech frames
            if speech_frames:
                audio_file = self._save_speech(speech_frames)
                callback(audio_file)

    def _frame_generator(self, audio_data):
        """Generate frames from audio data"""
        offset = 0
        frame_length = self.frame_size

        while offset + frame_length <= len(audio_data):
            frame = audio_data[offset:offset + frame_length]

            # Ensure frame is exactly the right size
            if len(frame) == frame_length:
                yield frame

            offset += frame_length

    def _save_speech(self, frames):
        """Save detected speech to WAV file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = os.path.join(self.temp_dir, f"speech_{timestamp}.wav")

        # Convert frames to audio data
        audio_data = b''.join(frames)

        # Save to WAV file
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit audio
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_data)

        return filename

    def cleanup_temp_files(self, age_minutes=10):
        """Remove old VAD temporary files"""
        current_time = datetime.now()
        for file in os.listdir(self.temp_dir):
            file_path = os.path.join(self.temp_dir, file)
            if os.path.isfile(file_path):
                file_age = current_time - datetime.fromtimestamp(os.path.getctime(file_path))
                if file_age.total_seconds() / 60 > age_minutes:
                    try:
                        os.remove(file_path)
                        self.logger.debug(f"Removed old VAD temp file: {file_path}")
                    except PermissionError:
                        self.logger.warning(f"Permission denied when deleting: {file_path}")
                    except OSError as e:
                        self.logger.warning(f"Error deleting file {file_path}: {e}")
                    except Exception as e:
                        self.logger.error(f"Unexpected error deleting file {file_path}: {e}")