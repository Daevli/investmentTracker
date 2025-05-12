import pandas as pd
import yfinance as yf
import os
import pickle
import datetime
from typing import List, Dict, Optional


class MainProgramData:

    def __init__(self):
        self.trackedTickers = []
        self.users = []
        self.session_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        self.save_dir = "saved_sessions"

        # Create save directory if it doesn't exist
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)

    def save_program_data(self, saveId=None):
        """Save the current program state with the given ID or use the session ID"""
        if saveId is None:
            saveId = self.session_id

        save_path = os.path.join(self.save_dir, f"session_{saveId}.pkl")
        with open(save_path, 'wb') as f:
            pickle.dump(self, f)
        return saveId

    def load_saved_data(self, saveId):
        """Load a saved program state with the given ID"""
        save_path = os.path.join(self.save_dir, f"session_{saveId}.pkl")
        if os.path.exists(save_path):
            with open(save_path, 'rb') as f:
                loaded_data = pickle.load(f)
                return loaded_data
        return None

    def get_available_sessions(self):
        """Get a list of all available saved sessions"""
        sessions = []
        if os.path.exists(self.save_dir):
            for file in os.listdir(self.save_dir):
                if file.startswith("session_") and file.endswith(".pkl"):
                    session_id = file.replace("session_", "").replace(".pkl", "")
                    sessions.append(session_id)
        return sessions

    def add_user(self, name):
        """Add a new user to the program"""
        user = UserProfile(name)
        self.users.append(user)
        return user

    def get_user(self, name):
        """Get a user by name"""
        for user in self.users:
            if user.name == name:
                return user
        return None

    def remove_user(self, user_id):
        """Remove a user from the program"""
        for i, user in enumerate(self.users):
            if user.id == user_id:
                self.users.pop(i)
                return True
        return False

    def add_ticker(self, ticker_id):
        """Add a new ticker to track"""
        # Check if ticker already exists
        for ticker in self.trackedTickers:
            if ticker.tickerId == ticker_id:
                return ticker

        # Create new ticker
        ticker = Ticker(ticker_id)
        self.trackedTickers.append(ticker)
        return ticker


