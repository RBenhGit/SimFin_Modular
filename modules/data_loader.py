# modules/data_loader.py
import os
import logging
import simfin as sf
from utils.config_loader import ConfigLoader
import yfinance as yf

logger = logging.getLogger(__name__)

def _get_resolved_path(config_loader, section, key, fallback_relative_path):
    if not isinstance(config_loader, ConfigLoader):
        logger.error("_get_resolved_path: Invalid ConfigLoader instance provided.")
        try:
            config_loader = ConfigLoader()
            logger.warning("_get_resolved_path: Created a new ConfigLoader instance as fallback.")
        except Exception as e:
            logger.error(f"_get_resolved_path: Failed to create fallback ConfigLoader: {e}")
            return None

    try:
        resolved_path = config_loader.get_absolute_path(section, key, fallback_relative_path=fallback_relative_path)
        if not resolved_path:
             logger.warning(f"Path for {section}.{key} (fallback: {fallback_relative_path}) resolved to None or empty.")
        return resolved_path
    except Exception as e:
        logger.error(f"Error using config_loader.get_absolute_path for {section}.{key}: {e}", exc_info=True)
        return None

def load_simfin_api_key(config_loader_instance=None):
    config = config_loader_instance if config_loader_instance else ConfigLoader()
    api_key_file_path = _get_resolved_path(config, 'API', 'api_key_file', 'config/simfin_api_key.txt')
    logger.info(f"Loading SimFin API key. Attempting to use file: {api_key_file_path if api_key_file_path else 'Default behavior'}")

    api_key_to_use = config.get('API', 'default_key', 'free')

    if api_key_file_path and os.path.exists(api_key_file_path):
        try:
            with open(api_key_file_path, 'r') as f:
                read_key = f.read().strip()
            if read_key:
                api_key_to_use = read_key
                logger.info(f"Loaded custom API key from: {api_key_file_path}")
            else:
                logger.info(f"API key file '{api_key_file_path}' is empty, using default '{api_key_to_use}'.")
        except IOError as e:
            logger.error(f"Could not read API key file '{api_key_file_path}': {e}. Using '{api_key_to_use}'.")
    elif api_key_file_path:
        logger.info(f"API key file not found at '{api_key_file_path}'. Using '{api_key_to_use}'.")
    else:
        logger.warning(f"API key file path could not be determined. Using '{api_key_to_use}'.")
    return api_key_to_use

def configure_simfin(api_key_val=None, data_dir_val=None, config_loader_instance=None):
    logger.info("configure_simfin: Configuring SimFin settings...")
    config = config_loader_instance if config_loader_instance else ConfigLoader()

    current_api_key = api_key_val if api_key_val is not None else load_simfin_api_key(config_loader_instance=config)
    try:
        sf.set_api_key(current_api_key)
        logger.info(f"SimFin API key set (type: {'Custom' if current_api_key and current_api_key != 'free' else 'Free/Default'})")
    except Exception as e:
        logger.error(f"Failed to set SimFin API key: {e}", exc_info=True)

    simfin_data_directory_path = data_dir_val if data_dir_val is not None \
        else _get_resolved_path(config, 'PATHS', 'simfin_data_directory', 'data/simfin_data')
    logger.info(f"SimFin data directory path to be set: {simfin_data_directory_path}")

    configured_data_dir = None
    if simfin_data_directory_path:
        try:
            os.makedirs(simfin_data_directory_path, exist_ok=True)
            sf.set_data_dir(simfin_data_directory_path)
            logger.info(f"SimFin data directory set successfully to: {simfin_data_directory_path}")
            configured_data_dir = simfin_data_directory_path
        except Exception as e:
            logger.error(f"Failed to create or set SimFin data directory '{simfin_data_directory_path}': {e}", exc_info=True)
    else:
        logger.error("SimFin data directory path could not be determined. SimFin not configured correctly.")

    return current_api_key, configured_data_dir

