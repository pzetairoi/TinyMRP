"""
This script runs the TinyWEB to be used as an entry point to our application by gunicorn
"""

from flasky import app


if __name__ == '__main__':
    
    app.run()
