"""
LemonFox Voice Module

Advanced voice recording and transcription functionality including:
- Voice recording with keyboard shortcuts
- Voice activity detection
- Text injection capabilities
- System tray integration
"""

from .voice_recorder import VoiceRecorder
from .vad_processor import VADProcessor
from .keyboard_handler import KeyboardHandler
from .text_injector import TextInjector
from .tray_icon import TrayIcon
from .voice_app import VoiceToTextApp

__all__ = [
    'VoiceRecorder',
    'VADProcessor',
    'KeyboardHandler',
    'TextInjector',
    'TrayIcon',
    'VoiceToTextApp'
]