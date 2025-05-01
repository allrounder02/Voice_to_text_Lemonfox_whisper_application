import sounddevice as sd
import numpy as np
import wave
import tempfile
import threading
import queue
from datetime import datetime
import os


class VoiceRecorder:
    def __init__(self, sample_rate=44100, channels=1, chunk_size=1024):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.recording_thread = None
        self.temp_dir = os.path.join(tempfile.gettempdir(), 'lemonfox_audio')
        os.makedirs(self.temp_dir, exist_ok=True)

    def start_recording(self):
        """Start recording from microphone"""
        if not self.is_recording:
            self.is_recording = True
            self.recording_thread = threading.Thread(target=self._record_audio)
            self.recording_thread.daemon = True
            self.recording_thread.start()

    def stop_recording(self):
        """Stop recording and save to file"""
        if self.is_recording:
            self.is_recording = False
            if self.recording_thread:
                self.recording_thread.join()

            # Create audio file from queued data
            return self._save_recording()

    def _record_audio(self):
        """Internal method to handle audio recording"""
        with sd.InputStream(samplerate=self.sample_rate,
                            channels=self.channels,
                            callback=self._audio_callback):
            while self.is_recording:
                sd.sleep(100)

    def _audio_callback(self, indata, frames, time, status):
        """Callback for audio input stream"""
        if status:
            print(f"Audio input status: {status}")
        self.audio_queue.put(indata.copy())

    def _save_recording(self):
        """Save queued audio data to WAV file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.temp_dir, f"recording_{timestamp}.wav")

        # Collect all audio data
        audio_data = []
        while not self.audio_queue.empty():
            audio_data.append(self.audio_queue.get())

        if not audio_data:
            return None

        # Combine all chunks
        audio_array = np.concatenate(audio_data)

        # Save to WAV file
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)  # 16-bit audio
            wf.setframerate(self.sample_rate)
            wf.writeframes((audio_array * 32767).astype(np.int16).tobytes())

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