-- Options Buddy Database Schema

-- Core positions table
CREATE TABLE IF NOT EXISTS positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    underlying TEXT NOT NULL,
    option_type TEXT NOT NULL CHECK(option_type IN ('CALL', 'PUT')),
    strike REAL NOT NULL,
    expiry DATE NOT NULL,
    quantity INTEGER NOT NULL,
    premium_collected REAL NOT NULL,
    open_date DATE NOT NULL,
    close_date DATE,
    close_price REAL,
    status TEXT NOT NULL DEFAULT 'OPEN'
        CHECK(status IN ('OPEN', 'CLOSED', 'ASSIGNED', 'EXPIRED', 'ROLLED')),
    strategy_type TEXT NOT NULL
        CHECK(strategy_type IN ('CSP', 'CC', 'BULL_PUT', 'BEAR_CALL',
                                'IRON_CONDOR', 'STRANGLE', 'STRADDLE', 'NAKED')),
    notes TEXT,
    ibkr_con_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trade history for each position
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    position_id INTEGER NOT NULL,
    action TEXT NOT NULL CHECK(action IN ('OPEN', 'CLOSE', 'ROLL_CLOSE', 'ROLL_OPEN', 'ADJUST')),
    price REAL NOT NULL,
    quantity INTEGER NOT NULL,
    fees REAL DEFAULT 0,
    trade_date TIMESTAMP NOT NULL,
    notes TEXT,
    FOREIGN KEY (position_id) REFERENCES positions(id) ON DELETE CASCADE
);

-- Spread legs (for multi-leg strategies)
CREATE TABLE IF NOT EXISTS spread_legs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    position_id INTEGER NOT NULL,
    leg_type TEXT NOT NULL CHECK(leg_type IN ('LONG', 'SHORT')),
    option_type TEXT NOT NULL CHECK(option_type IN ('CALL', 'PUT')),
    strike REAL NOT NULL,
    expiry DATE NOT NULL,
    quantity INTEGER NOT NULL,
    premium REAL NOT NULL,
    FOREIGN KEY (position_id) REFERENCES positions(id) ON DELETE CASCADE
);

-- Watchlists
CREATE TABLE IF NOT EXISTS watchlists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Watchlist symbols (many-to-many)
CREATE TABLE IF NOT EXISTS watchlist_symbols (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    watchlist_id INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (watchlist_id) REFERENCES watchlists(id) ON DELETE CASCADE,
    UNIQUE(watchlist_id, symbol)
);

-- Alerts for position monitoring
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    position_id INTEGER,
    alert_type TEXT NOT NULL
        CHECK(alert_type IN ('NEAR_EXPIRY', 'ITM', 'PROFIT_TARGET',
                             'LOSS_LIMIT', 'DELTA_THRESHOLD', 'ASSIGNMENT_RISK')),
    threshold_value REAL,
    threshold_days INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    triggered_at TIMESTAMP,
    FOREIGN KEY (position_id) REFERENCES positions(id) ON DELETE CASCADE
);

-- User settings and thresholds (key-value store)
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Scan results history (for tracking and backtesting)
CREATE TABLE IF NOT EXISTS scan_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_date TIMESTAMP NOT NULL,
    underlying TEXT NOT NULL,
    option_type TEXT NOT NULL,
    strike REAL NOT NULL,
    expiry DATE NOT NULL,
    bid REAL,
    ask REAL,
    iv REAL,
    hv REAL,
    iv_hv_ratio REAL,
    model_price REAL,
    market_price REAL,
    mispricing_score REAL,
    delta REAL,
    theta REAL,
    was_traded BOOLEAN DEFAULT FALSE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_positions_status ON positions(status);
CREATE INDEX IF NOT EXISTS idx_positions_expiry ON positions(expiry);
CREATE INDEX IF NOT EXISTS idx_positions_underlying ON positions(underlying);
CREATE INDEX IF NOT EXISTS idx_trades_position ON trades(position_id);
CREATE INDEX IF NOT EXISTS idx_trades_date ON trades(trade_date);
CREATE INDEX IF NOT EXISTS idx_watchlist_symbols_watchlist ON watchlist_symbols(watchlist_id);
CREATE INDEX IF NOT EXISTS idx_alerts_position ON alerts(position_id);
CREATE INDEX IF NOT EXISTS idx_alerts_active ON alerts(is_active);
CREATE INDEX IF NOT EXISTS idx_scan_history_date ON scan_history(scan_date);
CREATE INDEX IF NOT EXISTS idx_scan_history_underlying ON scan_history(underlying);

-- Insert default watchlist
INSERT OR IGNORE INTO watchlists (name, description)
VALUES ('Default', 'Default watchlist for scanning');
