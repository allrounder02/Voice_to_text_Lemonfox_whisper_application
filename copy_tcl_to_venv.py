"""
copy_tcl_to_venv.py - Script to copy TCL/TK from Python installation to virtual environment
Specifically designed to fix Tkinter issues in Python 3.13 and virtual environments
"""

import os
import sys
import shutil
import platform


def copy_tcl_to_venv():
    """Copy TCL/TK directories from Python installation to virtual environment"""
    print("Fixing TCL/TK for virtual environment...")

    # Get Python installation directory (system Python)
    if hasattr(sys, 'base_prefix'):
        # For venv virtual environments
        system_python_dir = sys.base_prefix
    elif hasattr(sys, 'real_prefix'):
        # For virtualenv virtual environments
        system_python_dir = sys.real_prefix
    else:
        # Not in a virtual environment
        print("Not running in a virtual environment. No fix needed.")
        return False

    # Get current virtual environment directory
    venv_dir = sys.prefix

    print(f"System Python directory: {system_python_dir}")
    print(f"Virtual environment directory: {venv_dir}")

    # Check if we're in a virtual environment
    if system_python_dir == venv_dir:
        print("Not running in a virtual environment. No fix needed.")
        return False

    # Source and destination paths
    tcl_source = os.path.join(system_python_dir, 'tcl')
    tcl_dest = os.path.join(venv_dir, 'tcl')

    if not os.path.exists(tcl_source):
        print(f"Error: TCL directory not found at {tcl_source}")
        return False

    # Check if destination already exists
    if os.path.exists(tcl_dest):
        print(f"TCL directory already exists at {tcl_dest}. Removing it first...")
        try:
            shutil.rmtree(tcl_dest)
        except Exception as e:
            print(f"Error removing existing TCL directory: {e}")
            return False

    # Copy TCL directory
    try:
        print(f"Copying TCL from {tcl_source} to {tcl_dest}...")
        shutil.copytree(tcl_source, tcl_dest)
        print("TCL directory copied successfully!")
    except Exception as e:
        print(f"Error copying TCL directory: {e}")
        return False

    # Setup environment variables
    try:
        # Find specific TCL/TK paths
        import glob
        tcl_paths = glob.glob(os.path.join(tcl_dest, 'tcl*'))
        tk_paths = glob.glob(os.path.join(tcl_dest, 'tk*'))

        if tcl_paths:
            os.environ['TCL_LIBRARY'] = tcl_paths[0]
            print(f"Set TCL_LIBRARY to: {tcl_paths[0]}")

        if tk_paths:
            os.environ['TK_LIBRARY'] = tk_paths[0]
            os.environ['TKPATH'] = tk_paths[0]
            print(f"Set TK_LIBRARY and TKPATH to: {tk_paths[0]}")
    except Exception as e:
        print(f"Error setting environment variables: {e}")

    # For Windows: Update the activate scripts to set these variables
    if platform.system() == "Windows":
        try:
            # Update activate.bat
            activate_bat = os.path.join(venv_dir, 'Scripts', 'activate.bat')
            if os.path.exists(activate_bat):
                with open(activate_bat, 'r') as f:
                    content = f.read()

                # Check if we already modified this file
                if "SET TCL_LIBRARY=" not in content:
                    # Add environment variables
                    additions = "\n\n"
                    additions += "REM TCL/TK environment variables\n"
                    if tcl_paths:
                        additions += f'SET TCL_LIBRARY="{tcl_paths[0]}"\n'
                    if tk_paths:
                        additions += f'SET TK_LIBRARY="{tk_paths[0]}"\n'
                        additions += f'SET TKPATH="{tk_paths[0]}"\n'

                    # Find where to insert (before the end)
                    insert_pos = content.rfind("REM")
                    if insert_pos == -1:
                        # If no REM found, add to the end
                        with open(activate_bat, 'a') as f:
                            f.write(additions)
                    else:
                        # Otherwise, insert before the last REM
                        new_content = content[:insert_pos] + additions + content[insert_pos:]
                        with open(activate_bat, 'w') as f:
                            f.write(new_content)

                    print(f"Updated {activate_bat} with TCL/TK environment variables")

            # For PowerShell: Update activate.ps1
            activate_ps1 = os.path.join(venv_dir, 'Scripts', 'Activate.ps1')
            if os.path.exists(activate_ps1):
                with open(activate_ps1, 'r') as f:
                    content = f.read()

                # Check if we already modified this file
                if "$env:TCL_LIBRARY" not in content:
                    # Add environment variables
                    additions = "\n\n"
                    additions += "# TCL/TK environment variables\n"
                    if tcl_paths:
                        additions += f'$env:TCL_LIBRARY = "{tcl_paths[0]}"\n'
                    if tk_paths:
                        additions += f'$env:TK_LIBRARY = "{tk_paths[0]}"\n'
                        additions += f'$env:TKPATH = "{tk_paths[0]}"\n'

                    # Add to the end
                    with open(activate_ps1, 'a') as f:
                        f.write(additions)

                    print(f"Updated {activate_ps1} with TCL/TK environment variables")
        except Exception as e:
            print(f"Error updating activation scripts: {e}")

    # For Linux/Mac: Update activate script
    elif platform.system() in ["Linux", "Darwin"]:
        try:
            # Update activate script
            activate_sh = os.path.join(venv_dir, 'bin', 'activate')
            if os.path.exists(activate_sh):
                with open(activate_sh, 'r') as f:
                    content = f.read()

                # Check if we already modified this file
                if "export TCL_LIBRARY=" not in content:
                    # Add environment variables
                    additions = "\n\n"
                    additions += "# TCL/TK environment variables\n"
                    if tcl_paths:
                        additions += f'export TCL_LIBRARY="{tcl_paths[0]}"\n'
                    if tk_paths:
                        additions += f'export TK_LIBRARY="{tk_paths[0]}"\n'
                        additions += f'export TKPATH="{tk_paths[0]}"\n'

                    # Add to the end
                    with open(activate_sh, 'a') as f:
                        f.write(additions)

                    print(f"Updated {activate_sh} with TCL/TK environment variables")
        except Exception as e:
            print(f"Error updating activation script: {e}")

    print("\nFix completed successfully!")
    print("Please deactivate and reactivate your virtual environment.")
    return True


def test_tkinter():
    """Test if Tkinter works now"""
    print("\nTesting Tkinter...")
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()  # Hide the window
        root.destroy()
        print("Tkinter test successful! TCL/TK is properly configured.")
        return True
    except Exception as e:
        print(f"Tkinter test failed: {e}")
        print("\nPossible solutions:")
        print("1. Deactivate and reactivate your virtual environment")
        print("2. If using an IDE, restart it to pick up the new environment variables")
        print("3. Try 'python -m tkinter' from the command line to test Tkinter")
        return False


if __name__ == "__main__":
    copy_tcl_to_venv()
    test_tkinter()