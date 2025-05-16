"""Configuration loader utility for SimFin Analyzer."""

import os
import configparser


class ConfigLoader:
    """Load and manage configuration settings from config files."""
    
    def __init__(self, config_path=None):
        """Initialize ConfigLoader with a config file path.
        
        Args:
            config_path: Path to the config file. If None, default is used.
        """
        self.config_path = config_path or os.path.join('config', 'config.ini')
        self.config = configparser.ConfigParser()
        
        # If config file doesn't exist, create with default values
        if not os.path.exists(self.config_path):
            self._create_default_config()
        else:
            self.config.read(self.config_path)
    
    def _create_default_config(self):
        """Create default configuration settings."""
        # Create default sections and settings
        self.config['API'] = {
            'api_key_file': 'simfin_api_key.txt',
            'default_key': 'free'
        }
        self.config['PATHS'] = {
            'simfin_data_directory': 'data/simfin_data',
            'processed_data_directory': 'data'
        }
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        
        # Write default config to file
        with open(self.config_path, 'w') as configfile:
            self.config.write(configfile)
    
    def get(self, section, key, fallback=None):
        """Get a configuration value for a given section and key.
        
        Args:
            section: Configuration section name
            key: Configuration key name
            fallback: Default value if the key doesn't exist
            
        Returns:
            Configuration value or fallback value
        """
        try:
            return self.config[section][key]
        except (KeyError, configparser.NoSectionError):
            return fallback
    
    def save(self):
        """Save current configuration to the file."""
        with open(self.config_path, 'w') as configfile:
            self.config.write(configfile)
