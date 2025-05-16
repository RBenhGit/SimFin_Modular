"""
SimFin Analyzer - Main Application Entry Point

This is the main application file for SimFin Analyzer, which sets up the Flask application,
registers blueprints, configures the application, and starts the web server.
"""

import os
import logging
from flask import Flask

# Import route blueprints
from modules.routes import home_bp, graphs_bp, valuations_bp

# Import configuration and setup utilities
from modules.data_loader import configure_simfin
from utils.config_loader import ConfigLoader


def create_app():
    """Create and configure the Flask application."""
    # Set up basic logging
    logging.basicConfig(
        filename='app.log',
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create Flask application
    app = Flask(__name__)
    
    # Load application configuration
    config = ConfigLoader()
    
    # Configure the app secret key
    try:
        # Try to import secret key from a separate file
        from secrets import FLASK_SECRET_KEY
        app.config['SECRET_KEY'] = FLASK_SECRET_KEY
    except ImportError:
        # If not available, use a default key (not secure for production)
        default_key = os.urandom(24).hex()
        app.config['SECRET_KEY'] = default_key
        logging.warning(
            "No secrets.py file with FLASK_SECRET_KEY found. Using a generated key. "
            "For production, create a secrets.py file with a strong random key."
        )
    
    # Register blueprints
    app.register_blueprint(home_bp)
    app.register_blueprint(graphs_bp, url_prefix='/graphs')
    app.register_blueprint(valuations_bp, url_prefix='/valuations')
    
    # Configure SimFin API and data directories
    api_key, data_dir = configure_simfin()
    logging.info(f"SimFin configured with data directory: {data_dir}")
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
