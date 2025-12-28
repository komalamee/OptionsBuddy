# Options Buddy - Product Requirements Document

**Version:** 1.0.0
**Last Updated:** 2024-12-28
**Status:** In Development (V1 - Read-Only)
**Author:** Koko

---

## Executive Summary

Options Buddy is a personal options trading analysis platform that leverages the Black-Scholes model to identify mispriced options for premium-selling strategies. Built with Streamlit and integrated with Interactive Brokers (IBKR), it provides real-time opportunity scanning, volatility analysis, and position tracking.

---

## Problem Statement

Options traders face several challenges:

1. **Identifying Overpriced Options:** Manually comparing implied volatility (IV) to historical volatility (HV) across hundreds of strikes is time-consuming
2. **Opportunity Scoring:** No standardised way to rank and prioritise premium-selling opportunities
3. **Position Management:** Tracking multiple short options positions, expiries, and profit targets requires constant vigilance
4. **Volatility Analysis:** Understanding current IV percentile and HV trends requires multiple tools

---

## Solution

Options Buddy provides an integrated platform that:

- **Scans** option chains for overpriced opportunities using IV/HV ratio analysis
- **Scores** opportunities using a weighted multi-factor algorithm (0-100)
- **Tracks** positions with automated alerts for expiry, profit targets, and loss limits
- **Analyses** volatility using multiple calculation methods (Standard, Parkinson, Garman-Klass, Rogers-Satchell)

---

## Target User

- **Primary:** Individual options traders using Interactive Brokers
- **Experience Level:** Intermediate to advanced (understands Greeks, IV, HV concepts)
- **Strategy Focus:** Premium sellers (Cash-Secured Puts, Covered Calls, Credit Spreads)
- **Portfolio Size:** $25,000 - $500,000

---

## Product Vision

### V1 (Current) - Read-Only Analysis Platform
Focus on data analysis and position tracking without trade execution.

### V2 (Future) - Trade Execution
Add order placement, position adjustments, and automated rolling.

### V3 (Future) - Backtesting & Strategy Optimisation
Historical strategy backtesting and parameter optimisation.

---

## Functional Requirements

### FR-1: IBKR Integration

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-1.1 | Connect to TWS/IB Gateway via ib_insync | P0 | Done |
| FR-1.2 | Fetch real-time stock prices | P0 | Done |
| FR-1.3 | Retrieve option chain expirations | P0 | Done |
| FR-1.4 | Retrieve option chain strikes with Greeks | P0 | Done |
| FR-1.5 | Fetch historical OHLCV data | P0 | Done |
| FR-1.6 | Get current positions (read-only) | P1 | Done |
| FR-1.7 | Get account summary | P1 | Done |
| FR-1.8 | Support paper trading (port 7497) | P0 | Done |
| FR-1.9 | Support live trading (port 7496) | P1 | Done |

### FR-2: Black-Scholes Pricing Engine

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-2.1 | Calculate theoretical option prices | P0 | Done |
| FR-2.2 | Calculate implied volatility from market prices | P0 | Done |
| FR-2.3 | Calculate all Greeks (Delta, Gamma, Theta, Vega, Rho) | P0 | Done |
| FR-2.4 | Handle edge cases (expiration, zero volatility) | P0 | Done |
| FR-2.5 | Support both calls and puts | P0 | Done |
| FR-2.6 | Fallback scipy implementation if py_vollib fails | P1 | Done |

### FR-3: Volatility Analysis

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-3.1 | Calculate standard historical volatility | P0 | Done |
| FR-3.2 | Calculate Parkinson volatility (high-low range) | P1 | Done |
| FR-3.3 | Calculate Garman-Klass volatility (OHLC) | P1 | Done |
| FR-3.4 | Calculate Rogers-Satchell volatility | P2 | Done |
| FR-3.5 | Multiple calculation windows (10, 21, 63, 126, 252 days) | P0 | Done |
| FR-3.6 | IV percentile ranking | P1 | Done |
| FR-3.7 | Volatility cone visualisation | P2 | Done |

### FR-4: Mispricing Detection

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-4.1 | Detect when IV > HV (configurable threshold) | P0 | Done |
| FR-4.2 | Detect when market price > model price | P0 | Done |
| FR-4.3 | Filter by DTE range | P0 | Done |
| FR-4.4 | Filter by delta range | P0 | Done |
| FR-4.5 | Filter by minimum premium | P0 | Done |
| FR-4.6 | Filter by liquidity (bid-ask spread) | P1 | Done |
| FR-4.7 | Batch analysis of full option chain | P0 | Done |

