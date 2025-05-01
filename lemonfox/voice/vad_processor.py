import webrtcvad  # numpy import removed as it's unused
import collections
import wave
import tempfile
from datetime import datetime
import os
import logging


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
        self.frame_size = int(self.sample_rate * frame_duration_ms / 1000)
        self.temp_dir = os.path.join(tempfile.gettempdir(), 'lemonfox_vad')
        os.makedirs(self.temp_dir, exist_ok=True)

    def process_stream(self, audio_stream, callback):
        """Process continuous audio stream with VAD"""
        frame_buffer = collections.deque(maxlen=int(self.silence_threshold * 1000 / self.frame_duration_ms))
        is_speech = False
        speech_frames = []

        # Create a consistent silence counter for the method
        silence_frames = 0

        for frame in self._frame_generator(audio_stream):
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

    def _frame_generator(self, audio_data):
        """Generate frames from audio data"""
        offset = 0
        while offset + self.frame_size <= len(audio_data):
            yield audio_data[offset:offset + self.frame_size]
            offset += self.frame_size

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
                        logging.debug(f"Removed old VAD temp file: {file_path}")
                    except PermissionError:
                        logging.warning(f"Permission denied when deleting: {file_path}")
                    except OSError as e:
                        logging.warning(f"Error deleting file {file_path}: {e}")
                    except Exception as e:  # Last resort for unexpected errors
                        logging.error(f"Unexpected error deleting file {file_path}: {e}")