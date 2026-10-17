# Valuating Alphabet Inc. (GOOGL)

A Python script that estimates Alphabet's weighted average cost of capital (WACC) using market data from the [Alpha Vantage](https://www.alphavantage.co/) API.

## What it does

1. Pulls monthly prices for GOOGL and SPY (as the S&P 500 proxy).
2. Computes GOOGL's beta from the last ~24 monthly returns.
3. Gets market cap and total debt to calculate capital structure weights.
4. Calculates cost of equity (CAPM) and WACC.

Example output:

```
GOOGL Beta: 1.71
Weight of Equity: 97.12%
Weight of Debt: 2.88%
Cost of Equity: 11.15%
Cost of Debt: 0.79%
WACC: 10.85%
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Get a free API key from [Alpha Vantage](https://www.alphavantage.co/support/#api-key) and set it as an environment variable (never commit it):

```bash
export ALPHAVANTAGE_API_KEY="your_key"
```

## Run

```bash
python3 "GOOGL Valuation.py"
```

## Free-tier notes

- The free key allows about 1 request per second and 25 requests per day. The script pauses between requests.
- The `OVERVIEW` endpoint (market cap) is premium-only. If it fails, the script prompts you to enter market cap in $ billions manually. Total debt falls back to a prompt the same way.

## Assumptions (hardcoded in the script)

| Input | Value |
| --- | --- |
| Risk-free rate | 4.234% |
| Market equity risk premium | 4.04% |
| Cost of debt | 0.79% |
| Tax rate | 21% |

Update these to match current market conditions.

## Disclaimer

For educational purposes only. Not investment advice.