### FR-5: Opportunity Scoring

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-5.1 | Weighted scoring algorithm (0-100) | P0 | Done |
| FR-5.2 | IV/HV ratio weight (30%) | P0 | Done |
| FR-5.3 | Price deviation weight (20%) | P0 | Done |
| FR-5.4 | Delta optimisation weight (15%) | P0 | Done |
| FR-5.5 | Theta decay weight (15%) | P0 | Done |
| FR-5.6 | Liquidity weight (10%) | P1 | Done |
| FR-5.7 | DTE optimisation weight (10%) | P1 | Done |
| FR-5.8 | Calculate probability of profit | P1 | Done |
| FR-5.9 | Calculate risk/reward ratio | P1 | Done |

### FR-6: Position Tracking

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-6.1 | Add positions manually | P0 | Done |
| FR-6.2 | Track position status (Open, Closed, Assigned, Expired, Rolled) | P0 | Done |
| FR-6.3 | Record premium collected | P0 | Done |
| FR-6.4 | Calculate days to expiry | P0 | Done |
| FR-6.5 | Support multiple strategies (CSP, CC, spreads) | P0 | Done |
| FR-6.6 | Position edit capability | P1 | Done |
| FR-6.7 | Position close/expire workflow | P1 | Done |
| FR-6.8 | Trade history logging | P1 | Done |

### FR-7: Alerting System

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-7.1 | Near-expiry alerts (configurable days) | P0 | Done |
| FR-7.2 | ITM (in-the-money) alerts | P1 | Done |
| FR-7.3 | Profit target alerts (default 50%) | P1 | Done |
| FR-7.4 | Loss limit alerts (default 200%) | P1 | Done |
| FR-7.5 | Delta threshold alerts (assignment risk) | P2 | Done |
| FR-7.6 | Alert persistence in database | P1 | Done |

### FR-8: User Interface (Streamlit)

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-8.1 | Multi-page application structure | P0 | Done |
| FR-8.2 | Dashboard with portfolio overview | P0 | Done |
| FR-8.3 | Opportunity scanner with filters | P0 | Done |
| FR-8.4 | Option chain analyser | P0 | Done |
| FR-8.5 | Volatility analysis tab | P1 | Done |
| FR-8.6 | Black-Scholes calculator | P1 | Done |
| FR-8.7 | Payoff diagram visualisation | P2 | Done |
| FR-8.8 | Position management interface | P0 | Done |
| FR-8.9 | Smart suggestions page | P1 | Done |
| FR-8.10 | Settings/configuration page | P0 | Done |
| FR-8.11 | IBKR connection status indicator | P0 | Done |

### FR-9: Data Persistence

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-9.1 | SQLite database for local storage | P0 | Done |
| FR-9.2 | Positions table | P0 | Done |
| FR-9.3 | Trades table | P0 | Done |
| FR-9.4 | Watchlists table | P1 | Done |
| FR-9.5 | Alerts table | P1 | Done |
| FR-9.6 | Settings key-value store | P1 | Done |
| FR-9.7 | Scan results caching | P2 | Done |
| FR-9.8 | Auto-initialisation on first run | P0 | Done |

---

## Non-Functional Requirements

### NFR-1: Performance

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-1.1 | Option chain fetch time | < 5 seconds |
| NFR-1.2 | Full chain scan time | < 30 seconds |
| NFR-1.3 | Page load time | < 2 seconds |
| NFR-1.4 | Historical data caching | 1 hour TTL |

### NFR-2: Reliability

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-2.1 | IBKR reconnection handling | Automatic retry |
| NFR-2.2 | Graceful degradation without IBKR | Demo mode |
| NFR-2.3 | Database backup capability | Manual export |

### NFR-3: Security

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-3.1 | No credentials in code | Environment variables |
| NFR-3.2 | Local-only database | SQLite file |
| NFR-3.3 | V1 read-only mode | No trade execution |

### NFR-4: Usability

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-4.1 | Mobile-responsive (Streamlit native) | Yes |
| NFR-4.2 | Clear connection status | Sidebar indicator |
| NFR-4.3 | Helpful error messages | Contextual guidance |

---

## Technical Architecture

### Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Frontend | Streamlit | >= 1.30.0 |
| Backend | Python | >= 3.10 |
| IBKR API | ib_insync | >= 0.9.86 |
| Options Pricing | py_vollib | >= 1.0.1 |
| Data Processing | pandas, numpy | >= 2.0.0, >= 1.24.0 |
| Visualisation | plotly | >= 5.18.0 |
| Database | SQLite | Built-in |
| ORM | SQLAlchemy | >= 2.0.0 |

### Directory Structure

