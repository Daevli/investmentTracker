from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_bootstrap import Bootstrap
import os
import datetime
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import json
import numpy as np

from classes import MainProgramData, Ticker, Investment, UserProfile

# Custom JSON encoder to handle numpy types
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'investment-tracker-secret-key'
bootstrap = Bootstrap(app)

# Initialize the main program data
program_data = MainProgramData()

# Routes
@app.route('/')
def index():
    """Home page showing available sessions and users"""
    available_sessions = program_data.get_available_sessions()
    return render_template('index.html', 
                          sessions=available_sessions, 
                          current_session=program_data.session_id,
                          users=program_data.users)

@app.route('/load_session/<session_id>')
def load_session(session_id):
    """Load a saved session"""
    global program_data
    loaded_data = program_data.load_saved_data(session_id)
    if loaded_data:
        program_data = loaded_data
        flash(f'Session {session_id} loaded successfully', 'success')
    else:
        flash(f'Failed to load session {session_id}', 'danger')
    return redirect(url_for('index'))

@app.route('/save_session', methods=['POST'])
def save_session():
    """Save the current session"""
    session_id = request.form.get('session_id')
    saved_id = program_data.save_program_data(session_id)
    flash(f'Session saved with ID: {saved_id}', 'success')
    return redirect(url_for('index'))

@app.route('/users')
def users():
    """Show all users"""
    return render_template('users.html', users=program_data.users)

@app.route('/remove_user/<user_id>')
def remove_user(user_id):
    """Remove a user"""
    if program_data.remove_user(user_id):
        flash('User removed successfully', 'success')
    else:
        flash('Failed to remove user', 'danger')
    return redirect(url_for('users'))

@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    """Add a new user"""
    if request.method == 'POST':
        name = request.form.get('name')
        if name:
            user = program_data.add_user(name)
            flash(f'User {name} added successfully', 'success')
            return redirect(url_for('user_profile', user_id=user.id))
    return render_template('add_user.html')

@app.route('/user/<user_id>')
def user_profile(user_id):
    """Show user profile and investments"""
    user = None
    for u in program_data.users:
        if u.id == user_id:
            user = u
            break

    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('users'))

    # Get investment summaries without forcing updates
    investments = user.get_investments_summary()

    # Get sold investment summaries
    sold_investments = user.get_sold_investments_summary() if hasattr(user, 'sold_investments') else []

    # Calculate portfolio metrics for active investments
    total_value = user.get_total_value()
    total_initial = user.get_total_initial_investment()
    overall_performance = user.get_overall_performance()

    # Calculate metrics for sold investments
    total_sold_value = 0
    total_sold_initial = 0
    total_sold_profit = 0

    if sold_investments:
        for inv in sold_investments:
            if inv['selling_price'] is not None and inv['number_of_shares'] is not None:
                total_sold_value += inv['selling_price'] * inv['number_of_shares']
            if inv['initial_investment'] is not None:
                total_sold_initial += inv['initial_investment']
            if inv['profit'] is not None:
                total_sold_profit += inv['profit']

    # Calculate overall performance for sold investments
    sold_performance = 0
    if total_sold_initial > 0:
        sold_performance = (total_sold_profit / total_sold_initial) * 100

    # Get total dividends with backward compatibility
    total_dividends = user.total_dividends if hasattr(user, 'total_dividends') else 0

    return render_template('user_profile.html', 
                          user=user, 
                          investments=investments,
                          sold_investments=sold_investments,
                          total_value=total_value,
                          total_initial=total_initial,
                          overall_performance=overall_performance,
                          total_sold_value=total_sold_value,
                          total_sold_initial=total_sold_initial,
                          total_sold_profit=total_sold_profit,
                          sold_performance=sold_performance,
                          total_dividends=total_dividends)

