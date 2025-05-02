try:
    from setuptools import setup, find_packages
except ImportError:
    # Fallback if setuptools is not installed
    print("Error: setuptools is not installed. Please install it first:")
    print("    pip install setuptools")
    exit(1)

import sys
import os
import glob

# Define platform-specific dependencies
platform_deps = []
if sys.platform == 'win32':
    platform_deps = ['pywin32']
elif sys.platform == 'darwin':
    platform_deps = ['pyobjc-framework-Cocoa']
elif sys.platform.startswith('linux'):
    platform_deps = []  # System packages required: python3-xlib, xdotool

# Add TCL/TK environment setup for Windows
if sys.platform == 'win32':
    # Try to find TCL/TK libraries and set environment variables
    try:
        # Common Python installation paths
        python_dir = sys.prefix
        tcl_paths = glob.glob(os.path.join(python_dir, 'tcl', 'tcl*'))
        tk_paths = glob.glob(os.path.join(python_dir, 'tcl', 'tk*'))

        if tcl_paths:
            os.environ['TCL_LIBRARY'] = tcl_paths[0]
        if tk_paths:
            os.environ['TK_LIBRARY'] = tk_paths[0]

        print("TCL/TK paths configured successfully")
    except Exception as e:
        print(f"Warning: Could not configure TCL/TK paths: {e}")

setup(
    name="lemonfox",
    version="1.0.0",
    description="Audio transcription with voice recording capabilities",
    packages=find_packages(),
    install_requires=[
        # Core dependencies
        'requests>=2.28.0',
        'python-dotenv>=0.21.0',

        # Audio processing
        'numpy>=1.20.0',
        'scipy>=1.7.0',

        # Voice module dependencies (optional)
        'sounddevice>=0.4.5',
        'webrtcvad>=2.0.10',
        'tk>=0.1.0',  # Ensure Tkinter support
    ],
    extras_require={
        'voice': [
                     'pynput>=1.7.6',
                     'pyautogui>=0.9.53',
                     'pyperclip>=1.8.2',
                     'pystray>=0.19.4',
                     'Pillow>=9.0.0',
                 ] + platform_deps,
    },
    entry_points={
        'console_scripts': [
            'lemonfox=main:main',
        ],
    },
    python_requires='>=3.7',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)