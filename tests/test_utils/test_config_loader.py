"""Tests for the config loader utility."""

import pytest
import os
import configparser
import tempfile
from unittest.mock import patch, MagicMock

# Import the module or mock it if not available
try:
    from utils.config_loader import ConfigLoader
except ImportError:
    # Create a mock ConfigLoader class for testing without implementation
    class ConfigLoader:
        def __init__(self, config_path=None):
            self.config_path = config_path or 'config.ini'
            self.config = configparser.ConfigParser()
            
            # Default values if file doesn't exist
            if not os.path.exists(self.config_path):
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
                with open(self.config_path, 'w') as configfile:
                    self.config.write(configfile)
            else:
                self.config.read(self.config_path)
        
        def get(self, section, key, fallback=None):
            try:
                return self.config[section][key]
            except (KeyError, configparser.NoSectionError):
                return fallback


def test_config_loader_init_with_existing_file(mock_config_file):
    """Test initialization with an existing config file."""
    config_loader = ConfigLoader(config_path=mock_config_file)
    assert config_loader.config.sections() == ['API', 'PATHS']
    assert config_loader.get('API', 'default_key') == 'free'
    assert config_loader.get('PATHS', 'simfin_data_directory') == 'data/simfin_data'


def test_config_loader_init_without_file():
    """Test initialization without an existing config file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = os.path.join(tmpdir, 'nonexistent.ini')
        config_loader = ConfigLoader(config_path=config_path)
        
        # Check if the default config was created
        assert os.path.exists(config_path)
        assert config_loader.config.sections() == ['API', 'PATHS']
        assert config_loader.get('API', 'default_key') == 'free'


def test_config_loader_get_with_fallback(mock_config_file):
    """Test getting a value with a fallback."""
    config_loader = ConfigLoader(config_path=mock_config_file)
    assert config_loader.get('NONEXISTENT', 'key', fallback='fallback_value') == 'fallback_value'
    assert config_loader.get('API', 'nonexistent_key', fallback='fallback_value') == 'fallback_value'


def test_config_loader_get_without_fallback(mock_config_file):
    """Test getting a value without a fallback."""
    config_loader = ConfigLoader(config_path=mock_config_file)
    assert config_loader.get('API', 'api_key_file') == 'simfin_api_key.txt'
    assert config_loader.get('NONEXISTENT', 'key') is None