@app.route('/add_investment/<user_id>', methods=['GET', 'POST'])
def add_investment(user_id):
    """Add a new investment for a user"""
    user = None
    for u in program_data.users:
        if u.id == user_id:
            user = u
            break

    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('users'))

    if request.method == 'POST':
        ticker_id = request.form.get('ticker_id')
        currency = request.form.get('currency', 'EUR')
        investment_type = request.form.get('investment_type', 'amount')

        # Get purchase date if provided
        purchase_date_str = request.form.get('purchase_date')
        purchase_date = None
        if purchase_date_str:
            try:
                # Parse the date string from the form
                purchase_date = datetime.datetime.strptime(purchase_date_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                flash('Invalid date format. Using current date.', 'warning')

        # Check if ticker exists or create a new one
        ticker = None
        for t in program_data.trackedTickers:
            if t.tickerId == ticker_id:
                ticker = t
                break

        if not ticker:
            ticker = program_data.add_ticker(ticker_id)

        # Get current price for the ticker
        current_price = ticker.get_current_price()

        # Get tags if provided
        tags_str = request.form.get('tags', '')
        tags = [tag.strip() for tag in tags_str.split(',')] if tags_str.strip() else []

        # Handle investment by amount or by shares
        if investment_type == 'shares':
            # User specified number of shares
            number_of_shares = float(request.form.get('number_of_shares', 0))

            # Handle empty purchase price
            purchase_price_str = request.form.get('purchase_price', '')
            if purchase_price_str.strip():
                purchase_price = float(purchase_price_str)
            else:
                purchase_price = None  # Will use price at purchase date in Investment class

            # Calculate initial investment based on shares and price
            initial_investment = number_of_shares * purchase_price if purchase_price else 0

            # Add investment with number of shares and purchase price
            investment = user.add_investment(
                ticker, 
                initial_investment, 
                currency, 
                number_of_shares, 
                purchase_price,
                purchase_date,
                tags
            )
        else:
            # User specified investment amount
            initial_investment = float(request.form.get('initial_investment', 1000))

            # Handle empty purchase price
            purchase_price_str = request.form.get('purchase_price', '')
            if purchase_price_str.strip():
                purchase_price = float(purchase_price_str)
            else:
                purchase_price = None  # Will use price at purchase date in Investment class

            # Add investment with amount and purchase price
            investment = user.add_investment(
                ticker, 
                initial_investment, 
                currency, 
                None,  # No specific number of shares
                purchase_price,
                purchase_date,
                tags
            )

        flash(f'Investment in {ticker_id} added successfully', 'success')
        return redirect(url_for('user_profile', user_id=user.id))

    return render_template('add_investment.html', user=user)

@app.route('/investment/<user_id>/<investment_id>')
def investment_details(user_id, investment_id):
    """Show investment details"""
    user = None
    for u in program_data.users:
        if u.id == user_id:
            user = u
            break

    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('users'))

    investment = user.get_investment(investment_id)
    if not investment:
        flash('Investment not found', 'danger')
        return redirect(url_for('user_profile', user_id=user.id))

    # Update investment data
    investment.update_data()

    # Get performance history
    performance_history = investment.get_performance_history(days=90)

    # Create chart data
    if not performance_history.empty:
        fig = px.line(performance_history, 
                     title=f'Investment Value History - {investment.ticker.name}',
                     labels={'value': 'Value', 'index': 'Date'})
        chart_json = json.dumps(fig.to_dict(), cls=NumpyEncoder)
    else:
        chart_json = None

    return render_template('investment_details.html', 
                          user=user, 
                          investment=investment.to_dict(),
                          chart_json=chart_json)

@app.route('/remove_investment/<user_id>/<investment_id>')
def remove_investment(user_id, investment_id):
    """Remove an investment"""
    user = None
    for u in program_data.users:
        if u.id == user_id:
            user = u
            break

    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('users'))

    if user.remove_investment(investment_id):
        flash('Investment removed successfully', 'success')
    else:
        flash('Failed to remove investment', 'danger')

    return redirect(url_for('user_profile', user_id=user.id))

@app.route('/remove_sold_investment/<user_id>/<investment_id>')
def remove_sold_investment(user_id, investment_id):
    """Remove a sold investment"""
    user = None
    for u in program_data.users:
        if u.id == user_id:
            user = u
            break

    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('users'))

    if hasattr(user, 'remove_sold_investment') and user.remove_sold_investment(investment_id):
        flash('Sold investment removed successfully', 'success')
    else:
        flash('Failed to remove sold investment', 'danger')

    return redirect(url_for('user_profile', user_id=user.id))

@app.route('/refresh_investments/<user_id>')
def refresh_investments(user_id):
    """Force refresh of all investment data"""
    user = None
    for u in program_data.users:
        if u.id == user_id:
            user = u
            break

    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('users'))

    # Force update all investments
    user.update_all_investments(force=True)
    flash('Investment data refreshed successfully', 'success')

    return redirect(url_for('user_profile', user_id=user.id))

