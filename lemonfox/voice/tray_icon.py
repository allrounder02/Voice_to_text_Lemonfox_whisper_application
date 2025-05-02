import pystray
from PIL import Image, ImageDraw
import threading
import logging
import tkinter as tk
from tkinter import ttk
import time


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
        self.status_window = None
        self.logger = logging.getLogger(__name__)

    def start(self):
        """Start system tray icon"""
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop system tray icon"""
        if self.icon:
            self.icon.stop()
        if self.status_window:
            self.status_window.close()

    def update_status(self, recording=None, listening=None):
        """Update tray icon status"""
        if recording is not None:
            self.recording = recording
        if listening is not None:
            self.listening = listening

        if self.icon:
            self.icon.icon = self._create_icon()
            self.icon.menu = self._create_menu()

        # Update status window if it exists
        if self.status_window:
            self.status_window.update_status(self.recording, self.listening)

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

        # Draw microphone body (circle)
        draw.ellipse([width // 4, height // 4, width * 3 // 4, height * 3 // 4], fill=color)

        # Draw microphone stand
        draw.rectangle([width // 2 - 4, height * 2 // 3, width // 2 + 4, height - 8], fill=color)
        draw.rectangle([width // 3, height - 8, width * 2 // 3, height - 4], fill=color)

        # Add status indicator (small circle in corner)
        if self.recording:
            indicator_color = 'yellow'
        elif self.listening:
            indicator_color = 'lightgreen'
        else:
            indicator_color = 'white'

        draw.ellipse([width - 20, 4, width - 4, 20], fill=indicator_color)

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

        # Show status window
        menu_items.append(pystray.MenuItem(
            "Show Status Window",
            self._show_status_window,
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
            # Show status window when starting listening mode
            if self.listening:
                self._show_status_window(icon, item)

    def _show_status_window(self, icon, item):
        """Show the status window"""
        if not self.status_window or not self.status_window.is_visible():
            self.status_window = StatusWindow(self)
            self.status_window.show()

    def _quit(self, icon, item):
        """Handle quit action"""
        if self.on_quit:
            self.on_quit()
        self.stop()

    def show_status_window(self, icon=None, item=None):
        """Public method to show the status window"""
        self._show_status_window(icon, item)


class StatusWindow:
    def __init__(self, tray_icon):
        self.tray_icon = tray_icon
        self.root = None
        self.visible = False

    # Replace the show method in StatusWindow class in tray_icon.py with this improved version:

    def show(self):
        """Show the status window with improved error handling"""
        try:
            # Check if we already have a root window
            if self.root and hasattr(self.root, 'winfo_exists') and self.root.winfo_exists():
                self.visible = True
                self.root.deiconify()
                self.root.lift()
                self.root.focus_force()
                return

            # Create a new root window with proper error handling
            try:
                self.root = tk.Tk()
            except tk.TclError as e:
                logging.error(f"Failed to create Tkinter window: {e}")
                # Try to fix Tcl/Tk paths and retry
                import os
                import sys
                python_dir = sys.prefix
                os.environ['TCL_LIBRARY'] = os.path.join(python_dir, 'tcl', 'tcl8.6')
                os.environ['TK_LIBRARY'] = os.path.join(python_dir, 'tcl', 'tk8.6')
                # Retry
                self.root = tk.Tk()

            # Use a simple text title with emoji instead of an icon
            self.root.title("🎤 LemonFox Voice - Status")
            self.root.geometry("400x300")
            self.root.resizable(False, False)

            # Create main frame - Fix the sticky parameter issue by using a string
            main_frame = ttk.Frame(self.root, padding="10")
            main_frame.grid(row=0, column=0, sticky="nsew")  # Use string instead of tuple

            # Status label with emoji
            status_text = "Status: "
            if self.tray_icon.recording:
                status_text += "🔴 Recording"
            elif self.tray_icon.listening:
                status_text += "🟢 Listening"
            else:
                status_text += "⚪ Idle"

            self.status_label = ttk.Label(main_frame, text=status_text, font=('Arial', 14, 'bold'))
            self.status_label.grid(row=0, column=0, columnspan=2, pady=10)

            # Recording status with colored text
            recording_frame = ttk.LabelFrame(main_frame, text="Recording", padding="5")
            recording_frame.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
            self.recording_status = ttk.Label(
                recording_frame,
                text="● Active" if self.tray_icon.recording else "○ Inactive",
                foreground="red" if self.tray_icon.recording else "gray"
            )
            self.recording_status.grid(row=0, column=0)

            # Listening status with colored text
            listening_frame = ttk.LabelFrame(main_frame, text="Listening Mode", padding="5")
            listening_frame.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
            self.listening_status = ttk.Label(
                listening_frame,
                text="● Active" if self.tray_icon.listening else "○ Inactive",
                foreground="green" if self.tray_icon.listening else "gray"
            )
            self.listening_status.grid(row=0, column=0)

            # Activity log
            log_frame = ttk.LabelFrame(main_frame, text="Activity Log", padding="5")
            log_frame.grid(row=2, column=0, columnspan=2, pady=10, sticky="ew")

            self.log_text = tk.Text(log_frame, height=10, width=50)
            self.log_text.grid(row=0, column=0, sticky="ew")

            scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
            scrollbar.grid(row=0, column=1, sticky="ns")
            self.log_text['yscrollcommand'] = scrollbar.set
            self.log_text.config(state=tk.DISABLED)

            # Buttons
            button_frame = ttk.Frame(main_frame)
            button_frame.grid(row=3, column=0, columnspan=2, pady=10)

            ttk.Button(button_frame, text="Toggle Recording", command=self._toggle_recording).grid(row=0, column=0,
                                                                                                   padx=5)
            ttk.Button(button_frame, text="Toggle Listening", command=self._toggle_listening).grid(row=0, column=1,
                                                                                                   padx=5)
            ttk.Button(button_frame, text="Close", command=self.close).grid(row=0, column=2, padx=5)

            # Handle window close
            self.root.protocol("WM_DELETE_WINDOW", self.close)

            # Add log entry for window creation
            self._add_log_entry("Status window opened")

            # Start update loop
            self._update_loop()

            # Set visible and focus
            self.visible = True
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()

        except Exception as e:
            logging.error(f"Error creating status window: {e}")
            # Create a very minimal fallback window if everything else fails
            try:
                import tkinter.messagebox as messagebox
                messagebox.showinfo("LemonFox Status",
                                    f"Recording: {'ON' if self.tray_icon.recording else 'OFF'}\n"
                                    f"Listening: {'ON' if self.tray_icon.listening else 'OFF'}")
            except Exception as fallback_error:
                # Log the fallback error properly instead of silently passing
                logging.critical(f"Critical error: Failed to create fallback message box: {fallback_error}")
                print(f"CRITICAL ERROR: Failed to create status window: {e}")
                print(f"Fallback error: {fallback_error}")

    def close(self):
        """Close the status window"""
        if self.root:
            self.root.withdraw()
            self.visible = False

    def is_visible(self):
        """Check if the window is visible"""
        return self.visible and self.root and self.root.winfo_exists()

    def update_status(self, recording, listening):
        """Update the status display with color indicators"""
        if not self.root:
            return

        # Update status labels with colors
        if recording:
            self.recording_status.config(text="● Active", foreground="red")
            self.status_label.config(text="Status: Recording", foreground="red")
        else:
            self.recording_status.config(text="○ Inactive", foreground="gray")

        if listening:
            self.listening_status.config(text="● Active", foreground="green")
            self.status_label.config(text="Status: Listening", foreground="green")
        else:
            self.listening_status.config(text="○ Inactive", foreground="gray")

        if not recording and not listening:
            self.status_label.config(text="Status: Idle", foreground="black")

        # Add log entry
        self._add_log_entry(
            f"Recording: {'Active' if recording else 'Inactive'}, Listening: {'Active' if listening else 'Inactive'}")

    def _add_log_entry(self, message):
        """Add an entry to the activity log"""
        if not self.root:
            return

        self.log_text.config(state=tk.NORMAL)
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def _toggle_recording(self):
        """Toggle recording through the tray icon"""
        if self.tray_icon.on_toggle_recording:
            self.tray_icon.on_toggle_recording()

    def _toggle_listening(self):
        """Toggle listening through the tray icon"""
        if self.tray_icon.on_toggle_listening:
            self.tray_icon.on_toggle_listening()

    def _update_loop(self):
        """Periodic update loop for the status window"""
        if self.root and self.visible:
            # Update status periodically (in case of external changes)
            self.update_status(self.tray_icon.recording, self.tray_icon.listening)
            self.root.after(1000, self._update_loop)

    def _create_icon_image(self):
        """Create a simple icon image for the window"""
        try:
            from PIL import Image, ImageDraw

            # Create a 64x64 icon
            width = 64
            height = 64
            image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)

            # Draw microphone shape (similar to the tray icon)
            color = 'green' if self.tray_icon.listening else 'red' if self.tray_icon.recording else 'gray'

            # Draw microphone body (circle)
            draw.ellipse([width // 4, height // 4, width * 3 // 4, height * 3 // 4], fill=color)

            # Draw microphone stand
            draw.rectangle([width // 2 - 4, height * 2 // 3, width // 2 + 4, height - 8], fill=color)
            draw.rectangle([width // 3, height - 8, width * 2 // 3, height - 4], fill=color)

            return image
        except Exception as e:
            logging.warning(f"Error creating icon image: {e}")
            return None