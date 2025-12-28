"""Black-Scholes option pricing using py_vollib."""

import logging
from typing import Optional, Tuple, Dict
from dataclasses import dataclass

import numpy as np

# py_vollib imports
try:
    from py_vollib.black_scholes import black_scholes as bs_price
    from py_vollib.black_scholes.implied_volatility import implied_volatility as bs_iv
    from py_vollib.black_scholes.greeks.analytical import (
        delta as bs_delta,
        gamma as bs_gamma,
        theta as bs_theta,
        vega as bs_vega,
        rho as bs_rho
    )
    VOLLIB_AVAILABLE = True
except ImportError:
    VOLLIB_AVAILABLE = False
    logging.warning("py_vollib not installed. Using fallback Black-Scholes implementation.")

from config.constants import (
    TRADING_DAYS_PER_YEAR,
    CALENDAR_DAYS_PER_YEAR,
    DEFAULT_RISK_FREE_RATE,
    CALL, PUT
)

logger = logging.getLogger(__name__)


@dataclass
class OptionGreeks:
    """Container for option Greeks."""
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float

    def to_dict(self) -> Dict[str, float]:
        return {
            'delta': self.delta,
            'gamma': self.gamma,
            'theta': self.theta,
            'vega': self.vega,
            'rho': self.rho
        }


