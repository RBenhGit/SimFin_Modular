"""Test fixtures and configuration for SimFin Analyzer tests."""

import pytest
import os
import sys
from _pytest.terminal import TerminalReporter

# Include the summary plugin functionality directly in conftest.py
class SummaryReporter:
    """A custom terminal reporter to create a short summary of test results."""

    def __init__(self, config):
        """Initialize the reporter."""
        self.config = config
        self.test_results = {
            'passed': [],
            'failed': [],
            'errors': []
        }
        self.failure_details = {}

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_protocol(self, item, nextitem):
        """Hook into the test run protocol."""
        yield
        
    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self, item, call):
        """Process test reports to gather information."""
        outcome = yield
        report = outcome.get_result()
        
        if report.when == 'call':  # Only process the actual test call (not setup/teardown)
            test_id = item.nodeid
            if report.passed:
                self.test_results['passed'].append(test_id)
            elif report.failed:
                self.test_results['failed'].append(test_id)
                if hasattr(report, 'longrepr'):
                    # Extract the error message (last line of traceback usually contains the error)
                    error_msg = str(report.longrepr).split('\n')[-1] if report.longrepr else "No error message"
                    self.failure_details[test_id] = error_msg
            
    def pytest_terminal_summary(self, terminalreporter, exitstatus, config):
        """Print a custom summary at the end of the test session."""
        # Create a more visually distinct report with clear separation
        separator = "="*80
        
        print("\n\n" + separator)
        print("🔍 SIMFIN ANALYZER TEST SUMMARY REPORT 🔍".center(80))
        print(separator)
        
        # Print passed tests - now with test names for better visibility
        passed_count = len(self.test_results['passed'])
        print(f"\n✅ PASSED: {passed_count} tests")
        if passed_count > 0 and passed_count <= 10:  # Only show names if there are few passed tests
            for i, test_id in enumerate(self.test_results['passed'], 1):
                module_name = test_id.split("::")[0].replace("tests/", "").replace(".py", "")
                test_name = test_id.split("::")[-1]
                print(f"  • {module_name}::{test_name}")
        
        # Print failed tests with reasons
        failed_count = len(self.test_results['failed'])
        if failed_count:
            print(f"\n❌ FAILED: {failed_count} tests")
            for i, test_id in enumerate(self.test_results['failed'], 1):
                module_name = test_id.split("::")[0].replace("tests/", "").replace(".py", "")
                test_name = test_id.split("::")[-1]
                reason = self.failure_details.get(test_id, "Unknown reason")
                print(f"  {i}. {module_name}::{test_name}")
                print(f"     Reason: {reason}")
        
        # Print error tests
        error_count = len(self.test_results['errors'])
        if error_count:
            print(f"\n⚠️ ERRORS: {error_count} tests")
            for i, test_id in enumerate(self.test_results['errors'], 1):
                module_name = test_id.split("::")[0].replace("tests/", "").replace(".py", "")
                test_name = test_id.split("::")[-1] if "::" in test_id else "setup error"
                print(f"  {i}. {module_name}::{test_name}")
        
        # Print overall status with a more prominent indication
        total_tests = sum(len(tests) for tests in self.test_results.values())
        print("\n" + separator)
        if failed_count == 0 and error_count == 0:
            print("✨ STATUS: ALL TESTS PASSED! ✨".center(80))
            print(f"Total: {total_tests} tests completed successfully".center(80))
        else:
            print("📊 STATUS: SOME TESTS FAILED".center(80))
            print(f"Results: {passed_count}/{total_tests} tests passed, {failed_count} failed, {error_count} errors".center(80))
        print(separator + "\n")


def pytest_configure(config):
    """Configure the plugin."""
    # Register the summary reporter
    summary_reporter = SummaryReporter(config)
    config.pluginmanager.register(summary_reporter, 'summary_reporter')
import os
import tempfile
import pandas as pd
import json
from flask import Flask
try:
    import simfin as sf
except ImportError:
    # Mock simfin if not installed
    class MockSimFin:
        def set_api_key(self, key):
            self.api_key = key
        
        def set_data_dir(self, dir_path):
            self.data_dir = dir_path
    
    sf = MockSimFin()

