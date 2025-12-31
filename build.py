#!/usr/bin/env python3
"""
Build script for PyShell executable using PyInstaller
"""

import subprocess
import sys
import os

def build_executable():
    """Build PyShell as a standalone Windows executable."""
    
    print("=" * 70)
    print("Building PyShell Executable")
    print("=" * 70)
    
    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--onefile",           # Single executable file
        "--name", "PyShell",   # Output name
        "--console",           # Console application
        "--clean",             # Clean cache
        "--noconfirm",         # Overwrite without asking
        "app/main.py"          # Entry point
    ]
    
    print(f"\nBuild command: {' '.join(cmd)}\n")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        
        print("\n" + "=" * 70)
        print("Build Complete!")
        print("=" * 70)
        print(f"\nExecutable location: dist/PyShell.exe")
        print(f"Size: {os.path.getsize('dist/PyShell.exe') / 1024 / 1024:.2f} MB")
        print("\nYou can now run PyShell.exe from the dist folder.")
        
        return 0
    except subprocess.CalledProcessError as e:
        print(f"\nBuild failed with exit code {e.returncode}")
        return 1
    except FileNotFoundError:
        print("\nError: PyInstaller not found. Please install it with:")
        print("  pip install pyinstaller")
        return 1

if __name__ == "__main__":
    sys.exit(build_executable())

