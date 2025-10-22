# Synthalingua Troubleshooting Guide

This guide provides solutions for common issues you might encounter while using Synthalingua.

## Installation Issues

### Python Version Mismatch
**Issue**: "Python not recognized" or version errors
**Solution**: 
- Ensure Python 3.12.x is installed and added to PATH
- Restart your terminal/command prompt after Python installation
- Check version: `python --version` or `python3 --version`

### CUDA/GPU Issues
**Issue**: CUDA not available or GPU features not working
**Solution**:
- **Windows**: Install [CUDA 12.9](https://developer.nvidia.com/cuda-downloads) for Windows
- **Linux**: Use `setup.sh` to select GPU/HIP support
- Verify installation: Run `nvidia-smi` to check GPU detection
- **CPU fallback**: Use `--device cpu` if GPU issues persist

### FFMPEG Installation
**Issue**: "ffmpeg not found" errors
**Solution**:
- **Windows**: Download from [FFmpeg official site](https://ffmpeg.org/download.html)
- **Linux**: Install via package manager: `sudo apt install ffmpeg` or `sudo yum install ffmpeg`
- **macOS**: Use Homebrew: `brew install ffmpeg`
- Add FFmpeg to system PATH

## Audio Input Issues

### No Available Microphones
**Issue**: Microphone not detected or no audio input
**Solution**:
- Run `--list_microphones` to see available devices
- Check system audio settings
- Ensure microphone permissions are granted
- Try different microphone device index

### Audio Quality Problems
**Issue**: Poor transcription accuracy
**Solution**:
- Increase energy threshold: `--energy_threshold 300`
- Extend calibration time: `--mic_calibration_time 15`
- Use higher quality model: `--ram 11gb-v3`
- Check for background noise interference

## Performance Issues

### Out of Memory Errors
**Issue**: System runs out of RAM/VRAM
**Solution**:
- Reduce model size: Use `--ram 3gb`, `--ram 6gb`, etc.
- Use CPU mode: `--device cpu`
- Close other applications
- Check with `--ramforce` (advanced users only)

### Slow Processing
**Issue**: Transcription taking too long
**Solution**:
- Use GPU acceleration with CUDA
- Enable FP16 mode: `--fp16`
- Use adaptive batch processing: `--adaptive_batch`
- Optimize for silent periods: `--silent_detect`

## Common Errors

### "No module named" errors
**Issue**: Missing Python packages
**Solution**:
- Ensure virtual environment is activated
- Re-run setup script: `setup.bat` or `setup.bash`
- Install missing packages manually: `pip install [package]`

### Network Issues
**Issue**: Stream failures or offline problems
**Solution**:
- Check internet connection
- Use `--cookies` for authentication if needed
- Try different stream quality: `--selectsource bestaudio`
- Restart with stable connection

### Permission Errors
**Issue**: Access denied when creating files
**Solution**:
- Run terminal as administrator (Windows)
- Check write permissions in output directory
- Specify custom output folder: `--save_folder ./my_output`

## Stream-Specific Issues

### YouTube Live Not Working
**Issue**: Cannot access YouTube live streams
**Solution**:
- Use `--cookies-from-browser chrome` or similar
- Update yt-dlp: `pip install -U yt-dlp`
- Try specific format: `--selectsource 91`

### Twitch Stream Issues
**Issue**: Twitch audio not processing correctly
**Solution**:
- Increase chunk size: `--stream_chunks 10`
- Use specific quality: `--selectsource audio_only`
- Check for stream quality restrictions

## General Solutions

### Debug Mode
Run with `--debug` flag for detailed logging information
```bash
python synthalingua.py --debug --ram 6gb --makecaptions --file_input example.mp4
```

### Bug Report
Generate comprehensive system report:
```bash
python synthalingua.py --bugreport
```

### Version Check
Check for updates:
```bash
python synthalingua.py --checkupdate
```

## Getting Help

If problems persist:
1. Create a bug report: `--bugreport`
2. Check GitHub Issues: [GitHub Issues](https://github.com/cyberofficial/Synthalingua/issues)
3. Join community discussions on Discord
4. Share your system information when reporting issues

## Environment Examples

### Minimal Setup (CPU)
```bash
python synthalingua.py --ram 1gb --device cpu --makecaptions --file_input test.mp4
```

### Optimal Setup (GPU)
```bash
python synthalingua.py --ram 11gb-v3 --device cuda --adaptive_batch --isolate_vocals --silent_detect --makecaptions --file_input test.mp4