"""Historical data fetching for volatility calculations."""

import logging
from typing import Optional, List
from datetime import datetime, timedelta

import pandas as pd
import numpy as np
from ib_insync import util

from .ibkr_client import get_ibkr_client
from config.constants import TRADING_DAYS_PER_YEAR

logger = logging.getLogger(__name__)


class HistoricalDataFetcher:
    """Fetches historical price data from IBKR for volatility calculations."""

    def __init__(self):
        self.client = get_ibkr_client()
        self._cache = {}  # Simple in-memory cache

    def get_historical_bars(
        self,
        symbol: str,
        duration: str = "1 Y",
        bar_size: str = "1 day",
        what_to_show: str = "TRADES",
        use_rth: bool = True
    ) -> pd.DataFrame:
        """
        Fetch historical OHLCV data.

        Args:
            symbol: Stock symbol
            duration: How far back (e.g., "1 Y", "6 M", "30 D")
            bar_size: Bar size (e.g., "1 day", "1 hour")
            what_to_show: Data type (TRADES, MIDPOINT, BID, ASK)
            use_rth: Use regular trading hours only

        Returns:
            DataFrame with OHLCV data
        """
        if not self.client.ensure_connected():
            logger.error("Not connected to IBKR")
            return pd.DataFrame()

        cache_key = f"{symbol}_{duration}_{bar_size}"
        if cache_key in self._cache:
            cached_data, cache_time = self._cache[cache_key]
            # Cache valid for 1 hour
            if datetime.now() - cache_time < timedelta(hours=1):
                return cached_data.copy()

        try:
            contract = self.client.create_stock_contract(symbol)
            self.client.qualify_contracts([contract])

            bars = self.client.ib.reqHistoricalData(
                contract,
                endDateTime='',
                durationStr=duration,
                barSizeSetting=bar_size,
                whatToShow=what_to_show,
                useRTH=use_rth,
                formatDate=1
            )

            if not bars:
                logger.warning(f"No historical data for {symbol}")
                return pd.DataFrame()

            # Convert to DataFrame
            df = util.df(bars)
            df = df.rename(columns={
                'date': 'Date',
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close',
                'volume': 'Volume'
            })

            # Ensure Date is datetime
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])
                df = df.set_index('Date')

            # Cache the result
            self._cache[cache_key] = (df.copy(), datetime.now())

            return df

        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return pd.DataFrame()

    def get_closing_prices(
        self,
        symbol: str,
        lookback_days: int = 252
    ) -> pd.Series:
        """Get closing prices for the specified lookback period."""
        # Calculate duration string
        if lookback_days <= 30:
            duration = f"{lookback_days} D"
        elif lookback_days <= 365:
            months = (lookback_days // 30) + 1
            duration = f"{months} M"
        else:
            years = (lookback_days // 252) + 1
            duration = f"{years} Y"

        df = self.get_historical_bars(symbol, duration=duration)

        if df.empty:
            return pd.Series(dtype=float)

        return df['Close']

    def calculate_returns(
        self,
        prices: pd.Series,
        log_returns: bool = True
    ) -> pd.Series:
        """Calculate returns from price series."""
        if prices.empty or len(prices) < 2:
            return pd.Series(dtype=float)

        if log_returns:
            returns = np.log(prices / prices.shift(1))
        else:
            returns = prices.pct_change()

        return returns.dropna()

    def calculate_historical_volatility(
        self,
        symbol: str,
        window: int = 21,
        lookback_days: int = 252,
        annualize: bool = True
    ) -> Optional[float]:
        """
        Calculate historical volatility using standard rolling std of log returns.

        Args:
            symbol: Stock symbol
            window: Rolling window for std calculation (trading days)
            lookback_days: How far back to fetch data
            annualize: Whether to annualize the volatility

        Returns:
            Historical volatility as decimal (e.g., 0.25 for 25%)
        """
        prices = self.get_closing_prices(symbol, lookback_days)
        if prices.empty or len(prices) < window + 1:
            return None

        returns = self.calculate_returns(prices)
        if returns.empty:
            return None

        # Calculate rolling std
        rolling_std = returns.rolling(window=window).std()

        # Get the most recent value
        hv = rolling_std.iloc[-1]

        if pd.isna(hv):
            return None

        # Annualize if requested
        if annualize:
            hv = hv * np.sqrt(TRADING_DAYS_PER_YEAR)

        return float(hv)

    def calculate_volatility_cone(
        self,
        symbol: str,
        windows: List[int] = None,
        lookback_days: int = 252
    ) -> pd.DataFrame:
        """
        Calculate volatility cone with multiple windows.

        Returns DataFrame with columns for each window showing
        min, 25th percentile, median, 75th percentile, max, and current HV.
        """
        if windows is None:
            windows = [10, 21, 63, 126, 252]

        prices = self.get_closing_prices(symbol, lookback_days * 2)  # Extra data for calculation
        if prices.empty:
            return pd.DataFrame()

        returns = self.calculate_returns(prices)
        if returns.empty:
            return pd.DataFrame()

        cone_data = []
        for window in windows:
            if len(returns) < window:
                continue

            rolling_vol = returns.rolling(window=window).std() * np.sqrt(TRADING_DAYS_PER_YEAR)
            rolling_vol = rolling_vol.dropna()

            if rolling_vol.empty:
                continue

            cone_data.append({
                'window': window,
                'min': rolling_vol.min(),
                'pct_25': rolling_vol.quantile(0.25),
                'median': rolling_vol.median(),
                'pct_75': rolling_vol.quantile(0.75),
                'max': rolling_vol.max(),
                'current': rolling_vol.iloc[-1]
            })

        return pd.DataFrame(cone_data)

    def get_volatility_history(
        self,
        symbol: str,
        window: int = 21,
        lookback_days: int = 252
    ) -> pd.Series:
        """Get historical volatility time series."""
        prices = self.get_closing_prices(symbol, lookback_days)
        if prices.empty:
            return pd.Series(dtype=float)

        returns = self.calculate_returns(prices)
        if returns.empty:
            return pd.Series(dtype=float)

        hv = returns.rolling(window=window).std() * np.sqrt(TRADING_DAYS_PER_YEAR)
        return hv.dropna()

    def clear_cache(self) -> None:
        """Clear the data cache."""
        self._cache.clear()
