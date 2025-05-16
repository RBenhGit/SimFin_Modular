# SimFin Analyzer

A modular Flask-based web application for analyzing financial data from SimFin API, with comprehensive visualization tools for financial statements, price history, and valuation metrics.

## Project Structure

The application follows a modular architecture to improve maintainability and extensibility:

```
SimFin_Modular/
├── app.py                     # Main application entry point
├── requirements.txt           # Project dependencies
├── config/
│   └── config.ini             # Configuration settings
├── data/
│   └── simfin_data/           # Data storage directory
├── modules/
│   ├── data_loader.py         # API key loading, configuration functions
│   ├── financial_statements.py # Financial statements downloading and processing
│   ├── price_history.py       # Price history downloading and processing
│   ├── chart_creator.py       # Chart generation functions
│   └── routes/
│       ├── home.py            # Home page route handlers
│       ├── graphs.py          # Graph-related route handlers
│       └── valuations.py      # Valuation-related route handlers
├── utils/
│   ├── helpers.py             # Helper functions (file paths, etc.)
│   └── config_loader.py       # Configuration loading utilities
├── templates/
│   ├── base_layout.html       # Main layout template
│   ├── content_graphs.html    # Graphs display template
│   ├── content_home.html      # Home page content
│   └── content_valuations.html # Valuations content
└── static/
    ├── css/                   # CSS stylesheets
    ├── js/                    # JavaScript files
    └── images/                # Image assets
```

## Features

- **Data Retrieval**: Download and process financial statements from SimFin API
- **Price Data**: Fetch historical price data with various technical indicators
- **Visualization**: Generate interactive charts for financial metrics
- **Modular Design**: Clean separation of concerns for better maintainability
- **Blueprint Architecture**: Organized Flask routes using blueprints
- **Comprehensive Testing**: Complete test suite with unit and integration tests

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/SimFin_Modular.git
   cd SimFin_Modular
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Configure the application:
   - Create a `config/config.ini` file (will be created automatically on first run)
   - Optionally create a `secrets.py` file with your `FLASK_SECRET_KEY` for better security

## Configuration

### SimFin API Key

1. Get a free or premium API key from [SimFin](https://simfin.com/)
2. You can set the API key directly in the application interface after starting the app

### Data Directories

The application will create the following directories automatically:
- `config/`: For configuration files
- `data/simfin_data/`: For SimFin data downloads
- `data/[TICKER]/`: For processed financial statements by ticker

## Usage

1. Start the application:
   ```
   python app.py
   ```

2. Open your web browser and navigate to [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

3. Enter a stock ticker (e.g., AAPL, MSFT) to analyze

4. Navigate through the tabs to view:
   - Home: Price history with candlestick chart
   - Graphs: Annual and quarterly financial metrics
   - Valuations: Stock valuation metrics and analysis

## Testing

Run the test suite with:

```
# Run all tests
python -m pytest

# Run with coverage report
python -m pytest --cov=SimFin_Modular tests/ --cov-report=html

# Windows users can use the batch file
run_tests.bat
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [SimFin](https://simfin.com/) for providing financial data API
- [Flask](https://flask.palletsprojects.com/) for the web framework
- [Plotly](https://plotly.com/) for interactive visualizations
