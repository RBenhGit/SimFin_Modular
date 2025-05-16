"""Pytest plugin to generate a summarized test report."""

import pytest
from _pytest.terminal import TerminalReporter


def pytest_configure(config):
    """Configure the plugin."""
    # Register an additional terminal reporter
    standard_reporter = config.pluginmanager.getplugin('terminalreporter')
    summary_reporter = SummaryReporter(config)
    config.pluginmanager.register(summary_reporter, 'summary_reporter')


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
