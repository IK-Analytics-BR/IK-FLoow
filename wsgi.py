"""
WSGI entry point for production servers
Compatible with Passenger WSGI, Gunicorn, and uWSGI
"""
import os
import sys

# Get the directory containing this file
current_dir = os.path.dirname(os.path.abspath(__file__))

# Add app directory to path
app_dir = os.path.join(current_dir, 'app')
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

# Load environment variables
from dotenv import load_dotenv
env_path = os.path.join(app_dir, '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)

# Import the Flask application
try:
    from main_mysql import app as application
    app = application
except ImportError as e:
    print(f"Error importing application: {e}")
    raise

def application(env, start_response):
    """WSGI application entry point"""
    return app(env, start_response)

# For Passenger WSGI
if __name__ == '__main__':
    app.run()
