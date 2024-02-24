import sqlite3
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

'''
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
'''

def create_stock_data_table():
    conn = sqlite3.connect('stock_data.db')
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stock_data (
            stock_symbol VARCHAR(5) NOT NULL,
            closing_date DATE NOT NULL,
            open_price DECIMAL(16, 6) NOT NULL,
            high_price DECIMAL(16, 6) NOT NULL,
            low_price DECIMAL(16, 6) NOT NULL,
            close_price DECIMAL(16, 6) NOT NULL,
            adj_close_price DECIMAL(16, 6) NOT NULL,
            volume BIGINT NOT NULL,
            PRIMARY KEY (stock_symbol, closing_date)
        )
    """)
    conn.commit()
    conn.close()

create_stock_data_table()


def check_stock_data_in_db(symbol):
    # Connect to the SQLite database
    conn = sqlite3.connect('stock_data.db')
    cursor = conn.cursor()
    one_year_ago = datetime.now() - timedelta(days=365)
    
    query = """
    SELECT stock_symbol, closing_date, open_price, high_price, low_price, close_price, adj_close_price, volume
    FROM stock_data
    WHERE stock_symbol = ? AND closing_date >= ?
    ORDER BY closing_date ASC;
    """
    cursor.execute(query, (symbol, one_year_ago.strftime('%Y-%m-%d')))
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_daily_time_series(symbol):
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={symbol}&apikey={API_KEY}&outputsize=full'
    response = requests.get(url)
    data = response.json()
    time_series = data.get('Time Series (Daily)', {})
    one_year_ago = datetime.now() - timedelta(days=365)
    rows_to_insert = []
    for date_str, daily_data in time_series.items():
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        if date_obj >= one_year_ago:
            row = (
                symbol,
                date_str,
                float(daily_data['1. open']),
                float(daily_data['2. high']),
                float(daily_data['3. low']),
                float(daily_data['4. close']),
                float(daily_data['5. adjusted close']),
                int(daily_data['6. volume']),
            )
            rows_to_insert.append(row)

    return rows_to_insert


def store_stock_data_to_db(rows_to_insert):
    conn = sqlite3.connect('stock_data.db')
    cursor = conn.cursor()
    insert_query = """
    INSERT OR IGNORE INTO stock_data 
    (stock_symbol, closing_date, open_price, high_price, low_price, close_price, adj_close_price, volume)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    cursor.executemany(insert_query, rows_to_insert)
    conn.commit()
    conn.close()


def check_and_update_data(symbol):
    existing_data = check_stock_data_in_db(symbol)
    if not existing_data:
        print(f"No existing data for {symbol} found in database. Fetching from API...")
        new_data = get_daily_time_series(symbol)
        if new_data:
            store_stock_data_to_db(new_data)
            print(f"Data for {symbol} fetched from API and stored in database.")
            return new_data
        else:
            print(f"Failed to fetch data for {symbol} from API.")
            return None
    else:
        print(f"Using existing data for {symbol} from database.")
        one_year_ago = datetime.now() - timedelta(days=365)
        filtered_data = [row for row in existing_data if datetime.strptime(row[1], '%Y-%m-%d') >= one_year_ago]
        return filtered_data
