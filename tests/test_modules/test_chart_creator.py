"""Tests for the chart creator module."""

import pytest
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from unittest.mock import patch, MagicMock

try:
    from modules.chart_creator import create_timeseries_chart, create_candlestick_chart_with_mavg
except ImportError:
    # Mock chart functions if module not available
    def create_timeseries_chart(df, y_column, title, x_column_name_in_df=None, y_axis_title=None, chart_type='bar'):
        """Mock create_timeseries_chart function."""
        return {"data": [], "layout": {}}
    
    def create_candlestick_chart_with_mavg(df_prices, ticker_symbol, moving_averages_to_plot=None):
        """Mock create_candlestick_chart_with_mavg function."""
        return {"data": [], "layout": {}}


@patch('plotly.express.bar')
@patch('plotly.express.line')
def test_create_timeseries_chart_bar(mock_line, mock_bar):
    """Test creating a bar chart."""
    # Set up mock figure and return value
    mock_fig = MagicMock()
    mock_fig.data = [{"type": "bar"}]
    mock_fig.layout = {"title": "Test Chart"}
    mock_bar.return_value = mock_fig
    
    # Create test data
    dates = pd.date_range(start='2020-01-01', periods=5, freq='M')
    df = pd.DataFrame({
        'Revenue': [100, 200, 300, 400, 500],
        'Net Income': [10, 20, 30, 40, 50]
    }, index=dates)
    
    # Call the function with bar chart type
    result = create_timeseries_chart(df, 'Revenue', 'Revenue Chart', chart_type='bar')
    
    # Assertions
    mock_bar.assert_called_once()
    assert "data" in result
    assert "layout" in result
    assert result["data"] == [{"type": "bar"}]
    assert result["layout"] == {"title": "Test Chart"}


@patch('plotly.express.bar')
@patch('plotly.express.line')
def test_create_timeseries_chart_line(mock_line, mock_bar):
    """Test creating a line chart."""
    # Set up mock figure and return value
    mock_fig = MagicMock()
    mock_fig.data = [{"type": "line"}]
    mock_fig.layout = {"title": "Test Chart"}
    mock_line.return_value = mock_fig
    
    # Create test data
    dates = pd.date_range(start='2020-01-01', periods=5, freq='M')
    df = pd.DataFrame({
        'Revenue': [100, 200, 300, 400, 500],
        'Net Income': [10, 20, 30, 40, 50]
    }, index=dates)
    
    # Call the function with line chart type
    result = create_timeseries_chart(df, 'Revenue', 'Revenue Chart', chart_type='line')
    
    # Assertions
    mock_line.assert_called_once()
    assert "data" in result
    assert "layout" in result
    assert result["data"] == [{"type": "line"}]
    assert result["layout"] == {"title": "Test Chart"}


def test_create_timeseries_chart_empty_df():
    """Test chart creation with empty DataFrame."""
    df = pd.DataFrame()
    result = create_timeseries_chart(df, 'Revenue', 'Revenue Chart')
    
    assert "error" in result
    assert "empty" in result["error"].lower()


def test_create_timeseries_chart_column_not_found():
    """Test chart creation with non-existent column."""
    dates = pd.date_range(start='2020-01-01', periods=5, freq='M')
    df = pd.DataFrame({
        'Revenue': [100, 200, 300, 400, 500]
    }, index=dates)
    
    result = create_timeseries_chart(df, 'NonExistentColumn', 'Test Chart')
    
    assert "error" in result
    assert "not found" in result["error"].lower()


def test_create_timeseries_chart_non_numeric_data():
    """Test chart creation with non-numeric data."""
    dates = pd.date_range(start='2020-01-01', periods=5, freq='M')
    df = pd.DataFrame({
        'Revenue': ['a', 'b', 'c', 'd', 'e']  # Non-numeric data
    }, index=dates)
    
    result = create_timeseries_chart(df, 'Revenue', 'Revenue Chart')
    
    assert "error" in result
    assert "no valid numeric data" in result["error"].lower()


