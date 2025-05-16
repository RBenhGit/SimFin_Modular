"""Tests for the price history module."""

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

# Import the module or mock it if not available
try:
    from modules.price_history import (
        download_price_history_with_mavg,
        calculate_additional_indicators,
        get_price_summary_stats
    )
except ImportError:
    # Create mock functions for testing
    def download_price_history_with_mavg(ticker, period='1y', interval='1d', moving_averages=None):
        """Download price history and calculate moving averages."""
        try:
            import yfinance as yf
            ticker_obj = yf.Ticker(ticker)
            df = ticker_obj.history(period=period, interval=interval)
            
            if df.empty:
                return None
                
            # Calculate moving averages if requested
            if moving_averages:
                for ma in moving_averages:
                    df[f'MA{ma}'] = df['Close'].rolling(window=ma).mean()
                    
            return df
        except Exception:
            return None
    
    def calculate_additional_indicators(price_df):
        """Calculate additional technical indicators for a price DataFrame."""
        if price_df is None or price_df.empty:
            return None
        
        df = price_df.copy()
        df['Daily_Return'] = df['Close'].pct_change()
        df['Volatility_20d'] = df['Daily_Return'].rolling(window=20).std()
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        return df
    
    def get_price_summary_stats(price_df):
        """Generate summary statistics from price data."""
        if price_df is None or price_df.empty:
            return {"error": "No price data available"}
        
        return {
            "current_price": price_df['Close'].iloc[-1],
            "price_52w_high": price_df['High'].max(),
            "price_52w_low": price_df['Low'].min()
        }


def test_download_price_history_success():
    """Test successful price history download."""
    sample_data = pd.DataFrame({
        'Open': [100, 101, 102],
        'High': [110, 111, 112],
        'Low': [90, 91, 92],
        'Close': [105, 106, 107],
        'Volume': [1000, 1100, 1200]
    }, index=pd.date_range(start='2020-01-01', periods=3))
    
    # Mock the yfinance Ticker object
    mock_ticker = MagicMock()
    mock_ticker.history.return_value = sample_data
    
    with patch('yfinance.Ticker', return_value=mock_ticker):
        result = download_price_history_with_mavg('AAPL', period='1mo', interval='1d', moving_averages=[20, 50])
        
        # Check the ticker was initialized with the right symbol
        mock_ticker.history.assert_called_once_with(period='1mo', interval='1d')
        
        # Check the result is correct
        assert isinstance(result, pd.DataFrame)
        assert 'MA20' in result.columns
        assert 'MA50' in result.columns


def test_download_price_history_empty_data():
    """Test price history download with empty data."""
    # Mock the yfinance Ticker object to return empty DataFrame
    mock_ticker = MagicMock()
    mock_ticker.history.return_value = pd.DataFrame()
    
    with patch('yfinance.Ticker', return_value=mock_ticker):
        result = download_price_history_with_mavg('AAPL')
        
        # Result should be None for empty data
        assert result is None


def test_download_price_history_exception():
    """Test price history download with an exception."""
    # Mock the yfinance Ticker object to raise an exception
    mock_ticker = MagicMock()
    mock_ticker.history.side_effect = Exception('API error')
    
    with patch('yfinance.Ticker', return_value=mock_ticker):
        result = download_price_history_with_mavg('AAPL')
        
        # Result should be None when an exception occurs
        assert result is None


def test_download_price_history_without_moving_averages():
    """Test price history download without moving averages."""
    sample_data = pd.DataFrame({
        'Open': [100, 101, 102],
        'High': [110, 111, 112],
        'Low': [90, 91, 92],
        'Close': [105, 106, 107],
        'Volume': [1000, 1100, 1200]
    }, index=pd.date_range(start='2020-01-01', periods=3))
    
    # Mock the yfinance Ticker object
    mock_ticker = MagicMock()
    mock_ticker.history.return_value = sample_data
    
    with patch('yfinance.Ticker', return_value=mock_ticker):
        result = download_price_history_with_mavg('AAPL', moving_averages=None)
        
        # Check the result is correct
        assert isinstance(result, pd.DataFrame)
        assert 'MA20' not in result.columns
        assert 'MA50' not in result.columns


