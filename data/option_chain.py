"""Option chain data fetching and processing."""

import logging
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta
from dataclasses import dataclass

import pandas as pd
from ib_insync import Option, util

from .ibkr_client import get_ibkr_client
from config.constants import CALL, PUT

logger = logging.getLogger(__name__)


@dataclass
class OptionQuote:
    """Represents a single option quote with Greeks."""
    symbol: str
    expiry: str
    strike: float
    option_type: str  # CALL or PUT
    bid: float
    ask: float
    last: float
    volume: int
    open_interest: int
    iv: Optional[float]  # Implied volatility
    delta: Optional[float]
    gamma: Optional[float]
    theta: Optional[float]
    vega: Optional[float]
    underlying_price: Optional[float]
    con_id: Optional[int] = None

    @property
    def mid_price(self) -> float:
        """Calculate mid price."""
        if self.bid > 0 and self.ask > 0:
            return (self.bid + self.ask) / 2
        return self.last or 0

    @property
    def spread(self) -> float:
        """Calculate bid-ask spread."""
        if self.bid > 0 and self.ask > 0:
            return self.ask - self.bid
        return 0

    @property
    def spread_percent(self) -> float:
        """Calculate spread as percentage of mid price."""
        mid = self.mid_price
        if mid > 0:
            return (self.spread / mid) * 100
        return 0

    @property
    def dte(self) -> int:
        """Days to expiration."""
        expiry_date = datetime.strptime(self.expiry, "%Y%m%d").date()
        return (expiry_date - date.today()).days


