import os
import sys

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the WSGI application from Django
from inventory_project.wsgi import application

# This is the application object that gunicorn will use
app = application 