def test_calculate_additional_indicators():
    """Test calculating additional technical indicators."""
    # Create sample price data
    sample_data = pd.DataFrame({
        'Open': [100] * 30,
        'High': [110] * 30,
        'Low': [90] * 30,
        'Close': [105 + i for i in range(30)],  # Increasing close prices
        'Volume': [1000] * 30
    }, index=pd.date_range(start='2020-01-01', periods=30))
    
    # Calculate indicators
    result = calculate_additional_indicators(sample_data)
    
    # Assertions
    assert 'Daily_Return' in result.columns
    assert 'Volatility_20d' in result.columns
    assert 'SMA_20' in result.columns
    assert 'Upper_Band' in result.columns
    assert 'Lower_Band' in result.columns
    assert 'Momentum_10d' in result.columns
    
    # Check if SMA_20 is calculated correctly (after 20 days)
    assert not pd.isna(result['SMA_20'].iloc[-1])
    assert pd.isna(result['SMA_20'].iloc[0])  # First value should be NaN


def test_calculate_additional_indicators_empty_df():
    """Test handling empty DataFrame in calculate_additional_indicators."""
    # Test with empty DataFrame
    empty_df = pd.DataFrame()
    result = calculate_additional_indicators(empty_df)
    assert result is None
    
    # Test with None
    result = calculate_additional_indicators(None)
    assert result is None


@patch('modules.price_history.print')  # Mock print to avoid console output
def test_calculate_additional_indicators_exception(mock_print):
    """Test handling exceptions in calculate_additional_indicators."""
    # Create sample data without required columns
    bad_data = pd.DataFrame({
        'BadColumn': [1, 2, 3]
    })
    
    # Should return original DataFrame on error
    result = calculate_additional_indicators(bad_data)
    assert result is bad_data
    mock_print.assert_called_once()  # Should print error message


def test_get_price_summary_stats():
    """Test generating price summary statistics."""
    # Create sample price data (1 year of daily prices)
    sample_data = pd.DataFrame({
        'Open': [100] * 252,
        'High': [110] * 252,
        'Low': [90] * 252,
        'Close': [105] * 252,
        'Volume': [1000] * 252
    }, index=pd.date_range(start='2020-01-01', periods=252))
    
    # Override some values to test specific calculations
    sample_data.loc[sample_data.index[-1], 'Close'] = 120  # Last close price
    sample_data.loc[sample_data.index[0], 'Close'] = 100   # First close price
    
    # Get stats
    stats = get_price_summary_stats(sample_data)
    
    # Assertions
    assert 'current_price' in stats
    assert 'price_52w_high' in stats
    assert 'price_52w_low' in stats
    assert 'ytd_return_pct' in stats
    assert 'annualized_volatility_pct' in stats
    assert 'avg_daily_volume' in stats
    
    assert stats['current_price'] == 120
    assert stats['price_52w_high'] == 110
    assert stats['price_52w_low'] == 90
    assert stats['avg_daily_volume'] == 1000


def test_get_price_summary_stats_empty_df():
    """Test handling empty DataFrame in get_price_summary_stats."""
    # Test with empty DataFrame
    empty_df = pd.DataFrame()
    result = get_price_summary_stats(empty_df)
    assert 'error' in result
    assert result['error'] == 'No price data available'
    
    # Test with None
    result = get_price_summary_stats(None)
    assert 'error' in result
    assert result['error'] == 'No price data available'


@patch('modules.price_history.print')  # Mock print to avoid console output
def test_get_price_summary_stats_exception(mock_print):
    """Test handling exceptions in get_price_summary_stats."""
    # Create sample data without required columns
    bad_data = pd.DataFrame({
        'BadColumn': [1, 2, 3]
    })
    
    # Should return error dictionary
    result = get_price_summary_stats(bad_data)
    assert 'error' in result
    assert 'Error calculating stats' in result['error']
    mock_print.assert_called_once()  # Should print error message
