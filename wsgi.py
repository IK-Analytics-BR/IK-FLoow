"""
WSGI entry point for production servers
"""
import os
import sys

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(os.path.join('app', '.env'))

# Import the Flask application
from main_mysql import app as application

# For Gunicorn
app = application

if __name__ == '__main__':
    application.run()
