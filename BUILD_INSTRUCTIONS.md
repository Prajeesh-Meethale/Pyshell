# PyShell Build Instructions

## Building the Standalone Executable

### Prerequisites

1. Install PyInstaller:
```bash
pip install pyinstaller
```

### Build Command

Run the build script:
```bash
python build.py
```

Or manually:
```bash
pyinstaller --onefile --name PyShell --console --clean --noconfirm app/main.py
```

### Build Options Explained

- `--onefile`: Bundles everything into a single `.exe` file
- `--name PyShell`: Sets the output filename to `PyShell.exe`
- `--console`: Ensures it runs correctly in a terminal window
- `--clean`: Removes temporary cache files before building
- `--noconfirm`: Overwrites existing files without asking

### Output

The executable will be created in the `dist/` folder:
- **File:** `dist/PyShell.exe`
- **Size:** ~8-10 MB (includes Python interpreter and all dependencies)
- **Type:** Standalone Windows executable (no Python installation required)

### Frozen Executable Handling

The code includes support for PyInstaller's frozen executable mode:
- Checks for `sys.frozen` attribute
- Uses `sys._MEIPASS` for resource paths when frozen
- All internal logic works correctly in both script and executable modes

### Testing the Executable

After building, test the executable:
```bash
cd dist
.\PyShell.exe
```

You should see the PyShell prompt (`$ `) and be able to run commands normally.

### Distribution

The `PyShell.exe` file is completely standalone:
- No Python installation required on target machine
- No external dependencies needed
- Can be copied to any Windows machine and run directly
- All features work identically to the script version

### Build Artifacts

PyInstaller creates several folders:
- `build/` - Temporary build files (can be deleted)
- `dist/` - Final executable (this is what you distribute)
- `PyShell.spec` - Build specification file (can be used for custom builds)

### Troubleshooting

If the build fails:
1. Ensure PyInstaller is installed: `pip install pyinstaller`
2. Check Python version compatibility (Python 3.14+)
3. Review build warnings in `build/PyShell/warn-PyShell.txt`
4. Try cleaning: `pyinstaller --clean` or delete `build/` and `dist/` folders

---

*Built with PyInstaller 6.17.0*

