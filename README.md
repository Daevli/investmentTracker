# Investment Tracker

A Flask application for tracking financial investments. This application allows users to track financial instruments, collect price data from Yahoo Finance, and monitor investment performance over time.

## Features

- Track financial instruments and collect price data from Yahoo Finance API
- Support multiple users and their investments
- Save/load session states with unique IDs
- Interactive charts showing investment performance
- Responsive web interface

## Installation

1. Clone the repository:
```
git clone <repository-url>
cd investmentTracker
```

2. Create and activate a virtual environment (recommended):
```
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

3. Install the required dependencies:
```
pip install -r requirements.txt
```

## Usage

1. Run the application:
```
python app.py
```

2. Open your web browser and navigate to:
```
http://localhost:5000
```

3. Getting started:
   - Create a user profile
   - Add investments to track by entering ticker symbols
   - View detailed information and performance charts
   - Save your session to continue later

## Application Structure

- `app.py`: Main Flask application entry point
- `classes.py`: Core classes for the application
  - `MainProgramData`: Manages program data and sessions
  - `Ticker`: Handles financial instrument data from Yahoo Finance
  - `Investment`: Tracks individual investments
  - `UserProfile`: Manages user-specific investments
- `templates/`: HTML templates for the web interface
- `saved_sessions/`: Directory for saved session data
- `ticker_data/`: Directory for cached ticker data

## Data Sources

The application uses the Yahoo Finance API (via the yfinance package) to fetch financial data for tracked instruments. This includes:
- Historical price data
- Current price information
- Basic instrument details (name, sector, currency)

## Session Management

- Each session has a unique ID based on the timestamp
- Sessions can be saved and loaded at any time
- All user data, investments, and tracked tickers are preserved between sessions

## Example Tickers

- US Stocks: AAPL (Apple), MSFT (Microsoft), AMZN (Amazon), GOOGL (Google), TSLA (Tesla)
- ETFs: SPY (S&P 500), VTI (Vanguard Total Stock Market), QQQ (Nasdaq)
- European Stocks: SAP.DE (SAP SE), SIE.DE (Siemens), ASML.AS (ASML Holding)
- Cryptocurrencies: BTC-USD (Bitcoin), ETH-USD (Ethereum)

## Dependencies

- Flask: Web framework
- yfinance: Yahoo Finance API client
- pandas: Data manipulation
- plotly: Interactive charts
- Bootstrap: Frontend styling

## Performance Optimization

The application includes several performance optimizations:

- Time-based caching of ticker data to reduce API calls to Yahoo Finance
- Manual refresh option for updating investment data when needed
- Efficient data loading to improve page load times
- DataTables for client-side sorting and filtering of investment data

## Development

### .gitignore

The repository includes a `.gitignore` file that excludes the following from version control:

- Python cache files and bytecode (`__pycache__/`, `*.pyc`, etc.)
- Virtual environment directories (`.venv/`, `venv/`, etc.)
- IDE-specific files (`.idea/`, `.vscode/`, etc.)
- Application-specific data directories (`ticker_data/`, `saved_sessions/`, etc.)

This ensures that only the necessary source code is tracked in the repository, while generated files and user data remain local.

### Contributing

Contributions to the Investment Tracker are welcome! Here's how you can contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This application is free to use by anyone.
