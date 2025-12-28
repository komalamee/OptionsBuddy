# Changelog

All notable changes to Options Buddy will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned
- Unit tests for core modules
- Demo mode with sample data
- Improved error handling

---

## [1.0.0] - 2024-12-28

### Added

#### Core Infrastructure
- **Project scaffolding** - Complete directory structure with modular architecture
- **Configuration system** (`config/`)
  - `constants.py` - Trading constants (252 trading days, volatility windows, strategies)
  - `settings.py` - Application settings (IBKR connection, scanner defaults, alerts)
- **Environment setup** - `.env.example` template for secure configuration

#### Black-Scholes Pricing Engine (`core/black_scholes.py`)
- Theoretical option pricing using py_vollib
- Implied volatility calculation from market prices
- Full Greeks calculation (Delta, Gamma, Theta, Vega, Rho)
- Edge case handling (expiration, zero volatility)
- Scipy fallback implementation for reliability

#### Volatility Analysis (`core/volatility.py`)
- Standard historical volatility (close-to-close)
- Parkinson volatility (high-low range)
- Garman-Klass volatility (OHLC)
- Rogers-Satchell volatility (drift-independent)
- Multiple calculation windows (10, 21, 63, 126, 252 days)
- Volatility percentile ranking
- Volatility cone generation

#### Mispricing Detection (`core/mispricing.py`)
- IV vs HV ratio analysis
- Market price vs model price comparison
- Configurable threshold rules (DTE, delta, premium, liquidity)
- Batch option chain analysis
- Opportunity filtering and ranking

#### Opportunity Scoring (`core/scoring.py`)
- Weighted multi-factor scoring algorithm (0-100)
- Factor weights: IV/HV (30%), Price deviation (20%), Delta (15%), Theta (15%), Liquidity (10%), DTE (10%)
- Probability of profit calculation
- Risk/reward ratio analysis

#### Interactive Brokers Integration (`data/`)
- **ibkr_client.py** - Singleton connection manager
  - TWS/IB Gateway connection
  - Paper trading (port 7497) and live trading (port 7496) support
  - Market data type configuration (live, frozen, delayed)
- **option_chain.py** - Option chain data fetcher
  - Full chain retrieval with Greeks
  - Delta, premium, and liquidity filtering
  - DTE calculation
- **historical_data.py** - OHLCV data fetcher
  - In-memory caching (1 hour TTL)
  - Historical volatility computation
  - Volatility cone data

#### Database Layer (`database/`)
- **models.py** - Data models
  - Position (status tracking, premium, strategy)
  - Trade (action logging, fees)
  - SpreadLeg (multi-leg strategies)
  - Watchlist (symbol grouping)
  - Alert (notifications)
  - ScanResult (opportunity caching)
- **db_manager.py** - Database operations
  - CRUD operations for all models
  - Portfolio metrics calculation
  - Win rate tracking
  - Auto-initialisation on first run

#### Streamlit User Interface (`pages/`)
- **1_dashboard.py** - Portfolio overview
  - Key metrics (positions, premium, win rate)
  - Open positions table
  - Near-expiry alerts
- **2_scanner.py** - Opportunity scanner
  - Watchlist-based scanning
  - Filter sidebar (DTE, delta, strategy, premium)
  - IV/HV threshold configuration
  - IBKR connection requirement
- **3_analyzer.py** - Deep-dive analysis
  - Option chain viewer
  - Volatility analysis tab
  - Black-Scholes calculator
  - Payoff diagram visualisation
- **4_positions.py** - Position management
  - Open positions list
  - Manual position entry form
  - Position edit and close workflow
  - Trade history
- **5_suggestions.py** - Smart recommendations
  - Categorised by urgency (Critical, Expiring, Approaching, Stable)
  - Action suggestions (close, roll, monitor)
  - Strategy-aware recommendations
- **6_settings.py** - Configuration
  - IBKR connection settings
  - Scanner defaults
  - Alert thresholds

#### Main Application (`app.py`)
- Streamlit multi-page app entry point
- IBKR connection status indicator in sidebar
- Session state management

#### Documentation
- `requirements.txt` - Python dependencies with version constraints
- `docs/PRD.md` - Full product requirements document
- `docs/CHANGELOG.md` - This changelog
- `docs/TASKS.md` - Task tracking system

### Technical Decisions

- **Read-only V1**: No trade execution to reduce risk during development
- **Singleton IBKR client**: Prevents connection conflicts
- **SQLite for persistence**: Simple, file-based, no external dependencies
- **py_vollib for pricing**: Industry-standard, fast, accurate
- **Streamlit for UI**: Rapid development, Python-native, interactive

### Dependencies
```
streamlit>=1.30.0
ib_insync>=0.9.86
pandas>=2.0.0
numpy>=1.24.0
py_vollib>=1.0.1
sqlalchemy>=2.0.0
plotly>=5.18.0
python-dotenv>=1.0.0
python-dateutil>=2.8.2
pytest>=7.4.0
```

---

## Version History Summary

| Version | Date | Highlights |
|---------|------|------------|
| 1.0.0 | 2024-12-28 | Initial release - complete read-only analysis platform |

---

## Upcoming Releases

### v1.1.0 (Planned)
- Unit tests for core modules
- Demo mode without IBKR connection
- Improved error messages
- Performance optimisations

### v2.0.0 (Future)
- Trade execution capability
- Order placement (market, limit)
- Position rolling
- Auto-close at profit targets

### v3.0.0 (Future)
- Backtesting engine
- Strategy simulation
- Parameter optimisation
- Performance analytics

---

## How to Read This Changelog

- **Added**: New features
- **Changed**: Changes in existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Vulnerability fixes

---

*Maintained by the Options Buddy development team.*
