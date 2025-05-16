# SimFin Analyzer - Project Map

This document provides a comprehensive map of the SimFin Analyzer modular implementation, explaining the purpose and relationships between different components.

## Overview

The SimFin Analyzer application has been refactored from a monolithic structure into a modular, maintainable architecture. The application follows modern Python practices including:

- Separation of concerns
- Modular design
- Blueprint-based routing
- Comprehensive testing
- Configuration management

## Core Components

### 1. Application Entry Point

**File**: `app.py`

The main entry point that:
- Configures the Flask application
- Sets up logging
- Initializes the SimFin API connection
- Registers blueprints for different sections
- Handles secret key management

### 2. Utility Modules

Utility modules provide common functionality used across the application:

**File**: `utils/config_loader.py`
- Manages application configuration
- Loads settings from config.ini
- Creates default configuration if needed
- Provides a centralized configuration interface

**File**: `utils/helpers.py`
- Contains helper functions used throughout the application
- File path management
- API key status display
- Number formatting

### 3. Core Functional Modules

The application's core functionality is divided into focused modules:

**File**: `modules/data_loader.py`
- Manages SimFin API configuration
- Handles API key loading and management
- Configures data directories

**File**: `modules/financial_statements.py`
- Downloads financial statements from SimFin
- Processes and saves statements to CSV files
- Provides functions for loading data from session or files

**File**: `modules/price_history.py`
- Downloads historical price data using yfinance
- Calculates moving averages and technical indicators
- Generates price summary statistics

**File**: `modules/chart_creator.py`
- Creates interactive time series charts
- Generates candlestick charts with indicators
- Handles various chart types and configurations

### 4. Route Handlers

The application's routes are organized into logical blueprints:

**File**: `modules/routes/home.py`
- Handles the main home page display
- Processes ticker selection
- Manages API key updates

**File**: `modules/routes/graphs.py`
- Handles annual and quarterly graph views
- Generates revenue and income charts
- Processes financial statements data for display

**File**: `modules/routes/valuations.py`
- Handles valuation-related views
- (Placeholder for future valuation metrics implementation)

## Testing Framework

The application includes a comprehensive testing framework:

**Directory**: `tests/`
- Unit tests for all core modules
- Integration tests for API interactions
- Route tests for web interfaces
- Fixtures for common test scenarios

## Key Relationships

1. **Configuration Flow**:
   - `ConfigLoader` loads settings
   - `data_loader.py` uses these settings to configure SimFin
   - Route handlers use configuration for paths and settings

2. **Data Processing Pipeline**:
   - User selects ticker in UI
   - `home.py` routes trigger data download via `financial_statements.py`
   - Data is processed and stored in session and CSV files
   - `graphs.py` routes retrieve this data and create visualizations via `chart_creator.py`

3. **Visualization Chain**:
   - Financial data is loaded from session or CSV
   - `chart_creator.py` functions transform data into visualizations
   - Route handlers convert these to JSON for frontend display

## Future Enhancement Areas

1. **Valuation Models**:
   - Implement DCF, dividend discount models
   - Add ratio analysis and comparative valuations

2. **Data Caching**:
   - Implement more efficient caching mechanisms
   - Add data expiration and refresh strategies

3. **User Accounts**:
   - Add user authentication
   - Allow saving favorite tickers and analyses

4. **Export Functionality**:
   - Add PDF report generation
   - Enable Excel/CSV export of analysis results

5. **Advanced Analytics**:
   - Add machine learning predictions
   - Implement sector comparison analysis
