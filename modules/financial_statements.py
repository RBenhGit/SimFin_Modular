"""Module for downloading and processing financial statements in SimFin Analyzer."""

import os
import pandas as pd
import simfin as sf
import time
from utils.helpers import ensure_directory_exists


def download_financial_statements(ticker_symbol, market='us'):
    """
    Downloads ANNUAL and QUARTERLY financial statements (income, balance, cashflow)
    for a specific ticker.

    Args:
        ticker_symbol (str): The stock ticker.
        market (str): The market (e.g., 'us').

    Returns:
        dict: A dictionary where keys are like 'income_annual', 'income_quarterly', etc.,
              and values are DataFrames or error dictionaries.
    """
    results = {}
    ticker_upper = ticker_symbol.upper()
    variants = ['annual', 'quarterly']
    statement_types_map = {
        'income': sf.load_income,
        'balance': sf.load_balance,
        'cashflow': sf.load_cashflow
    }
    statement_type_readable_names = {
        'income': 'Income Statement',
        'balance': 'Balance Sheet',
        'cashflow': 'Cash Flow Statement'
    }

    for variant in variants:
        for stmt_key, load_function in statement_types_map.items():
            result_key = f"{stmt_key}_{variant}"
            readable_name = statement_type_readable_names[stmt_key]
            time.sleep(0.5)  # Short delay to avoid API rate limits

            try:
                df_all = load_function(variant=variant, market=market)
                
                current_df = None
                if df_all is not None:
                    if 'Ticker' in df_all.index.names:
                        if ticker_upper in df_all.index.get_level_values('Ticker'):
                            current_df = df_all.loc[ticker_upper]
                        else:
                            current_df = pd.DataFrame()
                    elif 'Ticker' in df_all.columns:
                        current_df = df_all[df_all['Ticker'] == ticker_upper]
                    else:
                        results[result_key] = {"Error": "FilterFailed", "Details": f"Could not find 'Ticker' info in {readable_name} ({variant}) dataset."}
                        continue

                    if current_df is not None:
                        if not current_df.empty:
                            results[result_key] = current_df.copy()
                        else:
                            results[result_key] = {"Error": "NoDataFound", "Details": f"No {readable_name} ({variant}) data for {ticker_symbol} (DataFrame empty after filter)."}
                else:
                    results[result_key] = {"Error": "LoadFailed", "Details": f"Failed to load ALL {readable_name} ({variant}) (SimFin returned None)."}
                    print(f"Error: LoadFailed for ALL {result_key} for {ticker_symbol}")

            except Exception as e:
                print(f"Exception for {result_key} for {ticker_symbol}: {e}")
                results[result_key] = {"Error": "ProcessingException", "Details": str(e)}
                
    return results


def save_financial_statements(financial_data, ticker, base_dir='data'):
    """
    Save downloaded financial statements to CSV files.
    
    Args:
        financial_data (dict): Dictionary with financial statements data
        ticker (str): Stock ticker symbol
        base_dir (str): Base directory for storing data
    
    Returns:
        dict: Status for each saved statement
    """
    status = {}
    ticker = ticker.upper()
    
    # Create a directory for the ticker if it doesn't exist
    ticker_dir = os.path.join(base_dir, ticker)
    ensure_directory_exists(ticker_dir)
    
    # Define statement type to file name mapping
    statement_names = {
        'income': 'Income_Statement',
        'balance': 'Balance_Sheet',
        'cashflow': 'Cash_Flow_Statement',
    }
    
    # Save each statement to a CSV file
    for variant in ['annual', 'quarterly']:
        for stmt_key in ['income', 'balance', 'cashflow']:
            result_key = f"{stmt_key}_{variant}"
            data_item = financial_data.get(result_key)
            
            if isinstance(data_item, pd.DataFrame) and not data_item.empty:
                file_name = f"{ticker}_{statement_names[stmt_key]}_{variant}.csv"
                save_path = os.path.join(ticker_dir, file_name)
                
                try:
                    # Ensure index has a name if it's a DatetimeIndex
                    if isinstance(data_item.index, pd.DatetimeIndex) and data_item.index.name is None:
                        data_item.index.name = 'Report Date'
                    
                    data_item.to_csv(save_path, index=True)
                    status[result_key] = f"Saved: {os.path.basename(save_path)}"
                except Exception as e:
                    status[result_key] = f"Error saving CSV for {result_key}: {e}"
                    print(f"Error saving {result_key} for {ticker} to CSV: {e}")
            elif isinstance(data_item, dict) and "Error" in data_item:
                status[result_key] = f"Download Error for {result_key}: {data_item.get('Details', 'Unknown error')}"
            else:
                status[result_key] = f"No data or empty data for {result_key}."
    
    return status


