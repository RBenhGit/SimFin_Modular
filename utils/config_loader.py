# utils/config_loader.py
import configparser
import os
import logging

logger = logging.getLogger(__name__)

class ConfigLoader:
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    def __init__(self, config_file_relative_path='config/config.ini'):
        self.config_file_path = os.path.join(self.PROJECT_ROOT, config_file_relative_path)
        self.config = configparser.ConfigParser()

        if not os.path.exists(self.config_file_path):
            logger.warning(f"Config file not found at {self.config_file_path}. Creating a default one.")
            self._create_default_config()
        try:
            self.config.read(self.config_file_path)
            logger.info(f"Config file '{self.config_file_path}' loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to read config file '{self.config_file_path}': {e}", exc_info=True)


    def _create_default_config(self):
        """Creates a default config file if it doesn't exist."""
        self.config['API'] = {
            'api_key_file': 'config/simfin_api_key.txt', # Relative to project root
            'default_key': 'free'
        }
        self.config['PATHS'] = {
            'simfin_data_directory': 'data/simfin_data', # Relative to project root
            'log_file': 'app.log' # Relative to project root
        }
        try:
            os.makedirs(os.path.dirname(self.config_file_path), exist_ok=True)
            with open(self.config_file_path, 'w') as configfile:
                self.config.write(configfile)
            logger.info(f"Default config file created at {self.config_file_path}")
        except Exception as e:
            logger.error(f"Failed to create default config file at {self.config_file_path}: {e}", exc_info=True)


    def get(self, section, key, fallback=None):
        """Gets a value from the config file."""
        try:
            return self.config.get(section, key, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError):
            logger.warning(f"Config key '{key}' not found in section '{section}'. Using fallback: {fallback}")
            return fallback

    def get_absolute_path(self, section, key, fallback_relative_path=None):
        """
        Gets a path value from config, assumes it's relative to project root if not absolute,
        and returns an absolute path.
        """
        value = self.get(section, key) # Try to get from config
        if value is None and fallback_relative_path: # If not in config, use fallback
            value = fallback_relative_path
            logger.debug(f"Using fallback path '{fallback_relative_path}' for {section}.{key}")
        elif value is None:
             logger.warning(f"No value or fallback provided for config path {section}.{key}")
             return None

        if os.path.isabs(value):
            return value
        else:
            abs_path = os.path.join(self.PROJECT_ROOT, value)
            logger.debug(f"Resolved path for {section}.{key}: '{value}' -> '{abs_path}'")
            return abs_path