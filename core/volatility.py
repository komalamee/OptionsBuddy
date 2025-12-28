"""Volatility calculation methods."""

import logging
from typing import Optional, List, Dict, Any

import numpy as np
import pandas as pd

from config.constants import (
    TRADING_DAYS_PER_YEAR,
    HV_WINDOW_SHORT,
    HV_WINDOW_MEDIUM,
    HV_WINDOW_LONG
)

logger = logging.getLogger(__name__)


class VolatilityCalculator:
    """
    Calculate historical volatility using multiple methods.

    Supports:
    - Standard (close-to-close)
    - Parkinson (high-low range)
    - Garman-Klass (OHLC)
    - Rogers-Satchell (OHLC, no drift assumption)
    """

    @staticmethod
    def calculate_standard(
        prices: pd.Series,
        window: int = HV_WINDOW_MEDIUM,
        annualize: bool = True
    ) -> Optional[float]:
        """
        Calculate standard close-to-close volatility.

        This is the most common method: rolling standard deviation
        of log returns, annualized.

        Args:
            prices: Series of closing prices
            window: Rolling window in trading days
            annualize: Whether to annualize the result

        Returns:
            Volatility as decimal (e.g., 0.25 for 25%)
        """
        if prices is None or len(prices) < window + 1:
            return None

        # Calculate log returns
        log_returns = np.log(prices / prices.shift(1)).dropna()

        if len(log_returns) < window:
            return None

        # Rolling standard deviation
        rolling_std = log_returns.rolling(window=window).std()

        # Get most recent value
        hv = rolling_std.iloc[-1]

        if pd.isna(hv):
            return None

        if annualize:
            hv = hv * np.sqrt(TRADING_DAYS_PER_YEAR)

        return float(hv)

    @staticmethod
    def calculate_parkinson(
        high: pd.Series,
        low: pd.Series,
        window: int = HV_WINDOW_MEDIUM,
        annualize: bool = True
    ) -> Optional[float]:
        """
        Calculate Parkinson volatility using high-low range.

        More efficient than close-to-close as it uses intraday information.
        Assumes no drift and continuous prices.

        Args:
            high: Series of high prices
            low: Series of low prices
            window: Rolling window in trading days
            annualize: Whether to annualize the result

        Returns:
            Volatility as decimal
        """
        if high is None or low is None or len(high) < window:
            return None

        # Parkinson estimator
        log_hl = np.log(high / low) ** 2
        factor = 1 / (4 * np.log(2))

        variance = factor * log_hl.rolling(window=window).mean()
        volatility = np.sqrt(variance)

        hv = volatility.iloc[-1]

        if pd.isna(hv):
            return None

        if annualize:
            hv = hv * np.sqrt(TRADING_DAYS_PER_YEAR)

        return float(hv)

    @staticmethod
    def calculate_garman_klass(
        open_prices: pd.Series,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        window: int = HV_WINDOW_MEDIUM,
        annualize: bool = True
    ) -> Optional[float]:
        """
        Calculate Garman-Klass volatility using OHLC data.

        More efficient than Parkinson, using both overnight and intraday info.

        Args:
            open_prices: Series of open prices
            high: Series of high prices
            low: Series of low prices
            close: Series of close prices
            window: Rolling window in trading days
            annualize: Whether to annualize the result

        Returns:
            Volatility as decimal
        """
        if any(x is None or len(x) < window for x in [open_prices, high, low, close]):
            return None

        log_hl = np.log(high / low) ** 2
        log_co = np.log(close / open_prices) ** 2

        # Garman-Klass estimator
        variance = 0.5 * log_hl - (2 * np.log(2) - 1) * log_co
        variance = variance.rolling(window=window).mean()
        volatility = np.sqrt(variance)

        hv = volatility.iloc[-1]

        if pd.isna(hv):
            return None

        if annualize:
            hv = hv * np.sqrt(TRADING_DAYS_PER_YEAR)

        return float(hv)

    @staticmethod
    def calculate_rogers_satchell(
        open_prices: pd.Series,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        window: int = HV_WINDOW_MEDIUM,
        annualize: bool = True
    ) -> Optional[float]:
        """
        Calculate Rogers-Satchell volatility.

        Does not assume zero drift, making it suitable for trending markets.

        Args:
            open_prices: Series of open prices
            high: Series of high prices
            low: Series of low prices
            close: Series of close prices
            window: Rolling window in trading days
            annualize: Whether to annualize the result

        Returns:
            Volatility as decimal
        """
        if any(x is None or len(x) < window for x in [open_prices, high, low, close]):
            return None

        log_ho = np.log(high / open_prices)
        log_hc = np.log(high / close)
        log_lo = np.log(low / open_prices)
        log_lc = np.log(low / close)

        # Rogers-Satchell estimator
        variance = log_ho * log_hc + log_lo * log_lc
        variance = variance.rolling(window=window).mean()

        # Handle negative values (can happen in low volatility)
        variance = variance.clip(lower=0)
        volatility = np.sqrt(variance)

        hv = volatility.iloc[-1]

        if pd.isna(hv):
            return None

        if annualize:
            hv = hv * np.sqrt(TRADING_DAYS_PER_YEAR)

        return float(hv)

    @staticmethod
    def calculate_all_methods(
        df: pd.DataFrame,
        window: int = HV_WINDOW_MEDIUM
    ) -> Dict[str, Optional[float]]:
        """
        Calculate volatility using all available methods.

        Args:
            df: DataFrame with OHLC columns (Open, High, Low, Close)
            window: Rolling window in trading days

        Returns:
            Dictionary with volatility by method
        """
        results = {}

        # Standard (close-to-close)
        if 'Close' in df.columns:
            results['standard'] = VolatilityCalculator.calculate_standard(
                df['Close'], window
            )

        # Parkinson (high-low)
        if 'High' in df.columns and 'Low' in df.columns:
            results['parkinson'] = VolatilityCalculator.calculate_parkinson(
                df['High'], df['Low'], window
            )

        # Garman-Klass (OHLC)
        if all(col in df.columns for col in ['Open', 'High', 'Low', 'Close']):
            results['garman_klass'] = VolatilityCalculator.calculate_garman_klass(
                df['Open'], df['High'], df['Low'], df['Close'], window
            )
            results['rogers_satchell'] = VolatilityCalculator.calculate_rogers_satchell(
                df['Open'], df['High'], df['Low'], df['Close'], window
            )

        return results

    @staticmethod
    def calculate_volatility_percentile(
        prices: pd.Series,
        current_window: int = HV_WINDOW_MEDIUM,
        lookback_days: int = 252
    ) -> Optional[float]:
        """
        Calculate where current volatility sits relative to historical range.

        Args:
            prices: Series of closing prices
            current_window: Window for current HV calculation
            lookback_days: How far back to look for percentile

        Returns:
            Percentile (0-100) of current volatility
        """
        if prices is None or len(prices) < lookback_days:
            return None

        log_returns = np.log(prices / prices.shift(1)).dropna()
        if len(log_returns) < current_window:
            return None

        rolling_vol = log_returns.rolling(window=current_window).std()
        rolling_vol = rolling_vol.dropna()

        if len(rolling_vol) < 2:
            return None

        current_vol = rolling_vol.iloc[-1]

        # Calculate percentile
        percentile = (rolling_vol < current_vol).sum() / len(rolling_vol) * 100

        return float(percentile)

    @staticmethod
    def get_volatility_summary(
        df: pd.DataFrame,
        windows: List[int] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive volatility summary.

        Args:
            df: DataFrame with OHLC data
            windows: List of windows to calculate

        Returns:
            Summary dictionary with all volatility metrics
        """
        if windows is None:
            windows = [HV_WINDOW_SHORT, HV_WINDOW_MEDIUM, HV_WINDOW_LONG]

        summary = {
            'by_window': {},
            'by_method': {},
            'percentile': None
        }

        if 'Close' not in df.columns:
            return summary

        # Calculate for each window
        for window in windows:
            summary['by_window'][window] = VolatilityCalculator.calculate_standard(
                df['Close'], window
            )

        # Calculate using different methods (medium window)
        summary['by_method'] = VolatilityCalculator.calculate_all_methods(
            df, HV_WINDOW_MEDIUM
        )

        # Calculate percentile
        summary['percentile'] = VolatilityCalculator.calculate_volatility_percentile(
            df['Close']
        )

        return summary