def test_create_timeseries_chart_unsupported_type():
    """Test chart creation with unsupported chart type."""
    dates = pd.date_range(start='2020-01-01', periods=5, freq='M')
    df = pd.DataFrame({
        'Revenue': [100, 200, 300, 400, 500]
    }, index=dates)
    
    result = create_timeseries_chart(df, 'Revenue', 'Revenue Chart', chart_type='unsupported')
    
    assert "error" in result
    assert "unsupported chart type" in result["error"].lower()


def test_create_timeseries_chart_with_x_column():
    """Test chart creation with specified x column."""
    with patch('plotly.express.bar') as mock_bar:
        mock_fig = MagicMock()
        mock_fig.data = [{"type": "bar"}]
        mock_fig.layout = {"title": "Test Chart"}
        mock_bar.return_value = mock_fig
        
        df = pd.DataFrame({
            'Date': pd.date_range(start='2020-01-01', periods=5, freq='M'),
            'Revenue': [100, 200, 300, 400, 500],
            'Net Income': [10, 20, 30, 40, 50]
        })
        
        result = create_timeseries_chart(df, 'Revenue', 'Revenue Chart', x_column_name_in_df='Date')
        
        mock_bar.assert_called_once()
        assert "data" in result
        assert "layout" in result


@patch('plotly.graph_objects.Figure')
@patch('plotly.graph_objects.Candlestick')
@patch('plotly.graph_objects.Scatter')
def test_create_candlestick_chart(mock_scatter, mock_candlestick, mock_figure):
    """Test creating a candlestick chart."""
    # Set up mock figure and return value
    mock_fig = MagicMock()
    mock_fig.data = [{"type": "candlestick"}]
    mock_fig.layout = {"title": "Test Candlestick Chart"}
    mock_figure.return_value = mock_fig
    
    # Create test price data
    dates = pd.date_range(start='2020-01-01', periods=5, freq='D')
    df = pd.DataFrame({
        'Open': [100, 101, 102, 103, 104],
        'High': [110, 111, 112, 113, 114],
        'Low': [90, 91, 92, 93, 94],
        'Close': [105, 106, 107, 108, 109],
        'MA20': [103, 104, 105, 106, 107],
        'MA50': [101, 102, 103, 104, 105]
    }, index=dates)
    
    # Call the function
    result = create_candlestick_chart_with_mavg(df, 'AAPL', moving_averages_to_plot=['MA20', 'MA50'])
    
    # Assertions
    mock_figure.assert_called_once()
    mock_candlestick.assert_called_once()
    assert mock_scatter.call_count == 2  # Should be called twice for two MAs
    assert "data" in result
    assert "layout" in result
    assert result["data"] == [{"type": "candlestick"}]
    assert result["layout"] == {"title": "Test Candlestick Chart"}


def test_create_candlestick_chart_empty_df():
    """Test candlestick chart creation with empty DataFrame."""
    df = pd.DataFrame()
    result = create_candlestick_chart_with_mavg(df, 'AAPL')
    
    assert "error" in result
    assert "no price data available" in result["error"].lower()


@patch('plotly.graph_objects.Figure')
@patch('plotly.graph_objects.Candlestick')
def test_create_candlestick_chart_no_ma(mock_candlestick, mock_figure):
    """Test creating a candlestick chart without moving averages."""
    # Set up mock figure and return value
    mock_fig = MagicMock()
    mock_fig.data = [{"type": "candlestick"}]
    mock_fig.layout = {"title": "Test Candlestick Chart"}
    mock_figure.return_value = mock_fig
    
    # Create test price data
    dates = pd.date_range(start='2020-01-01', periods=5, freq='D')
    df = pd.DataFrame({
        'Open': [100, 101, 102, 103, 104],
        'High': [110, 111, 112, 113, 114],
        'Low': [90, 91, 92, 93, 94],
        'Close': [105, 106, 107, 108, 109]
    }, index=dates)
    
    # Call the function with no moving averages
    result = create_candlestick_chart_with_mavg(df, 'AAPL')
    
    # Assertions
    mock_figure.assert_called_once()
    mock_candlestick.assert_called_once()
    assert "data" in result
    assert "layout" in result
