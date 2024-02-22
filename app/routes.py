from flask import Blueprint, render_template, request
from .alphavantage import get_stock_info, get_news, get_quote, get_52_week_high_low, get_daily_time_series

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/stock_info', methods=['POST'])
def stock_info():
    stock_symbol = request.form['stock_symbol']
    data = get_stock_info(stock_symbol)
    if data is None or "Note" in data or "Error Message" in data:
        error_message = 'Stock symbol not found. Please try again.'
        return render_template('error.html', error_message=error_message)
    news = get_news(stock_symbol)
    quote = get_quote(stock_symbol)
    high_52, low_52 = get_52_week_high_low(stock_symbol)
    dates, closing_prices = get_daily_time_series(stock_symbol)
    return render_template('stock_info.html', data=data, news = news, quote = quote, high_52 = high_52, low_52 = low_52, dates = dates, closing_prices = closing_prices)