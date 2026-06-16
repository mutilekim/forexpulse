"""
ForexPulse Data Fetcher
Fetches forex price data from Yahoo Finance (free, no API key required).
Author: Ruth Mutile Kimeu | BriefDesk Solutions
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta


# Major forex pairs to monitor
FOREX_PAIRS = {
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "USDJPY=X",
    "AUD/USD": "AUDUSD=X",
    "USD/CAD": "USDCAD=X",
    "NZD/USD": "NZDUSD=X",
    "USD/CHF": "USDCHF=X",
    "EUR/GBP": "EURGBP=X",
    "EUR/JPY": "EURJPY=X",
    "GBP/JPY": "GBPJPY=X",
}


def fetch_pair_data(
    pair_name: str,
    period: str = "1mo",
    interval: str = "1h",
) -> pd.DataFrame:
    """
    Fetch OHLCV data for a forex pair.

    Args:
        pair_name: Human-readable pair name (e.g. "EUR/USD")
        period: Data period ("1d", "5d", "1mo", "3mo", "6mo", "1y")
        interval: Candle interval ("1m", "5m", "15m", "1h", "4h", "1d")

    Returns:
        DataFrame with columns: open, high, low, close, volume
    """
    ticker_symbol = FOREX_PAIRS.get(pair_name)
    if not ticker_symbol:
        raise ValueError(f"Unknown pair: {pair_name}. Available: {list(FOREX_PAIRS.keys())}")

    ticker = yf.Ticker(ticker_symbol)
    df = ticker.history(period=period, interval=interval)

    if df.empty:
        raise ValueError(f"No data returned for {pair_name}")

    df.columns = [c.lower() for c in df.columns]
    df = df[["open", "high", "low", "close"]].copy()
    df.dropna(inplace=True)

    return df


def fetch_all_pairs(
    period: str = "1mo",
    interval: str = "1h",
) -> dict[str, pd.DataFrame]:
    """Fetch data for all monitored forex pairs."""
    results = {}
    for pair_name in FOREX_PAIRS:
        try:
            df = fetch_pair_data(pair_name, period, interval)
            if len(df) >= 50:
                results[pair_name] = df
                print(f"  Fetched {pair_name}: {len(df)} candles")
            else:
                print(f"  Skipped {pair_name}: only {len(df)} candles")
        except Exception as e:
            print(f"  Failed {pair_name}: {e}")
    return results


def fetch_daily_data(pair_name: str, months: int = 6) -> pd.DataFrame:
    """Fetch daily data for backtesting."""
    period = f"{months}mo"
    return fetch_pair_data(pair_name, period=period, interval="1d")


if __name__ == "__main__":
    print("Testing data fetcher...")
    print()

    df = fetch_pair_data("EUR/USD", period="5d", interval="1h")
    print(f"EUR/USD: {len(df)} hourly candles")
    print(df.tail())
    print()

    print("Fetching all pairs...")
    all_data = fetch_all_pairs(period="5d", interval="1h")
    print(f"\nSuccessfully fetched {len(all_data)} pairs")
