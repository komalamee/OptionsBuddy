"""Database management for Options Buddy."""

import sqlite3
from pathlib import Path
from datetime import date, datetime
from typing import List, Optional, Dict, Any
from contextlib import contextmanager

from .models import Position, Trade, Watchlist, Alert, SpreadLeg


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
