"""
LemonFox - Audio Transcription Application

A comprehensive audio transcription solution supporting URLs, local files,
and voice activation with advanced features.
"""

import os
from pathlib import Path

# Package version
__version__ = "1.0.0"

# Package metadata
__author__ = "LemonFox Team"
__license__ = "MIT"

# Package-level constants
CONFIG_DIR = Path.home() / ".lemonfox"
TEMP_DIR = CONFIG_DIR / "temp"
OUTPUT_DIR = CONFIG_DIR / "output"

# Ensure directories exist
for directory in [CONFIG_DIR, TEMP_DIR, OUTPUT_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Import main components for easier access
# Import both functions from config.py
from .config import load_config, ensure_output_directory
from .lemonfox_transcriber import LemonFoxTranscriber
from .voice_activation_transcriber import VoiceActivationTranscriber

# Conditional voice imports
try:
    from .voice import VoiceToTextApp, VoiceRecorder, VADProcessor, KeyboardHandler, TextInjector, TrayIcon
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False

# Define what's available when using "from lemonfox import *"
__all__ = [
    'load_config',
    'ensure_output_directory',  # Added this to __all__
    'LemonFoxTranscriber',
    'VoiceActivationTranscriber',
    'CONFIG_DIR',
    'TEMP_DIR',
    'OUTPUT_DIR',
    'VOICE_AVAILABLE',
    '__version__'
]

# Add voice components to __all__ if available
if VOICE_AVAILABLE:
    __all__.extend([
        'VoiceToTextApp',
        'VoiceRecorder',
        'VADProcessor',
        'KeyboardHandler',
        'TextInjector',
        'TrayIcon'
    ])