def ensure_simfin_configured(config_loader_instance=None):
    logger.info("ensure_simfin_configured: Ensuring SimFin is configured for the current operation.")
    return configure_simfin(config_loader_instance=config_loader_instance)

def get_api_key_status_for_display(config_loader_instance=None):
    config = config_loader_instance if config_loader_instance else ConfigLoader()
    api_key_file_path = _get_resolved_path(config, 'API', 'api_key_file', 'config/simfin_api_key.txt')
    logger.info(f"get_api_key_status_for_display: Checking API key file: {api_key_file_path}")

    if not api_key_file_path or not os.path.exists(api_key_file_path) or os.path.getsize(api_key_file_path) == 0:
        return "קובץ מפתח לא קיים או ריק, משתמש במפתח 'free'"
    try:
        with open(api_key_file_path, 'r') as f:
            key = f.read().strip()
    except IOError as e:
        logger.error(f"Could not read API key file '{api_key_file_path}' for status display: {e}")
        return "שגיאה בקריאת קובץ מפתח API"
    if key.lower() == 'free' or not key:
        return f"משתמש במפתח 'free' (קובץ '{os.path.basename(api_key_file_path)}' ריק או מכיל 'free')"
    else:
        return f"מפתח API מותאם אישית נטען מהקובץ '{os.path.basename(api_key_file_path)}'"

def get_company_info(ticker_symbol, market='us'):
    """
    Get company information from SimFin.
    
    Args:
        ticker_symbol (str): The stock ticker.
        market (str): The market (e.g., 'us').
        
    Returns:
        dict: Dictionary containing company information or error details.
    """
    try:
        logger.info(f"Loading company info for ticker {ticker_symbol} from SimFin...")
        # Load company info from SimFin
        df_companies = sf.load_companies(market=market)
        
        if df_companies is not None and not df_companies.empty:
            logger.info(f"Successfully loaded companies data. Shape: {df_companies.shape}")
            logger.info(f"Companies data columns: {df_companies.columns.tolist()}")
            logger.info(f"First few rows of companies data:\n{df_companies.head()}")
            
            # Try to find the company by ticker - handle both possible column names
            ticker_col = 'Ticker' if 'Ticker' in df_companies.columns else 'Symbol'
            logger.info(f"Using column '{ticker_col}' for ticker lookup")
            
            company_info = df_companies[df_companies[ticker_col] == ticker_symbol.upper()]
            logger.info(f"Found {len(company_info)} matching companies for ticker {ticker_symbol}")
            
            if not company_info.empty:
                name_col = 'Company Name' if 'Company Name' in company_info.columns else 'Name'
                logger.info(f"Using column '{name_col}' for company name")
                logger.info(f"Company info row:\n{company_info.iloc[0]}")
                
                result = {
                    'name': company_info[name_col].iloc[0],
                    'sector': company_info['Sector'].iloc[0] if 'Sector' in company_info.columns else None,
                    'industry': company_info['Industry'].iloc[0] if 'Industry' in company_info.columns else None
                }
                logger.info(f"Found company info for {ticker_symbol}: {result}")
                return result
            else:
                logger.warning(f"No company found with ticker {ticker_symbol}")
                return {"Error": "CompanyNotFound", "Details": f"No company information found for {ticker_symbol}"}
        else:
            logger.error("Failed to load companies data from SimFin")
            return {"Error": "LoadFailed", "Details": "Failed to load company information from SimFin"}
            
    except Exception as e:
        logger.error(f"Error getting company info for {ticker_symbol}: {e}", exc_info=True)
        return {"Error": "ProcessingException", "Details": str(e)}

def get_company_name_yf(ticker_symbol):
    """
    Get company name from yfinance.
    Args:
        ticker_symbol (str): The stock ticker.
    Returns:
        str or None: Company name if found, else None.
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        name = info.get('shortName') or info.get('longName') or info.get('name')
        return name
    except Exception as e:
        logger.error(f"Error getting company name from yfinance for {ticker_symbol}: {e}")
        return None