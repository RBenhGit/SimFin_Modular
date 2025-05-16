"""Tests for helper utility functions."""

import os
import tempfile
import pytest
from utils.helpers import (
    get_statement_file_path,
    get_api_key_status_for_display,
    ensure_directory_exists,
    format_number_for_display
)


def test_get_statement_file_path():
    """Test getting a statement file path."""
    path = get_statement_file_path('AAPL', 'income', 'annual', 'test_data')
    assert path == os.path.join('test_data', 'AAPL', 'AAPL_Income_Statement_annual.csv')
    
    path = get_statement_file_path('MSFT', 'balance', 'quarterly', 'data')
    assert path == os.path.join('data', 'MSFT', 'MSFT_Balance_Sheet_quarterly.csv')
    
    # Test with unknown statement type
    path = get_statement_file_path('GOOG', 'unknown', 'annual', 'data')
    assert path == os.path.join('data', 'GOOG', 'GOOG_Unknown_unknown_annual.csv')


def test_get_api_key_status_for_display():
    """Test getting API key status display text."""
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
        # Test with a custom API key
        temp_file.write('my_custom_key')
        temp_file.flush()
        status = get_api_key_status_for_display(temp_file.name)
        assert "מותאם אישית" in status
        
        # Test with 'free' API key
        temp_file.seek(0)
        temp_file.truncate()
        temp_file.write('free')
        temp_file.flush()
        status = get_api_key_status_for_display(temp_file.name)
        assert "free" in status
        
    # Clean up
    os.unlink(temp_file.name)
    
    # Test with non-existent file
    status = get_api_key_status_for_display('nonexistent_file.txt')
    assert "free" in status


def test_ensure_directory_exists():
    """Test ensuring a directory exists."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Test with a file path
        file_path = os.path.join(temp_dir, 'subdir', 'test_file.txt')
        ensure_directory_exists(file_path)
        assert os.path.exists(os.path.dirname(file_path))
        
        # Test with a directory path
        dir_path = os.path.join(temp_dir, 'another_subdir')
        ensure_directory_exists(dir_path)
        assert os.path.exists(dir_path)


def test_format_number_for_display():
    """Test formatting numbers for display."""
    # Test with regular number
    formatted = format_number_for_display(1234.5678)
    assert formatted == "1,234.57"
    
    # Test with prefix and suffix
    formatted = format_number_for_display(1234.5678, prefix='$', suffix='%')
    assert formatted == "$1,234.57%"
    
    # Test with None
    formatted = format_number_for_display(None)
    assert formatted == "N/A"
    
    # Test with non-numeric value
    formatted = format_number_for_display("not a number")
    assert formatted == "not a number"