class Ticker:

    def __init__(self, tickerId):
        self.tickerId = tickerId
        self.closingPrices = pd.DataFrame()
        self.intradayPrices = pd.DataFrame()
        self.dividendType = None
        self.xDate = None
        self.name = None
        self.currency = None
        self.sector = None
        self.data_dir = "ticker_data"
        self.last_updated = None
        self.update_interval = datetime.timedelta(minutes=15)  # Only update data every 15 minutes

        # Create data directory if it doesn't exist
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

        # Try to load existing data or fetch new data
        if not self.load_local_data():
            self.update_data(force=True)

    def update_data(self, force=False):
        """Fetch data from Yahoo Finance API"""
        # Ensure backward compatibility with older sessions
        if not hasattr(self, 'update_interval'):
            self.update_interval = datetime.timedelta(minutes=15)  # Default: update every 15 minutes

        # Check if we need to update the data
        current_time = datetime.datetime.now()
        if not force and self.last_updated and (current_time - self.last_updated) < self.update_interval:
            # Data is still fresh, no need to update
            return True

        try:
            # Get ticker info
            ticker = yf.Ticker(self.tickerId)
            info = ticker.info

            # Store basic info
            self.name = info.get('shortName', self.tickerId)
            self.currency = info.get('currency', 'EUR')
            self.sector = info.get('sector', 'Unknown')

            # Get historical data (last 2 years)
            end_date = current_time
            start_date = end_date - datetime.timedelta(days=730)

            # Fetch historical data
            self.closingPrices = ticker.history(start=start_date, end=end_date)

            # Get intraday data if available (last 7 days)
            try:
                intraday_start = end_date - datetime.timedelta(days=7)
                self.intradayPrices = ticker.history(start=intraday_start, end=end_date, interval="1h")
            except Exception as e:
                print(f"Could not fetch intraday data for {self.tickerId}: {e}")

            # Update the last_updated timestamp
            self.last_updated = current_time

            # Save the data locally
            self.save_data_locally()
            return True
        except Exception as e:
            print(f"Error updating data for {self.tickerId}: {e}")
            return False

    def save_data_locally(self):
        """Save ticker data to local file"""
        # Ensure backward compatibility with older sessions
        if not hasattr(self, 'update_interval'):
            self.update_interval = datetime.timedelta(minutes=15)  # Default: update every 15 minutes

        data = {
            'tickerId': self.tickerId,
            'name': self.name,
            'currency': self.currency,
            'sector': self.sector,
            'closingPrices': self.closingPrices,
            'intradayPrices': self.intradayPrices,
            'dividendType': self.dividendType,
            'xDate': self.xDate,
            'last_updated': self.last_updated,
            'update_interval': self.update_interval
        }

        file_path = os.path.join(self.data_dir, f"{self.tickerId}.pkl")
        with open(file_path, 'wb') as f:
            pickle.dump(data, f)

    def load_local_data(self):
        """Load ticker data from local file"""
        file_path = os.path.join(self.data_dir, f"{self.tickerId}.pkl")
        if os.path.exists(file_path):
            try:
                with open(file_path, 'rb') as f:
                    data = pickle.load(f)

                self.name = data.get('name', self.tickerId)
                self.currency = data.get('currency', 'USD')
                self.sector = data.get('sector', 'Unknown')
                self.closingPrices = data.get('closingPrices', pd.DataFrame())
                self.intradayPrices = data.get('intradayPrices', pd.DataFrame())
                self.dividendType = data.get('dividendType', None)
                self.xDate = data.get('xDate', None)
                self.last_updated = data.get('last_updated', None)
                # Load update_interval with a default if not present in saved data
                self.update_interval = data.get('update_interval', datetime.timedelta(minutes=15))
                return True
            except Exception as e:
                print(f"Error loading data for {self.tickerId}: {e}")
        return False

    def get_current_price(self):
        """Get the most recent price, preferring intraday data when available"""
        # First check if we have recent intraday data
        if not self.intradayPrices.empty:
            # Get the most recent date in the intraday data
            most_recent_intraday_date = self.intradayPrices.index.max()

            # Get the most recent date in the closing prices
            most_recent_closing_date = self.closingPrices.index.max() if not self.closingPrices.empty else None

            # If intraday data is more recent than closing data, use it
            if most_recent_closing_date is None or most_recent_intraday_date > most_recent_closing_date:
                return self.intradayPrices['Close'].iloc[-1]

        # Fall back to closing prices if intraday data is not available or not more recent
        if not self.closingPrices.empty:
            return self.closingPrices['Close'].iloc[-1]

        return None

    def get_price_history(self, days=30):
        """Get price history for the specified number of days"""
        if not self.closingPrices.empty:
            return self.closingPrices['Close'].tail(days)
        return pd.Series()

    def get_price_at_date(self, date):
        """Get the price at a specific date and time, preferring intraday data when available"""
        # Convert date to pandas Timestamp for comparison
        date_ts = pd.Timestamp(date)

        # First try to get intraday price if available
        if not self.intradayPrices.empty:
            # Check if we have intraday data for the date
            intraday_dates = self.intradayPrices.index.floor('D').unique()
            target_date = date_ts.floor('D')

            if target_date in intraday_dates:
                # Get all intraday prices for the target date
                day_prices = self.intradayPrices[self.intradayPrices.index.floor('D') == target_date]

                if not day_prices.empty:
                    # Find the closest time
                    # Convert date_ts to UTC if the index has timezone info
                    if hasattr(day_prices.index, 'tz') and day_prices.index.tz is not None:
                        # If date_ts is naive, localize it to UTC
                        if date_ts.tz is None:
                            date_ts = date_ts.tz_localize('UTC')
                        # Convert both to UTC for comparison
                        time_diffs = abs(day_prices.index.tz_convert('UTC') - date_ts.tz_convert('UTC'))
                    else:
                        # If index is naive, ensure date_ts is also naive
                        if date_ts.tz is not None:
                            date_ts = date_ts.tz_localize(None)
                        time_diffs = abs(day_prices.index - date_ts)

                    closest_idx = time_diffs.argmin()
                    closest_time = day_prices.index[closest_idx]
                    return day_prices.loc[closest_time, 'Close']

        # Fall back to daily closing prices if intraday data is not available
        if not self.closingPrices.empty:
            # Try to get the exact date
            # Handle timezone differences for the exact date comparison
            target_date = date_ts.floor('D')
            if hasattr(self.closingPrices.index, 'tz') and self.closingPrices.index.tz is not None:
                # If target_date is naive, localize it to match the index timezone
                if target_date.tz is None:
                    target_date = target_date.tz_localize(self.closingPrices.index.tz)
                # Convert both to the same timezone for comparison
                index_dates = self.closingPrices.index.floor('D')
                # Check if the date exists in the index
                for idx_date in index_dates:
                    if idx_date.tz_convert('UTC').floor('D') == target_date.tz_convert('UTC').floor('D'):
                        return self.closingPrices.loc[idx_date, 'Close']
            else:
                # If index is naive, ensure target_date is also naive
                if target_date.tz is not None:
                    target_date = target_date.tz_localize(None)
                if target_date in self.closingPrices.index:
                    return self.closingPrices.loc[target_date, 'Close']

            # If exact date not found, get the closest date before the specified date
            # Handle timezone differences
            if hasattr(self.closingPrices.index, 'tz') and self.closingPrices.index.tz is not None:
                # If date_ts is naive, localize it to UTC
                if date_ts.tz is None:
                    date_ts = date_ts.tz_localize('UTC')
                # Convert index to UTC for comparison
                idx_utc = self.closingPrices.index.tz_convert('UTC')
                earlier_dates = self.closingPrices.index[idx_utc <= date_ts.tz_convert('UTC')]
            else:
                # If index is naive, ensure date_ts is also naive
                if date_ts.tz is not None:
                    date_ts = date_ts.tz_localize(None)
                earlier_dates = self.closingPrices.index[self.closingPrices.index <= date_ts]

            if not earlier_dates.empty:
                closest_date = earlier_dates[-1]
                return self.closingPrices.loc[closest_date, 'Close']

            # If no earlier date found, get the earliest available date
            if not self.closingPrices.empty:
                earliest_date = self.closingPrices.index[0]
                return self.closingPrices.loc[earliest_date, 'Close']

        # If no data available, return None
        return None


