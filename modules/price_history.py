"""Module for downloading and processing stock price history in SimFin Analyzer."""

import pandas as pd
import yfinance as yf


def download_price_history_with_mavg(ticker_symbol, period="10y", interval="1d", moving_averages=None):
    """
    Downloads historical price data for a ticker and calculates specified moving averages.

    Args:
        ticker_symbol (str): The stock ticker.
        period (str): Period for historical data (e.g., "1mo", "6mo", "1y", "5y", "max").
        interval (str): Data interval (e.g., "1d", "1wk", "1mo").
        moving_averages (list of int, optional): List of window sizes for moving averages.
                                                 Defaults to None (no moving averages).

    Returns:
        pd.DataFrame: DataFrame with OHLC, Volume, and calculated moving averages, or None if error.
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        hist_df = ticker.history(period=period, interval=interval)

        if hist_df.empty:
            print(f"No price history found for {ticker_symbol} with period {period}, interval {interval}.")
            return None

        if moving_averages:
            for ma in moving_averages:
                if isinstance(ma, int) and ma > 0:
                    hist_df[f'MA{ma}'] = hist_df['Close'].rolling(window=ma).mean()
        
        return hist_df
    except Exception as e:
        print(f"Error downloading price history for {ticker_symbol}: {e}")
        return None


def calculate_additional_indicators(price_df):
    """
    Calculate additional technical indicators for a price DataFrame.
    
    Args:
        price_df (pd.DataFrame): Price DataFrame with OHLC data
        
    Returns:
        pd.DataFrame: DataFrame with additional indicators
    """
    if price_df is None or price_df.empty:
        return None
    
    result_df = price_df.copy()
    
    try:
        # Calculate daily returns
        result_df['Daily_Return'] = result_df['Close'].pct_change()
        
        # Calculate volatility (20-day rolling standard deviation of returns)
        result_df['Volatility_20d'] = result_df['Daily_Return'].rolling(window=20).std()
        
        # Calculate Bollinger Bands (20-day)
        result_df['SMA_20'] = result_df['Close'].rolling(window=20).mean()
        result_df['Upper_Band'] = result_df['SMA_20'] + (result_df['Close'].rolling(window=20).std() * 2)
        result_df['Lower_Band'] = result_df['SMA_20'] - (result_df['Close'].rolling(window=20).std() * 2)
        
        # Calculate simple momentum (price change over 10 days)
        result_df['Momentum_10d'] = result_df['Close'].diff(10)
        
        return result_df
    except Exception as e:
        print(f"Error calculating indicators: {e}")
        return price_df  # Return original dataframe if calculation fails


def get_price_summary_stats(price_df):
    """
    Generate summary statistics from price data.
    
    Args:
        price_df (pd.DataFrame): Price DataFrame with OHLC data
        
    Returns:
        dict: Dictionary with summary statistics
    """
    if price_df is None or price_df.empty:
        return {"error": "No price data available"}
    
    try:
        # Get basic stats
        current_price = price_df['Close'].iloc[-1]
        price_52w_high = price_df['High'].rolling(window=252).max().iloc[-1]
        price_52w_low = price_df['Low'].rolling(window=252).min().iloc[-1]
        
        # Calculate returns
        daily_returns = price_df['Close'].pct_change().dropna()
        ytd_return = (price_df['Close'].iloc[-1] / price_df['Close'].iloc[0] - 1) * 100
        
        # Calculate volatility
        volatility = daily_returns.std() * (252 ** 0.5) * 100  # Annualized volatility
        
        # Calculate volume statistics
        avg_volume = price_df['Volume'].mean()
        
        return {
            "current_price": current_price,
            "price_52w_high": price_52w_high,
            "price_52w_low": price_52w_low,
            "ytd_return_pct": ytd_return,
            "annualized_volatility_pct": volatility,
            "avg_daily_volume": avg_volume
        }
    except Exception as e:
        print(f"Error calculating price summary stats: {e}")
        return {"error": f"Error calculating stats: {e}"}
