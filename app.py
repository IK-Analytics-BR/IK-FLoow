"""
Entry point for compatibility with some PaaS platforms
"""
from wsgi import app

if __name__ == '__main__':
    app.run()
