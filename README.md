# Options Buddy

A personal options trading analysis platform that identifies mispriced options for premium-selling strategies using Black-Scholes pricing and IV/HV analysis.

**Version:** 1.0.0 | **Status:** V1 Read-Only | **Last Updated:** 2024-12-28

---

## Features

- **Opportunity Scanner** - Find overpriced options using IV/HV ratio analysis
- **Multi-Factor Scoring** - Rank opportunities (0-100) based on IV, Greeks, liquidity
- **Volatility Analysis** - 4 calculation methods (Standard, Parkinson, Garman-Klass, Rogers-Satchell)
- **Position Tracking** - Log trades, track P&L, manage expiries
- **Smart Alerts** - Near-expiry, ITM, profit targets, loss limits
- **IBKR Integration** - Real-time data from Interactive Brokers

---

## Quick Start

### Prerequisites

- Python 3.10+
- Interactive Brokers TWS or IB Gateway (for live data)

### Installation

```bash
# Clone the repository
cd "Options Buddy"

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
```

### Configuration

Edit `.env` with your settings:

```env
IBKR_HOST=127.0.0.1
IBKR_PORT=7497          # 7497 for paper, 7496 for live
IBKR_CLIENT_ID=1
```

### Running the App

```bash
streamlit run app.py
```

Open http://localhost:8501 in your browser.

---

## Pages

| Page | Purpose |
|------|---------|
| **Dashboard** | Portfolio overview, open positions, alerts |
| **Scanner** | Find mispriced options with customisable filters |
| **Analyzer** | Deep-dive into specific symbols (chain, volatility, calculator) |
| **Positions** | Add, edit, close positions manually |
| **Suggestions** | Smart recommendations based on position status |
| **Settings** | IBKR connection, scanner defaults, alert thresholds |

---

## Architecture

```
Options Buddy/
├── app.py              # Streamlit entry point
├── config/             # Constants and settings
├── core/               # Black-Scholes, volatility, mispricing, scoring
├── data/               # IBKR client, option chain, historical data
├── database/           # SQLite models and manager
├── pages/              # Streamlit UI pages
└── docs/               # PRD, changelog, tasks
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [docs/PRD.md](docs/PRD.md) | Full product requirements |
| [docs/CHANGELOG.md](docs/CHANGELOG.md) | Version history |
| [docs/TASKS.md](docs/TASKS.md) | Task tracking and status |

---

## IBKR Setup

1. Install TWS or IB Gateway
2. Configure > API > Settings
3. Enable "Enable ActiveX and Socket Clients"
4. Set port to 7497 (paper) or 7496 (live)
5. Add 127.0.0.1 to trusted IPs
6. Connect via Options Buddy Settings page

---

## Trading Strategies Supported

- **CSP** - Cash-Secured Puts
- **CC** - Covered Calls
- **Bull Put Spread**
- **Bear Call Spread**
- **Iron Condor**
- **Strangle**
- **Straddle**

---

## Tech Stack

- **Streamlit** - Web UI
- **ib_insync** - IBKR API
- **py_vollib** - Black-Scholes pricing
- **pandas/numpy** - Data processing
- **plotly** - Visualisation
- **SQLite** - Local database

---

## Testing

```bash
# Run documentation validation tests
pytest tests/test_docs.py -v

# Run all tests
pytest tests/ -v
```

---

## Roadmap

- **V1.0** (Current) - Read-only analysis platform
- **V1.1** (Next) - Unit tests, demo mode, polish
- **V2.0** (Future) - Trade execution
- **V3.0** (Future) - Backtesting engine

---

## License

Private project - not for distribution.

---

## Contributing

This is a personal project. See [docs/TASKS.md](docs/TASKS.md) for current work items.
