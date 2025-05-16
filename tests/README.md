# SimFin Analyzer Test Suite

## Overview

This directory contains the test suite for the SimFin Analyzer application. The tests are designed to validate the functionality of each module and ensure that the application works as expected.

## Test Structure

The test suite is organized to mirror the application structure:

```
tests/
├── test_app.py                 # Tests for the main app module
├── test_modules/               # Tests for application modules
│   ├── test_chart_creator.py   # Tests for chart creation functions
│   ├── test_data_loader.py     # Tests for data loading utilities
│   ├── test_financial_statements.py # Tests for financial statement handling
│   └── test_price_history.py   # Tests for price history retrieval
├── test_routes/                # Tests for route handlers
│   ├── test_graphs.py          # Tests for graph routes
│   ├── test_home.py            # Tests for home routes
│   └── test_valuations.py      # Tests for valuation routes
└── test_utils/                 # Tests for utility functions
    ├── test_config_loader.py   # Tests for configuration loading
    └── test_helpers.py         # Tests for helper functions
```

## Running Tests

To run the tests, use the provided batch file or run pytest directly:

```bash
# Using the provided batch file
run_tests.bat

# Or using pytest directly
python -m pytest
```

To run a specific test file:

```bash
python -m pytest tests/test_app.py
```

To run a specific test:

```bash
python -m pytest tests/test_app.py::test_create_app_registers_blueprints
```

## Testing Approach

The tests utilize several approaches:

1. **Unit Tests**: Test individual functions and methods in isolation
2. **Integration Tests**: Test the interaction between components
3. **Mocking**: Simulate external dependencies like the SimFin API
4. **Fixtures**: Provide reusable test data and configuration

## Key Fixtures

- `app`: Creates a Flask application for testing
- `client`: Provides a test client for making requests
- `sample_price_data`: Generates sample price history data
- `sample_financial_data`: Generates sample financial statement data
- `mock_api_key_file`: Creates a mock API key file
- `mock_config_file`: Creates a mock configuration file

## Test Summary Plugin

The test suite includes a custom plugin (`test_summary_plugin.py`) that provides a more readable summary of test results, including:

- Number of passed, failed, and error tests
- Details about each failure
- Clear visual indicators of test status

## Coverage Reporting

The test suite also generates coverage reports to help identify untested code. After running the tests, you can find HTML coverage reports in the `htmlcov` directory.

## Writing New Tests

When adding new functionality to the application, follow these guidelines for writing tests:

1. Create tests in the appropriate directory based on the module being tested
2. Use fixtures to avoid repetition
3. Mock external dependencies
4. Test both success and failure cases
5. Follow the existing naming convention: `test_<function_name>_<scenario>`

## Common Issues and Solutions

- **Templates Not Found**: Ensure that the Flask app is configured with the correct template folder
- **Import Errors**: Use try/except blocks to handle modules that might not be available
- **SimFin API Errors**: Mock the SimFin API responses to avoid actual API calls
- **Session Data**: Use `client.session_transaction()` to set or verify session data