class OptionChainFetcher:
    """Fetches and processes option chain data from IBKR."""

    def __init__(self):
        self.client = get_ibkr_client()

    def get_full_chain(
        self,
        symbol: str,
        min_dte: int = 0,
        max_dte: int = 90,
        min_strike_pct: float = 0.7,  # 70% of underlying price
        max_strike_pct: float = 1.3,  # 130% of underlying price
        option_types: List[str] = None
    ) -> pd.DataFrame:
        """
        Fetch full option chain for a symbol with filters.

        Args:
            symbol: Stock symbol
            min_dte: Minimum days to expiration
            max_dte: Maximum days to expiration
            min_strike_pct: Minimum strike as % of underlying
            max_strike_pct: Maximum strike as % of underlying
            option_types: List of option types to include ['CALL', 'PUT']

        Returns:
            DataFrame with option chain data
        """
        if not self.client.ensure_connected():
            logger.error("Not connected to IBKR")
            return pd.DataFrame()

        if option_types is None:
            option_types = [CALL, PUT]

        try:
            # Get underlying price
            underlying_price = self.client.get_stock_price(symbol)
            if underlying_price is None:
                logger.error(f"Could not get price for {symbol}")
                return pd.DataFrame()

            # Calculate strike range
            min_strike = underlying_price * min_strike_pct
            max_strike = underlying_price * max_strike_pct

            # Get available expirations
            expirations = self.client.get_option_chain_expirations(symbol)

            # Filter expirations by DTE
            today = date.today()
            filtered_expirations = []
            for exp in expirations:
                exp_date = datetime.strptime(exp, "%Y%m%d").date()
                dte = (exp_date - today).days
                if min_dte <= dte <= max_dte:
                    filtered_expirations.append(exp)

            if not filtered_expirations:
                logger.warning(f"No expirations found for {symbol} within DTE range {min_dte}-{max_dte}")
                return pd.DataFrame()

            # Build option contracts
            options = []
            for exp in filtered_expirations:
                strikes = self.client.get_option_chain_strikes(symbol, exp)
                filtered_strikes = [s for s in strikes if min_strike <= s <= max_strike]

                for strike in filtered_strikes:
                    for opt_type in option_types:
                        right = 'C' if opt_type == CALL else 'P'
                        options.append(
                            self.client.create_option_contract(
                                symbol=symbol,
                                expiry=exp,
                                strike=strike,
                                right=right
                            )
                        )

            if not options:
                logger.warning(f"No options found for {symbol}")
                return pd.DataFrame()

            # Qualify contracts in batches
            qualified = []
            batch_size = 50
            for i in range(0, len(options), batch_size):
                batch = options[i:i + batch_size]
                try:
                    qualified.extend(self.client.qualify_contracts(batch))
                except Exception as e:
                    logger.warning(f"Error qualifying batch: {e}")

            if not qualified:
                return pd.DataFrame()

            # Request market data for all options
            quotes = self._fetch_option_quotes(qualified, underlying_price)

            # Convert to DataFrame
            df = pd.DataFrame([vars(q) for q in quotes])

            if df.empty:
                return df

            # Sort by expiry, strike, option_type
            df = df.sort_values(['expiry', 'strike', 'option_type'])
            df = df.reset_index(drop=True)

            return df

        except Exception as e:
            logger.error(f"Error fetching option chain for {symbol}: {e}")
            return pd.DataFrame()

    def _fetch_option_quotes(
        self,
        contracts: List[Option],
        underlying_price: float
    ) -> List[OptionQuote]:
        """Fetch quotes and Greeks for option contracts."""
        quotes = []
        ib = self.client.ib

        try:
            # Request tickers for all contracts
            tickers = []
            for contract in contracts:
                ticker = ib.reqMktData(contract, '', False, False)
                tickers.append((contract, ticker))

            # Wait for data
            ib.sleep(3)

            # Process tickers
            for contract, ticker in tickers:
                try:
                    # Get Greeks from model
                    greeks = ticker.modelGreeks

                    quote = OptionQuote(
                        symbol=contract.symbol,
                        expiry=contract.lastTradeDateOrContractMonth,
                        strike=contract.strike,
                        option_type=CALL if contract.right == 'C' else PUT,
                        bid=ticker.bid if not util.isNan(ticker.bid) else 0,
                        ask=ticker.ask if not util.isNan(ticker.ask) else 0,
                        last=ticker.last if not util.isNan(ticker.last) else 0,
                        volume=ticker.volume if ticker.volume and not util.isNan(ticker.volume) else 0,
                        open_interest=0,  # Would need separate request
                        iv=greeks.impliedVol if greeks else None,
                        delta=greeks.delta if greeks else None,
                        gamma=greeks.gamma if greeks else None,
                        theta=greeks.theta if greeks else None,
                        vega=greeks.vega if greeks else None,
                        underlying_price=underlying_price,
                        con_id=contract.conId
                    )
                    quotes.append(quote)

                except Exception as e:
                    logger.debug(f"Error processing option {contract}: {e}")

            # Cancel market data
            for contract, _ in tickers:
                try:
                    ib.cancelMktData(contract)
                except:
                    pass

        except Exception as e:
            logger.error(f"Error fetching option quotes: {e}")

        return quotes

    def get_chain_for_expiry(
        self,
        symbol: str,
        expiry: str,
        option_types: List[str] = None
    ) -> pd.DataFrame:
        """Get option chain for a specific expiration."""
        if not self.client.ensure_connected():
            return pd.DataFrame()

        if option_types is None:
            option_types = [CALL, PUT]

        try:
            underlying_price = self.client.get_stock_price(symbol)
            if underlying_price is None:
                return pd.DataFrame()

            strikes = self.client.get_option_chain_strikes(symbol, expiry)
            if not strikes:
                return pd.DataFrame()

            options = []
            for strike in strikes:
                for opt_type in option_types:
                    right = 'C' if opt_type == CALL else 'P'
                    options.append(
                        self.client.create_option_contract(
                            symbol=symbol,
                            expiry=expiry,
                            strike=strike,
                            right=right
                        )
                    )

            qualified = self.client.qualify_contracts(options)
            quotes = self._fetch_option_quotes(qualified, underlying_price)

            df = pd.DataFrame([vars(q) for q in quotes])
            if not df.empty:
                df = df.sort_values(['strike', 'option_type'])
                df = df.reset_index(drop=True)

            return df

        except Exception as e:
            logger.error(f"Error fetching chain for {symbol} {expiry}: {e}")
            return pd.DataFrame()

    def filter_by_delta(
        self,
        chain_df: pd.DataFrame,
        min_delta: float = 0.15,
        max_delta: float = 0.35
    ) -> pd.DataFrame:
        """Filter option chain by delta range (absolute value)."""
        if chain_df.empty or 'delta' not in chain_df.columns:
            return chain_df

        # Use absolute delta for filtering (puts have negative delta)
        mask = chain_df['delta'].notna()
        mask &= chain_df['delta'].abs() >= min_delta
        mask &= chain_df['delta'].abs() <= max_delta

        return chain_df[mask].copy()

    def filter_by_premium(
        self,
        chain_df: pd.DataFrame,
        min_premium: float = 0.50
    ) -> pd.DataFrame:
        """Filter by minimum bid price."""
        if chain_df.empty or 'bid' not in chain_df.columns:
            return chain_df

        return chain_df[chain_df['bid'] >= min_premium].copy()

    def filter_by_liquidity(
        self,
        chain_df: pd.DataFrame,
        max_spread_pct: float = 10.0
    ) -> pd.DataFrame:
        """Filter by bid-ask spread percentage."""
        if chain_df.empty:
            return chain_df

        # Calculate spread percentage if not present
        if 'spread_percent' not in chain_df.columns:
            mid = (chain_df['bid'] + chain_df['ask']) / 2
            spread = chain_df['ask'] - chain_df['bid']
            chain_df['spread_percent'] = (spread / mid * 100).where(mid > 0, 100)

        return chain_df[chain_df['spread_percent'] <= max_spread_pct].copy()
