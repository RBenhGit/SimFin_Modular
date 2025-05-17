# SimFin Analyzer - Project Map & Memory Bank

**Last Updated:** May 17, 2025

This document provides a comprehensive map of the SimFin Analyzer modular implementation, explaining the purpose and relationships between different components, key design decisions, historical context, and future considerations.

## Overview

The SimFin Analyzer application has been refactored from a monolithic structure into a modular, maintainable architecture. The application follows modern Python practices including:

- Separation of concerns
- Modular design
- Blueprint-based routing
- Comprehensive testing (planned/in-progress, as per `README.md`)
- Configuration management

## 1. Overall Program Goal:

* To create a web application (Flask-based in Python) that allows users to analyze financial data of companies.
* The application retrieves data from sources like SimFin (financial statements) and Yahoo Finance (historical price data).
* The application saves data (primarily as CSV files in dedicated folders for each ticker, and also uses the session for certain data) and presents it visually (interactive Plotly graphs).
* Future functionality for performing valuations, user accounts, data export, and more is planned.

## 2. Core Components & File Structure:

### 2.1. Application Entry Point
    **File**: `app.py`
    * Main entry point that configures the Flask application.
    * Sets up logging.
    * Initializes the SimFin API connection (via `modules.data_loader`).
    * Registers blueprints for different sections.
    * Handles secret key management (checks for `secrets.py` or generates a default key).

### 2.2. Configuration
    **Directory**: `config/`
    **File**: `config/config.ini` (Expected)
    * Stores application settings like API keys, file paths.
    * Loaded by `utils.config_loader`.

### 2.3. Data Storage
    **Directory**: `data/`
    * `data/simfin_data/`: For raw SimFin data as managed by the SimFin library.
    * `data/[TICKER]/`: Dynamically created directories for each ticker, storing processed CSV financial statements.

### 2.4. Core Functional Modules
    **Directory**: `modules/`

    **File**: `modules/data_loader.py`
    * Manages SimFin API configuration.
    * Handles API key loading (from file or 'free' default) and management.
    * Configures SimFin data directories.
    * Provides `get_api_key_status_for_display` for UI.

    **File**: `modules/financial_statements.py`
    * Downloads financial statements (income, balance, cashflow; annual & quarterly) from SimFin.
    * Processes data: Loads full dataset and filters by ticker.
    * Saves statements to CSV files under `data/[TICKER]/`.
    * Provides `get_dataframe_from_session_or_csv` for loading data, prioritizing session then CSV.
    * Uses `utils.helpers.ensure_directory_exists` (implicitly, based on previous code).

    **File**: `modules/price_history.py`
    * Downloads historical price data (OHLCV) using `yfinance`.
    * Calculates moving averages (e.g., MA20, MA50, MA100, MA150, MA200).
    * Can calculate additional technical indicators and summary statistics.

    **File**: `modules/chart_creator.py`
    * Creates interactive time series charts (bar, line) using Plotly Express.
    * Generates candlestick charts with moving averages using Plotly Graph Objects.
    * Returns chart data as JSON (data and layout) for client-side rendering.
    * Handles cases of missing or invalid data for plotting.

### 2.5. Route Handlers (Blueprints)
    **Directory**: `modules/routes/`

    **File**: `modules/routes/home.py` (Blueprint: `home_bp`)
    * Handles the main home page display (`/`).
    * Processes ticker selection (POST request), triggers data download, and updates session.
    * Manages API key updates (POST request from modal).
    * Displays candlestick chart and data download status.

    **File**: `modules/routes/graphs.py` (Blueprint: `graphs_bp`, prefix: `/graphs`)
    * Handles annual (`/annual`) and quarterly (`/quarterly`) graph views.
    * Generates and displays revenue and net income charts.
    * Processes financial statements data for display, loading from session or CSV.

    **File**: `modules/routes/valuations.py` (Blueprint: `valuations_bp`, prefix: `/valuations`)
    * Handles valuation-related views (`/`).
    * Currently a placeholder for future valuation metrics implementation.

### 2.6. Utility Modules
    **Directory**: `utils/`

    **File**: `utils/config_loader.py` (Assumed based on imports)
    * Manages application configuration.
    * Loads settings from `config.ini`.
    * Creates default configuration if `config.ini` is missing (expected behavior).
    * Provides a centralized configuration interface.

    **File**: `utils/helpers.py` (Assumed based on imports, e.g., `ensure_directory_exists`)
    * Contains common helper functions.
    * File path management.
    * Potentially other utility functions.

### 2.7. Templates & Static Files
    **Directory**: `templates/`
    * `base_layout.html`: Main layout, includes sidebar, top ticker form, API key modal, Plotly.js.
    * `content_home.html`: Home page specific content, candlestick chart rendering script.
    * `content_graphs.html`: Graphs page specific content, financial chart rendering script.
    * `content_valuations.html`: Valuations page placeholder.

    **Directory**: `static/` (Standard Flask directory for CSS, JS, images)

### 2.8. Other Key Files
    * `requirements.txt`: Project dependencies.
    * `README.md`: Main project documentation.
    * `secrets.py` (Optional, not in Git): For `FLASK_SECRET_KEY`.
    * `app.log`: Log file for application events.

## 3. Key Relationships & Data Flow:

1.  **Configuration Flow**:
    * `utils.config_loader` loads settings from `config.ini`.
    * `modules.data_loader` uses these settings to configure SimFin (API key, data directory).
    * Route handlers in `modules.routes` use configuration for paths and settings.

