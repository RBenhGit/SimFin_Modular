@echo off
echo Running SimFin Analyzer tests...

echo.
echo Running unit tests...
python -m pytest tests\test_utils tests\test_modules tests\test_routes -q

echo.
echo Running integration tests...
if exist tests\test_integration python -m pytest tests\test_integration -q

echo.
echo Running coverage report...
python -m pytest --cov=. tests\ --cov-report=html

echo.
echo Tests complete! Check the htmlcov directory for the coverage report.
