import requests
from datetime import datetime, timedelta
from config import API_KEY

def get_stock_info(symbol):
    url = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={API_KEY}'
    response = requests.get(url)
    data = response.json()
    if not data or "Note" in data or "Error Message" in data:
        return None
    return data

def get_news(symbol):
    url = f'https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={symbol}&apikey={API_KEY}'
    response = requests.get(url)
    news_data = response.json()
    
    return news_data.get('feed', [])[:5]

def get_quote(symbol):
    url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={API_KEY}'
    response = requests.get(url)
    quote = response.json()

    return quote


def get_52_week_high_low(symbol):
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_WEEKLY&symbol={symbol}&apikey={API_KEY}'
    response = requests.get(url)
    data = response.json()
    time_series = data.get('Weekly Time Series')
    if time_series is None:
        return None, None
    one_year_ago = datetime.now() - timedelta(weeks=52)
    highs = []
    lows = []

    for date, price_data in time_series.items():
        if datetime.strptime(date, '%Y-%m-%d') >= one_year_ago:
            highs.append(price_data['2. high'])
            lows.append(price_data['3. low'])
    
    week_52_high = max(highs) if highs else None
    week_52_low = min(lows) if lows else None

    return week_52_high, week_52_low

def get_daily_time_series(symbol):
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={API_KEY}&outputsize=full'
    response = requests.get(url)
    data = response.json()
    time_series = data.get('Time Series (Daily)', {})
    dates = []
    closing_prices = []
    one_year_ago = datetime.now() - timedelta(days=365)
    sorted_dates = sorted(time_series.keys())
    
    for date in sorted_dates:
        date_dt = datetime.strptime(date, '%Y-%m-%d')
        if date_dt >= one_year_ago:
            dates.append(date)
            closing_prices.append(time_series[date]['4. close'])

    return dates, closing_prices
