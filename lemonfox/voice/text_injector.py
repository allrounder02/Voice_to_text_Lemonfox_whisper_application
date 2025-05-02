import pyautogui
import pyperclip
import platform
import time
import logging


class TextInjector:
    def __init__(self):
        self.platform = platform.system().lower()
        # Set pyautogui fail-safe
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1

        # Platform-specific import checking
        self.platform_available = True

        if self.platform == 'windows':
            try:
                import win32gui
                self.win32gui = win32gui
            except ImportError:
                logging.error("win32gui not available. Please install pywin32 for Windows support.")
                self.platform_available = False
        elif self.platform == 'darwin':
            try:
                from AppKit import NSWorkspace
                self.NSWorkspace = NSWorkspace
            except ImportError:
                logging.error("AppKit not available. Please install pyobjc-framework-Cocoa for macOS support.")
                self.platform_available = False
        elif self.platform.startswith('linux'):
            try:
                import subprocess
                # Test if xdotool is available
                result = subprocess.run(['which', 'xdotool'], capture_output=True)
                if result.returncode != 0:
                    logging.error("xdotool not found. Please install xdotool for Linux support.")
                    self.platform_available = False
            except Exception as e:
                logging.error(f"Error checking Linux dependencies: {e}")
                self.platform_available = False

    def inject_text(self, text):
        """Inject text into the currently active window"""
        try:
            # Store current clipboard content
            original_clipboard = self._get_clipboard()

            # Copy text to clipboard
            pyperclip.copy(text)
            time.sleep(0.1)  # Give time for clipboard to update

            # Paste using keyboard shortcut
            if self.platform == 'darwin':  # macOS
                pyautogui.hotkey('cmd', 'v')
            else:  # Windows, Linux
                pyautogui.hotkey('ctrl', 'v')

            time.sleep(0.1)  # Give time for paste to complete

            # Optionally restore original clipboard
            # self._restore_clipboard(original_clipboard)

            return True
        except Exception as e:
            logging.error(f"Failed to inject text: {e}")
            return False

    def type_text(self, text, interval=0.05):
        """Alternative method: Type text directly (slower but more compatible)"""
        try:
            pyautogui.typewrite(text, interval=interval)
            return True
        except Exception as e:
            logging.error(f"Failed to type text: {e}")
            return False

    def get_active_window(self):
        """Get information about the active window"""
        if not self.platform_available:
            logging.warning("Platform functionality not available")
            return {"title": "Unknown"}

        try:
            if self.platform == 'windows':
                window = self.win32gui.GetForegroundWindow()
                title = self.win32gui.GetWindowText(window)
                return {"title": title, "handle": window}
            elif self.platform == 'darwin':
                active_app = self.NSWorkspace.sharedWorkspace().frontmostApplication()
                return {"title": active_app.localizedName(), "bundle": active_app.bundleIdentifier()}
            else:  # Linux
                import subprocess
                result = subprocess.run(['xdotool', 'getactivewindow', 'getwindowname'],
                                        capture_output=True, text=True)
                return {"title": result.stdout.strip()}
        except Exception as e:
            logging.warning(f"Could not get active window: {e}")
            return {"title": "Unknown"}

    def _get_clipboard(self):
        """Get current clipboard content"""
        try:
            return pyperclip.paste()
        except:
            return ""

    def _restore_clipboard(self, content):
        """Restore clipboard content"""
        try:
            pyperclip.copy(content)
        except:
            pass

    # Modified version of TextInjector.focus_window method
    def focus_window(self, window_info):
        """Focus a specific window with improved error handling"""
        if not self.platform_available:
            logging.warning("Platform functionality not available")
            return False

        # Safety check for empty window info
        if not window_info:
            logging.warning("Empty window info provided")
            return False

        try:
            if self.platform == 'windows':
                if 'handle' in window_info and window_info['handle']:
                    # Try focusing with multiple methods
                    try:
                        # Try SetForegroundWindow first
                        self.win32gui.SetForegroundWindow(window_info['handle'])
                    except Exception as e:
                        logging.warning(f"SetForegroundWindow failed: {e}")
                        # Try alternate method - simulate Alt+Tab
                        pyautogui.keyDown('alt')
                        pyautogui.press('tab')
                        pyautogui.keyUp('alt')
                        time.sleep(0.2)
                else:
                    # No handle, try focusing by title
                    if 'title' in window_info and window_info['title']:
                        # Focus by title using Alt+Tab sequence
                        pyautogui.keyDown('alt')
                        pyautogui.press('tab')
                        pyautogui.keyUp('alt')
                        time.sleep(0.2)
            elif self.platform == 'darwin':
                # macOS implementation remains unchanged
                import subprocess
                if 'bundle' in window_info:
                    subprocess.run(['osascript', '-e',
                                    f'tell application "{window_info["bundle"]}" to activate'])
            else:  # Linux
                # Linux implementation remains unchanged
                import subprocess
                if 'title' in window_info:
                    subprocess.run(['xdotool', 'search', '--name', window_info['title'],
                                    'windowactivate'])
            return True
        except Exception as e:
            logging.error(f"Failed to focus window: {e}")
            # Don't throw an exception, just return false
            return False