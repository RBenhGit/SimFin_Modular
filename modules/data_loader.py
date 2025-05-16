"""Module for API key loading and data configuration in SimFin Analyzer."""

import os
import simfin as sf
from utils.config_loader import ConfigLoader


def load_simfin_api_key(api_key_file=None):
    """Load the SimFin API key from file.
    
    Args:
        api_key_file: Path to the API key file. If None, uses default path.
    
    Returns:
        str: The API key if found, 'free' otherwise.
    """
    config = ConfigLoader()
    if api_key_file is None:
        api_key_file = config.get('API', 'api_key_file')
    
    api_key = config.get('API', 'default_key', 'free')
    
    if os.path.exists(api_key_file):
        try:
            with open(api_key_file, 'r') as f:
                read_key = f.read().strip()
            if read_key:
                api_key = read_key
        except IOError:
            print(f"Could not read API key file '{api_key_file}'. Using '{api_key}'.")
    
    return api_key


def configure_simfin(api_key=None, data_dir=None):
    """Configure SimFin API with the given key and data directory.
    
    Args:
        api_key: The API key to use. If None, loads from file.
        data_dir: Directory to store SimFin data. If None, uses default.
    
    Returns:
        tuple: (api_key, data_dir) that were configured
    """
    config = ConfigLoader()
    
    # Set API key
    if api_key is None:
        api_key = load_simfin_api_key()
    sf.set_api_key(api_key)
    
    # Set data directory
    if data_dir is None:
        data_dir = config.get('PATHS', 'simfin_data_directory', 'data/simfin_data')
    
    os.makedirs(data_dir, exist_ok=True)
    sf.set_data_dir(data_dir)
    
    return api_key, data_dir


def get_api_key_status_for_display(api_key_file=None):
    """Get a user-friendly status string for API key configuration.
    
    Args:
        api_key_file: Path to the API key file. If None, uses default path.
    
    Returns:
        str: A string describing the API key status
    """
    config = ConfigLoader()
    if api_key_file is None:
        api_key_file = config.get('API', 'api_key_file')
    
    if not os.path.exists(api_key_file) or os.path.getsize(api_key_file) == 0:
        return "קובץ מפתח לא קיים או ריק, משתמש במפתח 'free'"
    
    with open(api_key_file, 'r') as f:
        key = f.read().strip()
        
    if key.lower() == 'free':
        return f"משתמש במפתח 'free' מהקובץ {api_key_file}"
    else:
        return f"מפתח API מותאם אישית נטען מהקובץ {api_key_file}"
