#!/usr/bin/env python3
"""
Entry point for Python hosting
This file must be in the root directory for proper detection
"""
import sys
import os

# Add app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Import and expose the Flask application
from main_mysql import app as application

# For WSGI servers
app = application

if __name__ == "__main__":
    app.run()
