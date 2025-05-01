import pystray
from PIL import Image, ImageDraw
import threading
import logging


class TrayIcon:
    def __init__(self, app_name="LemonFox Voice", on_toggle_recording=None,
                 on_toggle_listening=None, on_quit=None):
        self.app_name = app_name
        self.on_toggle_recording = on_toggle_recording
        self.on_toggle_listening = on_toggle_listening
        self.on_quit = on_quit
        self.icon = None
        self.thread = None
        self.recording = False
        self.listening = False

    def start(self):
        """Start system tray icon"""
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop system tray icon"""
        if self.icon:
            self.icon.stop()

    def update_status(self, recording=None, listening=None):
        """Update tray icon status"""
        if recording is not None:
            self.recording = recording
        if listening is not None:
            self.listening = listening

        if self.icon:
            self.icon.icon = self._create_icon()
            self.icon.menu = self._create_menu()

    def _run(self):
        """Run the tray icon"""
        self.icon = pystray.Icon(
            name=self.app_name,
            title=self.app_name,
            icon=self._create_icon(),
            menu=self._create_menu()
        )
        self.icon.run()

    def _create_icon(self):
        """Create tray icon image based on status"""
        # Create a 64x64 icon
        width = 64
        height = 64
        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        # Draw microphone shape
        if self.recording:
            # Red when recording
            color = 'red'
        elif self.listening:
            # Green when listening
            color = 'green'
        else:
            # Gray when idle
            color = 'gray'

        # Draw microphone body
        draw.ellipse([width // 4, height // 4, width * 3 // 4, height * 3 // 4], fill=color)

        # Draw microphone stand
        draw.rectangle([width // 2 - 4, height * 2 // 3, width // 2 + 4, height - 8], fill=color)
        draw.rectangle([width // 3, height - 8, width * 2 // 3, height - 4], fill=color)

        return image

    def _create_menu(self):
        """Create tray icon menu"""
        menu_items = []

        # Recording toggle
        if self.recording:
            menu_items.append(pystray.MenuItem(
                "Stop Recording",
                self._toggle_recording,
                enabled=True
            ))
        else:
            menu_items.append(pystray.MenuItem(
                "Start Recording",
                self._toggle_recording,
                enabled=True
            ))

        # Listening toggle
        if self.listening:
            menu_items.append(pystray.MenuItem(
                "Stop Listening Mode",
                self._toggle_listening,
                enabled=True
            ))
        else:
            menu_items.append(pystray.MenuItem(
                "Start Listening Mode",
                self._toggle_listening,
                enabled=True
            ))

        # Separator
        menu_items.append(pystray.Menu.SEPARATOR)

        # Quit option
        menu_items.append(pystray.MenuItem(
            "Quit",
            self._quit,
            enabled=True
        ))

        return pystray.Menu(*menu_items)

    def _toggle_recording(self, icon, item):
        """Handle recording toggle"""
        if self.on_toggle_recording:
            self.on_toggle_recording()

    def _toggle_listening(self, icon, item):
        """Handle listening toggle"""
        if self.on_toggle_listening:
            self.on_toggle_listening()

    def _quit(self, icon, item):
        """Handle quit action"""
        if self.on_quit:
            self.on_quit()
        self.stop()