"""
Launcher script for LemonFox with improved error handling
"""
import os  # This import was missing
import sys
import platform
import logging
import subprocess  # This import had a typo
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('lemonfox_launcher.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('lemonfox_launcher')

def check_tcl_tk_fix():
    """Check if the TCL/TK fix script exists and run it if needed"""
    fix_script = 'fix_tcl_tk.py'

    if os.path.exists(fix_script):
        logger.info(f"Running TCL/TK fix script: {fix_script}")
        try:
            # Run the script - fixed subprocess reference
            result = subprocess.run([sys.executable, fix_script],
                                   capture_output=True,
                                   text=True)

            if result.returncode == 0:
                logger.info("TCL/TK fix applied successfully")
                return True
            else:
                logger.error(f"TCL/TK fix failed: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error running TCL/TK fix: {e}")
            return False
    else:
        logger.warning(f"TCL/TK fix script not found: {fix_script}")

        # Fall back to manual fix on Windows
        if platform.system() == "Windows":
            try:
                # These imports are already available from above
                python_dir = sys.prefix

                # Set environment variables directly
                os.environ['TCL_LIBRARY'] = os.path.join(python_dir, 'tcl', 'tcl8.6')
                os.environ['TK_LIBRARY'] = os.path.join(python_dir, 'tcl', 'tk8.6')

                logger.info("Applied manual TCL/TK fix")
                return True
            except Exception as e:
                logger.error(f"Error applying manual TCL/TK fix: {e}")
                return False

    return True  # Continue even if no fix was applied


def launch_application():
    """Launch the main LemonFox application"""
    try:
        logger.info("Launching LemonFox application...")

        # Add a handler to gracefully handle Ctrl+C
        import signal
        def sigint_handler(signum, frame):
            logger.info("Received interrupt signal, cleaning up...")
            # Allow time for cleanup
            time.sleep(1)
            sys.exit(0)

        signal.signal(signal.SIGINT, sigint_handler)

        # Launch the main application
        try:
            import main
            main.main()
        except ImportError as e:
            # Properly define what to do in this except block
            logger.error(f"Failed to import main module: {e}")
            logger.info("Running as script instead.")

            try:
                subprocess.run([sys.executable, "main.py", "--verbose"])
            except Exception as script_e:
                logger.error(f"Failed to run main.py as script: {script_e}")
                print(f"Error: Could not launch LemonFox. Please check logs.")

    except Exception as e:
        logger.error(f"Error launching application: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    # Apply TCL/TK fix first
    check_tcl_tk_fix()

    # Launch the application
    launch_application()