def get_dataframe_from_session_or_csv(ticker, variant, statement_key, session=None, base_dir='data'):
    """
    Attempt to get financial data from session, or fall back to CSV file.
    
    Args:
        ticker (str): Stock ticker symbol
        variant (str): 'annual' or 'quarterly'
        statement_key (str): 'income', 'balance', or 'cashflow'
        session (dict, optional): Flask session object
        base_dir (str): Base directory for data files
    
    Returns:
        tuple: (DataFrame or None, error_message, info_message)
    """
    session_key = f"{statement_key}_{variant}_df_json"
    df = None
    error_message = None
    info_message = None

    # Try to get data from session
    if session and session_key in session:
        try:
            df_json_str = session.get(session_key)
            if df_json_str:
                df = pd.read_json(df_json_str, orient='split', convert_dates=['index'])
                if not isinstance(df.index, pd.DatetimeIndex):
                    df.index = pd.to_datetime(df.index, errors='coerce')
                df = df.sort_index()
                if not df.empty:
                    info_message = f"Data for {statement_key} ({variant}) loaded from session."
                else:
                    df = None
                    info_message = f"Data for {statement_key} ({variant}) from session is empty. Trying CSV."
            else:
                if session:
                    session.pop(session_key, None)
                info_message = f"Invalid data in session for {statement_key} ({variant}). Trying CSV."
        except Exception as e:
            error_message = f"Error loading {statement_key} ({variant}) from session: {e}. Trying CSV."
            if session:
                session.pop(session_key, None)
            df = None

    # If we couldn't get data from session, try CSV file
    if df is None:
        file_path = get_statement_file_path(ticker, statement_key, variant, base_dir)
        if os.path.exists(file_path):
            try:
                df = pd.read_csv(file_path, index_col=0)
                if not isinstance(df.index, pd.DatetimeIndex):
                    df.index = pd.to_datetime(df.index, errors='coerce')
                df = df[df.index.notna()]
                df = df.sort_index()

                if not df.empty:
                    loaded_from_csv_msg = f"Data for {statement_key} ({variant}) loaded from CSV: {os.path.basename(file_path)}"
                    info_message = f"{info_message} {loaded_from_csv_msg}".strip() if info_message else loaded_from_csv_msg
                    if statement_key == 'income' and session:
                        session[session_key] = df.to_json(orient='split', date_format='iso')
                else:
                    empty_csv_msg = f"CSV file for {statement_key} ({variant}) is empty."
                    info_message = f"{info_message} {empty_csv_msg}".strip() if info_message else empty_csv_msg
                    df = None
            except Exception as e:
                csv_error_msg = f"Error reading CSV {os.path.basename(file_path)} for {statement_key} ({variant}): {e}"
                error_message = f"{error_message} {csv_error_msg}".strip() if error_message else csv_error_msg
                df = None
        elif not error_message:
            file_not_found_msg = f"CSV file for {statement_key} ({variant}) not found for {ticker}."
            error_message = file_not_found_msg
    
    return df, error_message, info_message


def get_statement_file_path(ticker, statement_type, period_type, base_dir='data'):
    """
    Get the path for a specific financial statement file.
    
    Args:
        ticker (str): Stock ticker symbol
        statement_type (str): Type of statement ('income', 'balance', 'cashflow')
        period_type (str): Period type ('annual', 'quarterly')
        base_dir (str): Base directory for data storage
    
    Returns:
        str: Path to the statement file
    """
    statement_names = {
        'income': 'Income_Statement',
        'balance': 'Balance_Sheet',
        'cashflow': 'Cash_Flow_Statement',
    }
    
    statement_name = statement_names.get(statement_type, f'Unknown_{statement_type}')
    return os.path.join(base_dir, ticker, f'{ticker}_{statement_name}_{period_type}.csv')
