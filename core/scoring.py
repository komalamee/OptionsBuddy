"""Opportunity scoring and ranking."""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

import pandas as pd
import numpy as np

from .mispricing import MispricingSignal

logger = logging.getLogger(__name__)


@dataclass
class ScoringWeights:
    """Weights for different scoring components."""
    iv_hv_ratio: float = 0.30  # Higher IV/HV = more premium
    price_deviation: float = 0.20  # Market > Model = overpriced
    delta_optimal: float = 0.15  # Prefer certain delta range
    theta_decay: float = 0.15  # Higher theta = faster decay
    liquidity: float = 0.10  # Tighter spreads = better fills
    dte_optimal: float = 0.10  # Prefer certain DTE range


class OpportunityScorer:
    """
    Scores and ranks option opportunities based on multiple factors.

    The goal is to identify the best premium-selling opportunities
    considering mispricing signals, Greeks, and liquidity.
    """

    def __init__(
        self,
        weights: Optional[ScoringWeights] = None,
        optimal_delta_range: tuple = (0.20, 0.30),
        optimal_dte_range: tuple = (14, 35)
    ):
        """
        Initialize the scorer.

        Args:
            weights: Scoring weights for each component
            optimal_delta_range: Preferred delta range for scoring
            optimal_dte_range: Preferred DTE range for scoring
        """
        self.weights = weights or ScoringWeights()
        self.optimal_delta_range = optimal_delta_range
        self.optimal_dte_range = optimal_dte_range

    def score_opportunity(
        self,
        signal: MispricingSignal,
        spread_pct: float = None
    ) -> float:
        """
        Calculate composite score for a mispricing signal.

        Args:
            signal: MispricingSignal to score
            spread_pct: Bid-ask spread as percentage (for liquidity scoring)

        Returns:
            Score from 0-100 (higher is better)
        """
        scores = {}

        # 1. IV/HV Ratio Score (0-100)
        # Higher ratio = more overpriced = better for selling
        if signal.iv_hv_ratio:
            if signal.iv_hv_ratio >= 1.5:
                scores['iv_hv'] = 100
            elif signal.iv_hv_ratio >= 1.3:
                scores['iv_hv'] = 80
            elif signal.iv_hv_ratio >= 1.2:
                scores['iv_hv'] = 60
            elif signal.iv_hv_ratio >= 1.1:
                scores['iv_hv'] = 40
            elif signal.iv_hv_ratio >= 1.0:
                scores['iv_hv'] = 20
            else:
                scores['iv_hv'] = 0
        else:
            scores['iv_hv'] = 0

        # 2. Price Deviation Score (0-100)
        # Positive deviation = market > model = overpriced
        if signal.price_deviation_pct > 20:
            scores['price_dev'] = 100
        elif signal.price_deviation_pct > 10:
            scores['price_dev'] = 70
        elif signal.price_deviation_pct > 5:
            scores['price_dev'] = 50
        elif signal.price_deviation_pct > 0:
            scores['price_dev'] = 30
        else:
            scores['price_dev'] = 0

        # 3. Delta Score (0-100)
        # Prefer delta in optimal range
        if signal.delta:
            abs_delta = abs(signal.delta)
            min_d, max_d = self.optimal_delta_range
            if min_d <= abs_delta <= max_d:
                scores['delta'] = 100
            elif abs_delta < min_d:
                # Too far OTM
                scores['delta'] = max(0, 100 - (min_d - abs_delta) * 500)
            else:
                # Too close to ITM
                scores['delta'] = max(0, 100 - (abs_delta - max_d) * 200)
        else:
            scores['delta'] = 50  # Neutral if unknown

        # 4. Theta Score (0-100)
        # Higher (less negative) theta = more premium per day
        if signal.theta:
            # Theta is typically negative, so more negative = faster decay
            abs_theta = abs(signal.theta)
            if abs_theta >= 0.05:
                scores['theta'] = 100
            elif abs_theta >= 0.03:
                scores['theta'] = 70
            elif abs_theta >= 0.01:
                scores['theta'] = 40
            else:
                scores['theta'] = 20
        else:
            scores['theta'] = 50

        # 5. Liquidity Score (0-100)
        # Tighter spread = better
        if spread_pct is not None:
            if spread_pct <= 2:
                scores['liquidity'] = 100
            elif spread_pct <= 5:
                scores['liquidity'] = 70
            elif spread_pct <= 10:
                scores['liquidity'] = 40
            else:
                scores['liquidity'] = 20
        else:
            scores['liquidity'] = 50

        # 6. DTE Score (0-100)
        # Prefer DTE in optimal range
        dte = signal.dte
        min_dte, max_dte = self.optimal_dte_range
        if min_dte <= dte <= max_dte:
            scores['dte'] = 100
        elif dte < min_dte:
            scores['dte'] = max(0, 100 - (min_dte - dte) * 10)
        else:
            scores['dte'] = max(0, 100 - (dte - max_dte) * 2)

        # Calculate weighted score
        total_score = (
            scores['iv_hv'] * self.weights.iv_hv_ratio +
            scores['price_dev'] * self.weights.price_deviation +
            scores['delta'] * self.weights.delta_optimal +
            scores['theta'] * self.weights.theta_decay +
            scores['liquidity'] * self.weights.liquidity +
            scores['dte'] * self.weights.dte_optimal
        )

        return round(total_score, 1)

    def score_and_rank(
        self,
        signals: List[MispricingSignal],
        chain_df: pd.DataFrame = None
    ) -> List[MispricingSignal]:
        """
        Score and rank a list of mispricing signals.

        Args:
            signals: List of MispricingSignal objects
            chain_df: Optional DataFrame with spread data

        Returns:
            List of signals sorted by score (highest first)
        """
        if not signals:
            return []

        # Calculate spread percentages if chain data available
        spread_map = {}
        if chain_df is not None and not chain_df.empty:
            for _, row in chain_df.iterrows():
                key = (row['expiry'], row['strike'], row['option_type'])
                mid = (row['bid'] + row['ask']) / 2
                spread = row['ask'] - row['bid']
                spread_pct = (spread / mid * 100) if mid > 0 else 100
                spread_map[key] = spread_pct

        # Score each signal
        for signal in signals:
            key = (signal.expiry, signal.strike, signal.option_type)
            spread_pct = spread_map.get(key)
            signal.mispricing_score = self.score_opportunity(signal, spread_pct)

        # Sort by score descending
        signals.sort(key=lambda s: s.mispricing_score, reverse=True)

        return signals

    def get_top_opportunities(
        self,
        signals: List[MispricingSignal],
        n: int = 10,
        min_score: float = 40.0
    ) -> List[MispricingSignal]:
        """
        Get top N opportunities above minimum score.

        Args:
            signals: List of scored signals
            n: Number of top signals to return
            min_score: Minimum score threshold

        Returns:
            Top N signals with score >= min_score
        """
        # Filter by minimum score
        filtered = [s for s in signals if s.mispricing_score >= min_score]

        # Return top N
        return filtered[:n]

    def generate_summary(self, signals: List[MispricingSignal]) -> Dict[str, Any]:
        """
        Generate summary statistics for scored opportunities.

        Args:
            signals: List of scored signals

        Returns:
            Summary dictionary
        """
        if not signals:
            return {
                'count': 0,
                'avg_score': 0,
                'avg_iv_hv': 0,
                'by_type': {}
            }

        scores = [s.mispricing_score for s in signals]
        iv_hvs = [s.iv_hv_ratio for s in signals if s.iv_hv_ratio]

        # Count by option type
        by_type = {}
        for signal in signals:
            opt_type = signal.option_type
            if opt_type not in by_type:
                by_type[opt_type] = 0
            by_type[opt_type] += 1

        return {
            'count': len(signals),
            'avg_score': np.mean(scores) if scores else 0,
            'max_score': max(scores) if scores else 0,
            'min_score': min(scores) if scores else 0,
            'avg_iv_hv': np.mean(iv_hvs) if iv_hvs else 0,
            'by_type': by_type
        }


