# Server Force Shutdown Feature

## Overview

This feature implements a PID file-based force shutdown mechanism to prevent the Flask web server from hanging during shutdown. When you press `Ctrl+C`, the system will now properly force-kill the Flask server if it doesn't shut down gracefully.

## How It Works

### 1. **PID File Creation**
- When the Flask server starts, it creates a `server.pid` file containing the process ID
- This file serves as a "heartbeat" indicator that the server should keep running

### 2. **Watchdog Monitor**
- A background thread continuously monitors the existence of the `server.pid` file (every 2 seconds)
- If the file is deleted, the watchdog immediately force-kills the Flask server

### 3. **Force Shutdown Process**
When `Ctrl+C` is pressed or `kill_server()` is called:

1. **Graceful attempt**: Deletes the PID file and waits 3 seconds
2. **Force kill**: If server is still running, forces immediate termination
3. **Cleanup**: Removes PID file and cleans up resources

## Usage

### Normal Operation
```bash
# Start Synthalingua with web server
python synthalingua.py --portnumber 8080 --stream https://youtube.com/watch?v=abc123

# Press Ctrl+C to shutdown (now works properly!)
```

### Manual Force Kill
If the server gets stuck, you can force kill it:

#### Option 1: Use the kill utility
```bash
python kill_server.py
```

#### Option 2: Delete PID file manually
```bash
# Windows
del server.pid

# Linux/Mac
rm server.pid
```

#### Option 3: From another Python script
```python
import os
if os.path.exists("server.pid"):
    os.remove("server.pid")
```

## Files Created

- **`server.pid`**: Contains the process ID of the running server
  - Created when server starts
  - Deleted when server stops
  - Automatically cleaned up on program exit

## Benefits

✅ **No More Hanging**: Server shutdown is now reliable and fast
✅ **Force Kill Option**: Multiple ways to force shutdown if needed  
✅ **Clean Termination**: Proper cleanup of resources and temporary files
✅ **User Feedback**: Clear messages about shutdown progress
✅ **Cross-Platform**: Works on Windows, Linux, and macOS

## Technical Details

### Key Components

1. **`create_pid_file()`**: Creates the PID file when server starts
2. **`remove_pid_file()`**: Safely removes the PID file
3. **`watchdog_monitor()`**: Background thread that monitors PID file
4. **`force_shutdown_server()`**: Immediately terminates the server
5. **`kill_server()`**: Main shutdown function with fallback mechanisms

### Server Lifecycle

```
Start Server → Create PID File → Start Watchdog → Run Flask
     ↓
Ctrl+C Detected → Delete PID File → Watchdog Triggers → Force Kill → Cleanup
```

### Error Handling

- **Missing psutil**: Falls back to basic termination methods
- **PID file errors**: Graceful degradation with warnings
- **Watchdog failures**: Server continues running, manual kill still works
- **Force kill failures**: Multiple termination strategies attempted

## Troubleshooting

### Server Won't Stop
1. Try the kill utility: `python kill_server.py`
2. Delete PID file manually: `del server.pid` (Windows) or `rm server.pid` (Linux/Mac)
3. Use Task Manager/Process Monitor to kill Python processes

### PID File Issues
- If you see "Warning: Could not create PID file", the force kill feature won't work, but the server will still run normally
- Leftover PID files from crashes are automatically cleaned up on next startup

### Multiple Instances
- Each server instance creates its own PID file
- Running multiple servers on different ports is supported
- Kill utility affects the most recent server instance

## Compatibility

- **Python 3.6+**: Core functionality
- **psutil**: Optional, provides enhanced process management
- **Windows**: Full support
- **Linux/macOS**: Full support

## Installation Note

This feature is built into the existing codebase and requires no additional setup. The `kill_server.py` utility is included for convenience but is optional.
