"""Tests for the financial statements module."""

import pytest
import os
import pandas as pd
from unittest.mock import patch, MagicMock, mock_open

try:
    from modules.financial_statements import (
        download_financial_statements,
        save_financial_statements,
        get_dataframe_from_session_or_csv,
        get_statement_file_path
    )
except ImportError:
    # Define mocks for testing if module not available
    def download_financial_statements(ticker_symbol, market='us'):
        """Mock download_financial_statements function."""
        return {}
    
    def save_financial_statements(financial_data, ticker, base_dir='data'):
        """Mock save_financial_statements function."""
        return {}
    
    def get_dataframe_from_session_or_csv(ticker, variant, statement_key, session=None, base_dir='data'):
        """Mock get_dataframe_from_session_or_csv function."""
        return None, "Mock error", "Mock info"
    
    def get_statement_file_path(ticker, statement_type, period_type, base_dir='data'):
        """Mock get_statement_file_path function."""
        return os.path.join(base_dir, ticker, f'{ticker}_{statement_type}_{period_type}.csv')


def test_get_statement_file_path():
    """Test generating file paths for financial statements."""
    # Test various statement types
    income_path = get_statement_file_path('AAPL', 'income', 'annual', 'test_dir')
    assert income_path == os.path.join('test_dir', 'AAPL', 'AAPL_Income_Statement_annual.csv')
    
    balance_path = get_statement_file_path('MSFT', 'balance', 'quarterly', 'test_dir')
    assert balance_path == os.path.join('test_dir', 'MSFT', 'MSFT_Balance_Sheet_quarterly.csv')
    
    cashflow_path = get_statement_file_path('GOOG', 'cashflow', 'annual', 'test_dir')
    assert cashflow_path == os.path.join('test_dir', 'GOOG', 'GOOG_Cash_Flow_Statement_annual.csv')
    
    # Test with unknown statement type
    unknown_path = get_statement_file_path('AAPL', 'unknown', 'annual', 'test_dir')
    assert unknown_path == os.path.join('test_dir', 'AAPL', 'AAPL_Unknown_unknown_annual.csv')


@patch('modules.financial_statements.ensure_directory_exists')
@patch('builtins.open', new_callable=mock_open)
@patch('pandas.DataFrame.to_csv')
def test_save_financial_statements_success(mock_to_csv, mock_file, mock_ensure_dir):
    """Test saving financial statements successfully."""
    # Create mock data
    mock_df = pd.DataFrame({
        'Revenue': [100, 200, 300],
        'Net Income': [10, 20, 30]
    }, index=pd.date_range('2020-01-01', periods=3, freq='Y'))
    
    financial_data = {
        'income_annual': mock_df,
        'balance_annual': mock_df,
        'cashflow_annual': mock_df,
        'income_quarterly': mock_df,
        'balance_quarterly': mock_df,
        'cashflow_quarterly': mock_df
    }
    
    # Call the function
    status = save_financial_statements(financial_data, 'AAPL', 'test_dir')
    
    # Assertions
    assert mock_ensure_dir.call_count == 1
    assert mock_to_csv.call_count == 6  # 6 dataframes saved
    
    # Verify status dictionary contains success messages
    assert all('Saved:' in msg for msg in status.values())
    assert len(status) == 6


@patch('modules.financial_statements.ensure_directory_exists')
@patch('pandas.DataFrame.to_csv', side_effect=Exception("Test error"))
def test_save_financial_statements_error(mock_to_csv, mock_ensure_dir):
    """Test saving financial statements with error."""
    # Create mock data with one valid DataFrame
    mock_df = pd.DataFrame({
        'Revenue': [100, 200, 300],
        'Net Income': [10, 20, 30]
    }, index=pd.date_range('2020-01-01', periods=3, freq='Y'))
    
    financial_data = {
        'income_annual': mock_df,
        'balance_annual': {"Error": "NoDataFound", "Details": "Test error details"},
        'cashflow_annual': pd.DataFrame()  # Empty DataFrame
    }
    
    # Call the function
    status = save_financial_statements(financial_data, 'AAPL', 'test_dir')
    
    # Assertions
    assert mock_ensure_dir.call_count == 1
    assert mock_to_csv.call_count == 1  # Only one DataFrame attempted to save
    
    # Check status for different scenarios
    assert "Error saving CSV" in status['income_annual']  # Error on save
    assert "Download Error" in status['balance_annual']  # Error dict
    assert "No data or empty data" in status['cashflow_annual']  # Empty DataFrame


@patch('os.path.exists', return_value=True)
@patch('pandas.read_csv')
def test_get_dataframe_from_session_or_csv_from_csv(mock_read_csv, mock_exists):
    """Test getting DataFrame from CSV when session data is not available."""
    # Setup mock DataFrame return value
    mock_df = pd.DataFrame({
        'Revenue': [100, 200, 300],
        'Net Income': [10, 20, 30]
    }, index=pd.date_range('2020-01-01', periods=3, freq='Y'))
    mock_read_csv.return_value = mock_df
    
    # Call the function with no session data
    df, error, info = get_dataframe_from_session_or_csv('AAPL', 'annual', 'income', None, 'test_dir')
    
    # Assertions
    assert df is not None
    assert df.equals(mock_df)
    assert error is None
    assert "loaded from CSV" in info


