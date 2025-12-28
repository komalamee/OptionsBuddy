"""Mispricing detection for options."""

import logging
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field

import pandas as pd
import numpy as np

from .black_scholes import BlackScholes
from .volatility import VolatilityCalculator
from config.constants import (
    DEFAULT_IV_HV_THRESHOLD,
    CALL, PUT,
    HV_WINDOW_MEDIUM
)

logger = logging.getLogger(__name__)


@dataclass
class MispricingSignal:
    """Represents a mispricing signal for an option."""
    symbol: str
    expiry: str
    strike: float
    option_type: str

    # Prices
    market_price: float
    model_price: float
    underlying_price: float

    # Volatility
    iv: Optional[float]
    hv: Optional[float]

    # Mispricing metrics
    iv_hv_ratio: Optional[float]
    price_deviation_pct: float  # (market - model) / model * 100
    is_overpriced: bool  # True = good for selling premium

    # Greeks
    delta: Optional[float] = None
    theta: Optional[float] = None

    # Scoring
    mispricing_score: float = 0.0
    signals: List[str] = field(default_factory=list)

    @property
    def dte(self) -> int:
        """Days to expiration."""
        from datetime import date, datetime
        expiry_date = datetime.strptime(self.expiry, "%Y%m%d").date()
        return (expiry_date - date.today()).days


@dataclass
class ThresholdRules:
    """Configurable threshold rules for mispricing detection."""
    min_iv_hv_ratio: float = 1.0  # IV must be at least equal to HV
    target_iv_hv_ratio: float = DEFAULT_IV_HV_THRESHOLD  # Ideal: IV > HV by 20%
    max_price_deviation_pct: float = 20.0  # Max % model can deviate from market
    min_delta: float = 0.10
    max_delta: float = 0.40
    min_premium: float = 0.50
    min_dte: int = 7
    max_dte: int = 45


