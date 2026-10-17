import os
import sys
import time
import requests
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Load API Key from environment variable for security
# (set it with: export ALPHAVANTAGE_API_KEY="your_key")
API_KEY = os.getenv("ALPHAVANTAGE_API_KEY")
if not API_KEY:
    sys.exit("Set the ALPHAVANTAGE_API_KEY environment variable first.")

BASE_URL = "https://www.alphavantage.co/query"
SYMBOL = "GOOGL"
SP500_SYMBOL = "SPY"


def av_request(params):
    # Call Alpha Vantage and return the JSON, or None (with a message) on failure.
    time.sleep(1.5)  # free tier allows ~1 request per second
    response = requests.get(BASE_URL, params={**params, "apikey": API_KEY}, timeout=30)
    if response.status_code != 200:
        print(f"HTTP {response.status_code} for {params.get('function')}.")
        return None
    data = response.json()
    # Alpha Vantage reports rate limits / bad keys in 200 responses
    for key in ("Error Message", "Note", "Information"):
        if key in data:
            print(f"Alpha Vantage: {data[key]}")
            return None
    return data


# Function to fetch time series data
def get_historical_data(symbol):
    # Monthly series is free and has full history (daily outputsize=full is premium)
    data = av_request({"function": "TIME_SERIES_MONTHLY", "symbol": symbol})
    if data and "Monthly Time Series" in data:
        df = pd.DataFrame.from_dict(data["Monthly Time Series"], orient="index").astype(
            float
        )
        df.index = pd.to_datetime(df.index)
        return df.sort_index()
    print(f"Error fetching data for {symbol}.")
    return None


# Fetch data for GOOGL and S&P 500
googl_data = get_historical_data(SYMBOL)
sp500_data = get_historical_data(SP500_SYMBOL)
if googl_data is None or sp500_data is None:
    sys.exit("Could not fetch price data.")

# Select last 2 years of data
end_date = datetime.today()
start_date = end_date - timedelta(days=760)  # extra month so we get 24 returns
googl_data = googl_data.loc[start_date:end_date]
sp500_data = sp500_data.loc[start_date:end_date]

# Calculate monthly returns ('ME' = month end; 'M' is removed in newer pandas)
googl_returns = googl_data["4. close"].resample("ME").last().pct_change().dropna()
sp500_returns = sp500_data["4. close"].resample("ME").last().pct_change().dropna()

# Compute beta
aligned_data = pd.DataFrame({"GOOGL": googl_returns, "SP500": sp500_returns}).dropna()
beta, _ = np.polyfit(aligned_data["SP500"], aligned_data["GOOGL"], 1)
print(f"GOOGL Beta: {beta:.2f}")


# Fetch market cap and total debt
def num(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def ask_billions(label):
    # Fallback when an endpoint is premium-only on the free key
    while True:
        try:
            return float(input(f"Enter {label} in $ billions: ")) * 1e9
        except ValueError:
            print("Please enter a number, e.g. 3800")


def get_market_cap(symbol):
    overview = av_request({"function": "OVERVIEW", "symbol": symbol})
    return num(overview.get("MarketCapitalization")) if overview else 0.0


def get_total_debt(symbol):
    # OVERVIEW has no debt field; take it from the latest balance sheet
    balance = av_request({"function": "BALANCE_SHEET", "symbol": symbol})
    if not balance or not balance.get("quarterlyReports"):
        return 0.0
    latest = balance["quarterlyReports"][0]
    total_debt = num(latest.get("shortLongTermDebtTotal"))
    if not total_debt:
        total_debt = num(latest.get("longTermDebt")) + num(latest.get("currentDebt"))
    return total_debt


current_price = googl_data["4. close"].iloc[-1]

market_cap = get_market_cap(SYMBOL)
if not market_cap:
    print("Could not fetch market cap from the API; enter it manually.")
    market_cap = ask_billions("GOOGL market cap")

total_debt = get_total_debt(SYMBOL)
if not total_debt:
    print("Could not fetch total debt from the API; enter it manually.")
    total_debt = ask_billions("GOOGL total debt (short + long term)")

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
wacc = (weight_of_equity * cost_of_equity) + (
    weight_of_debt * cost_of_debt * (1 - tax_rate)
)

print(f"Cost of Equity: {cost_of_equity:.2%}")
print(f"Cost of Debt: {cost_of_debt:.2%}")
print(f"WACC: {wacc:.2%}")
