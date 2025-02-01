import os
import requests
import numpy as np
import pandas as pd
from datetime import datetime

# Load API Key from environment variable for security
API_KEY = os.getenv("PSIPB7O0KFTWDTIN")
BASE_URL = 'https://www.alphavantage.co/query'
SYMBOL = 'GOOGL'
SP500_SYMBOL = 'SPY'

# Function to fetch time series data
def get_historical_data(symbol):
    params = {
        'function': 'TIME_SERIES_DAILY',
        'symbol': symbol,
        'outputsize': 'full',
        'apikey': API_KEY
    }
    response = requests.get(BASE_URL, params=params)
    if response.status_code == 200:
        data = response.json()
        if 'Time Series (Daily)' in data:
            df = pd.DataFrame.from_dict(data['Time Series (Daily)'], orient='index').astype(float)
            df.index = pd.to_datetime(df.index)
            df = df.sort_index()
            return df
    print(f"Error fetching data for {symbol}.")
    return None

# Fetch data for GOOGL and S&P 500
googl_data = get_historical_data(SYMBOL)
sp500_data = get_historical_data(SP500_SYMBOL)

if googl_data is not None and sp500_data is not None:
    # Select last 2 years of data
    start_date = datetime(2022, 11, 20)
    end_date = datetime.today()
    googl_data = googl_data.loc[start_date:end_date]
    sp500_data = sp500_data.loc[start_date:end_date]

    # Calculate monthly returns
    googl_returns = googl_data['4. close'].resample('M').last().pct_change().dropna()
    sp500_returns = sp500_data['4. close'].resample('M').last().pct_change().dropna()

    # Compute beta
    aligned_data = pd.DataFrame({'GOOGL': googl_returns, 'SP500': sp500_returns}).dropna()
    beta, _ = np.polyfit(aligned_data['SP500'], aligned_data['GOOGL'], 1)
    print(f"GOOGL Beta: {beta:.2f}")

# Fetch market cap and stock price
def get_stock_metrics(symbol):
    params = {'function': 'OVERVIEW', 'symbol': symbol, 'apikey': API_KEY}
    response = requests.get(BASE_URL, params=params)
    data = response.json()
    if data:
        market_cap = float(data.get('MarketCapitalization', 0))
        total_debt = float(data.get('TotalDebt', 0))
        return market_cap, total_debt
    return None, None

market_cap, total_debt = get_stock_metrics(SYMBOL)
current_price = googl_data['4. close'].iloc[-1] if googl_data is not None else None

if market_cap and total_debt and current_price:
    implied_shares_outstanding = market_cap / current_price
    total_value = market_cap + total_debt
    weight_of_equity = market_cap / total_value
    weight_of_debt = total_debt / total_value
    print(f"Weight of Equity: {weight_of_equity:.2%}")
    print(f"Weight of Debt: {weight_of_debt:.2%}")

# Compute WACC
risk_free_rate = 0.04234  # 4.234%
market_equity_risk_premium = 0.0404  # 4.04%
cost_of_equity = risk_free_rate + beta * market_equity_risk_premium

effective_interest_rate = 0.0079  # 0.79%
cost_of_debt = effective_interest_rate

tax_rate = 0.21  # 21% assumed corporate tax rate
wacc = (weight_of_equity * cost_of_equity) + (weight_of_debt * cost_of_debt * (1 - tax_rate))

print(f"Cost of Equity: {cost_of_equity:.2%}")
print(f"Cost of Debt: {cost_of_debt:.2%}")
print(f"WACC: {wacc:.2%}")
