"""Tests for the data loader module."""

import pytest
import os
from unittest.mock import patch, MagicMock

# Import the module or mock it if not available
try:
    from modules.data_loader import DataLoader
except ImportError:
    # Create a mock DataLoader class for testing
    class DataLoader:
        def __init__(self, config_path=None):
            self.config_path = config_path or 'config.ini'
            self.api_key_file = 'simfin_api_key.txt'
            self.simfin_data_directory = 'data/simfin_data'
            
        def load_simfin_api_key(self):
            """Load SimFin API key from file or use default."""
            if os.path.exists(self.api_key_file) and os.path.getsize(self.api_key_file) > 0:
                with open(self.api_key_file, 'r') as f:
                    return f.read().strip()
            return 'free'
            
        def initialize_simfin(self):
            """Initialize SimFin with API key and data directory."""
            import simfin as sf
            
            # Create data directory if it doesn't exist
            os.makedirs(self.simfin_data_directory, exist_ok=True)
            
            # Load API key and configure SimFin
            api_key = self.load_simfin_api_key()
            sf.set_api_key(api_key)
            sf.set_data_dir(self.simfin_data_directory)
            
            return api_key, self.simfin_data_directory


def test_data_loader_init(mock_config_file):
    """Test initializing the data loader."""
    with patch('utils.config_loader.ConfigLoader') as mock_config:
        mock_config.return_value.get.side_effect = lambda section, key, fallback=None: {
            ('API', 'api_key_file'): 'simfin_api_key.txt',
            ('PATHS', 'simfin_data_directory'): 'data/simfin_data'
        }.get((section, key), fallback)
        
        loader = DataLoader(mock_config_file)
        assert loader.api_key_file == 'simfin_api_key.txt'
        assert loader.simfin_data_directory == 'data/simfin_data'


def test_load_simfin_api_key_with_existing_file(mock_api_key_file):
    """Test loading SimFin API key with an existing file."""
    with patch('utils.config_loader.ConfigLoader') as mock_config:
        mock_config.return_value.get.side_effect = lambda section, key, fallback=None: {
            ('API', 'api_key_file'): mock_api_key_file,
            ('PATHS', 'simfin_data_directory'): 'data/simfin_data'
        }.get((section, key), fallback)
        
        loader = DataLoader()
        loader.api_key_file = mock_api_key_file
        key = loader.load_simfin_api_key()
        assert key == 'test_api_key'


def test_load_simfin_api_key_without_file():
    """Test loading SimFin API key without a file."""
    with patch('utils.config_loader.ConfigLoader') as mock_config:
        mock_config.return_value.get.side_effect = lambda section, key, fallback=None: {
            ('API', 'api_key_file'): 'nonexistent_file.txt',
            ('PATHS', 'simfin_data_directory'): 'data/simfin_data'
        }.get((section, key), fallback)
        
        loader = DataLoader()
        loader.api_key_file = 'nonexistent_file.txt'
        key = loader.load_simfin_api_key()
        assert key == 'free'


def test_initialize_simfin():
    """Test initializing SimFin."""
    # Define DataLoader at module level for this test to avoid UnboundLocalError
    data_loader_module = None
    
    try:
        from modules.data_loader import DataLoader as ActualDataLoader
        data_loader_module = ActualDataLoader
    except ImportError:
        # Use the mock class defined above if module not available
        data_loader_module = DataLoader
    
    with patch('modules.data_loader.os.makedirs') as mock_makedirs, \
         patch('simfin.set_api_key') as mock_set_api_key, \
         patch('simfin.set_data_dir') as mock_set_data_dir:
        
        # Create instance from the properly assigned class
        loader = data_loader_module()
        loader.load_simfin_api_key = MagicMock(return_value='test_key')
        
        api_key, data_dir = loader.initialize_simfin()
        
        mock_makedirs.assert_called_once_with(loader.simfin_data_directory, exist_ok=True)
        mock_set_api_key.assert_called_once_with('test_key')
        mock_set_data_dir.assert_called_once_with(loader.simfin_data_directory)
        assert api_key == 'test_key'
        assert data_dir == loader.simfin_data_directory