2.  **Data Processing Pipeline (on Ticker Selection)**:
    * User selects ticker in UI (form in `base_layout.html`).
    * `modules.routes.home.route_set_ticker` (POST) receives the ticker.
    * Triggers data download via:
        * `modules.financial_statements.download_financial_statements` (SimFin data).
        * `modules.price_history.download_price_history_with_mavg` (Yahoo Finance data).
    * Data is processed and financial statements are stored as CSV files in `data/[TICKER]/` by `modules.financial_statements.save_financial_statements`.
    * Key data (e.g., income statement DataFrames as JSON, download status) is stored in the Flask `session`.
    * User is redirected to the home page (or current page refreshed).

3.  **Visualization Chain**:
    * When a page requiring charts is loaded (e.g., home, graphs):
        * Route handlers (e.g., in `modules.routes.home`, `modules.routes.graphs`) retrieve necessary data:
            * Price history from `modules.price_history`.
            * Financial statements by calling `modules.financial_statements.get_dataframe_from_session_or_csv`.
        * `modules.chart_creator` functions (`create_candlestick_chart_with_mavg`, `create_timeseries_chart`) transform data into Plotly figure JSON (data and layout).
        * Route handlers pass this JSON to the HTML templates.
        * JavaScript in the templates (`content_home.html`, `content_graphs.html`) uses `Plotly.newPlot()` to render the charts client-side.

## 4. Key Design Decisions:

* **Modular Architecture:** Transitioned from monolithic to a modular structure using Flask Blueprints for better organization and maintainability.
* **Client-Side Graph Rendering:** Plotly graphs are generated as JSON on the server and rendered in the browser using Plotly.js to improve interactivity and reduce server load for rendering.
* **Data Persistence:**
    * Financial statements are saved as CSV files per ticker for long-term storage and to avoid repeated API calls.
    * Flask `session` is used to cache frequently accessed data (like income statements as JSON, ticker status) for the current user session, with a fallback to CSV.
* **SimFin Data Retrieval Strategy:** Due to API limitations with direct ticker filtering in some `load_*` functions, the strategy is to load the full relevant dataset (e.g., all annual income statements) and then filter by the specific ticker in the Python code.
* **API Key Management:** Implemented a user-friendly way to update the SimFin API key via a modal in the UI, storing it in a local file.

## 5. Historical Challenges & Solutions:

* **`TypeError` with `yfinance` and older Python versions:** Resolved by upgrading the Python environment (e.g., to Python 3.10+).
* **`ModuleNotFoundError` for `simfin` or `yfinance`:** Ensured correct installation within the active virtual environment using `python -m pip install ...`.
* **`NameError` for functions:** Ensured proper function definitions before calls and correct imports between modules (greatly aided by modularization).
* **SimFin `load()` error with `ticker` argument:** Adopted a workaround: load the entire dataset and filter programmatically. This remains the current approach.
* **Graphs not rendering in browser:**
    * Initial issues with passing HTML directly.
    * Solved by server generating Plotly chart specs as JSON, and client-side JavaScript rendering using `Plotly.newPlot()`.
    * Ensured up-to-date Plotly.js CDN link.
* **CSV Permission Denied errors:** Advised user to check file locks and permissions; issue seemed to resolve.
* **Git Branch Management confusion:** Explained correct Git commands (`checkout -- .`, `reset --hard`, `push --force-with-lease`).

## 6. Current/Future Considerations & Enhancement Areas:

### 6.1. Core Functionality Enhancements
* **Graph Customization:**
    * Allow user selection of moving averages and their periods for candlestick charts.
    * Enable user selection of date ranges for candlestick charts.
    * Add more financial statement items to graph (e.g., Gross Profit, Operating Income, FCF, R&D, SG&A).
* **Valuation Module (`modules/routes/valuations.py`):**
    * Define and implement specific valuation models (e.g., DCF, DDM, P/E, P/S, EV/EBITDA).
    * Require data from multiple financial statements (income, balance, cashflow) and potentially price data.
* **Error Handling & User Feedback:** Continue to improve robustness and clarity of messages.
* **Session Management:**
    * Monitor session size, especially if more DataFrames are stored.
    * Ensure proper clearing of ticker-specific session data upon new ticker selection.

### 6.2. Performance & Optimization
* **SimFin Data Download Efficiency:** The current "load all then filter" approach for SimFin might be inefficient for many tickers. Investigate if newer SimFin library versions offer better direct filtering.
* **Data Caching:** Implement more sophisticated server-side caching (beyond Flask session) for frequently accessed, less volatile data (e.g., using Flask-Caching) to reduce file I/O and API calls. Consider data expiration and refresh strategies.

### 6.3. New Features (Long-Term)
* **User Accounts:**
    * Implement user registration and login.
    * Allow users to save favorite tickers, custom analysis, or chart configurations.
* **Export Functionality:**
    * Allow exporting chart data or tables to CSV/Excel.
    * Generate PDF reports of analyses.
* **Advanced Analytics & Comparisons:**
    * Sector comparison analysis.
    * Basic machine learning predictions (e.g., trend analysis).
* **UI/UX Improvements:**
    * More polished visual design.
    * Enhanced interactivity in charts (e.g., drill-downs, annotations).

### 6.4. Testing
* Expand test coverage as per `README.md` and `project_map.md` (Unit tests for all core modules, Integration tests for API interactions, Route tests for web interfaces).

This comprehensive `project_map.md` should serve as an excellent "memory bank" for any AI tool, as well as for human developers working on the project.