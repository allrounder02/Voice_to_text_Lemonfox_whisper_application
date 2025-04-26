# LemonFox Transcription Utility

A Python utility for transcribing audio using the LemonFox.ai API.

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/lemonfox-transcriber.git
cd lemonfox-transcriber
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up your configuration

Create a `.env` file in the project root with your LemonFox API key and other settings:

```bash
# Create .env file
cp .env.example .env

# Edit with your favorite editor
nano .env
```

Your `.env` file should look like this:

```
LEMONFOX_API_KEY=your_api_key_here
LEMONFOX_DEFAULT_LANGUAGE=english
OUTPUT_DIRECTORY=./transcriptions
```

## Usage

### Command Line

```bash
# Transcribe audio from a URL
python lemonfox_transcriber.py --url https://example.com/audio.mp3 --output my_transcription.json

# Transcribe a local audio file
python lemonfox_transcriber.py --file /path/to/audio.mp3

# Specify a language
python lemonfox_transcriber.py --url https://example.com/audio.mp3 --language spanish
```

### As a Python Module

```python
from lemonfox_transcriber import LemonFoxTranscriber
from config import load_config

# Load configuration from .env file
config = load_config()

# Initialize transcriber
transcriber = LemonFoxTranscriber(config=config)

# Transcribe from URL
response = transcriber.transcribe_url("https://example.com/audio.mp3")
print(response["text"])

# Transcribe local file
response = transcriber.transcribe_file("/path/to/audio.mp3")

# Save transcription to file
output_file = transcriber.save_transcription(response)
print(f"Saved to: {output_file}")
```

### Example Scripts

Check the `examples/` directory for usage examples:

```bash
python examples/basic_usage.py
```

## Security Notes

- **Never commit your `.env` file to Git**. It's already in the `.gitignore` file, but always double-check.
- If you accidentally push sensitive information to a Git repository, consider it compromised and generate a new API key.
- Consider using environment variables instead of a `.env` file for production environments.

## License

[MIT License](LICENSE)