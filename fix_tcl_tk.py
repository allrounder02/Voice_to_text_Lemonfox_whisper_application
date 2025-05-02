"""
Simple script to fix TCL/TK path issues on Windows for the LemonFox application
"""
import os
import sys
import glob
import shutil
import platform
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tcl_tk_fix")

def fix_tcl_tk():
    """Fix TCL/TK paths for Windows"""
    if platform.system() != "Windows":
        logger.info("TCL/TK fix only needed on Windows")
        return True

    try:
        logger.info("Fixing TCL/TK paths...")

        # Get Python installation directory
        python_dir = sys.prefix
        logger.info(f"Python directory: {python_dir}")

        # Find TCL/TK directories
        tcl_paths = glob.glob(os.path.join(python_dir, 'tcl', 'tcl*'))
        tk_paths = glob.glob(os.path.join(python_dir, 'tcl', 'tk*'))

        logger.info(f"Found TCL paths: {tcl_paths}")
        logger.info(f"Found TK paths: {tk_paths}")

        # If not found in standard location, check Lib directory
        if not tcl_paths:
            tcl_paths = glob.glob(os.path.join(python_dir, 'Lib', 'tcl*'))
        if not tk_paths:
            tk_paths = glob.glob(os.path.join(python_dir, 'Lib', 'tk*'))

        # Create directories if needed
        lib_dir = os.path.join(python_dir, 'Lib')

        # If paths found, set environment variables
        if tcl_paths:
            tcl_dir = tcl_paths[0]
            os.environ['TCL_LIBRARY'] = tcl_dir
            logger.info(f"Set TCL_LIBRARY to {tcl_dir}")
        else:
            # Create a dummy directory
            tcl_dir = os.path.join(lib_dir, 'tcl8.6')
            os.makedirs(tcl_dir, exist_ok=True)
            with open(os.path.join(tcl_dir, 'init.tcl'), 'w') as f:
                f.write('# Placeholder init.tcl file\n')
            os.environ['TCL_LIBRARY'] = tcl_dir
            logger.info(f"Created and set TCL_LIBRARY to {tcl_dir}")

        if tk_paths:
            tk_dir = tk_paths[0]
            os.environ['TK_LIBRARY'] = tk_dir
            logger.info(f"Set TK_LIBRARY to {tk_dir}")
        else:
            # Create a dummy directory
            tk_dir = os.path.join(lib_dir, 'tk8.6')
            os.makedirs(tk_dir, exist_ok=True)
            os.environ['TK_LIBRARY'] = tk_dir
            logger.info(f"Created and set TK_LIBRARY to {tk_dir}")

        # Test if Tkinter works
        try:
            import tkinter as tk
            root = tk.Tk()
            root.destroy()
            logger.info("Tkinter test successful!")
            return True
        except Exception as e:
            logger.error(f"Tkinter test failed: {e}")
            return False

    except Exception as e:
        logger.error(f"Error fixing TCL/TK paths: {e}")
        return False

if __name__ == "__main__":
    success = fix_tcl_tk()
    if success:
        print("TCL/TK paths fixed successfully!")
    else:
        print("Failed to fix TCL/TK paths")