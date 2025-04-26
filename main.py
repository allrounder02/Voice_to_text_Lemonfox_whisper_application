import os
import requests
import argparse
import json
from typing import Optional, Dict, Any, Union
import logging

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

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the LemonFox transcriber.

        Args:
            api_key: API key for LemonFox. If not provided, looks for LEMONFOX_API_KEY environment variable.
        """
        self.api_key = api_key or os.environ.get("LEMONFOX_API_KEY")
        if not self.api_key:
            raise ValueError("API key must be provided or set as LEMONFOX_API_KEY environment variable")

        self.headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

    def transcribe_url(self,
                       audio_url: str,
                       language: str = "english",
                       response_format: str = "json") -> Dict[str, Any]:
        """
        Transcribe audio from a URL.

        Args:
            audio_url: URL to the audio file
            language: Language of the audio (default: english)
            response_format: Format of the response (default: json)

        Returns:
            Transcription response as a dictionary
        """
        data = {
            "file": audio_url,
            "language": language,
            "response_format": response_format
        }

        logger.info(f"Transcribing audio from URL: {audio_url}")
        return self._make_request(data=data)

    def transcribe_file(self,
                        file_path: str,
                        language: str = "english",
                        response_format: str = "json") -> Dict[str, Any]:
        """
        Transcribe audio from a local file.

        Args:
            file_path: Path to the local audio file
            language: Language of the audio (default: english)
            response_format: Format of the response (default: json)

        Returns:
            Transcription response as a dictionary
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")

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
            if response.text:
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
            raise ValueError(f"Invalid JSON response: {response.text}")


def save_transcription(response: Dict[str, Any], output_file: str) -> None:
    """
    Save the transcription to a file.

    Args:
        response: The transcription response
        output_file: Path to the output file
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(response, f, indent=2, ensure_ascii=False)
    logger.info(f"Transcription saved to {output_file}")


def main():
    """Command line interface for the LemonFox transcriber."""
    parser = argparse.ArgumentParser(description="Transcribe audio using LemonFox.ai API")
    parser.add_argument("--api-key", help="LemonFox API key (or set LEMONFOX_API_KEY env var)")

    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--url", help="URL to the audio file")
    source_group.add_argument("--file", help="Path to the local audio file")

    parser.add_argument("--language", default="english", help="Language of the audio (default: english)")
    parser.add_argument("--format", default="json", help="Response format (default: json)")
    parser.add_argument("--output", help="Output file for the transcription")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    try:
        transcriber = LemonFoxTranscriber(api_key=args.api_key)

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

        if args.output:
            save_transcription(response, args.output)
        else:
            print(json.dumps(response, indent=2))

    except Exception as e:
        logger.error(f"Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()