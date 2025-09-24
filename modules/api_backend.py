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
"""

import os
import logging
import time
import threading
import signal
import atexit
from flask import Flask, send_from_directory, url_for, Blueprint
from threading import Thread, Event
from functools import lru_cache
import ssl
import tempfile
from werkzeug.serving import make_server
from colorama import Fore, Style

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

def watchdog_monitor():
    """Monitor PID file existence and force shutdown if file is deleted."""
    global force_shutdown_flag
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

def force_shutdown_server():
    """Force shutdown the Flask server immediately."""
    global server_thread, force_shutdown_flag
    force_shutdown_flag = True
    
    if server_thread and server_thread.is_alive():
        print(" Force killing Flask server...")
        try:
            # Set shutdown flag
            server_thread.shutdown_event.set()
            
            # Force close the server socket if available
            if hasattr(server_thread, 'server') and server_thread.server:
                try:
                    server_thread.server.server_close()
                except:
                    pass
            
            # Give it a moment to shutdown gracefully
            server_thread.join(timeout=1)
            
            # If still alive, we need to force kill the process
            if server_thread.is_alive():
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
    Serves static files (CSS, JS, images, etc.).
    
    Args:
        filename (str): Name of the static file to serve
    """
    return send_from_directory(get_static_dir(), filename)

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
    def __init__(self, port, use_https=False):
        super().__init__()
        self.port = port
        self.use_https = use_https
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

        # Add headers
        @app.after_request
        def add_header(response):
            response.headers.update({
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
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
        
        # Start watchdog thread
        global watchdog_thread
        watchdog_thread = threading.Thread(target=watchdog_monitor, daemon=True)
        watchdog_thread.start()
        
        if self.use_https:
            ssl_context, ssl_dir = self.setup_https()
            if not ssl_context:
                print("Falling back to HTTP")

        try:
            self.server = make_server('0.0.0.0', self.port, self.app, 
                                    ssl_context=ssl_context)
            print(f"Starting Flask Server on port: {self.port}")
            print(f"You can access the server at http{'s' if ssl_context else ''}://localhost:{self.port}")
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

def flask_server(operation, portnumber, https_port=None):
    """
    Controls the Flask server operation.
    
    Args:
        operation (str): "start" to start the server
        portnumber (int): Port number for the HTTP server (can be None)
        https_port (int): Port number for the HTTPS server (can be None)
    """
    global server_thread, https_server_thread
    if operation == "start":
        create_pid_file()
        
        # Start HTTP server if port is specified
        if portnumber:
            server_thread = FlaskServerThread(portnumber, use_https=False)
            server_thread.daemon = True
            server_thread.start()
            
            # If we're also starting HTTPS server, wait for HTTP startup to complete
            if https_port:
                server_thread.startup_complete.wait()  # Wait for HTTP server messages to finish
        
        # Start HTTPS server if port is specified
        if https_port:
            https_server_thread = FlaskServerThread(https_port, use_https=True)
            https_server_thread.daemon = True
            https_server_thread.start()
        
        # Start watchdog thread only once
        global watchdog_thread
        watchdog_thread = threading.Thread(target=watchdog_monitor)
        watchdog_thread.daemon = True
        watchdog_thread.start()

def kill_server():
    """Force shutdown the server using PID file mechanism."""
    global server_thread, https_server_thread
    servers_running = []
    
    if server_thread and server_thread.is_alive():
        servers_running.append(('HTTP', server_thread))
    if https_server_thread and https_server_thread.is_alive():
        servers_running.append(('HTTPS', https_server_thread))
    
    if servers_running:
        print("Initiating server shutdown...")
        
        # First try graceful shutdown by deleting PID file
        remove_pid_file()
        
        # Wait a moment for watchdog to detect and shutdown
        time.sleep(3)
        
        # Check if servers are still running and force shutdown if needed
        for server_type, thread in servers_running:
            if thread.is_alive():
                print(f"{server_type} server still running, forcing shutdown...")
                force_shutdown_server()
        
        # Wait for threads to finish
        for server_type, thread in servers_running:
            thread.join(timeout=2)
            if not thread.is_alive():
                print(f"{server_type} server shutdown complete!")
            else:
                print(f"{server_type} server may still be running in background")
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