@pytest.fixture
def app():
    """Create and configure a Flask app for testing."""
    import os
    import sys
    
    # Get the project root directory (one level up from tests directory)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Add templates directory for testing
    template_folder = os.path.join(project_root, 'templates')
    
    # Import blueprints conditionally to avoid errors if not installed
    try:
        from modules.routes import home_bp, graphs_bp, valuations_bp
        
        # Create Flask app with proper template folder
        app = Flask(__name__, 
                    template_folder=template_folder,
                    static_folder=os.path.join(project_root, 'static'))
        
        app.config.update({
            'TESTING': True,
            'SECRET_KEY': 'test_key',
            'SERVER_NAME': 'localhost',  # Required for url_for to work in tests
        })
        
        # Register blueprints
        app.register_blueprint(home_bp, url_prefix='/')
        app.register_blueprint(graphs_bp, url_prefix='/graphs')
        app.register_blueprint(valuations_bp, url_prefix='/valuations')
        
        # Create mock for template rendering to avoid actual template rendering
        with app.app_context():
            app.jinja_env.globals.update(
                url_for=lambda endpoint, **kwargs: f"/{endpoint.split('.')[-1]}"
            )
        
    except ImportError:
        # Create a minimal Flask app if modules are not available
        app = Flask(__name__, 
                    template_folder=template_folder,
                    static_folder=os.path.join(project_root, 'static'))
        
        app.config.update({
            'TESTING': True,
            'SECRET_KEY': 'test_key',
            'SERVER_NAME': 'localhost',
        })
    
    # Create a test request context
    with app.test_request_context():
        yield app

@pytest.fixture
def client(app):
    """A test client for the app."""
    with app.test_client() as client:
        # Configure the client to work with the app context
        client.environ_base['HTTP_ACCEPT'] = 'text/html'
        yield client

@pytest.fixture
def runner(app):
    """A test CLI runner for the app."""
    return app.test_cli_runner()

@pytest.fixture
def mock_config_dir():
    """Create a temporary directory for configuration files."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        os.makedirs(os.path.join(tmpdirname, 'config'), exist_ok=True)
        yield tmpdirname

@pytest.fixture
def mock_api_key_file(mock_config_dir):
    """Create a mock API key file."""
    api_key_file = os.path.join(mock_config_dir, 'config', 'simfin_api_key.txt')
    with open(api_key_file, 'w') as f:
        f.write('test_api_key')
    return api_key_file

@pytest.fixture
def mock_config_file(mock_config_dir):
    """Create a mock configuration file."""
    config_file = os.path.join(mock_config_dir, 'config', 'config.ini')
    with open(config_file, 'w') as f:
        f.write("""[API]
api_key_file = simfin_api_key.txt
default_key = free

[PATHS]
simfin_data_directory = data/simfin_data
processed_data_directory = data
""")
    return config_file

@pytest.fixture
def sample_price_data():
    """Generate sample price history data."""
    dates = pd.date_range(start='2020-01-01', periods=10, freq='D')
    data = {
        'Open': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109],
        'High': [110, 111, 112, 113, 114, 115, 116, 117, 118, 119],
        'Low': [90, 91, 92, 93, 94, 95, 96, 97, 98, 99],
        'Close': [105, 106, 107, 108, 109, 110, 111, 112, 113, 114],
        'Volume': [1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900],
        'MA20': [103, 104, 105, 106, 107, 108, 109, 110, 111, 112],
        'MA50': [101, 102, 103, 104, 105, 106, 107, 108, 109, 110]
    }
    return pd.DataFrame(data, index=dates)

@pytest.fixture
def sample_financial_data():
    """Generate sample financial statement data."""
    dates = pd.date_range(start='2020-01-01', periods=4, freq='Q')
    data = {
        'Revenue': [1000000, 1100000, 1200000, 1300000],
        'Net Income': [100000, 110000, 120000, 130000],
        'Total Assets': [5000000, 5100000, 5200000, 5300000],
        'Total Liabilities': [2000000, 2100000, 2200000, 2300000],
        'Total Equity': [3000000, 3000000, 3000000, 3000000]
    }
    return pd.DataFrame(data, index=dates)

@pytest.fixture
def mock_session():
    """Create a mock Flask session."""
    class MockSession(dict):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            
    return MockSession()
