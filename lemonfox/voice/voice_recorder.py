import sounddevice as sd
import numpy as np
import wave
import tempfile
import queue
from datetime import datetime
import os


class VoiceRecorder:
    def __init__(self, sample_rate=16000, channels=1, chunk_size=1024):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.recording_thread = None
        self.temp_dir = os.path.join(tempfile.gettempdir(), 'lemonfox_audio')
        os.makedirs(self.temp_dir, exist_ok=True)
        self.recorded_chunks = []
        self.stream = None

    def start_recording(self):
        """Start recording from microphone"""
        if not self.is_recording:
            self.is_recording = True
            self.recorded_chunks = []
            self.audio_queue = queue.Queue()  # Reset queue

            # Start recording stream with specific parameters for VAD compatibility
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                callback=self._audio_callback,
                blocksize=int(self.sample_rate * 0.03),  # 30ms blocks for VAD compatibility
                dtype=np.int16  # Use 16-bit PCM directly
            )
            self.stream.start()

    def stop_recording(self):
        """Stop recording and save to file"""
        if self.is_recording:
            self.is_recording = False

            if self.stream:
                self.stream.stop()
                self.stream.close()
                self.stream = None

            # Signal end of stream
            self.audio_queue.put(None)

            # Create audio file from recorded chunks
            return self._save_recording()

    def _audio_callback(self, indata, frames, time, status):
        """Callback for audio input stream"""
        if status:
            print(f"Audio input status: {status}")

        if self.is_recording:
            # Convert to int16 if needed
            if indata.dtype != np.int16:
                audio_chunk = (indata * 32767).astype(np.int16)
            else:
                audio_chunk = indata.copy()

            # Ensure mono
            if len(audio_chunk.shape) > 1:
                audio_chunk = audio_chunk.mean(axis=1).astype(np.int16)

            # Ensure proper frame size for VAD
            frame_size = int(self.sample_rate * 0.03) * 2  # 30ms * 2 bytes per sample
            chunk_size = len(audio_chunk) * 2  # 2 bytes per sample

            # Pad or truncate to proper frame size if needed
            if chunk_size != frame_size:
                if chunk_size < frame_size:
                    padding = np.zeros(frame_size - chunk_size, dtype=np.int16)
                    audio_chunk = np.concatenate([audio_chunk, padding])
                else:
                    audio_chunk = audio_chunk[:frame_size // 2]

            # Store for later saving
            self.recorded_chunks.append(audio_chunk.copy())

            # Put in queue for VAD processing
            self.audio_queue.put(audio_chunk.copy())

    def _save_recording(self):
        """Save recorded audio data to WAV file"""
        if not self.recorded_chunks:
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.temp_dir, f"recording_{timestamp}.wav")

        # Combine all chunks
        audio_array = np.concatenate(self.recorded_chunks)

        # Save to WAV file
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)  # 16-bit audio
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_array.tobytes())

        return filename

    def cleanup_temp_files(self, age_minutes=10):
        """Remove old temporary audio files"""
        current_time = datetime.now()
        for file in os.listdir(self.temp_dir):
            file_path = os.path.join(self.temp_dir, file)
            if os.path.isfile(file_path):
                file_age = current_time - datetime.fromtimestamp(os.path.getctime(file_path))
                if file_age.total_seconds() / 60 > age_minutes:
                    try:
                        os.remove(file_path)
                    except:
                        pass