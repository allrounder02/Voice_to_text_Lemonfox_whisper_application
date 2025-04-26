import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)


def load_config() -> Dict[str, Any]:
    """
    Load configuration from environment variables or .env file

    Returns:
        Dictionary containing configuration values
    """
    # Try to load from .env file if it exists
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.exists(env_path):
        logger.info(f"Loading configuration from {env_path}")
        load_dotenv(env_path)
    else:
        logger.warning(".env file not found, using environment variables only")

    # Get required configuration
    api_key = os.environ.get("LEMONFOX_API_KEY")
    if not api_key:
        logger.warning("LEMONFOX_API_KEY not found in environment variables")

    # Get optional configuration with defaults
    config = {
        "api_key": api_key,
        "default_language": os.environ.get("LEMONFOX_DEFAULT_LANGUAGE", "english"),
        "output_directory": os.environ.get("OUTPUT_DIRECTORY", "./transcriptions"),
    }

    return config


def get_api_key() -> Optional[str]:
    """
    Get the LemonFox API key from environment variables

    Returns:
        API key if found, None otherwise
    """
    return os.environ.get("LEMONFOX_API_KEY")


# Create output directory if it doesn't exist
def ensure_output_directory(config: Dict[str, Any]) -> None:
    """
    Ensure the output directory exists

    Args:
        config: Configuration dictionary
    """
    output_dir = config.get("output_directory")
    if output_dir and not os.path.exists(output_dir):
        logger.info(f"Creating output directory: {output_dir}")
        os.makedirs(output_dir, exist_ok=True)