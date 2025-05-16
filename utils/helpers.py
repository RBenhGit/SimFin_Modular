"""Helper utility functions for SimFin Analyzer."""

import os


def get_statement_file_path(ticker, statement_type, period_type, base_dir='data'):
    """Get the path for a specific financial statement file.
    
    Args:
        ticker: Stock ticker symbol
        statement_type: Type of statement ('income', 'balance', 'cashflow')
        period_type: Period type ('annual', 'quarterly')
        base_dir: Base directory for data storage
    
    Returns:
        Path to the statement file
    """
    # Define statement type to file name mapping
    statement_names = {
        'income': 'Income_Statement',
        'balance': 'Balance_Sheet',
        'cashflow': 'Cash_Flow_Statement',
    }
    
    # Get the statement name from the mapping or create a generic name
    statement_name = statement_names.get(statement_type, f'Unknown_{statement_type}')
    
    # Construct and return the full file path
    return os.path.join(base_dir, ticker, f'{ticker}_{statement_name}_{period_type}.csv')


def get_api_key_status_for_display(api_key_file):
    """Get a user-friendly status string for API key configuration.
    
    Args:
        api_key_file: Path to the API key file
    
    Returns:
        A string describing the API key status
    """
    if not os.path.exists(api_key_file) or os.path.getsize(api_key_file) == 0:
        return "קובץ מפתח לא קיים או ריק, משתמש במפתח 'free'"
    
    with open(api_key_file, 'r') as f:
        key = f.read().strip()
        
    if key.lower() == 'free':
        return f"משתמש במפתח 'free' מהקובץ {api_key_file}"
    else:
        return f"מפתח API מותאם אישית נטען מהקובץ {api_key_file}"


def ensure_directory_exists(path):
    """Ensure that a directory exists.
    
    Args:
        path: Path to a directory or file. If a file path is provided,
              the directory containing the file will be created.
    """
    # Check if the path is a directory itself or a file path
    if os.path.splitext(path)[1]:  # If there's a file extension
        directory = os.path.dirname(path)
    else:
        directory = path
        
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)


def format_number_for_display(number, prefix='', suffix=''):
    """Format a number for display with thousands separator.
    
    Args:
        number: Number to format
        prefix: Prefix string (currency symbol, etc.)
        suffix: Suffix string (percentage sign, etc.)
    
    Returns:
        Formatted number string
    """
    if number is None:
        return "N/A"
    
    try:
        # Format with comma as thousands separator
        formatted = f"{prefix}{number:,.2f}{suffix}"
        return formatted
    except (ValueError, TypeError):
        return f"{prefix}{number}{suffix}"