```
Options Buddy/
├── app.py                    # Main Streamlit entry point
├── requirements.txt          # Python dependencies
├── .env.example             # Environment template
├── config/                  # Configuration management
│   ├── constants.py         # Trading constants
│   └── settings.py          # App settings
├── core/                    # Core trading logic
│   ├── black_scholes.py     # Pricing engine
│   ├── volatility.py        # HV calculations
│   ├── mispricing.py        # Mispricing detection
│   └── scoring.py           # Opportunity scoring
├── data/                    # Data integration
│   ├── ibkr_client.py       # IBKR wrapper
│   ├── option_chain.py      # Chain fetcher
│   └── historical_data.py   # OHLCV fetcher
├── database/                # Persistence
│   ├── models.py            # Data models
│   └── db_manager.py        # DB operations
├── pages/                   # Streamlit pages
│   ├── 1_dashboard.py       # Portfolio overview
│   ├── 2_scanner.py         # Opportunity scanner
│   ├── 3_analyzer.py        # Deep analysis
│   ├── 4_positions.py       # Position management
│   ├── 5_suggestions.py     # Smart recommendations
│   └── 6_settings.py        # Configuration
├── docs/                    # Documentation
│   ├── PRD.md              # This document
│   ├── CHANGELOG.md        # Version history
│   └── TASKS.md            # Task tracking
└── tests/                   # Test suite
    └── test_docs.py         # Documentation validation
```

### Data Flow

```
IBKR (TWS/IB Gateway)
        │
        ▼
┌───────────────────┐
│   ibkr_client.py  │  ◄── Singleton connection manager
└───────────────────┘
        │
        ├──────────────────┬────────────────────┐
        ▼                  ▼                    ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ option_chain │   │ historical   │   │ market data  │
│   .py        │   │ _data.py     │   │ (prices)     │
└──────────────┘   └──────────────┘   └──────────────┘
        │                  │                    │
        └──────────┬───────┴────────────────────┘
                   ▼
        ┌──────────────────┐
        │   Core Engine    │
        │ ─────────────────│
        │ • black_scholes  │
        │ • volatility     │
        │ • mispricing     │
        │ • scoring        │
        └──────────────────┘
                   │
                   ▼
        ┌──────────────────┐
        │ Streamlit Pages  │
        └──────────────────┘
                   │
                   ▼
        ┌──────────────────┐
        │  SQLite Database │
        └──────────────────┘
```

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Scanner accuracy | > 80% of flagged options are genuinely overpriced | Backtest validation |
| Position tracking completeness | 100% of trades logged | Manual audit |
| Alert relevance | > 90% of alerts are actionable | User feedback |
| Time saved vs manual analysis | > 2 hours/week | User survey |

---

## Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| IBKR API changes | High | Low | ib_insync abstracts most changes; monitor updates |
| py_vollib accuracy | Medium | Low | Scipy fallback; validated against broker prices |
| SQLite limitations at scale | Low | Low | V1 single-user; V2 could migrate to PostgreSQL |
| Market data delays | Medium | Medium | Support frozen/delayed data types; clear UI indicators |

---

## Future Roadmap

### V1.1 - Polish (Next)
- [ ] Add unit tests for core modules
- [ ] Improve error handling
- [ ] Add demo mode with sample data
- [ ] Documentation improvements

### V2.0 - Trade Execution
- [ ] Order placement (market, limit)
- [ ] Position rolling
- [ ] Auto-close at profit targets
- [ ] Order confirmations

### V3.0 - Backtesting
- [ ] Historical strategy simulation
- [ ] Parameter optimisation
- [ ] Performance analytics
- [ ] Strategy comparison

---

## Appendix

### A. Glossary

| Term | Definition |
|------|------------|
| IV | Implied Volatility - market's forecast of likely movement |
| HV | Historical Volatility - actual past price movement |
| DTE | Days to Expiration |
| CSP | Cash-Secured Put - selling puts with cash to cover assignment |
| CC | Covered Call - selling calls against owned shares |
| Greeks | Sensitivity measures (Delta, Gamma, Theta, Vega, Rho) |
| Premium | Price received for selling an option |

### B. Configuration Defaults

```python
# From config/constants.py
TRADING_DAYS_PER_YEAR = 252
VOLATILITY_WINDOWS = [10, 21, 63, 126, 252]
DEFAULT_RISK_FREE_RATE = 0.05

# Scanner defaults
MIN_DTE = 7
MAX_DTE = 45
MIN_DELTA = 0.15
MAX_DELTA = 0.35
IV_HV_THRESHOLD = 1.2

# Alert defaults
PROFIT_TARGET_PERCENT = 0.50
LOSS_LIMIT_PERCENT = 2.00
EXPIRY_WARNING_DAYS = 7
```

### C. IBKR Connection Setup

1. Download and install TWS or IB Gateway
2. Enable API connections in TWS: Configure > API > Settings
3. Check "Enable ActiveX and Socket Clients"
4. Set Socket Port: 7497 (paper) or 7496 (live)
5. Add 127.0.0.1 to trusted IPs
6. Run Options Buddy and connect via Settings page

---

*Document maintained by the Options Buddy development team.*
