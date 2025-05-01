import os
import requests
import argparse
import json
from typing import Optional, Dict, Any
import logging
import datetime
from lemonfox.config import load_config, ensure_output_directory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('lemonfox_transcriber')


class LemonFoxTranscriber:
    """
    A client for the LemonFox.ai API transcription service.
    """

    BASE_URL = "https://api.lemonfox.ai/v1/audio/transcriptions"

    def __init__(self, api_key: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the LemonFox transcriber.

        Args:
            api_key: API key for LemonFox. If not provided, looks for LEMONFOX_API_KEY env variable.
            config: Configuration dictionary. If provided, overrides other parameters.
        """
        # If config is provided, use it
        self.config = config or load_config()

        # API key priority: 1. Explicit parameter, 2. Config, 3. Environment variable
        self.api_key = api_key or self.config.get("api_key")

        if not self.api_key:
            raise ValueError("API key must be provided or set as LEMONFOX_API_KEY environment variable")

        self.headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        # Use the existing ensure_output_directory function with config
        if isinstance(self.config.get("output_directory"), dict):
            output_dir = self.config["output_directory"].get("path", "./transcriptions")
        else:
            output_dir = self.config.get("output_directory", "./transcriptions")

        ensure_output_directory(output_dir)

    def transcribe_url(self,
                       audio_url: str,
                       language: Optional[str] = None,
                       response_format: str = "json") -> Dict[str, Any]:
        """
        Transcribe audio from a URL.

        Args:
            audio_url: URL to the audio file
            language: Language of the audio (defaults to config setting)
            response_format: Format of the response (default: json)

        Returns:
            Transcription response as a dictionary
        """
        language = language or self.config.get("default_language", "english")

        data = {
            "file": audio_url,
            "language": language,
            "response_format": response_format
        }

        logger.info(f"Transcribing audio from URL: {audio_url}")
        return self._make_request(data=data)

    def transcribe_file(self,
                        file_path: str,
                        language: Optional[str] = None,
                        response_format: str = "json") -> Dict[str, Any]:
        """
        Transcribe audio from a local file.

        Args:
            file_path: Path to the local audio file
            language: Language of the audio (defaults to config setting)
            response_format: Format of the response (default: json)

        Returns:
            Transcription response as a dictionary
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        language = language or self.config.get("default_language", "english")

        data = {
            "language": language,
            "response_format": response_format
        }

        files = {
            "file": open(file_path, "rb")
        }

        logger.info(f"Transcribing audio from file: {file_path}")
        try:
            return self._make_request(data=data, files=files)
        finally:
            files["file"].close()

    def _make_request(self,
                      data: Dict[str, str],
                      files: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a request to the LemonFox API.

        Args:
            data: Request data
            files: Files to upload (optional)

        Returns:
            API response as a dictionary
        """
        response = None  # Initialize response variable

        try:
            response = requests.post(
                self.BASE_URL,
                headers=self.headers,
                data=data,
                files=files,
                timeout=60  # Set a reasonable timeout
            )
            response.raise_for_status()  # Raise an exception for 4XX/5XX responses
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            if response and response.text:  # Check if response exists before accessing
                logger.error(f"Response: {response.text}")
            raise
        except requests.exceptions.ConnectionError:
            logger.error("Connection error. Please check your internet connection.")
            raise
        except requests.exceptions.Timeout:
            logger.error("Request timed out. Please try again later.")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            raise
        except json.JSONDecodeError:
            logger.error("Failed to parse response as JSON")
            if response:  # Check if response exists before accessing
                raise ValueError(f"Invalid JSON response: {response.text}")
            else:
                raise

    def save_transcription(self, response: Dict[str, Any], output_file: Optional[str] = None) -> str:
        """
        Save the transcription to a file.

        Args:
            response: The transcription response
            output_file: Path to the output file (optional)

        Returns:
            Path to the saved file
        """
        if not output_file:
            # Generate a filename based on timestamp if not provided
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

            # Get output directory from config - handle both dict and string cases
            output_dir = self.config.get("output_directory", "./transcriptions")

            # If the config value is a dict, extract the path or use default
            if isinstance(output_dir, dict):
                output_dir = output_dir.get("path", "./transcriptions")

            # Convert to string to ensure compatibility
            output_dir = str(output_dir)

            # Ensure the directory exists using the existing function
            ensure_output_directory(output_dir)

            # Create the output path
            output_file = os.path.join(output_dir, f"transcription_{timestamp}.json")

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(response, f, indent=2, ensure_ascii=False)

        logger.info(f"Transcription saved to {output_file}")
        return output_file


def main():
    """Command line interface for the LemonFox transcriber."""
    parser = argparse.ArgumentParser(description="Transcribe audio using LemonFox.ai API")
    parser.add_argument("--api-key", help="LemonFox API key (or set LEMONFOX_API_KEY env var)")

    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--url", help="URL to the audio file")
    source_group.add_argument("--file", help="Path to the local audio file")

    parser.add_argument("--language", help="Language of the audio (defaults to config)")
    parser.add_argument("--format", default="json", help="Response format (default: json)")
    parser.add_argument("--output", help="Output file for the transcription")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    try:
        # Load config first
        config = load_config()

        # Initialize transcriber with command-line API key or config
        transcriber = LemonFoxTranscriber(api_key=args.api_key, config=config)

        if args.url:
            response = transcriber.transcribe_url(
                audio_url=args.url,
                language=args.language,
                response_format=args.format
            )
        else:
            response = transcriber.transcribe_file(
                file_path=args.file,
                language=args.language,
                response_format=args.format
            )

        # Save transcription to file
        transcriber.save_transcription(response, args.output)

    except Exception as e:
        logger.error(f"Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()