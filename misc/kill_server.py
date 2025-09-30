#!/usr/bin/env python3
"""
Server Kill Utility

This utility can be used to force shutdown the Synthalingua web server
by deleting the server.pid file, which triggers the watchdog mechanism
to immediately terminate the Flask server.

Usage:
    python kill_server.py

This is useful when:
- The server hangs during "graceful shutdown"
- Ctrl+C doesn't work properly
- You need to force kill the server from another terminal/process
"""

import os
import sys
import time

PID_FILE = "server.pid"

def kill_server():
    """Force kill the server by deleting the PID file."""
    if not os.path.exists(PID_FILE):
        print(" No server PID file found. Server may not be running.")
        return False
    
    try:
        print(f"🔥 Force killing server by removing {PID_FILE}...")
        os.remove(PID_FILE)
        
        # Give watchdog time to detect and shutdown
        print("⏳ Waiting for server shutdown...")
        time.sleep(3)
        
        # Check if PID file was recreated (server still running)
        if os.path.exists(PID_FILE):
            print(" Server may still be running (PID file recreated)")
            return False
        else:
            print(" Server shutdown complete!")
            return True
            
    except Exception as e:
        print(f" Error killing server: {e}")
        return False

def check_server_status():
    """Check if the server is running based on PID file existence."""
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, 'r') as f:
                pid = f.read().strip()
            print(f"🟢 Server appears to be running (PID: {pid})")
            return True
        except Exception as e:
            print(f" PID file exists but couldn't read it: {e}")
            return False
    else:
        print(" Server not running (no PID file)")
        return False

def main():
    print("🛠️ Synthalingua Server Kill Utility")
    print("=" * 40)
    
    # Check current status
    is_running = check_server_status()
    
    if not is_running:
        print("\n No action needed - server is not running.")
        return
    
    # Ask for confirmation
    print(f"\n This will force kill the Synthalingua web server.")
    print(" WARNING: This will immediately terminate the server!")
    
    try:
        response = input("\nContinue? (y/N): ").strip().lower()
        if response in ['y', 'yes']:
            success = kill_server()
            sys.exit(0 if success else 1)
        else:
            print(" Operation cancelled.")
            sys.exit(0)
    except KeyboardInterrupt:
        print("\n Operation cancelled.")
        sys.exit(0)

if __name__ == "__main__":
    main()
