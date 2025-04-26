# Voice-Activated Transcription with LemonFox

This extension to the LemonFox Transcriber allows for voice-activated transcription, where the system remains in a "sleeping" state until it detects voice input.

## How It Works

1. The application runs continuously in the background, monitoring audio input
2. When voice is detected, it starts recording
3. When silence is detected for a specified duration, it stops recording
4. The recorded audio is automatically sent to LemonFox for transcription
5. The transcription result is displayed and saved

## Installation

### Install Additional Dependencies

```bash
pip install sounddevice webrtcvad numpy scipy
```

Or use the updated requirements.txt:

```bash
pip install -r requirements.txt
```

### System Dependencies for WebRTC VAD

On Linux, you might need to install PortAudio:

```bash
# Ubuntu/Debian
sudo apt-get install portaudio19-dev

# Fedora
sudo dnf install portaudio-devel

# Arch Linux
sudo pacman -S portaudio
```

On macOS:

```bash
brew install portaudio
```

On Windows, the wheels should include all necessary dependencies.

## Usage

### Basic Usage

```bash
python voice_activated_transcriber.py
```

This will start the voice-activated transcriber in listening mode. Speak to start recording, and it will automatically stop recording when silence is detected.

### Advanced Options

```bash
# Adjust voice detection sensitivity
python voice_activated_transcriber.py --threshold 0.02

# Change silence duration (seconds) before stopping recording
python voice_activated_transcriber.py --silence-duration 2.0

# Change audio sample rate
python voice_activated_transcriber.py --sample-rate 44100

# Enable verbose logging
python voice_activated_transcriber.py --verbose
```

## Troubleshooting

### Microphone Access Issues

Make sure your application has permission to access the microphone:

- **Windows**: Check privacy settings in Windows Settings
- **macOS**: Check privacy settings in System Preferences
- **Linux**: Ensure your user has access to audio devices

### Voice Detection Problems

If the system doesn't detect your voice:

- Decrease the threshold (e.g., `--threshold 0.005`)
- Check your microphone is working properly
- Speak louder or move closer to the microphone

If the system detects too many false positives:

- Increase the threshold (e.g., `--threshold 0.03`)
- Increase the silence duration (e.g., `--silence-duration 2.0`)

## Configuration

You can add voice activation settings to your `.env` file:

```
# Voice activation settings
VAD_THRESHOLD=0.01
VAD_SILENCE_DURATION=1.5
VAD_SAMPLE_RATE=16000
```

## Integration

This module integrates with the main LemonFox transcriber and uses the same configuration system, ensuring consistency and security of your API keys.