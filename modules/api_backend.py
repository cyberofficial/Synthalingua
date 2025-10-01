"""
Flask-based web server module for handling real-time subtitle display and updates.

This module implements a web server that serves HTML pages and manages state for
displaying subtitles, translations, and transcriptions through a web interface.
It supports both HTTP and HTTPS protocols, with automatic certificate generation
for HTTPS connections.

The server provides endpoints for:
- Serving the main index page and player page
- Serving static files
- Updating header text for subtitles, translations, and transcriptions

Key Components:
- HeaderState: Class for managing subtitle text state
- FlaskServerThread: Thread-based Flask server implementation
- API Blueprint: Routes for handling web requests
- PID file-based force shutdown mechanism to prevent hanging servers
- HTTPS support with self-signed certificates
- Fuzzy security monitoring to block suspicious IPs attempting to access
  non-existent static files
"""

import os
import logging
import time
import threading
import signal
import atexit
from flask import Flask, send_from_directory, url_for, Blueprint, request, abort
from threading import Thread, Event
from functools import lru_cache
import ssl
import tempfile
from werkzeug.serving import make_server
from colorama import Fore, Style
from collections import defaultdict, deque

# State management class
class HeaderState:
    """
    Manages the state of header texts for subtitles, translations, and transcriptions.
    
    Attributes:
        header_text (str): Current subtitle text
        translated_header_text (str): Current translated text
        transcribed_header_text (str): Current transcribed text
    """
    def __init__(self):
        self.header_text = ""
        self.translated_header_text = ""
        self.transcribed_header_text = ""

    def update_header(self, new_header):
        """Updates the main subtitle text."""
        self.header_text = new_header

    def update_translated_header(self, new_header):
        """Updates the translated text."""
        self.translated_header_text = new_header

    def update_transcribed_header(self, new_header):
        """Updates the transcribed text."""
        self.transcribed_header_text = new_header

# PID file management for force shutdown
PID_FILE = "server.pid"
watchdog_thread = None
force_shutdown_flag = False
_debug_enabled = False  # Internal debug flag set from args.debug
watchdog_lock = threading.Lock()

# Security monitoring for static file access
failed_requests = defaultdict(deque)  # IP -> deque of failed request timestamps
blocked_ips = set()  # Set of blocked IP addresses
FAILED_REQUEST_THRESHOLD = 3  # Number of failed requests before blocking
FAILED_REQUEST_WINDOW = 300  # Time window in seconds (5 minutes)
BLOCK_DURATION = 3600  # Block duration in seconds (1 hour)
blocked_ips_timestamps = {}  # IP -> timestamp when blocked

def create_pid_file():
    """Create a PID file to track server status."""
    try:
        with open(PID_FILE, 'w') as f:
            f.write(str(os.getpid()))
        print(f"Created PID file: {PID_FILE}")
    except Exception as e:
        print(f"Warning: Could not create PID file: {e}")

def remove_pid_file():
    """Remove the PID file."""
    try:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
            print(f"Removed PID file: {PID_FILE}")
    except Exception as e:
        print(f"Warning: Could not remove PID file: {e}")

def is_ip_blocked(ip_address):
    """Check if an IP address is currently blocked."""
    current_time = time.time()
    
    # Clean up expired blocks
    expired_ips = []
    for blocked_ip, block_time in blocked_ips_timestamps.items():
        if current_time - block_time > BLOCK_DURATION:
            expired_ips.append(blocked_ip)
    
    for ip in expired_ips:
        blocked_ips.discard(ip)
        del blocked_ips_timestamps[ip]
        print(f"IP {ip} unblocked after timeout")
    
    return ip_address in blocked_ips

def record_failed_request(ip_address, filename):
    """Record a failed static file request and check if IP should be blocked."""
    current_time = time.time()
    
    # Clean old entries outside the window
    while failed_requests[ip_address] and current_time - failed_requests[ip_address][0] > FAILED_REQUEST_WINDOW:
        failed_requests[ip_address].popleft()
    
    # Add new failed request
    failed_requests[ip_address].append(current_time)
    
    # Check if threshold exceeded
    if len(failed_requests[ip_address]) >= FAILED_REQUEST_THRESHOLD:
        blocked_ips.add(ip_address)
        blocked_ips_timestamps[ip_address] = current_time
        print(f"SECURITY ALERT: IP {ip_address} blocked for suspicious file access attempts!")
        print(f"   Last attempt: {filename}")
        print(f"   Failed attempts: {len(failed_requests[ip_address])} in {FAILED_REQUEST_WINDOW//60} minutes")
        # Clear the failed requests for this IP since it's now blocked
        failed_requests[ip_address].clear()

