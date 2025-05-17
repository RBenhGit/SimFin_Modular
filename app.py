"""
SimFin Analyzer - Main Application Entry Point
"""
import os
import logging
from flask import Flask
from logging.handlers import RotatingFileHandler

# Import route blueprints
from modules.routes import home_bp, graphs_bp, valuations_bp

# Import configuration and setup utilities
from modules.data_loader import ensure_simfin_configured, get_api_key_status_for_display # configure_simfin is called by ensure_simfin_configured
from utils.config_loader import ConfigLoader

def create_app():
    """Create and configure the Flask application."""
    # Configure basic console logging and level for the root logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s'
    )

    # Get the root logger to add the rotating file handler
    root_logger = logging.getLogger()

    # Setup RotatingFileHandler
    log_file_path = 'app.log'
    # Rotate log file if it reaches 5MB, keep 5 backup files. UTF-8 encoding is specified.
    rotating_file_handler = RotatingFileHandler(
        log_file_path, maxBytes=5*1024*1024, backupCount=5, encoding='utf-8'
    )
    rotating_file_handler.setLevel(logging.INFO) # Set level for this handler
    
    # Define a formatter for the file logs (can be same or different from console)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s')
    rotating_file_handler.setFormatter(file_formatter)
    
    # Add the rotating file handler to the root logger
    root_logger.addHandler(rotating_file_handler)

    logger = logging.getLogger(__name__) # This specific logger will use the root's handlers

    app = Flask(__name__, instance_relative_config=False)
    logger.info("Flask application '%s' created.", app.name)

    config_ini_loader = None
    try:
        config_ini_loader = ConfigLoader()
        logger.info("ConfigLoader initialized successfully using file: %s", getattr(config_ini_loader, 'config_file_path', 'N/A'))
    except Exception as e:
        logger.error(f"CRITICAL: Failed to initialize ConfigLoader: {e}", exc_info=True)

    secret_key_source = "generated temporary key"
    if 'FLASK_SECRET_KEY' in os.environ:
        app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY')
        secret_key_source = "environment variable"
    else:
        try:
            secrets_config = {}
            # Construct the absolute path to secret.py relative to app.py
            # Assuming app.py is in the project root.
            current_dir = os.path.dirname(os.path.abspath(__file__))
            secret_file_path = os.path.join(current_dir, 'secret.py')
            with open(secret_file_path, encoding='utf-8') as f:
                exec(f.read(), secrets_config)
            app.config['SECRET_KEY'] = secrets_config['FLASK_SECRET_KEY']
            secret_key_source = "secret.py file"
            logger.info("Successfully loaded FLASK_SECRET_KEY from local secret.py.")
        except FileNotFoundError:
            logger.warning("local secret.py NOT FOUND in project root.")
            app.config['SECRET_KEY'] = os.urandom(24).hex()
        except KeyError:
            logger.error("FLASK_SECRET_KEY not found within local secret.py.")
            app.config['SECRET_KEY'] = os.urandom(24).hex()
        except Exception as e:
            logger.error(f"Error loading SECRET_KEY from local secret.py: {e}", exc_info=True)
            app.config['SECRET_KEY'] = os.urandom(24).hex()
            secret_key_source = "generated temporary key due to error"

    if "generated temporary key" in secret_key_source:
        logger.critical(
            "CRITICAL: FLASK_SECRET_KEY was %s. Sessions will NOT persist across restarts. "
            "Ensure secrets.py (with FLASK_SECRET_KEY) is in the project root or set FLASK_SECRET_KEY environment variable.",
            secret_key_source
        )
    else:
        logger.info(f"Effective FLASK_SECRET_KEY source: {secret_key_source}")

    if config_ini_loader:
        try:
            logger.info("Attempting initial SimFin configuration on app startup...")
            api_key, data_dir = ensure_simfin_configured(config_loader_instance=config_ini_loader)
            if data_dir:
                logger.info(f"Initial SimFin config successful. API key: {'Custom' if api_key and api_key != 'free' else 'Free/Default'}, Data directory: {data_dir}")
            else:
                logger.error("Initial SimFin configuration FAILED to set data directory. SimFin features may not work.")
        except Exception as e:
            logger.error(f"Error during initial SimFin configuration call: {e}", exc_info=True)
    else:
        logger.error("Initial SimFin configuration skipped because ConfigLoader failed to initialize.")

    @app.context_processor
    def inject_global_template_variables():
        api_status_val = "סטטוס מפתח API לא זמין (שגיאת תצורה)"
        if config_ini_loader:
            try:
                api_status_val = get_api_key_status_for_display(config_loader_instance=config_ini_loader)
            except Exception as e:
                logger.error(f"Failed to get API key status for display in context_processor: {e}", exc_info=True)
        return dict(api_key_status_display=api_status_val)
    logger.info("Context processor for API key status registered.")

    try:
        app.register_blueprint(home_bp)
        app.register_blueprint(graphs_bp)
        app.register_blueprint(valuations_bp)
        logger.info("Blueprints registered successfully.")
    except Exception as e:
        logger.error(f"Failed to register blueprints: {e}", exc_info=True)

    return app

if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    try:
        simfin_app = create_app()
        logger.info("SimFin Analyzer application starting...")
        simfin_app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        logger.critical(f"Failed to create or run the Flask application: {e}", exc_info=True)