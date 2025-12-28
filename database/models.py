"""Data models for Options Buddy."""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional, List


@dataclass
class Position:
    """Represents an options position."""
    id: Optional[int] = None
    underlying: str = ""
    option_type: str = ""  # 'CALL' or 'PUT'
    strike: float = 0.0
    expiry: date = None
    quantity: int = 0
    premium_collected: float = 0.0
    open_date: date = None
    close_date: Optional[date] = None
    close_price: Optional[float] = None
    status: str = "OPEN"  # OPEN, CLOSED, ASSIGNED, EXPIRED, ROLLED
    strategy_type: str = ""  # CSP, CC, BULL_PUT, etc.
    notes: Optional[str] = None
    ibkr_con_id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @property
    def is_call(self) -> bool:
        return self.option_type.upper() == "CALL"

    @property
    def is_put(self) -> bool:
        return self.option_type.upper() == "PUT"

    @property
    def days_to_expiry(self) -> int:
        if self.expiry is None:
            return 0
        return (self.expiry - date.today()).days

    @property
    def is_expired(self) -> bool:
        return self.days_to_expiry <= 0


@dataclass
class Trade:
    """Represents a trade/transaction for a position."""
    id: Optional[int] = None
    position_id: int = 0
    action: str = ""  # OPEN, CLOSE, ROLL_CLOSE, ROLL_OPEN, ADJUST
    price: float = 0.0
    quantity: int = 0
    fees: float = 0.0
    trade_date: datetime = None
    notes: Optional[str] = None


@dataclass
class SpreadLeg:
    """Represents a leg in a multi-leg strategy."""
    id: Optional[int] = None
    position_id: int = 0
    leg_type: str = ""  # LONG or SHORT
    option_type: str = ""  # CALL or PUT
    strike: float = 0.0
    expiry: date = None
    quantity: int = 0
    premium: float = 0.0


@dataclass
class Watchlist:
    """Represents a watchlist of symbols."""
    id: Optional[int] = None
    name: str = ""
    description: Optional[str] = None
    symbols: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Alert:
    """Represents an alert for a position."""
    id: Optional[int] = None
    position_id: Optional[int] = None
    alert_type: str = ""  # NEAR_EXPIRY, ITM, PROFIT_TARGET, etc.
    threshold_value: Optional[float] = None
    threshold_days: Optional[int] = None
    is_active: bool = True
    triggered_at: Optional[datetime] = None


@dataclass
class ScanResult:
    """Represents a scan result / opportunity."""
    id: Optional[int] = None
    scan_date: datetime = None
    underlying: str = ""
    option_type: str = ""
    strike: float = 0.0
    expiry: date = None
    bid: float = 0.0
    ask: float = 0.0
    iv: Optional[float] = None
    hv: Optional[float] = None
    iv_hv_ratio: Optional[float] = None
    model_price: Optional[float] = None
    market_price: Optional[float] = None
    mispricing_score: Optional[float] = None
    delta: Optional[float] = None
    gamma: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None
    was_traded: bool = False