def get_client_ip():
    """Get the real client IP address, considering proxies."""
    # Check for forwarded headers (for reverse proxies)
    x_forwarded_for = request.headers.get('X-Forwarded-For')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    
    x_real_ip = request.headers.get('X-Real-IP')
    if x_real_ip:
        return x_real_ip
    
    return request.remote_addr

def watchdog_monitor():
    """Monitor PID file existence and force shutdown if file is deleted."""
    global force_shutdown_flag, watchdog_thread
    try:
        while not force_shutdown_flag:
            try:
                if not os.path.exists(PID_FILE):
                    print("PID file deleted - Force shutting down Flask server!")
                    force_shutdown_server()
                    break
                time.sleep(2)  # Check every 2 seconds
            except Exception as e:
                print(f"Watchdog error: {e}")
                break
    finally:
        with watchdog_lock:
            if threading.current_thread() is watchdog_thread:
                watchdog_thread = None


def start_watchdog_thread():
    """Ensure the watchdog monitor is running exactly once."""
    global watchdog_thread
    with watchdog_lock:
        # Check if thread exists and is alive - using try-except for safety
        if watchdog_thread:
            try:
                if watchdog_thread.is_alive():
                    return
            except (AttributeError, RuntimeError):
                # Thread may have been terminated or in invalid state
                pass
        # Create and start new watchdog thread
        watchdog_thread = threading.Thread(
            target=watchdog_monitor,
            name="watchdog-monitor",
            daemon=True,
        )
        watchdog_thread.start()

def force_shutdown_server():
    """Force shutdown the Flask server immediately."""
    global server_thread, force_shutdown_flag
    force_shutdown_flag = True
    
    # Store reference to thread to avoid it being modified during shutdown
    thread_ref = server_thread
    if thread_ref:
        try:
            # Check if thread is alive before attempting shutdown operations
            if not thread_ref.is_alive():
                return
            
            print(" Force killing Flask server...")
            
            # Set shutdown flag
            if hasattr(thread_ref, 'shutdown_event'):
                thread_ref.shutdown_event.set()
            
            # Force close the server socket if available
            if hasattr(thread_ref, 'server') and thread_ref.server:
                try:
                    thread_ref.server.server_close()
                except (AttributeError, OSError) as e:
                    if _debug_enabled:
                        print(f"Debug: Could not close server socket: {e}")
                    # In production, we silently continue as the server may already be closed
                except Exception as e:
                    if _debug_enabled:
                        print(f"Debug: Unexpected error closing server: {e}")
                        import traceback
                        traceback.print_exc()
            
            # Give it a moment to shutdown gracefully
            thread_ref.join(timeout=1)
            
            # Check again if still alive for force kill
            try:
                if thread_ref.is_alive():
                    print(" Server thread still alive, using OS kill...")
                    try:
                        # Get current process ID and kill it
                        import psutil
                        current_process = psutil.Process()
                        
                        # Find and kill any child processes (Flask workers)
                        for child in current_process.children():
                            if 'flask' in child.name().lower() or 'python' in child.name().lower():
                                child.terminate()
                                
                    except ImportError:
                        print("psutil not available, using basic termination")
                    except Exception as e:
                        print(f"Error during force kill: {e}")
            except (AttributeError, RuntimeError):
                # Thread may have terminated during our operations
                pass
                    
        except Exception as e:
            print(f"Error during force shutdown: {e}")
        
        print("Flask server force shutdown complete!")

# Global state instance
state = HeaderState()

# Create blueprint for routes
api = Blueprint('api', __name__)

# Cache static file reading
@lru_cache(maxsize=32)
def read_cached_file(file_path):
    """
    Reads and caches file content to improve performance.
    
    Args:
        file_path (str): Path to the file to be read
        
    Returns:
        str: Content of the file
    """
    with open(file_path, 'r') as file:
        return file.read()

# Routes
@api.route('/')
def serve_index():
    """Serves the main index page with current subtitle text."""
    index_html_path = os.path.join(get_html_data_dir(), 'index.html')
    html_content = read_cached_file(index_html_path)
    return html_content.replace("{{ header_text }}", state.header_text)

@api.route('/player.html')
def serve_player():
    """Serves the player page."""
    player_html_path = os.path.join(get_html_data_dir(), 'player.html')
    return read_cached_file(player_html_path)

