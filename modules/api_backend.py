import os
import logging
from flask import Flask, send_from_directory, url_for
from threading import Thread

header_text = ""
translated_header_text = ""
transcribed_header_text = ""

def update_header(new_header):
    global header_text
    header_text = new_header

def update_translated_header(new_header):
    global translated_header_text
    translated_header_text = new_header

def update_transcribed_header(new_header):
    global transcribed_header_text
    transcribed_header_text = new_header

def flask_server(operation, portnumber):
    if operation == "start":
        # Define paths
        script_dir = os.path.dirname(os.path.realpath(__file__))
        project_root = os.path.dirname(script_dir)
        html_data_dir = os.path.join(project_root, 'html_data')
        static_dir = os.path.join(html_data_dir, 'static')

        # Flask server
        app = Flask(__name__, static_folder=static_dir, static_url_path='/static')
        app.config["DEBUG"] = False

        # Set the logging level to WARNING
        app.logger.setLevel(logging.WARNING)

        # Disable logging for "/update-header" route
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        log.disabled = True

        # Set port number
        port = portnumber

        # Time to start the server
        print("Starting Flask Server on port:", port)
        print("You can access the server at http://localhost:" + str(port))

        # Set the root directory
        @app.route('/')
        def serve_index():
            index_html_path = os.path.join(html_data_dir, 'index.html')
            with open(index_html_path, 'r') as file:
                html_content = file.read()
                updated_html = html_content.replace("{{ header_text }}", header_text)
            return updated_html

        # Serve static files (CSS, JS, images)
        @app.route('/static/<path:filename>')
        def serve_static(filename):
            return send_from_directory(static_dir, filename)

        # Route for updating the header dynamically
        @app.route('/update-header')
        def update_header_route():
            return header_text

        # Route for updating the translated header dynamically
        @app.route('/update-translated-header')
        def update_translated_header_route():
            return translated_header_text

        # Route for updating the transcribed header dynamically
        @app.route('/update-transcribed-header')
        def update_transcribed_header_route():
            return transcribed_header_text

        # Generate URL for static file in index.html
        @app.context_processor
        def override_url_for():
            return dict(url_for=dated_url_for)

        def dated_url_for(endpoint, **values):
            filename = values.get('filename', None)
            if filename:
                file_path = os.path.join(static_dir, filename)
                values['q'] = int(os.stat(file_path).st_mtime)
            return url_for(endpoint, **values)

        # Function to run the server
        def run():
            try:
                app.run(host='0.0.0.0', port=port)
            except Exception as e:
                print(f"Server crashed due to {e}")
                app.do_teardown_appcontext()

        # Start the server in a new thread
        Thread(target=run).start()

def kill_server():
    print("Killing Server")
    os._exit(0)

print("Web Server Module Loaded")