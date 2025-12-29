"""Database management for Options Buddy."""

import sqlite3
from pathlib import Path
from datetime import date, datetime
from typing import List, Optional, Dict, Any
from contextlib import contextmanager

from .models import Position, Trade, Watchlist, Alert, SpreadLeg, StockHolding


# Database path
DB_DIR = Path(__file__).parent.parent / "data_store"
DB_PATH = DB_DIR / "options_buddy.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def init_database() -> None:
    """Initialize the database with schema."""
    # Create data_store directory if it doesn't exist
    DB_DIR.mkdir(parents=True, exist_ok=True)

    with get_db_connection() as conn:
        with open(SCHEMA_PATH, 'r') as f:
            conn.executescript(f.read())
        conn.commit()


@contextmanager
def get_db_connection():
    """Get a database connection with context management."""
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


class DatabaseManager:
    """Manager class for all database operations."""

    # ==================== POSITIONS ====================

    @staticmethod
    def add_position(position: Position) -> int:
        """Add a new position. Returns the position ID."""
        with get_db_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO positions
                (underlying, option_type, strike, expiry, quantity, premium_collected,
                 open_date, status, strategy_type, notes, ibkr_con_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    position.underlying.upper(),
                    position.option_type.upper(),
                    position.strike,
                    position.expiry,
                    position.quantity,
                    position.premium_collected,
                    position.open_date or date.today(),
                    position.status,
                    position.strategy_type,
                    position.notes,
                    position.ibkr_con_id
                )
            )
            conn.commit()
            return cursor.lastrowid

    @staticmethod
    def update_position(position_id: int, updates: Dict[str, Any]) -> None:
        """Update a position with given fields."""
        if not updates:
            return

        # Add updated_at timestamp
        updates['updated_at'] = datetime.now()

        set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
        values = list(updates.values()) + [position_id]

        with get_db_connection() as conn:
            conn.execute(
                f"UPDATE positions SET {set_clause} WHERE id = ?",
                values
            )
            conn.commit()

    @staticmethod
    def close_position(position_id: int, close_price: float, status: str = "CLOSED") -> None:
        """Close a position."""
        DatabaseManager.update_position(position_id, {
            'status': status,
            'close_date': date.today(),
            'close_price': close_price
        })

    @staticmethod
    def get_position(position_id: int) -> Optional[Position]:
        """Get a position by ID."""
        with get_db_connection() as conn:
            row = conn.execute(
                "SELECT * FROM positions WHERE id = ?",
                (position_id,)
            ).fetchone()

            if row:
                return DatabaseManager._row_to_position(row)
            return None

    @staticmethod
    def get_open_positions() -> List[Position]:
        """Get all open positions."""
        with get_db_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM positions WHERE status = 'OPEN' ORDER BY expiry ASC"
            ).fetchall()
            return [DatabaseManager._row_to_position(row) for row in rows]

    @staticmethod
    def get_all_positions() -> List[Position]:
        """Get all positions."""
        with get_db_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM positions ORDER BY created_at DESC"
            ).fetchall()
            return [DatabaseManager._row_to_position(row) for row in rows]

    @staticmethod
    def get_positions_by_underlying(underlying: str) -> List[Position]:
        """Get positions for a specific underlying."""
        with get_db_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM positions WHERE underlying = ? ORDER BY expiry ASC",
                (underlying.upper(),)
            ).fetchall()
            return [DatabaseManager._row_to_position(row) for row in rows]

    @staticmethod
    def get_positions_near_expiry(days: int = 7) -> List[Position]:
        """Get open positions expiring within given days."""
        target_date = date.today()
        with get_db_connection() as conn:
            rows = conn.execute(
                """
                SELECT * FROM positions
                WHERE status = 'OPEN'
                AND julianday(expiry) - julianday(?) <= ?
                ORDER BY expiry ASC
                """,
                (target_date, days)
            ).fetchall()
            return [DatabaseManager._row_to_position(row) for row in rows]

    @staticmethod
    def delete_position(position_id: int) -> None:
        """Delete a position and its related records."""
        with get_db_connection() as conn:
            conn.execute("DELETE FROM positions WHERE id = ?", (position_id,))
            conn.commit()

    @staticmethod
    def _row_to_position(row: sqlite3.Row) -> Position:
        """Convert a database row to a Position object."""
        return Position(
            id=row['id'],
            underlying=row['underlying'],
            option_type=row['option_type'],
            strike=row['strike'],
            expiry=row['expiry'] if isinstance(row['expiry'], date) else
                   datetime.strptime(row['expiry'], '%Y-%m-%d').date() if row['expiry'] else None,
            quantity=row['quantity'],
            premium_collected=row['premium_collected'],
            open_date=row['open_date'] if isinstance(row['open_date'], date) else
                      datetime.strptime(row['open_date'], '%Y-%m-%d').date() if row['open_date'] else None,
            close_date=row['close_date'] if isinstance(row['close_date'], date) else
                       datetime.strptime(row['close_date'], '%Y-%m-%d').date() if row['close_date'] else None,
            close_price=row['close_price'],
            status=row['status'],
            strategy_type=row['strategy_type'],
            notes=row['notes'],
            ibkr_con_id=row['ibkr_con_id'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    # ==================== TRADES ====================

    @staticmethod
    def add_trade(trade: Trade) -> int:
        """Add a trade record. Returns the trade ID."""
        with get_db_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO trades (position_id, action, price, quantity, fees, trade_date, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    trade.position_id,
                    trade.action,
                    trade.price,
                    trade.quantity,
                    trade.fees,
                    trade.trade_date or datetime.now(),
                    trade.notes
                )
            )
            conn.commit()
            return cursor.lastrowid

    @staticmethod
    def get_trades_for_position(position_id: int) -> List[Trade]:
        """Get all trades for a position."""
        with get_db_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM trades WHERE position_id = ? ORDER BY trade_date ASC",
                (position_id,)
            ).fetchall()
            return [
                Trade(
                    id=row['id'],
                    position_id=row['position_id'],
                    action=row['action'],
                    price=row['price'],
                    quantity=row['quantity'],
                    fees=row['fees'],
                    trade_date=row['trade_date'],
                    notes=row['notes']
                )
                for row in rows
            ]

    # ==================== WATCHLISTS ====================

    @staticmethod
    def create_watchlist(name: str, description: str = None) -> int:
        """Create a new watchlist. Returns the watchlist ID."""
        with get_db_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO watchlists (name, description) VALUES (?, ?)",
                (name, description)
            )
            conn.commit()
            return cursor.lastrowid

    @staticmethod
    def get_watchlist(watchlist_id: int) -> Optional[Watchlist]:
        """Get a watchlist by ID with its symbols."""
        with get_db_connection() as conn:
            row = conn.execute(
                "SELECT * FROM watchlists WHERE id = ?",
                (watchlist_id,)
            ).fetchone()

            if not row:
                return None

            symbols = conn.execute(
                "SELECT symbol FROM watchlist_symbols WHERE watchlist_id = ? ORDER BY symbol",
                (watchlist_id,)
            ).fetchall()

            return Watchlist(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                symbols=[s['symbol'] for s in symbols],
                created_at=row['created_at']
            )

    @staticmethod
    def get_all_watchlists() -> List[Watchlist]:
        """Get all watchlists with their symbols."""
        with get_db_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM watchlists ORDER BY name"
            ).fetchall()

            watchlists = []
            for row in rows:
                symbols = conn.execute(
                    "SELECT symbol FROM watchlist_symbols WHERE watchlist_id = ? ORDER BY symbol",
                    (row['id'],)
                ).fetchall()

                watchlists.append(Watchlist(
                    id=row['id'],
                    name=row['name'],
                    description=row['description'],
                    symbols=[s['symbol'] for s in symbols],
                    created_at=row['created_at']
                ))

            return watchlists

    @staticmethod
    def add_symbol_to_watchlist(watchlist_id: int, symbol: str) -> None:
        """Add a symbol to a watchlist."""
        with get_db_connection() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO watchlist_symbols (watchlist_id, symbol) VALUES (?, ?)",
                (watchlist_id, symbol.upper())
            )
            conn.commit()

    @staticmethod
    def remove_symbol_from_watchlist(watchlist_id: int, symbol: str) -> None:
        """Remove a symbol from a watchlist."""
        with get_db_connection() as conn:
            conn.execute(
                "DELETE FROM watchlist_symbols WHERE watchlist_id = ? AND symbol = ?",
                (watchlist_id, symbol.upper())
            )
            conn.commit()

    @staticmethod
    def delete_watchlist(watchlist_id: int) -> None:
        """Delete a watchlist."""
        with get_db_connection() as conn:
            conn.execute("DELETE FROM watchlists WHERE id = ?", (watchlist_id,))
            conn.commit()

    # ==================== SETTINGS ====================

    @staticmethod
    def get_setting(key: str, default: str = None) -> Optional[str]:
        """Get a setting value."""
        with get_db_connection() as conn:
            row = conn.execute(
                "SELECT value FROM settings WHERE key = ?",
                (key,)
            ).fetchone()
            return row['value'] if row else default

    @staticmethod
    def set_setting(key: str, value: str) -> None:
        """Set a setting value."""
        with get_db_connection() as conn:
            conn.execute(
                """
                INSERT INTO settings (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET value = ?, updated_at = CURRENT_TIMESTAMP
                """,
                (key, value, value)
            )
            conn.commit()

    @staticmethod
    def get_all_settings() -> Dict[str, str]:
        """Get all settings as a dictionary."""
        with get_db_connection() as conn:
            rows = conn.execute("SELECT key, value FROM settings").fetchall()
            return {row['key']: row['value'] for row in rows}

    # ==================== PORTFOLIO METRICS ====================

    @staticmethod
    def calculate_total_premium_collected() -> float:
        """Calculate total premium collected from all positions."""
        with get_db_connection() as conn:
            row = conn.execute(
                "SELECT COALESCE(SUM(premium_collected * quantity * 100), 0) as total FROM positions"
            ).fetchone()
            return row['total']

    @staticmethod
    def calculate_open_premium() -> float:
        """Calculate premium from open positions only."""
        with get_db_connection() as conn:
            row = conn.execute(
                """
                SELECT COALESCE(SUM(premium_collected * quantity * 100), 0) as total
                FROM positions WHERE status = 'OPEN'
                """
            ).fetchone()
            return row['total']

    @staticmethod
    def get_position_stats() -> Dict[str, Any]:
        """Get summary statistics for positions."""
        with get_db_connection() as conn:
            stats = {}

            # Total positions by status
            rows = conn.execute(
                "SELECT status, COUNT(*) as count FROM positions GROUP BY status"
            ).fetchall()
            stats['by_status'] = {row['status']: row['count'] for row in rows}

            # Total positions by strategy
            rows = conn.execute(
                "SELECT strategy_type, COUNT(*) as count FROM positions GROUP BY strategy_type"
            ).fetchall()
            stats['by_strategy'] = {row['strategy_type']: row['count'] for row in rows}

            # Win rate (closed positions where close_price < premium_collected)
            row = conn.execute(
                """
                SELECT
                    COUNT(*) as total_closed,
                    SUM(CASE WHEN close_price < premium_collected THEN 1 ELSE 0 END) as wins
                FROM positions
                WHERE status IN ('CLOSED', 'EXPIRED')
                """
            ).fetchone()
            if row['total_closed'] > 0:
                stats['win_rate'] = row['wins'] / row['total_closed'] * 100
            else:
                stats['win_rate'] = 0

            return stats

    # ==================== P&L CALCULATIONS ====================

    @staticmethod
    def calculate_realized_pnl() -> Dict[str, Any]:
        """Calculate realized P&L from closed positions."""
        with get_db_connection() as conn:
            # For options sellers: P&L = premium collected - close price (if closed)
            # If expired worthless: P&L = full premium collected
            row = conn.execute(
                """
                SELECT
                    COALESCE(SUM(
                        CASE
                            WHEN status = 'EXPIRED' THEN premium_collected * quantity * 100
                            WHEN status IN ('CLOSED', 'ROLLED') THEN (premium_collected - COALESCE(close_price, 0)) * quantity * 100
                            WHEN status = 'ASSIGNED' THEN premium_collected * quantity * 100
                            ELSE 0
                        END
                    ), 0) as total_pnl,
                    COUNT(*) as closed_count
                FROM positions
                WHERE status IN ('CLOSED', 'EXPIRED', 'ASSIGNED', 'ROLLED')
                """
            ).fetchone()
            return {
                'total_pnl': row['total_pnl'],
                'closed_count': row['closed_count']
            }

    @staticmethod
    def calculate_unrealized_pnl(current_prices: Dict[int, float] = None) -> float:
        """
        Calculate unrealized P&L from open positions.
        current_prices: dict mapping position_id to current option price
        If not provided, returns 0 (need live data for accurate unrealized P&L)
        """
        if not current_prices:
            return 0.0

        with get_db_connection() as conn:
            rows = conn.execute(
                "SELECT id, premium_collected, quantity FROM positions WHERE status = 'OPEN'"
            ).fetchall()

            total_unrealized = 0.0
            for row in rows:
                if row['id'] in current_prices:
                    # P&L = (premium collected - current price) * quantity * 100
                    pnl = (row['premium_collected'] - current_prices[row['id']]) * row['quantity'] * 100
                    total_unrealized += pnl

            return total_unrealized

    @staticmethod
    def get_pnl_by_period(period: str = 'all') -> Dict[str, Any]:
        """
        Get P&L broken down by time period.
        period: 'today', 'week', 'month', 'year', 'all'
        """
        with get_db_connection() as conn:
            # Build date filter
            if period == 'today':
                date_filter = "AND date(close_date) = date('now')"
            elif period == 'week':
                date_filter = "AND date(close_date) >= date('now', '-7 days')"
            elif period == 'month':
                date_filter = "AND date(close_date) >= date('now', '-30 days')"
            elif period == 'year':
                date_filter = "AND date(close_date) >= date('now', '-365 days')"
            else:
                date_filter = ""

            row = conn.execute(
                f"""
                SELECT
                    COALESCE(SUM(
                        CASE
                            WHEN status = 'EXPIRED' THEN premium_collected * quantity * 100
                            WHEN status IN ('CLOSED', 'ROLLED') THEN (premium_collected - COALESCE(close_price, 0)) * quantity * 100
                            WHEN status = 'ASSIGNED' THEN premium_collected * quantity * 100
                            ELSE 0
                        END
                    ), 0) as pnl,
                    COUNT(*) as trade_count,
                    SUM(CASE WHEN (premium_collected - COALESCE(close_price, 0)) > 0 THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN (premium_collected - COALESCE(close_price, 0)) <= 0 THEN 1 ELSE 0 END) as losses
                FROM positions
                WHERE status IN ('CLOSED', 'EXPIRED', 'ASSIGNED', 'ROLLED')
                {date_filter}
                """
            ).fetchone()

            return {
                'pnl': row['pnl'],
                'trade_count': row['trade_count'],
                'wins': row['wins'] or 0,
                'losses': row['losses'] or 0,
                'win_rate': (row['wins'] / row['trade_count'] * 100) if row['trade_count'] > 0 else 0
            }

    @staticmethod
    def get_pnl_by_underlying() -> List[Dict[str, Any]]:
        """Get P&L breakdown by underlying symbol."""
        with get_db_connection() as conn:
            rows = conn.execute(
                """
                SELECT
                    underlying,
                    COUNT(*) as trade_count,
                    COALESCE(SUM(
                        CASE
                            WHEN status = 'EXPIRED' THEN premium_collected * quantity * 100
                            WHEN status IN ('CLOSED', 'ROLLED') THEN (premium_collected - COALESCE(close_price, 0)) * quantity * 100
                            WHEN status = 'ASSIGNED' THEN premium_collected * quantity * 100
                            ELSE 0
                        END
                    ), 0) as pnl,
                    SUM(CASE WHEN (premium_collected - COALESCE(close_price, 0)) > 0 THEN 1 ELSE 0 END) as wins
                FROM positions
                WHERE status IN ('CLOSED', 'EXPIRED', 'ASSIGNED', 'ROLLED')
                GROUP BY underlying
                ORDER BY pnl DESC
                """
            ).fetchall()

            return [
                {
                    'underlying': row['underlying'],
                    'trade_count': row['trade_count'],
                    'pnl': row['pnl'],
                    'wins': row['wins'] or 0,
                    'win_rate': (row['wins'] / row['trade_count'] * 100) if row['trade_count'] > 0 else 0
                }
                for row in rows
            ]

    @staticmethod
    def get_pnl_by_strategy() -> List[Dict[str, Any]]:
        """Get P&L breakdown by strategy type."""
        with get_db_connection() as conn:
            rows = conn.execute(
                """
                SELECT
                    strategy_type,
                    COUNT(*) as trade_count,
                    COALESCE(SUM(
                        CASE
                            WHEN status = 'EXPIRED' THEN premium_collected * quantity * 100
                            WHEN status IN ('CLOSED', 'ROLLED') THEN (premium_collected - COALESCE(close_price, 0)) * quantity * 100
                            WHEN status = 'ASSIGNED' THEN premium_collected * quantity * 100
                            ELSE 0
                        END
                    ), 0) as pnl,
                    SUM(CASE WHEN (premium_collected - COALESCE(close_price, 0)) > 0 THEN 1 ELSE 0 END) as wins
                FROM positions
                WHERE status IN ('CLOSED', 'EXPIRED', 'ASSIGNED', 'ROLLED')
                GROUP BY strategy_type
                ORDER BY pnl DESC
                """
            ).fetchall()

            return [
                {
                    'strategy_type': row['strategy_type'],
                    'trade_count': row['trade_count'],
                    'pnl': row['pnl'],
                    'wins': row['wins'] or 0,
                    'win_rate': (row['wins'] / row['trade_count'] * 100) if row['trade_count'] > 0 else 0
                }
                for row in rows
            ]

    @staticmethod
    def get_closed_positions(limit: int = None) -> List[Position]:
        """Get closed positions with optional limit."""
        with get_db_connection() as conn:
            query = """
                SELECT * FROM positions
                WHERE status IN ('CLOSED', 'EXPIRED', 'ASSIGNED', 'ROLLED')
                ORDER BY close_date DESC
            """
            if limit:
                query += f" LIMIT {limit}"

            rows = conn.execute(query).fetchall()
            return [DatabaseManager._row_to_position(row) for row in rows]

    @staticmethod
    def get_daily_pnl_history(days: int = 30) -> List[Dict[str, Any]]:
        """Get daily P&L for the last N days."""
        with get_db_connection() as conn:
            rows = conn.execute(
                """
                SELECT
                    date(close_date) as trade_date,
                    COALESCE(SUM(
                        CASE
                            WHEN status = 'EXPIRED' THEN premium_collected * quantity * 100
                            WHEN status IN ('CLOSED', 'ROLLED') THEN (premium_collected - COALESCE(close_price, 0)) * quantity * 100
                            WHEN status = 'ASSIGNED' THEN premium_collected * quantity * 100
                            ELSE 0
                        END
                    ), 0) as daily_pnl,
                    COUNT(*) as trade_count
                FROM positions
                WHERE status IN ('CLOSED', 'EXPIRED', 'ASSIGNED', 'ROLLED')
                AND date(close_date) >= date('now', ?)
                GROUP BY date(close_date)
                ORDER BY trade_date ASC
                """,
                (f'-{days} days',)
            ).fetchall()

            return [
                {
                    'date': row['trade_date'],
                    'pnl': row['daily_pnl'],
                    'trade_count': row['trade_count']
                }
                for row in rows
            ]

    # ==================== TRADE IMPORT ====================

    @staticmethod
    def import_trades_from_csv(trades_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Import trades from CSV data.
        Expected fields: underlying, option_type, strike, expiry, quantity,
                        premium_collected, open_date, close_date, close_price,
                        status, strategy_type, notes
        Returns: {'imported': count, 'errors': count}
        """
        imported = 0
        errors = 0

        with get_db_connection() as conn:
            for trade in trades_data:
                try:
                    # Parse dates
                    expiry = trade.get('expiry')
                    if isinstance(expiry, str):
                        expiry = datetime.strptime(expiry, '%Y-%m-%d').date()

                    open_date = trade.get('open_date')
                    if isinstance(open_date, str):
                        open_date = datetime.strptime(open_date, '%Y-%m-%d').date()

                    close_date = trade.get('close_date')
                    if isinstance(close_date, str) and close_date:
                        close_date = datetime.strptime(close_date, '%Y-%m-%d').date()
                    else:
                        close_date = None

                    conn.execute(
                        """
                        INSERT INTO positions
                        (underlying, option_type, strike, expiry, quantity, premium_collected,
                         open_date, close_date, close_price, status, strategy_type, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            trade.get('underlying', '').upper(),
                            trade.get('option_type', 'PUT').upper(),
                            float(trade.get('strike', 0)),
                            expiry,
                            int(trade.get('quantity', 1)),
                            float(trade.get('premium_collected', 0)),
                            open_date,
                            close_date,
                            float(trade.get('close_price', 0)) if trade.get('close_price') else None,
                            trade.get('status', 'CLOSED').upper(),
                            trade.get('strategy_type', 'CSP').upper(),
                            trade.get('notes', '')
                        )
                    )
                    imported += 1
                except Exception as e:
                    errors += 1
                    continue

            conn.commit()

        return {'imported': imported, 'errors': errors}

    # ==================== STOCK HOLDINGS ====================

    @staticmethod
    def upsert_stock_holding(holding: StockHolding) -> int:
        """Insert or update a stock holding. Returns the holding ID."""
        with get_db_connection() as conn:
            # Check if exists
            existing = conn.execute(
                "SELECT id FROM stock_holdings WHERE symbol = ?",
                (holding.symbol.upper(),)
            ).fetchone()

            if existing:
                # Update existing
                conn.execute(
                    """
                    UPDATE stock_holdings SET
                        quantity = ?, avg_cost = ?, current_price = ?,
                        market_value = ?, unrealized_pnl = ?, ibkr_con_id = ?,
                        last_synced = CURRENT_TIMESTAMP
                    WHERE symbol = ?
                    """,
                    (
                        holding.quantity,
                        holding.avg_cost,
                        holding.current_price,
                        holding.market_value,
                        holding.unrealized_pnl,
                        holding.ibkr_con_id,
                        holding.symbol.upper()
                    )
                )
                conn.commit()
                return existing['id']
            else:
                # Insert new
                cursor = conn.execute(
                    """
                    INSERT INTO stock_holdings
                    (symbol, quantity, avg_cost, current_price, market_value,
                     unrealized_pnl, ibkr_con_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        holding.symbol.upper(),
                        holding.quantity,
                        holding.avg_cost,
                        holding.current_price,
                        holding.market_value,
                        holding.unrealized_pnl,
                        holding.ibkr_con_id
                    )
                )
                conn.commit()
                return cursor.lastrowid

    @staticmethod
    def get_all_stock_holdings() -> List[StockHolding]:
        """Get all stock holdings."""
        with get_db_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM stock_holdings ORDER BY symbol ASC"
            ).fetchall()

            return [
                StockHolding(
                    id=row['id'],
                    symbol=row['symbol'],
                    quantity=row['quantity'],
                    avg_cost=row['avg_cost'],
                    current_price=row['current_price'],
                    market_value=row['market_value'],
                    unrealized_pnl=row['unrealized_pnl'],
                    ibkr_con_id=row['ibkr_con_id'],
                    last_synced=row['last_synced']
                )
                for row in rows
            ]

    @staticmethod
    def get_stock_holding(symbol: str) -> Optional[StockHolding]:
        """Get a stock holding by symbol."""
        with get_db_connection() as conn:
            row = conn.execute(
                "SELECT * FROM stock_holdings WHERE symbol = ?",
                (symbol.upper(),)
            ).fetchone()

            if row:
                return StockHolding(
                    id=row['id'],
                    symbol=row['symbol'],
                    quantity=row['quantity'],
                    avg_cost=row['avg_cost'],
                    current_price=row['current_price'],
                    market_value=row['market_value'],
                    unrealized_pnl=row['unrealized_pnl'],
                    ibkr_con_id=row['ibkr_con_id'],
                    last_synced=row['last_synced']
                )
            return None

    @staticmethod
    def delete_stock_holding(symbol: str) -> None:
        """Delete a stock holding."""
        with get_db_connection() as conn:
            conn.execute(
                "DELETE FROM stock_holdings WHERE symbol = ?",
                (symbol.upper(),)
            )
            conn.commit()

    @staticmethod
    def clear_all_stock_holdings() -> None:
        """Clear all stock holdings (used before full sync)."""
        with get_db_connection() as conn:
            conn.execute("DELETE FROM stock_holdings")
            conn.commit()

    @staticmethod
    def get_covered_call_eligible() -> List[Dict[str, Any]]:
        """Get stocks with enough shares for covered calls (100+ shares)."""
        with get_db_connection() as conn:
            rows = conn.execute(
                """
                SELECT symbol, quantity, avg_cost, current_price, market_value,
                       (quantity / 100) as cc_lots,
                       (quantity % 100) as remaining_shares
                FROM stock_holdings
                WHERE quantity >= 100
                ORDER BY quantity DESC
                """
            ).fetchall()

            return [
                {
                    'symbol': row['symbol'],
                    'quantity': row['quantity'],
                    'avg_cost': row['avg_cost'],
                    'current_price': row['current_price'],
                    'market_value': row['market_value'],
                    'cc_lots': row['cc_lots'],
                    'remaining_shares': row['remaining_shares']
                }
                for row in rows
            ]

    @staticmethod
    def get_portfolio_summary() -> Dict[str, Any]:
        """Get overall portfolio summary including stocks and options."""
        with get_db_connection() as conn:
            # Stock holdings summary
            stock_row = conn.execute(
                """
                SELECT
                    COUNT(*) as stock_count,
                    COALESCE(SUM(quantity), 0) as total_shares,
                    COALESCE(SUM(market_value), 0) as total_stock_value,
                    COALESCE(SUM(unrealized_pnl), 0) as stock_unrealized_pnl
                FROM stock_holdings
                """
            ).fetchone()

            # Open options summary
            options_row = conn.execute(
                """
                SELECT
                    COUNT(*) as options_count,
                    COALESCE(SUM(premium_collected * quantity * 100), 0) as open_premium
                FROM positions
                WHERE status = 'OPEN'
                """
            ).fetchone()

            # CC eligible
            cc_row = conn.execute(
                """
                SELECT COALESCE(SUM(quantity / 100), 0) as cc_lots
                FROM stock_holdings
                WHERE quantity >= 100
                """
            ).fetchone()

            return {
                'stock_count': stock_row['stock_count'],
                'total_shares': stock_row['total_shares'],
                'total_stock_value': stock_row['total_stock_value'],
                'stock_unrealized_pnl': stock_row['stock_unrealized_pnl'],
                'open_options_count': options_row['options_count'],
                'open_premium': options_row['open_premium'],
                'cc_lots_available': cc_row['cc_lots']
            }
