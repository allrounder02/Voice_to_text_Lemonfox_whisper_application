# LemonFox Transcription Application

LemonFox is a powerful audio transcription application that supports transcribing audio from URLs, local files, and voice input. It includes advanced voice activation features with support for continuous listening and voice activity detection.

## Features

- **URL Transcription**: Transcribe audio directly from URLs
- **File Transcription**: Process local audio files
- **Voice Activation**: Trigger transcription with voice commands
- **Voice Recording**: Record voice with keyboard shortcuts (Ctrl+Alt+V)
- **Voice Listening**: Continuous listening with automatic transcription after pauses (Ctrl+Alt+L)

## Installation

### Basic Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/lemonfox.git
   cd lemonfox
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. (Optional) Install voice module dependencies:
   ```bash
   pip install -r requirements_voice.txt
   ```

### Platform-specific Voice Dependencies

#### Windows
```bash
pip install pywin32
```

#### macOS
```bash
pip install pyobjc-framework-Cocoa
```

#### Linux
```bash
sudo apt-get install python3-xlib xdotool
```

## Configuration

1. Create a `.env` file in the project root:
   ```
   LEMONFOX_API_KEY=your_api_key_here
   ```

2. Or set environment variable:
   ```bash
   export LEMONFOX_API_KEY=your_api_key_here
   ```

## Usage

### Interactive Mode

Run the application:
```bash
python main.py
```

Menu options:
1. Transcribe audio from URL
2. Transcribe local audio file
3. Start voice-activated transcription (continuous)
4. Voice Recording Mode (new)
5. Voice Listening Mode with VAD (new)
6. Exit

### Direct Mode

Launch specific modes directly:
```bash
# Transcribe a URL
python main.py --direct url

# Transcribe a file
python main.py --direct file

# Start voice activation
python main.py --direct voice

# Start voice recording
python main.py --direct voice-recording

# Start voice listening
python main.py --direct voice-listening
```

### Voice Features

#### Voice Recording Mode
- Press `Ctrl+Alt+V` to start/stop recording
- Speak into your microphone
- Text is automatically injected into your active window

#### Voice Listening Mode
- Press `Ctrl+Alt+L` to start/stop continuous listening
- System automatically detects speech and pauses
- Transcribes after 3 seconds of silence
- Text is automatically injected into your active window

## Basic Usage Examples

Here are common usage patterns for LemonFox:

### Example 1: Basic File Transcription

```python
from lemonfox.config import load_config
from lemonfox.lemonfox_transcriber import LemonFoxTranscriber

# Initialize the transcriber
config = load_config()
transcriber = LemonFoxTranscriber(config=config)

# Transcribe a local audio file
result = transcriber.transcribe_file("path/to/audio.mp3")
print(f"Transcription: {result['text']}")

# Save the transcription
output_file = transcriber.save_transcription(result, "output_filename")
print(f"Saved to: {output_file}")
```

### Example 2: URL Transcription

```python
from lemonfox.config import load_config
from lemonfox.lemonfox_transcriber import LemonFoxTranscriber

# Initialize the transcriber
config = load_config()
transcriber = LemonFoxTranscriber(config=config)

# Transcribe audio from a URL
url = "https://example.com/audio.mp3"
result = transcriber.transcribe_url(url)
print(f"Transcription: {result['text']}")
```

### Example 3: Voice Activation

```python
from lemonfox.config import load_config
from lemonfox.voice_activation_transcriber import VoiceActivationTranscriber

# Initialize voice activation
config = load_config()
transcriber = VoiceActivationTranscriber(config=config)

# Start voice activation (will listen continuously)
transcriber.run()  # Use Ctrl+C to stop
```

### Example 4: Custom Voice Recording

```python
from lemonfox.voice.voice_recorder import VoiceRecorder
import time

# Initialize recorder
recorder = VoiceRecorder()

# Record for 5 seconds
recorder.start_recording()
time.sleep(5)
audio_file = recorder.stop_recording()

print(f"Recording saved to: {audio_file}")
```

### Example 5: Voice Activity Detection