class Investment:

    def __init__(self, ticker=None, initial_investment=500, currency='EUR', number_of_shares=None, purchase_price=None, purchase_date=None, tags=None):
        self.ticker = ticker
        self.initialInvestment = initial_investment
        self.currency = currency
        self.purchasePrice = purchase_price
        self.currentValue = initial_investment
        self.startDatetime = purchase_date if purchase_date else datetime.datetime.now()
        self.endDatetime = None
        self.tags = tags if tags is not None else []  # Initialize with empty list if no tags provided
        self.is_sold = False
        self.selling_price = None
        self.profit = None
        # Use purchase date for ID if provided, otherwise use current time
        timestamp = self.startDatetime.strftime('%Y%m%d%H%M%S')
        self.id = f"inv_{timestamp}_{ticker.tickerId if ticker else 'unknown'}"

        # Calculate number of shares based on initial investment and purchase price
        if number_of_shares is not None:
            self.numberOfShares = number_of_shares
        elif purchase_price is not None and purchase_price > 0:
            self.numberOfShares = initial_investment / purchase_price
        else:
            self.numberOfShares = 0
            if ticker:
                # If purchase date is provided and purchase price is not, use historical price
                if purchase_date and ticker.get_price_at_date(purchase_date):
                    self.purchasePrice = ticker.get_price_at_date(purchase_date)
                    self.numberOfShares = initial_investment / self.purchasePrice
                # Otherwise use current price
                elif ticker.get_current_price():
                    self.purchasePrice = ticker.get_current_price()
                    self.numberOfShares = initial_investment / self.purchasePrice

        # Update data immediately if ticker is provided
        if self.ticker:
            self.update_data()

    def update_data(self, force=False):
        """Update the current value of the investment based on ticker data"""
        if self.ticker:
            # Update ticker data if needed
            self.ticker.update_data(force=force)

            # Get current price and update value
            current_price = self.ticker.get_current_price()
            if current_price:
                self.currentValue = self.numberOfShares * current_price
        return self.currentValue

    def get_performance(self):
        """Calculate the performance of the investment"""
        if self.initialInvestment > 0:
            return (self.currentValue - self.initialInvestment) / self.initialInvestment * 100
        return 0

    def get_performance_history(self, days=30):
        """Get the performance history for the specified number of days"""
        if self.ticker:
            price_history = self.ticker.get_price_history(days)
            if not price_history.empty and self.numberOfShares > 0:
                value_history = price_history * self.numberOfShares
                return value_history
        return pd.Series()

    def sell(self, selling_price, sell_date=None):
        """Sell the investment at the specified price and date"""
        # Ensure backward compatibility with older sessions
        if not hasattr(self, 'is_sold'):
            self.is_sold = False
        if not hasattr(self, 'selling_price'):
            self.selling_price = None
        if not hasattr(self, 'profit'):
            self.profit = None

        if self.is_sold:
            return False  # Already sold

        self.selling_price = selling_price
        self.is_sold = True
        self.endDatetime = sell_date if sell_date else datetime.datetime.now()

        # Calculate profit
        sell_value = self.numberOfShares * selling_price
        self.profit = sell_value - self.initialInvestment

        return True

    def to_dict(self):
        """Convert investment to dictionary for display"""
        # Get current price and ensure it's a Python native type
        current_price = self.ticker.get_current_price() if self.ticker else None
        if current_price is not None:
            current_price = float(current_price)

        result = {
            'id': self.id,
            'ticker': self.ticker.tickerId if self.ticker else 'Unknown',
            'ticker_name': self.ticker.name if self.ticker else 'Unknown',
            'initial_investment': float(self.initialInvestment) if self.initialInvestment is not None else None,
            'currency': self.currency,
            'number_of_shares': float(self.numberOfShares) if self.numberOfShares is not None else None,
            'purchase_price': float(self.purchasePrice) if self.purchasePrice is not None else None,
            'current_price': current_price,
            'current_value': float(self.currentValue) if self.currentValue is not None else None,
            'performance': float(self.get_performance()) if self.get_performance() is not None else None,
            'start_date': self.startDatetime.strftime('%Y-%m-%d') if self.startDatetime else 'Unknown',
            'end_date': self.endDatetime.strftime('%Y-%m-%d') if self.endDatetime else 'Active',
            'tags': self.tags if hasattr(self, 'tags') else [],  # Ensure backward compatibility
            'is_sold': self.is_sold if hasattr(self, 'is_sold') else False,  # Ensure backward compatibility
            'selling_price': float(self.selling_price) if hasattr(self, 'selling_price') and self.selling_price is not None else None,
            'profit': float(self.profit) if hasattr(self, 'profit') and self.profit is not None else None
        }

        return result