@api.route('/static/<path:filename>')
def serve_static(filename):
    """
    Serves static files (CSS, JS, images, etc.) with security monitoring.
    
    Args:
        filename (str): Name of the static file to serve
    """
    client_ip = get_client_ip()
    
    # Check if IP is blocked
    if is_ip_blocked(client_ip):
        print(f"Blocked IP {client_ip} attempted to access: {filename}")
        abort(403)
    
    try:
        # Check if file exists before serving
        static_dir = get_static_dir()
        full_path = os.path.join(static_dir, filename)
        
        # Additional security: ensure the path doesn't escape the static directory
        real_static_dir = os.path.realpath(static_dir)
        real_file_path = os.path.realpath(full_path)
        
        # Harden path containment check using os.path.commonpath
        if os.path.commonpath([real_file_path, real_static_dir]) != real_static_dir:
            print(f"Path traversal attempt from {client_ip}: {filename}")
            record_failed_request(client_ip, filename)
            abort(403)
        
        if not os.path.exists(real_file_path):
            print(f"File not found request from {client_ip}: {filename}")
            record_failed_request(client_ip, filename)
            abort(404)

        return send_from_directory(static_dir, filename)
        
    except Exception as e:
        print(f"Error serving static file to {client_ip}: {filename} - {str(e)}")
        record_failed_request(client_ip, filename)
        abort(500)

@api.route('/update-header')
def update_header_route():
    """Returns current subtitle text."""
    return state.header_text

@api.route('/update-translated-header')
def update_translated_header_route():
    """Returns current translated text."""
    return state.translated_header_text

@api.route('/update-transcribed-header')
def update_transcribed_header_route():
    """Returns current transcribed text."""
    return state.transcribed_header_text

# Helper functions
def get_html_data_dir():
    """
    Gets the path to the HTML data directory.
    
    Returns:
        str: Path to the HTML data directory
    """
    script_dir = os.path.dirname(os.path.realpath(__file__))
    project_root = os.path.dirname(script_dir)
    return os.path.join(project_root, 'html_data')

def get_static_dir():
    """
    Gets the path to the static files directory.
    
    Returns:
        str: Path to the static files directory
    """
    return os.path.join(get_html_data_dir(), 'static')

class FlaskServerThread(Thread):
    """
    Thread-based Flask server implementation supporting both HTTP and HTTPS.
    
    Args:
        port (int): Port number for the server
        use_https (bool): Whether to use HTTPS protocol
    """
    def __init__(self, port, use_https=False, host: str = '127.0.0.1', debug=False):
        super().__init__()
        self.port = port
        self.use_https = use_https
        self.host = host
        self.debug = debug
        self.app = self.create_app()
        self.server = None
        self.shutdown_event = Event()
        self.startup_complete = Event()  # Event to signal when startup messages are complete

    def create_app(self):
        """Creates and configures the Flask application."""
        app = Flask(__name__, static_folder=get_static_dir(), static_url_path='/static')
        app.config["DEBUG"] = False
        
        # Configure logging
        app.logger.setLevel(logging.WARNING)
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        log.disabled = True

        # Register blueprint
        app.register_blueprint(api)

        # Add security headers
        @app.after_request
        def add_header(response):
            response.headers.update({
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
                "X-XSS-Protection": "1; mode=block",
                "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
            })
            return response

        return app

    def setup_https(self):
        """
        Sets up HTTPS with a self-signed certificate.
        
        Returns:
            tuple: (SSLContext, temporary directory path) or (None, temporary directory path) if setup fails
        """
        # Create temporary directory for SSL files
        ssl_dir = tempfile.mkdtemp()
        cert_file = os.path.join(ssl_dir, 'temp_cert.pem')
        key_file = os.path.join(ssl_dir, 'temp_key.pem')

        try:
            from OpenSSL import crypto
            # Create self-signed certificate
            key = crypto.PKey()
            key.generate_key(crypto.TYPE_RSA, 2048)
            
            cert = crypto.X509()
            cert.get_subject().CN = 'localhost'
            cert.set_serial_number(1000)
            cert.gmtime_adj_notBefore(0)
            cert.gmtime_adj_notAfter(365 * 24 * 60 * 60)
            cert.set_issuer(cert.get_subject())
            cert.set_pubkey(key)
            cert.sign(key, 'sha256')            # Save certificate and key
            with open(cert_file, 'wb') as cf, open(key_file, 'wb') as kf:
                cf.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
                kf.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key))

            context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
            context.load_cert_chain(certfile=cert_file, keyfile=key_file)
            return context, ssl_dir
            
        except Exception as e:
            print(f"Failed to set up HTTPS: {e}")
            return None, ssl_dir

    def run(self):
        """Runs the server and handles requests until shutdown."""
        ssl_context = None
        ssl_dir = None
        
        # Create PID file when server starts
        create_pid_file()

        # Start watchdog monitor once across all server threads
        start_watchdog_thread()
        
        if self.use_https:
            ssl_context, ssl_dir = self.setup_https()
            if not ssl_context:
                print("Falling back to HTTP")

        try:
            self.server = make_server(self.host, self.port, self.app, 
                                    ssl_context=ssl_context)
            print(f"Starting Flask Server on {self.host}:{self.port}")
            print(f"You can access the server at http{'s' if ssl_context else ''}://{self.host}:{self.port}")
            print(f" To force shutdown the server, delete the '{PID_FILE}' file")
            print()  # Add empty line to separate multiple server outputs
            
            # Signal that startup messages are complete
            self.startup_complete.set()
            
            while not self.shutdown_event.is_set() and not force_shutdown_flag:
                try:
                    self.server.handle_request()
                except OSError:
                    # Socket was closed, likely during shutdown
                    break
                    
        except Exception as e:
            print(f"Server error: {e}")
        finally:
            # Clean up PID file when server stops
            remove_pid_file()
            if ssl_dir:
                import shutil
                shutil.rmtree(ssl_dir, ignore_errors=True)

    def shutdown(self):
        """Gracefully shuts down the server."""
        self.shutdown_event.set()
        if self.server:
            self.server.shutdown()