def calculate_probability_of_profit(
    underlying_price: float,
    strike: float,
    iv: float,
    dte: int,
    option_type: str
) -> float:
    """
    Calculate approximate probability of profit for a short option.

    Uses delta as a proxy for probability of being ITM at expiration.
    For premium sellers, POP = 1 - P(ITM).

    Args:
        underlying_price: Current stock price
        strike: Option strike
        iv: Implied volatility
        dte: Days to expiration
        option_type: CALL or PUT

    Returns:
        Probability of profit (0-1)
    """
    from .black_scholes import BlackScholes

    bs = BlackScholes()
    time_to_expiry = bs.days_to_years(dte)

    if time_to_expiry <= 0:
        # At expiration
        if option_type == 'PUT':
            return 1.0 if underlying_price > strike else 0.0
        else:
            return 1.0 if underlying_price < strike else 0.0

    greeks = bs.calculate_greeks(
        underlying_price, strike, time_to_expiry, iv, option_type
    )

    # Delta approximates probability of finishing ITM
    # For short positions, we want high probability of OTM
    p_itm = abs(greeks.delta)
    p_otm = 1 - p_itm

    return p_otm


def calculate_risk_reward(
    premium: float,
    strike: float,
    underlying_price: float,
    option_type: str
) -> Dict[str, float]:
    """
    Calculate risk/reward metrics for a short option.

    Args:
        premium: Premium collected
        strike: Option strike
        underlying_price: Current stock price
        option_type: CALL or PUT

    Returns:
        Dictionary with max_profit, max_loss, risk_reward_ratio
    """
    max_profit = premium * 100  # Per contract

    if option_type == 'PUT':
        # Max loss = strike price - premium (if stock goes to 0)
        max_loss = (strike - premium) * 100
    else:
        # Max loss for naked call is theoretically unlimited
        # Use 2x underlying as practical estimate
        max_loss = (underlying_price * 2 - strike - premium) * 100
        max_loss = max(max_loss, 0)

    risk_reward = max_profit / max_loss if max_loss > 0 else float('inf')

    return {
        'max_profit': max_profit,
        'max_loss': max_loss,
        'risk_reward_ratio': risk_reward,
        'breakeven': strike - premium if option_type == 'PUT' else strike + premium
    }
