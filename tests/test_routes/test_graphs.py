"""Tests for graphs route module."""

import pytest
import json
from unittest.mock import patch, MagicMock
import pandas as pd

# Import modules or simulate them if not available
try:
    from modules.routes import graphs
except ImportError:
    # This will be used only for testing and won't affect real implementation
    graphs = MagicMock()


def test_route_graphs_annual_no_ticker(client):
    """Test the annual graphs route with no ticker."""
    response = client.get('/graphs/annual')
    
    assert response.status_code == 302  # Redirect to home
    # Accept either the full URL or relative path
    assert response.location in ['http://localhost/', '/']


def test_route_graphs_annual_with_ticker(client, sample_financial_data):
    """Test the annual graphs route with a ticker."""
    with client.session_transaction() as sess:
        sess['current_ticker'] = 'AAPL'
    
    with patch('modules.routes.graphs.get_dataframe_from_session_or_csv') as mock_get_df, \
         patch('modules.routes.graphs.create_timeseries_chart') as mock_create_chart, \
         patch('modules.routes.graphs.get_api_key_status_for_display') as mock_get_status:
        
        mock_get_df.return_value = (sample_financial_data, None, "Data loaded successfully")
        mock_create_chart.return_value = {"data": [], "layout": {}}
        mock_get_status.return_value = "Test API Key Status"
        
        response = client.get('/graphs/annual')
        
        assert response.status_code == 200
        assert b'AAPL' in response.data
        # Check for content that would be present in the rendered page
        # rather than the template name
        assert b'SimFin Analyzer' in response.data
        
        mock_get_df.assert_called_once()
        assert mock_create_chart.call_count >= 1  # At least one chart should be created


def test_route_graphs_annual_with_missing_revenue(client, sample_financial_data):
    """Test the annual graphs route with missing revenue column."""
    with client.session_transaction() as sess:
        sess['current_ticker'] = 'AAPL'
    
    # Remove the Revenue column
    modified_data = sample_financial_data.drop(columns=['Revenue'])
    
    with patch('modules.routes.graphs.get_dataframe_from_session_or_csv') as mock_get_df, \
         patch('modules.routes.graphs.create_timeseries_chart') as mock_create_chart, \
         patch('modules.routes.graphs.get_api_key_status_for_display') as mock_get_status:
        
        mock_get_df.return_value = (modified_data, None, "Data loaded successfully")
        # First chart creation fails with an error
        mock_create_chart.side_effect = [
            {"error": "Column 'Revenue' not found in DataFrame"},
            {"data": [], "layout": {}}  # Second call (Net Income) succeeds
        ]
        mock_get_status.return_value = "Test API Key Status"
        
        response = client.get('/graphs/annual')
        
        assert response.status_code == 200
        assert b'not found' in response.data


def test_route_graphs_quarterly_no_ticker(client):
    """Test the quarterly graphs route with no ticker."""
    response = client.get('/graphs/quarterly')
    
    assert response.status_code == 302  # Redirect to home
    # Accept either the full URL or relative path
    assert response.location in ['http://localhost/', '/']


def test_route_graphs_quarterly_with_ticker(client, sample_financial_data):
    """Test the quarterly graphs route with a ticker."""
    with client.session_transaction() as sess:
        sess['current_ticker'] = 'AAPL'
    
    with patch('modules.routes.graphs.get_dataframe_from_session_or_csv') as mock_get_df, \
         patch('modules.routes.graphs.create_timeseries_chart') as mock_create_chart, \
         patch('modules.routes.graphs.get_api_key_status_for_display') as mock_get_status:
        
        mock_get_df.return_value = (sample_financial_data, None, "Data loaded successfully")
        mock_create_chart.return_value = {"data": [], "layout": {}}
        mock_get_status.return_value = "Test API Key Status"
        
        response = client.get('/graphs/quarterly')
        
        assert response.status_code == 200
        assert b'AAPL' in response.data
        # Check for content that would be present in the rendered page
        # rather than the template name
        assert b'SimFin Analyzer' in response.data
        
        mock_get_df.assert_called_once()
        assert mock_create_chart.call_count >= 1  # At least one chart should be created


def test_route_graphs_quarterly_with_no_data(client):
    """Test the quarterly graphs route with no data available."""
    with client.session_transaction() as sess:
        sess['current_ticker'] = 'AAPL'
    
    with patch('modules.routes.graphs.get_dataframe_from_session_or_csv') as mock_get_df, \
         patch('modules.routes.graphs.get_api_key_status_for_display') as mock_get_status:
        
        mock_get_df.return_value = (None, "No data available", None)
        mock_get_status.return_value = "Test API Key Status"
        
        response = client.get('/graphs/quarterly')
        
        assert response.status_code == 200
        assert b'No data available' in response.data


def test_route_graphs_with_session_data(client, sample_financial_data):
    """Test the graphs route using data from session."""
    session_data = sample_financial_data.to_json(orient='split', date_format='iso')
    
    with client.session_transaction() as sess:
        sess['current_ticker'] = 'AAPL'
        sess['income_annual_df_json'] = session_data
    
    with patch('modules.routes.graphs.get_dataframe_from_session_or_csv') as mock_get_df, \
         patch('modules.routes.graphs.create_timeseries_chart') as mock_create_chart, \
         patch('modules.routes.graphs.get_api_key_status_for_display') as mock_get_status:
        
        # Make mock_get_df return the data as if it came from session
        mock_get_df.return_value = (sample_financial_data, None, "Data loaded from session")
        mock_create_chart.return_value = {"data": [], "layout": {}}
        mock_get_status.return_value = "Test API Key Status"
        
        response = client.get('/graphs/annual')
        
        assert response.status_code == 200
        assert b'Data loaded from session' in response.data