# Global server instances
server_thread = None
https_server_thread = None

def flask_server(operation, portnumber, https_port=None, host: str = '127.0.0.1', debug=False):
    """
    Controls the Flask server operation.
    
    Args:
        operation (str): "start" to start the server
        portnumber (int): Port number for the HTTP server (can be None)
        https_port (int): Port number for the HTTPS server (can be None)
    """
    global server_thread, https_server_thread, _debug_enabled, force_shutdown_flag
    if operation == "start":
        _debug_enabled = debug  # Set internal debug flag from args.debug
        force_shutdown_flag = False
        
        # Start HTTP server if port is specified
        if portnumber:
            server_thread = FlaskServerThread(portnumber, use_https=False, host=host, debug=debug)
            server_thread.daemon = True
            server_thread.start()
            
            # If we're also starting HTTPS server, wait for HTTP startup to complete
            if https_port:
                server_thread.startup_complete.wait()  # Wait for HTTP server messages to finish
        
        # Start HTTPS server if port is specified
        if https_port:
            https_server_thread = FlaskServerThread(https_port, use_https=True, host=host, debug=debug)
            https_server_thread.daemon = True
            https_server_thread.start()
        
        # Ensure watchdog monitor is running once
        start_watchdog_thread()

def kill_server():
    """Force shutdown the server using PID file mechanism."""
    global server_thread, https_server_thread
    servers_running = []
    
    # Collect threads that are alive at this moment, storing references
    http_thread = server_thread
    https_thread = https_server_thread
    
    try:
        if http_thread and http_thread.is_alive():
            servers_running.append(('HTTP', http_thread))
    except (AttributeError, RuntimeError):
        # Thread may have terminated or in invalid state
        pass
    
    try:
        if https_thread and https_thread.is_alive():
            servers_running.append(('HTTPS', https_thread))
    except (AttributeError, RuntimeError):
        # Thread may have terminated or in invalid state
        pass
    
    if servers_running:
        print("Initiating server shutdown...")
        
        # First try graceful shutdown by deleting PID file
        remove_pid_file()
        
        # Wait a moment for watchdog to detect and shutdown
        time.sleep(3)
        
        # Check if servers are still running and force shutdown if needed
        for server_type, thread in servers_running:
            try:
                if thread.is_alive():
                    print(f"{server_type} server still running, forcing shutdown...")
                    force_shutdown_server()
            except (AttributeError, RuntimeError):
                # Thread may have terminated during the wait
                print(f"{server_type} server already terminated")
        
        # Wait for threads to finish
        for server_type, thread in servers_running:
            try:
                thread.join(timeout=2)
                if not thread.is_alive():
                    print(f"{server_type} server shutdown complete!")
                else:
                    print(f"{server_type} server may still be running in background")
            except (AttributeError, RuntimeError):
                # Thread may be in invalid state
                print(f"{server_type} server shutdown status unknown")
    else:
        print("No servers running")
        # Clean up PID file just in case
        remove_pid_file()

# Register cleanup function to remove PID file on exit
atexit.register(remove_pid_file)

# Public interface functions
def update_header(new_header):
    """Updates the main subtitle text."""
    state.update_header(new_header)

def update_translated_header(new_header):
    """Updates the translated text."""
    state.update_translated_header(new_header)

def update_transcribed_header(new_header):
    """Updates the transcribed text."""
    state.update_transcribed_header(new_header)