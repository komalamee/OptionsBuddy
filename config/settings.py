"""Application settings management."""

import os
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv

from .constants import (
    DEFAULT_MIN_DTE, DEFAULT_MAX_DTE,
    DEFAULT_MIN_DELTA, DEFAULT_MAX_DELTA,
    DEFAULT_IV_HV_THRESHOLD, DEFAULT_MIN_PREMIUM,
    DEFAULT_RISK_FREE_RATE
)

# Load environment variables
load_dotenv()


@dataclass
class IBKRSettings:
    """Interactive Brokers connection settings."""
    host: str = "127.0.0.1"
    port: int = 4001  # IB Gateway default
    client_id: int = 1
    market_data_type: int = 2  # Frozen data

    @classmethod
    def from_env(cls) -> "IBKRSettings":
        """Load settings from environment variables."""
        return cls(
            host=os.getenv("IBKR_HOST", "127.0.0.1"),
            port=int(os.getenv("IBKR_PORT", "4001")),
            client_id=int(os.getenv("IBKR_CLIENT_ID", "1")),
            market_data_type=int(os.getenv("IBKR_MARKET_DATA_TYPE", "2"))
        )


@dataclass
class ScannerDefaults:
    """Default scanner filter settings."""
    min_dte: int = DEFAULT_MIN_DTE
    max_dte: int = DEFAULT_MAX_DTE
    min_delta: float = DEFAULT_MIN_DELTA
    max_delta: float = DEFAULT_MAX_DELTA
    iv_hv_threshold: float = DEFAULT_IV_HV_THRESHOLD
    min_premium: float = DEFAULT_MIN_PREMIUM
    strategies: list = field(default_factory=lambda: ["CSP", "CC"])


@dataclass
class AlertSettings:
    """Alert threshold settings."""
    days_to_expiry_warning: int = 7
    profit_target_percent: float = 50.0  # Close at 50% profit
    loss_limit_percent: float = 200.0    # Alert at 200% loss
    delta_warning_threshold: float = 0.70  # Alert when delta > 0.70


@dataclass
class Settings:
    """Main application settings container."""
    ibkr: IBKRSettings = field(default_factory=IBKRSettings.from_env)
    scanner: ScannerDefaults = field(default_factory=ScannerDefaults)
    alerts: AlertSettings = field(default_factory=AlertSettings)
    risk_free_rate: float = DEFAULT_RISK_FREE_RATE

    # Database path
    db_path: str = "data_store/options_buddy.db"

    @classmethod
    def load(cls) -> "Settings":
        """Load settings from environment and defaults."""
        return cls(
            ibkr=IBKRSettings.from_env()
        )


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings.load()
    return _settings


def update_settings(new_settings: Settings) -> None:
    """Update the global settings instance."""
    global _settings
    _settings = new_settings
