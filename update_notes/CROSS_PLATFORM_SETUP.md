# Cross-Platform Setup Script Update

## Overview
The `set_up_env.py` script has been updated to support Windows, Linux, and macOS with ROCm support for AMD GPUs.

> **⚠️ Experimental Feature:**  
> This cross-platform setup is experimental and may break or behave unexpectedly on some systems. Please report any issues you encounter.

## New Features

### 1. **Cross-Platform Support**
- **Windows**: Uses existing .exe and .7z downloads
- **Linux**: Uses static FFmpeg builds, native yt-dlp binary, and p7zip
- **macOS**: Uses appropriate binaries and Homebrew-compatible tools

### 2. **ROCm Support for AMD GPUs**
- Added ROCm (AMD GPU) support alongside existing CUDA support (Linux only)
- Platform-aware GPU selection:
  - Windows: cpu, cuda
  - Linux: cpu, cuda, rocm
  - macOS: cpu, cuda (with warnings)
- Uses appropriate PyTorch index URLs:
  - CUDA: `https://download.pytorch.org/whl/cu128`
  - ROCm: `https://download.pytorch.org/whl/rocm6.4` (Linux only)

### 3. **Linux Python Environment Choice**
- Linux users can now choose between:
  - **System Python**: Use existing Python installation with pip packages
  - **Miniconda**: Create isolated conda environment (default for Windows)
- Provides detailed explanations of each option during setup
- System Python option validates Python version (3.8+ required for demucs)
- Installs platform-appropriate PyTorch variants (CPU/CUDA/ROCm)

### 4. **Platform-Specific Configurations**

#### URLs and Downloads:
- **Windows**: 
  - FFmpeg: Windows .7z archive
  - yt-dlp: Windows .zip package
  - 7zip: 7zr.exe download
  - Miniconda: Windows .exe installer

- **Linux**:
  - FFmpeg: Static Linux .tar.xz build
  - yt-dlp: Native Linux binary
  - 7zip: System p7zip (auto-installed)
  - Miniconda: Linux .sh installer

- **macOS**:
  - FFmpeg: macOS .zip package
  - yt-dlp: macOS binary
  - 7zip: System 7z (via Homebrew)
  - Miniconda: macOS .sh installer

#### Configuration Files:
- **Windows**: Creates `ffmpeg_path.bat` batch file
- **Linux/macOS**: Creates `ffmpeg_path.sh` shell script (executable)

### 5. **Enhanced Extraction Support**
- `.7z` files: Uses 7zr.exe (Windows) or p7zip (Linux/macOS)
- `.zip` files: Uses Python zipfile module
- `.tar.xz` files: Uses Python tarfile module
- Auto-detection based on file extension

### 6. **Platform-Aware Paths**
- **Windows**: `C:\bin\Synthalingua\miniconda`
- **Linux**: `~/bin/Synthalingua/miniconda`
- **macOS**: `~/bin/Synthalingua/miniconda`

### 7. **Conda Executable Detection**
- **Windows**: `Scripts/conda.exe`, `condabin/conda.bat`
- **Linux/macOS**: `bin/conda`, `condabin/conda`

## Usage Examples

### Basic Setup (All Platforms)
```bash
python set_up_env.py
```

### With Vocal Isolation (All Platforms)
```bash
python set_up_env.py --using_vocal_isolation
```

### Linux Python Environment Selection
When running with `--using_vocal_isolation` on Linux, users will be prompted to choose their Python environment:
```
Would you like to use your system Python or install Miniconda? (system/miniconda): 
```

**Note**: Windows users automatically use Miniconda (no choice presented).

**System Python Option (Linux only):**
- Uses existing Python installation
- Installs packages globally via pip
- Requires Python 3.12.x (3.12.10 recommended for stability, automatically verified)
- Faster setup, smaller disk usage
- May conflict with other Python projects

**Miniconda Option (All platforms):**
- Creates isolated conda environment
- No conflicts with system packages
- Recommended for most users
- Requires ~8GB additional disk space

### Reinstall Everything
```bash
python set_up_env.py --reinstall --using_vocal_isolation
```

## GPU Support Matrix

| Platform | CPU | NVIDIA CUDA | AMD ROCm |
|----------|-----|-------------|----------|
| Windows  | ✅  | ✅          | ❌       |
| Linux    | ✅  | ✅          | ✅       |
| macOS    | ✅  | ⚠️*         | ❌       |

*CUDA on macOS may not work on Apple Silicon

## Configuration Files Generated

### Windows (`ffmpeg_path.bat`)

#### With Conda Environment:
```batch
@echo off
set "PATH=C:\path\to\tools;%PATH%"
echo FFmpeg, yt-dlp, and conda are available in this session.
call "C:\path\to\miniconda\Scripts\activate.bat" "C:\path\to\env"
```

#### With System Python (Linux only):
```batch
@echo off
set "PATH=C:\path\to\tools;%PATH%"
echo FFmpeg and yt-dlp are available in this session.
echo Vocal isolation is set up with system Python - demucs should be available.
```

### Linux/macOS (`ffmpeg_path.sh`)

#### With Conda Environment:
```bash
#!/bin/bash
export PATH="/path/to/tools:$PATH"
echo "FFmpeg, yt-dlp, and conda are available in this session."
source "/path/to/miniconda/bin/activate" "/path/to/env"
```

#### With System Python (Linux only):
```bash
#!/bin/bash
export PATH="/path/to/tools:$PATH"
echo "FFmpeg and yt-dlp are available in this session."
echo "Vocal isolation is set up with system Python - demucs should be available."
echo "To test: python -c \"import demucs; print('demucs installed successfully')\""
```

## Dependencies

### System Requirements
- **Linux**: p7zip package (auto-prompted for installation)
- **macOS**: p7zip via Homebrew (auto-prompted for installation)
- **Windows**: No additional system dependencies

### Python Packages
- All platforms use the same Python package requirements
- Platform-specific PyTorch installations based on GPU choice

## Compatibility Notes

1. **ROCm Support**: Linux only - not available on Windows or macOS
2. **macOS Limitations**: No ROCm support, CUDA may not work on Apple Silicon
3. **Path Handling**: Automatically handles platform-specific path separators
4. **Permissions**: Unix systems automatically set executable permissions on scripts and binaries
5. **Package Managers**: Integrates with system package managers for missing dependencies
6. **Linux Python Choice**: Linux users can choose between system Python and Miniconda for vocal isolation setup
7. **Python Version Requirements**: 
   - **Windows**: Python 3.12.10 recommended (Miniconda only)
   - **Linux**: Python 3.12.x supported (3.12.10 recommended for stability)
   - System Python option requires Python 3.12.x minimum (automatically verified during setup)

## Migration from Windows-Only Version

The script automatically detects the platform and uses appropriate configurations. No manual changes needed for existing installations - just run the updated script and it will handle platform differences automatically.