class UserProfile:

    def __init__(self, name):
        self.name = name
        self.investments = []
        self.sold_investments = []  # List to store sold investments
        self.id = f"user_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{name.replace(' ', '_')}"
        self.created_at = datetime.datetime.now()
        self.last_updated = self.created_at
        self.total_dividends = 0  # Total dividends not tied to any specific investment

    def add_investment(self, ticker, initial_investment=1000, currency='EUR', number_of_shares=None, purchase_price=None, purchase_date=None, tags=None):
        """Add a new investment to the user's portfolio"""
        investment = Investment(ticker, initial_investment, currency, number_of_shares, purchase_price, purchase_date, tags)
        self.investments.append(investment)
        self.last_updated = datetime.datetime.now()
        return investment

    def remove_investment(self, investment_id):
        """Remove an investment from the user's portfolio"""
        for i, investment in enumerate(self.investments):
            if investment.id == investment_id:
                self.investments.pop(i)
                self.last_updated = datetime.datetime.now()
                return True
        return False

    def get_investment(self, investment_id):
        """Get an investment by ID"""
        for investment in self.investments:
            if investment.id == investment_id:
                return investment
        return None

    def update_all_investments(self, force=False):
        """Update data for all investments"""
        for investment in self.investments:
            investment.update_data(force=force)
        self.last_updated = datetime.datetime.now()

    def get_total_value(self):
        """Get the total current value of all investments"""
        return sum(investment.currentValue for investment in self.investments)

    def get_total_initial_investment(self):
        """Get the total initial investment"""
        return sum(investment.initialInvestment for investment in self.investments)

    def get_overall_performance(self):
        """Get the overall performance of the portfolio"""
        total_initial = self.get_total_initial_investment()
        if total_initial > 0:
            return (self.get_total_value() - total_initial) / total_initial * 100
        return 0

    def sell_investment(self, investment_id, selling_price, sell_date=None):
        """Sell an investment and move it to sold_investments"""
        # Ensure backward compatibility with older sessions
        if not hasattr(self, 'sold_investments'):
            self.sold_investments = []

        for i, investment in enumerate(self.investments):
            if investment.id == investment_id:
                # Sell the investment
                if investment.sell(selling_price, sell_date):
                    # Move to sold investments
                    self.sold_investments.append(investment)
                    self.investments.pop(i)
                    self.last_updated = datetime.datetime.now()
                    return True
                return False
        return False

    def get_investments_summary(self):
        """Get a summary of all active investments"""
        return [investment.to_dict() for investment in self.investments]

    def get_sold_investments_summary(self):
        """Get a summary of all sold investments"""
        return [investment.to_dict() for investment in self.sold_investments]

    def remove_sold_investment(self, investment_id):
        """Remove a sold investment from the user's portfolio"""
        for i, investment in enumerate(self.sold_investments):
            if investment.id == investment_id:
                self.sold_investments.pop(i)
                self.last_updated = datetime.datetime.now()
                return True
        return False

    def add_total_dividend(self, amount, date=None):
        """Add a dividend to the total, not tied to any specific investment"""
        # Ensure backward compatibility with older sessions
        if not hasattr(self, 'total_dividends'):
            self.total_dividends = 0

        # Add the amount to the total
        self.total_dividends += amount
        self.last_updated = datetime.datetime.now()
        return True