```python
from lemonfox.voice.vad_processor import VADProcessor
from lemonfox.voice.voice_recorder import VoiceRecorder

# Initialize components
recorder = VoiceRecorder()
vad = VADProcessor(aggressiveness=3, silence_threshold=3)

# Callback for detected speech
def on_speech_detected(audio_file):
    print(f"Speech detected and saved to: {audio_file}")

# Start recording and process with VAD
recorder.start_recording()
vad.process_stream(recorder.audio_queue, callback=on_speech_detected)
```

### Example 6: System Tray Integration

```python
from lemonfox.voice.tray_icon import TrayIcon
from lemonfox.voice import VoiceToTextApp

# Create voice app with system tray
voice_app = VoiceToTextApp()

# Start the application (will appear in system tray)
voice_app.start()

# The system tray icon allows:
# - Right-click menu to control recording/listening
# - Visual indicator for status (gray/red/green)
# - Convenient access to all features
```

### Example 7: Text Injection

```python
from lemonfox.voice.text_injector import TextInjector

# Initialize text injector
injector = TextInjector()

# Get currently active window
window_info = injector.get_active_window()
print(f"Active window: {window_info['title']}")

# Inject text into the active window
text = "This text will be inserted at the cursor position"
injector.inject_text(text)

# Alternative: Type text character by character
injector.type_text("Slowly typed text", interval=0.05)
```

### Example 8: Error Handling

```python
from lemonfox.config import load_config
from lemonfox.lemonfox_transcriber import LemonFoxTranscriber
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # Initialize and transcribe
    config = load_config()
    transcriber = LemonFoxTranscriber(config=config)
    
    result = transcriber.transcribe_file("nonexistent.mp3")
    print(result['text'])
    
except FileNotFoundError:
    logger.error("Audio file not found")
except Exception as e:
    logger.error(f"Transcription failed: {e}")
    # Fallback or retry logic here
```

## Project Structure

```
lemonfox/
├── lemonfox/                    # Main package directory
│   ├── __init__.py             # Package initialization
│   ├── config.py               # Configuration management
│   ├── lemonfox_transcriber.py # Main transcription logic
│   ├── voice_activation_transcriber.py  # Voice transcription features
│   └── voice/                  # Voice module
│       ├── __init__.py         # Voice package init
│       ├── voice_recorder.py   # Audio recording
│       ├── vad_processor.py    # Voice activity detection
│       ├── keyboard_handler.py # Global shortcuts
│       ├── text_injector.py    # Text injection
│       └── tray_icon.py       # System tray integration
├── main.py                     # Entry point
├── requirements.txt            # Core dependencies
├── requirements_voice.txt      # Optional voice dependencies
├── setup.py                    # Installation script
└── README.md                   # This file
```

## Advanced Configuration

### Voice Activity Detection

Adjust VAD sensitivity in code:
```python
from lemonfox.voice.vad_processor import VADProcessor

vad = VADProcessor(
    aggressiveness=3,        # 0-3, higher is more aggressive
    silence_threshold=3,     # Seconds of silence before processing
    frame_duration_ms=30     # Frame duration in milliseconds
)
```

### Custom Keyboard Shortcuts

Modify shortcuts:
```python
from lemonfox.voice.keyboard_handler import KeyboardHandler

handler = KeyboardHandler()
handler.update_hotkeys(
    toggle_shortcut='ctrl+alt+r',  # Custom recording shortcut
    listening_shortcut='ctrl+alt+m'  # Custom listening shortcut
)
```

## Troubleshooting

### Common Issues

1. **"Voice activation not available"**
   - Install all dependencies from requirements.txt
   - Check microphone permissions

2. **"Voice recording module not available"**
   - Install requirements_voice.txt
   - Check platform-specific dependencies

3. **Keyboard shortcuts not working**
   - Ensure application has necessary permissions
   - Check for conflicting shortcuts
   - Verify platform-specific dependencies are installed

4. **Text not injecting**
   - Ensure target application is in focus
   - Check clipboard permissions
   - Try using typing mode instead of clipboard injection

5. **Audio quality issues**
   - Check microphone settings
   - Adjust recording sample rate in VoiceRecorder
   - Ensure proper input device is selected

### Debugging Tips

Enable verbose logging:
```bash
python main.py --verbose
```

Check log files:
- `lemonfox.log` - Main application log
- `lemonfox_voice.log` - Voice module log

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with Whisper for transcription
- Voice activity detection using WebRTC VAD
- Keyboard handling with pynput
- System tray integration with pystray