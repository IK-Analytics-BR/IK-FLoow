"""
Passenger WSGI entry point for Hostinger cPanel
This file is required for automatic Python detection
"""
import os
import sys

# Get the directory containing this file
current_dir = os.path.dirname(os.path.abspath(__file__))

# Add app directory to path
app_dir = os.path.join(current_dir, 'app')
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

# Add current directory to path
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Load environment variables
try:
    from dotenv import load_dotenv
    env_path = os.path.join(app_dir, '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
except ImportError:
    pass

# Import the Flask application - this is the key variable Passenger looks for
try:
    from main_mysql import app as application
except ImportError as e:
    print(f"Error importing application: {e}")
    # Create a simple error application
    def application(environ, start_response):
        status = '500 Internal Server Error'
        response_headers = [('Content-type', 'text/plain')]
        start_response(status, response_headers)
        return [b'Error loading application. Please check configuration.']

# For Passenger - this variable MUST be named 'application'
# Passenger will use this WSGI callable