class MispricingDetector:
    """
    Detects mispriced options using Black-Scholes model and IV/HV comparison.

    Two primary methods:
    1. IV vs HV: Options where IV significantly exceeds HV are overpriced
       (good for premium sellers)
    2. Model vs Market: Compare Black-Scholes theoretical price to market price
    """

    def __init__(
        self,
        risk_free_rate: float = 0.05,
        rules: Optional[ThresholdRules] = None
    ):
        """
        Initialize the detector.

        Args:
            risk_free_rate: Annual risk-free rate for BS calculations
            rules: Threshold rules for filtering
        """
        self.bs = BlackScholes(risk_free_rate)
        self.rules = rules or ThresholdRules()

    def analyze_option(
        self,
        symbol: str,
        expiry: str,
        strike: float,
        option_type: str,
        market_price: float,
        underlying_price: float,
        iv: Optional[float],
        hv: Optional[float],
        delta: Optional[float] = None
    ) -> MispricingSignal:
        """
        Analyze a single option for mispricing.

        Args:
            symbol: Underlying symbol
            expiry: Expiration date (YYYYMMDD)
            strike: Strike price
            option_type: CALL or PUT
            market_price: Current market price (mid or last)
            underlying_price: Current underlying price
            iv: Implied volatility (as decimal)
            hv: Historical volatility (as decimal)
            delta: Option delta (if known)

        Returns:
            MispricingSignal with analysis results
        """
        from datetime import date, datetime

        # Calculate time to expiry
        expiry_date = datetime.strptime(expiry, "%Y%m%d").date()
        dte = (expiry_date - date.today()).days
        time_to_expiry = self.bs.days_to_years(dte)

        signals = []

        # Calculate model price using HV (what option "should" be worth based on realized vol)
        model_price = 0.0
        if hv and hv > 0:
            model_price = self.bs.calculate_price(
                underlying_price, strike, time_to_expiry, hv, option_type
            )

        # Calculate price deviation
        price_deviation_pct = 0.0
        if model_price > 0:
            price_deviation_pct = ((market_price - model_price) / model_price) * 100

        # Calculate IV/HV ratio
        iv_hv_ratio = None
        if iv and hv and hv > 0:
            iv_hv_ratio = iv / hv

        # Determine if overpriced (good for selling)
        is_overpriced = False
        if iv_hv_ratio and iv_hv_ratio > self.rules.min_iv_hv_ratio:
            is_overpriced = True
            signals.append(f"IV/HV ratio {iv_hv_ratio:.2f} > {self.rules.min_iv_hv_ratio}")

        if price_deviation_pct > 5:  # Market price > model by 5%+
            is_overpriced = True
            signals.append(f"Market price {price_deviation_pct:.1f}% above model")

        # Check for strong signals
        if iv_hv_ratio and iv_hv_ratio >= self.rules.target_iv_hv_ratio:
            signals.append(f"STRONG: IV/HV {iv_hv_ratio:.2f} >= target {self.rules.target_iv_hv_ratio}")

        # Calculate Greeks if not provided
        if delta is None and iv and iv > 0:
            greeks = self.bs.calculate_greeks(
                underlying_price, strike, time_to_expiry, iv, option_type
            )
            delta = greeks.delta
            theta = greeks.theta
        else:
            theta = None
            if iv and iv > 0:
                greeks = self.bs.calculate_greeks(
                    underlying_price, strike, time_to_expiry, iv, option_type
                )
                theta = greeks.theta

        return MispricingSignal(
            symbol=symbol,
            expiry=expiry,
            strike=strike,
            option_type=option_type,
            market_price=market_price,
            model_price=model_price,
            underlying_price=underlying_price,
            iv=iv,
            hv=hv,
            iv_hv_ratio=iv_hv_ratio,
            price_deviation_pct=price_deviation_pct,
            is_overpriced=is_overpriced,
            delta=delta,
            theta=theta,
            signals=signals
        )

    def analyze_chain(
        self,
        chain_df: pd.DataFrame,
        hv: float,
        apply_filters: bool = True
    ) -> pd.DataFrame:
        """
        Analyze entire option chain for mispricing opportunities.

        Args:
            chain_df: DataFrame with option chain data
            hv: Historical volatility for the underlying
            apply_filters: Whether to apply threshold filters

        Returns:
            DataFrame with mispricing analysis added
        """
        if chain_df.empty:
            return chain_df

        df = chain_df.copy()

        # Calculate model prices using HV
        df['hv'] = hv
        df['model_price'] = df.apply(
            lambda row: self._calculate_model_price(row, hv),
            axis=1
        )

        # Calculate IV/HV ratio
        df['iv_hv_ratio'] = df['iv'] / hv if hv > 0 else None

        # Calculate price deviation
        df['price_deviation_pct'] = np.where(
            df['model_price'] > 0,
            ((df['mid_price'] - df['model_price']) / df['model_price']) * 100,
            0
        )

        # Determine if overpriced
        df['is_overpriced'] = (
            (df['iv_hv_ratio'] > self.rules.min_iv_hv_ratio) |
            (df['price_deviation_pct'] > 5)
        )

        # Apply filters if requested
        if apply_filters:
            df = self._apply_filters(df)

        return df

    def _calculate_model_price(self, row: pd.Series, hv: float) -> float:
        """Calculate model price for a row."""
        from datetime import date, datetime

        try:
            expiry_date = datetime.strptime(str(row['expiry']), "%Y%m%d").date()
            dte = (expiry_date - date.today()).days
            time_to_expiry = self.bs.days_to_years(dte)

            if time_to_expiry <= 0 or hv <= 0:
                return 0.0

            price = self.bs.calculate_price(
                row['underlying_price'],
                row['strike'],
                time_to_expiry,
                hv,
                row['option_type']
            )
            return price
        except Exception as e:
            logger.debug(f"Error calculating model price: {e}")
            return 0.0

    def _apply_filters(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply threshold rules to filter options."""
        if df.empty:
            return df

        # Calculate mid price if not present
        if 'mid_price' not in df.columns:
            df['mid_price'] = (df['bid'] + df['ask']) / 2

        # Calculate DTE if not present
        if 'dte' not in df.columns:
            from datetime import date, datetime
            df['dte'] = df['expiry'].apply(
                lambda x: (datetime.strptime(str(x), "%Y%m%d").date() - date.today()).days
            )

        # Apply filters
        mask = pd.Series(True, index=df.index)

        # DTE range
        mask &= df['dte'] >= self.rules.min_dte
        mask &= df['dte'] <= self.rules.max_dte

        # Delta range (use absolute value for puts)
        if 'delta' in df.columns:
            abs_delta = df['delta'].abs()
            mask &= abs_delta >= self.rules.min_delta
            mask &= abs_delta <= self.rules.max_delta

        # Minimum premium
        mask &= df['bid'] >= self.rules.min_premium

        # IV/HV ratio
        if 'iv_hv_ratio' in df.columns:
            mask &= df['iv_hv_ratio'] >= self.rules.min_iv_hv_ratio

        return df[mask].copy()

    def find_opportunities(
        self,
        chain_df: pd.DataFrame,
        hv: float,
        option_types: List[str] = None,
        top_n: int = 10
    ) -> List[MispricingSignal]:
        """
        Find top mispricing opportunities in an option chain.

        Args:
            chain_df: DataFrame with option chain data
            hv: Historical volatility for the underlying
            option_types: Filter by option types
            top_n: Number of top opportunities to return

        Returns:
            List of MispricingSignal objects sorted by score
        """
        if chain_df.empty:
            return []

        df = self.analyze_chain(chain_df, hv, apply_filters=True)

        if df.empty:
            return []

        # Filter by option type if specified
        if option_types:
            df = df[df['option_type'].isin(option_types)]

        if df.empty:
            return []

        # Convert to signals
        signals = []
        for _, row in df.iterrows():
            signal = self.analyze_option(
                symbol=row['symbol'],
                expiry=str(row['expiry']),
                strike=row['strike'],
                option_type=row['option_type'],
                market_price=row.get('mid_price', (row['bid'] + row['ask']) / 2),
                underlying_price=row['underlying_price'],
                iv=row.get('iv'),
                hv=hv,
                delta=row.get('delta')
            )
            signals.append(signal)

        # Sort by mispricing score (we'll calculate this in scoring module)
        # For now, sort by IV/HV ratio
        signals.sort(
            key=lambda s: s.iv_hv_ratio if s.iv_hv_ratio else 0,
            reverse=True
        )

        return signals[:top_n]

    def update_rules(self, **kwargs) -> None:
        """Update threshold rules with new values."""
        for key, value in kwargs.items():
            if hasattr(self.rules, key):
                setattr(self.rules, key, value)