@app.route('/update_tags/<user_id>/<investment_id>', methods=['POST'])
def update_tags(user_id, investment_id):
    """Update tags for an investment"""
    user = None
    for u in program_data.users:
        if u.id == user_id:
            user = u
            break

    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('users'))

    investment = user.get_investment(investment_id)
    if not investment:
        flash('Investment not found', 'danger')
        return redirect(url_for('user_profile', user_id=user.id))

    # Get tags from form
    tags_str = request.form.get('tags', '')
    tags = [tag.strip() for tag in tags_str.split(',')] if tags_str.strip() else []

    # Update investment tags
    investment.tags = tags
    user.last_updated = datetime.datetime.now()

    flash('Tags updated successfully', 'success')
    return redirect(url_for('investment_details', user_id=user.id, investment_id=investment.id))

@app.route('/add_total_dividend/<user_id>', methods=['POST'])
def add_total_dividend(user_id):
    """Add a dividend to the total, not tied to any specific investment"""
    user = None
    for u in program_data.users:
        if u.id == user_id:
            user = u
            break

    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('users'))

    # Get dividend amount from form
    try:
        dividend_amount = float(request.form.get('dividend_amount', 0))
    except ValueError:
        flash('Invalid dividend amount', 'danger')
        return redirect(url_for('user_profile', user_id=user.id))

    if dividend_amount <= 0:
        flash('Dividend amount must be greater than zero', 'danger')
        return redirect(url_for('user_profile', user_id=user.id))

    # Get dividend date from form if provided
    dividend_date = None
    dividend_date_str = request.form.get('dividend_date')
    if dividend_date_str:
        try:
            # Parse the date string from the form
            dividend_date = datetime.datetime.strptime(dividend_date_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash('Invalid date format. Using current date.', 'warning')

    # Add the dividend to the total
    if hasattr(user, 'add_total_dividend') and user.add_total_dividend(dividend_amount, dividend_date):
        flash('Dividend added to total successfully', 'success')
    else:
        flash('Failed to add dividend to total', 'danger')

    return redirect(url_for('user_profile', user_id=user.id))

@app.route('/sell_investment/<user_id>/<investment_id>', methods=['POST'])
def sell_investment(user_id, investment_id):
    """Sell an investment"""
    user = None
    for u in program_data.users:
        if u.id == user_id:
            user = u
            break

    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('users'))

    investment = user.get_investment(investment_id)
    if not investment:
        flash('Investment not found', 'danger')
        return redirect(url_for('user_profile', user_id=user.id))

    # Get selling price from form
    try:
        selling_price = float(request.form.get('selling_price', 0))
    except ValueError:
        flash('Invalid selling price', 'danger')
        return redirect(url_for('investment_details', user_id=user.id, investment_id=investment.id))

    if selling_price <= 0:
        flash('Selling price must be greater than zero', 'danger')
        return redirect(url_for('investment_details', user_id=user.id, investment_id=investment.id))

    # Get sell date from form if provided
    sell_date = None
    sell_date_str = request.form.get('sell_date')
    if sell_date_str:
        try:
            # Parse the date string from the form
            sell_date = datetime.datetime.strptime(sell_date_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash('Invalid date format. Using current date.', 'warning')

    # Sell the investment
    if hasattr(user, 'sell_investment') and user.sell_investment(investment_id, selling_price, sell_date):
        flash('Investment sold successfully', 'success')
    else:
        flash('Failed to sell investment', 'danger')

    return redirect(url_for('user_profile', user_id=user.id))

@app.route('/tickers')
def tickers():
    """Show all tracked tickers"""
    return render_template('tickers.html', tickers=program_data.trackedTickers)

@app.route('/ticker/<ticker_id>')
def ticker_details(ticker_id):
    """Show ticker details"""
    ticker = None
    for t in program_data.trackedTickers:
        if t.tickerId == ticker_id:
            ticker = t
            break

    if not ticker:
        flash('Ticker not found', 'danger')
        return redirect(url_for('tickers'))

    # Update ticker data
    ticker.update_data()

    # Get price history
    price_history = ticker.get_price_history(days=90)

    # Create chart data
    if not price_history.empty:
        fig = px.line(price_history, 
                     title=f'Price History - {ticker.name}',
                     labels={'value': 'Price', 'index': 'Date'})
        chart_json = json.dumps(fig.to_dict(), cls=NumpyEncoder)
    else:
        chart_json = None

    return render_template('ticker_details.html', 
                          ticker=ticker,
                          chart_json=chart_json)

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    if not os.path.exists('templates'):
        os.makedirs('templates')

    app.run(debug=True)
