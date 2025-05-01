from pynput import keyboard
import threading
import logging


class KeyboardHandler:
    def __init__(self, on_toggle_recording=None, on_start_listening=None):
        self.on_toggle_recording = on_toggle_recording
        self.on_start_listening = on_start_listening
        self.listener = None
        self.current_keys = set()
        self.running = False

        # Default shortcuts
        self.toggle_recording_hotkey = {keyboard.Key.ctrl_l, keyboard.Key.alt_l, keyboard.KeyCode.from_char('v')}
        self.listening_mode_hotkey = {keyboard.Key.ctrl_l, keyboard.Key.alt_l, keyboard.KeyCode.from_char('l')}

    def start(self):
        """Start keyboard listener in background thread"""
        if not self.running:
            self.running = True
            self.listener = keyboard.Listener(
                on_press=self._on_press,
                on_release=self._on_release
            )
            self.listener.start()
            logging.info("Keyboard handler started")

    def stop(self):
        """Stop keyboard listener"""
        if self.running:
            self.running = False
            if self.listener:
                self.listener.stop()
                self.listener = None
            logging.info("Keyboard handler stopped")

    def _on_press(self, key):
        """Handle key press events"""
        try:
            self.current_keys.add(key)

            # Check for hotkey combinations
            if self._is_hotkey_active(self.toggle_recording_hotkey):
                if self.on_toggle_recording:
                    threading.Thread(target=self.on_toggle_recording, daemon=True).start()

            elif self._is_hotkey_active(self.listening_mode_hotkey):
                if self.on_start_listening:
                    threading.Thread(target=self.on_start_listening, daemon=True).start()

        except AttributeError:
            pass

    def _on_release(self, key):
        """Handle key release events"""
        try:
            self.current_keys.discard(key)
        except:
            pass

    def _is_hotkey_active(self, hotkey):
        """Check if all keys in hotkey are currently pressed"""
        return self.current_keys.issuperset(hotkey)

    def update_hotkeys(self, toggle_shortcut=None, listening_shortcut=None):
        """Update hotkey combinations"""
        if toggle_shortcut:
            self.toggle_recording_hotkey = self._parse_shortcut(toggle_shortcut)
        if listening_shortcut:
            self.listening_mode_hotkey = self._parse_shortcut(listening_shortcut)

    def _parse_shortcut(self, shortcut_str):
        """Parse shortcut string like 'ctrl+alt+v' into key set"""
        parts = shortcut_str.lower().split('+')
        keys = set()

        for part in parts:
            if part == 'ctrl':
                keys.add(keyboard.Key.ctrl_l)
            elif part == 'alt':
                keys.add(keyboard.Key.alt_l)
            elif part == 'shift':
                keys.add(keyboard.Key.shift_l)
            elif len(part) == 1:
                keys.add(keyboard.KeyCode.from_char(part))
            else:
                # Handle special keys
                try:
                    keys.add(getattr(keyboard.Key, part))
                except AttributeError:
                    logging.warning(f"Unknown key: {part}")

        return keys