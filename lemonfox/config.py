import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Set up logging
logger = logging.getLogger(__name__)


def load_config():
    """Load configuration from environment variables and .env file."""

    # Construct the path to the .env file
    # This ensures we look for .env relative to the project root, not the current working directory
    project_root = Path(__file__).parent.parent  # This goes up to the project root directory
    env_path = project_root / '.env'

    # Load .env file if it exists
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        logger.info(f"Loaded .env file from {env_path}")
    else:
        logger.warning(f".env file not found at {env_path}, using environment variables only")

    # Get configuration values
    config = {
        "api_key": os.getenv("LEMONFOX_API_KEY"),
        "default_language": os.getenv("LEMONFOX_DEFAULT_LANGUAGE", "english"),
        "output_directory": os.getenv("OUTPUT_DIRECTORY", "./transcriptions"),
        "log_level": os.getenv("LOG_LEVEL", "INFO")
    }

    # Log warnings for missing critical values
    if not config["api_key"]:
        logger.warning("LEMONFOX_API_KEY not found in environment variables")

    return config


# Create output directory if it doesn't exist
def ensure_output_directory(directory_path):
    """Ensure the output directory exists."""
    path = Path(directory_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


# Configuration constants
CONFIG_DIR = Path.home() / ".lemonfox"