class BlackScholes:
    """
    Black-Scholes option pricing engine.

    Uses py_vollib for accurate and fast calculations.
    Falls back to basic implementation if py_vollib is not available.
    """

    def __init__(self, risk_free_rate: float = DEFAULT_RISK_FREE_RATE):
        """
        Initialize the pricing engine.

        Args:
            risk_free_rate: Annual risk-free interest rate (e.g., 0.05 for 5%)
        """
        self.risk_free_rate = risk_free_rate

    def calculate_price(
        self,
        underlying_price: float,
        strike: float,
        time_to_expiry: float,
        volatility: float,
        option_type: str = PUT,
        risk_free_rate: Optional[float] = None
    ) -> float:
        """
        Calculate theoretical option price using Black-Scholes.

        Args:
            underlying_price: Current price of the underlying
            strike: Option strike price
            time_to_expiry: Time to expiration in years
            volatility: Implied volatility as decimal (e.g., 0.25 for 25%)
            option_type: CALL or PUT
            risk_free_rate: Override risk-free rate

        Returns:
            Theoretical option price
        """
        if time_to_expiry <= 0:
            # At or past expiration
            if option_type == CALL:
                return max(0, underlying_price - strike)
            else:
                return max(0, strike - underlying_price)

        r = risk_free_rate if risk_free_rate is not None else self.risk_free_rate
        flag = 'c' if option_type == CALL else 'p'

        if VOLLIB_AVAILABLE:
            try:
                price = bs_price(flag, underlying_price, strike, time_to_expiry, r, volatility)
                return float(price)
            except Exception as e:
                logger.warning(f"py_vollib error: {e}. Using fallback.")

        # Fallback implementation
        return self._bs_price_fallback(
            underlying_price, strike, time_to_expiry, volatility, option_type, r
        )

    def calculate_implied_volatility(
        self,
        market_price: float,
        underlying_price: float,
        strike: float,
        time_to_expiry: float,
        option_type: str = PUT,
        risk_free_rate: Optional[float] = None
    ) -> Optional[float]:
        """
        Calculate implied volatility from market price.

        Args:
            market_price: Current market price of the option
            underlying_price: Current price of the underlying
            strike: Option strike price
            time_to_expiry: Time to expiration in years
            option_type: CALL or PUT
            risk_free_rate: Override risk-free rate

        Returns:
            Implied volatility as decimal, or None if calculation fails
        """
        if time_to_expiry <= 0 or market_price <= 0:
            return None

        r = risk_free_rate if risk_free_rate is not None else self.risk_free_rate
        flag = 'c' if option_type == CALL else 'p'

        if VOLLIB_AVAILABLE:
            try:
                iv = bs_iv(market_price, underlying_price, strike, time_to_expiry, r, flag)
                return float(iv)
            except Exception as e:
                logger.debug(f"IV calculation failed: {e}")
                return None

        # Fallback: Newton-Raphson iteration
        return self._iv_fallback(
            market_price, underlying_price, strike, time_to_expiry, option_type, r
        )

    def calculate_greeks(
        self,
        underlying_price: float,
        strike: float,
        time_to_expiry: float,
        volatility: float,
        option_type: str = PUT,
        risk_free_rate: Optional[float] = None
    ) -> OptionGreeks:
        """
        Calculate all Greeks for an option.

        Args:
            underlying_price: Current price of the underlying
            strike: Option strike price
            time_to_expiry: Time to expiration in years
            volatility: Implied volatility as decimal
            option_type: CALL or PUT
            risk_free_rate: Override risk-free rate

        Returns:
            OptionGreeks with all Greeks
        """
        if time_to_expiry <= 0:
            # At expiration
            itm = (option_type == CALL and underlying_price > strike) or \
                  (option_type == PUT and underlying_price < strike)
            return OptionGreeks(
                delta=1.0 if (option_type == CALL and itm) else (-1.0 if (option_type == PUT and itm) else 0.0),
                gamma=0.0,
                theta=0.0,
                vega=0.0,
                rho=0.0
            )

        r = risk_free_rate if risk_free_rate is not None else self.risk_free_rate
        flag = 'c' if option_type == CALL else 'p'

        if VOLLIB_AVAILABLE:
            try:
                return OptionGreeks(
                    delta=bs_delta(flag, underlying_price, strike, time_to_expiry, r, volatility),
                    gamma=bs_gamma(flag, underlying_price, strike, time_to_expiry, r, volatility),
                    theta=bs_theta(flag, underlying_price, strike, time_to_expiry, r, volatility),
                    vega=bs_vega(flag, underlying_price, strike, time_to_expiry, r, volatility),
                    rho=bs_rho(flag, underlying_price, strike, time_to_expiry, r, volatility)
                )
            except Exception as e:
                logger.warning(f"Greeks calculation error: {e}")

        # Fallback
        return self._greeks_fallback(
            underlying_price, strike, time_to_expiry, volatility, option_type, r
        )

    def calculate_delta(
        self,
        underlying_price: float,
        strike: float,
        time_to_expiry: float,
        volatility: float,
        option_type: str = PUT,
        risk_free_rate: Optional[float] = None
    ) -> float:
        """Calculate option delta."""
        greeks = self.calculate_greeks(
            underlying_price, strike, time_to_expiry, volatility, option_type, risk_free_rate
        )
        return greeks.delta

    @staticmethod
    def days_to_years(days: int, use_trading_days: bool = False) -> float:
        """Convert days to years for time to expiry."""
        if use_trading_days:
            return days / TRADING_DAYS_PER_YEAR
        return days / CALENDAR_DAYS_PER_YEAR

    # ==================== FALLBACK IMPLEMENTATIONS ====================

    def _bs_price_fallback(
        self,
        S: float,
        K: float,
        T: float,
        sigma: float,
        option_type: str,
        r: float
    ) -> float:
        """Basic Black-Scholes price calculation."""
        from scipy.stats import norm

        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)

        if option_type == CALL:
            price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        else:
            price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

        return float(price)

    def _iv_fallback(
        self,
        price: float,
        S: float,
        K: float,
        T: float,
        option_type: str,
        r: float,
        max_iterations: int = 100,
        tolerance: float = 1e-6
    ) -> Optional[float]:
        """Newton-Raphson IV calculation."""
        sigma = 0.2  # Initial guess

        for _ in range(max_iterations):
            bs_price = self._bs_price_fallback(S, K, T, sigma, option_type, r)
            greeks = self._greeks_fallback(S, K, T, sigma, option_type, r)
            vega = greeks.vega

            if abs(vega) < 1e-10:
                break

            diff = price - bs_price
            if abs(diff) < tolerance:
                return sigma

            sigma = sigma + diff / (vega * 100)  # Vega is per 1% vol change

            if sigma <= 0:
                sigma = 0.001

        return sigma if 0 < sigma < 5 else None

    def _greeks_fallback(
        self,
        S: float,
        K: float,
        T: float,
        sigma: float,
        option_type: str,
        r: float
    ) -> OptionGreeks:
        """Basic Greeks calculation."""
        from scipy.stats import norm

        sqrt_T = np.sqrt(T)
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * sqrt_T)
        d2 = d1 - sigma * sqrt_T

        # Delta
        if option_type == CALL:
            delta = norm.cdf(d1)
        else:
            delta = norm.cdf(d1) - 1

        # Gamma (same for calls and puts)
        gamma = norm.pdf(d1) / (S * sigma * sqrt_T)

        # Theta
        term1 = -(S * norm.pdf(d1) * sigma) / (2 * sqrt_T)
        if option_type == CALL:
            term2 = r * K * np.exp(-r * T) * norm.cdf(d2)
            theta = (term1 - term2) / CALENDAR_DAYS_PER_YEAR
        else:
            term2 = r * K * np.exp(-r * T) * norm.cdf(-d2)
            theta = (term1 + term2) / CALENDAR_DAYS_PER_YEAR

        # Vega (same for calls and puts) - per 1% change in vol
        vega = S * sqrt_T * norm.pdf(d1) / 100

        # Rho
        if option_type == CALL:
            rho = K * T * np.exp(-r * T) * norm.cdf(d2) / 100
        else:
            rho = -K * T * np.exp(-r * T) * norm.cdf(-d2) / 100

        return OptionGreeks(
            delta=float(delta),
            gamma=float(gamma),
            theta=float(theta),
            vega=float(vega),
            rho=float(rho)
        )
