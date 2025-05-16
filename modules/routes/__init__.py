"""Route modules for SimFin Analyzer.

This package contains route handler modules for different sections of the application.
"""

from flask import Blueprint

# Create blueprints for different sections
home_bp = Blueprint('home', __name__)
graphs_bp = Blueprint('graphs', __name__)
valuations_bp = Blueprint('valuations', __name__)

# Import route handlers to register routes with blueprints
try:
    from . import home
    from . import graphs
    from . import valuations
except ImportError:
    # This might happen during testing or initial setup
    pass