@patch('os.path.exists', return_value=True)
@patch('pandas.read_csv', side_effect=Exception("CSV read error"))
def test_get_dataframe_from_session_or_csv_error(mock_read_csv, mock_exists):
    """Test handling errors when reading CSV file."""
    # Call the function
    df, error, info = get_dataframe_from_session_or_csv('AAPL', 'annual', 'income', None, 'test_dir')
    
    # Assertions
    assert df is None
    assert "Error reading CSV" in error
    assert info is None


@patch('os.path.exists', return_value=False)
def test_get_dataframe_from_session_or_csv_file_not_found(mock_exists):
    """Test handling file not found scenario."""
    # Call the function
    df, error, info = get_dataframe_from_session_or_csv('AAPL', 'annual', 'income', None, 'test_dir')
    
    # Assertions
    assert df is None
    assert "not found" in error
    assert info is None


def test_get_dataframe_from_session_or_csv_from_session():
    """Test getting DataFrame from session."""
    # Create mock session and DataFrame
    mock_df = pd.DataFrame({
        'Revenue': [100, 200, 300],
        'Net Income': [10, 20, 30]
    }, index=pd.date_range('2020-01-01', periods=3, freq='Y'))
    
    mock_session = {
        'income_annual_df_json': mock_df.to_json(orient='split', date_format='iso')
    }
    
    # Call the function
    df, error, info = get_dataframe_from_session_or_csv('AAPL', 'annual', 'income', mock_session, 'test_dir')
    
    # Assertions
    assert df is not None
    assert error is None
    assert "loaded from session" in info


@patch('simfin.load_income')
@patch('simfin.load_balance')
@patch('simfin.load_cashflow')
@patch('time.sleep')
def test_download_financial_statements_success(mock_sleep, mock_load_cashflow, mock_load_balance, mock_load_income):
    """Test downloading financial statements successfully."""
    # Set up mock data
    mock_df = pd.DataFrame({
        'Revenue': [100, 200, 300],
        'Net Income': [10, 20, 30]
    }, index=pd.MultiIndex.from_tuples([('AAPL', pd.Timestamp('2020-01-01')),
                                        ('AAPL', pd.Timestamp('2021-01-01')),
                                        ('AAPL', pd.Timestamp('2022-01-01'))],
                                      names=['Ticker', 'Date']))
    
    # Configure mocks to return the same DataFrame for all statement types
    mock_load_income.return_value = mock_df
    mock_load_balance.return_value = mock_df
    mock_load_cashflow.return_value = mock_df
    
    # Call the function
    results = download_financial_statements('AAPL')
    
    # Assertions
    assert mock_sleep.call_count == 6  # Called for each statement type and variant
    assert len(results) == 6  # 3 statement types x 2 variants
    
    # Verify all results are DataFrames
    assert all(isinstance(df, pd.DataFrame) for df in results.values())


@patch('simfin.load_income', return_value=None)
@patch('simfin.load_balance', return_value=None)
@patch('simfin.load_cashflow', return_value=None)
@patch('time.sleep')
def test_download_financial_statements_load_failed(mock_sleep, *args):
    """Test handling load failures when downloading financial statements."""
    # Call the function
    results = download_financial_statements('AAPL')
    
    # Assertions
    assert mock_sleep.call_count == 6  # Called for each statement type and variant
    assert len(results) == 6  # 3 statement types x 2 variants
    
    # Verify all results contain error information
    assert all("Error" in result for result in results.values())
    assert all("LoadFailed" in result["Error"] for result in results.values())


@patch('simfin.load_income')
@patch('simfin.load_balance')
@patch('simfin.load_cashflow')
@patch('time.sleep')
def test_download_financial_statements_ticker_not_found(mock_sleep, mock_load_cashflow, mock_load_balance, mock_load_income):
    """Test handling when ticker is not found in the data."""
    # Set up mock data with different ticker
    mock_df = pd.DataFrame({
        'Revenue': [100, 200, 300],
        'Net Income': [10, 20, 30]
    }, index=pd.MultiIndex.from_tuples([('MSFT', pd.Timestamp('2020-01-01')),
                                        ('MSFT', pd.Timestamp('2021-01-01')),
                                        ('MSFT', pd.Timestamp('2022-01-01'))],
                                      names=['Ticker', 'Date']))
    
    # Configure mocks to return DataFrame without the requested ticker
    mock_load_income.return_value = mock_df
    mock_load_balance.return_value = mock_df
    mock_load_cashflow.return_value = mock_df
    
    # Call the function for a different ticker
    results = download_financial_statements('AAPL')
    
    # Assertions
    assert mock_sleep.call_count == 6  # Called for each statement type and variant
    assert len(results) == 6  # 3 statement types x 2 variants
    
    # Verify all results contain error information about ticker not found
    assert all("Error" in result for result in results.values())
    assert all(result["Error"] == "NoDataFound" for result in results.values())
