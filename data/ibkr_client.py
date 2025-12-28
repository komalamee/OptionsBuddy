"""Interactive Brokers API client wrapper using ib_insync."""

import logging
import asyncio
from typing import Optional, List
from dataclasses import dataclass
from datetime import datetime

# Apply nest_asyncio to allow nested event loops (needed for Streamlit)
import nest_asyncio
nest_asyncio.apply()

from config.settings import get_settings, IBKRSettings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lazy imports to avoid event loop issues at module load time
_ib_insync_imported = False
IB = None
Stock = None
Option = None
Contract = None
util = None


def _ensure_ib_insync_imported():
    """Lazily import ib_insync to avoid event loop issues."""
    global _ib_insync_imported, IB, Stock, Option, Contract, util
    if not _ib_insync_imported:
        from ib_insync import IB as _IB, Stock as _Stock, Option as _Option, Contract as _Contract, util as _util
        IB = _IB
        Stock = _Stock
        Option = _Option
        Contract = _Contract
        util = _util
        _ib_insync_imported = True


@dataclass
class ConnectionStatus:
    """Represents the IBKR connection status."""
    is_connected: bool
    host: str
    port: int
    client_id: int
    server_version: Optional[int] = None
    connection_time: Optional[datetime] = None
    error_message: Optional[str] = None


class IBKRClient:
    """
    Wrapper around ib_insync for Interactive Brokers connectivity.

    This client provides a simplified interface for:
    - Connecting/disconnecting to TWS or IB Gateway
    - Fetching option chains
    - Getting real-time and historical market data
    - Reading positions (no execution in V1)
    """

    _instance: Optional["IBKRClient"] = None

    def __init__(self, settings: Optional[IBKRSettings] = None):
        """Initialize the IBKR client."""
        self.settings = settings or get_settings().ibkr
        self._ib = None
        self._connected = False
        self._connection_time: Optional[datetime] = None

    def _get_ib(self):
        """Get or create the IB instance."""
        if self._ib is None:
            _ensure_ib_insync_imported()
            self._ib = IB()
        return self._ib

    @classmethod
    def get_instance(cls, settings: Optional[IBKRSettings] = None) -> "IBKRClient":
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = cls(settings)
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """Reset the singleton instance."""
        if cls._instance is not None:
            try:
                if cls._instance._ib and cls._instance._ib.isConnected():
                    cls._instance._ib.disconnect()
            except:
                pass
            cls._instance = None

    @property
    def ib(self):
        """Get the underlying IB instance."""
        return self._get_ib()

    @property
    def is_connected(self) -> bool:
        """Check if connected to IBKR."""
        try:
            if self._ib is None:
                return False
            return self._ib.isConnected()
        except:
            return False

    def connect(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        client_id: Optional[int] = None,
        timeout: int = 10
    ) -> ConnectionStatus:
        """
        Connect to TWS or IB Gateway.

        Args:
            host: IBKR host (default from settings)
            port: IBKR port (default from settings)
            client_id: Client ID (default from settings)
            timeout: Connection timeout in seconds

        Returns:
            ConnectionStatus with connection details
        """
        host = host or self.settings.host
        port = port or self.settings.port
        client_id = client_id or self.settings.client_id

        try:
            if self.is_connected:
                logger.info("Already connected to IBKR")
                return self.get_status()

            logger.info(f"Connecting to IBKR at {host}:{port} with client ID {client_id}")

            ib = self._get_ib()

            # Connect with timeout
            ib.connect(
                host=host,
                port=port,
                clientId=client_id,
                timeout=timeout,
                readonly=True  # V1 is read-only
            )

            # Set market data type
            ib.reqMarketDataType(self.settings.market_data_type)

            self._connected = True
            self._connection_time = datetime.now()

            logger.info("Successfully connected to IBKR")
            return self.get_status()

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to connect to IBKR: {error_msg}")
            return ConnectionStatus(
                is_connected=False,
                host=host,
                port=port,
                client_id=client_id,
                error_message=error_msg
            )

    def disconnect(self) -> None:
        """Disconnect from IBKR."""
        try:
            if self._ib and self._ib.isConnected():
                logger.info("Disconnecting from IBKR")
                self._ib.disconnect()
        except Exception as e:
            logger.error(f"Error disconnecting: {e}")
        finally:
            self._connected = False
            self._connection_time = None

    def get_status(self) -> ConnectionStatus:
        """Get the current connection status."""
        try:
            server_version = None
            if self.is_connected and self._ib:
                try:
                    server_version = self._ib.client.serverVersion()
                except:
                    pass

            return ConnectionStatus(
                is_connected=self.is_connected,
                host=self.settings.host,
                port=self.settings.port,
                client_id=self.settings.client_id,
                server_version=server_version,
                connection_time=self._connection_time
            )
        except Exception as e:
            return ConnectionStatus(
                is_connected=False,
                host=self.settings.host,
                port=self.settings.port,
                client_id=self.settings.client_id,
                error_message=str(e)
            )

    def ensure_connected(self) -> bool:
        """Ensure we're connected, attempting reconnection if needed."""
        if not self.is_connected:
            status = self.connect()
            return status.is_connected
        return True

    # ==================== CONTRACT HELPERS ====================

    def create_stock_contract(self, symbol: str, exchange: str = "SMART", currency: str = "USD"):
        """Create a stock contract."""
        _ensure_ib_insync_imported()
        return Stock(symbol.upper(), exchange, currency)

    def create_option_contract(
        self,
        symbol: str,
        expiry: str,  # Format: YYYYMMDD
        strike: float,
        right: str,  # 'C' or 'P'
        exchange: str = "SMART",
        currency: str = "USD"
    ):
        """Create an option contract."""
        _ensure_ib_insync_imported()
        return Option(
            symbol=symbol.upper(),
            lastTradeDateOrContractMonth=expiry,
            strike=strike,
            right=right.upper(),
            exchange=exchange,
            currency=currency
        )

    def qualify_contracts(self, contracts: List) -> List:
        """Qualify contracts with IBKR to get full details."""
        if not self.ensure_connected():
            raise ConnectionError("Not connected to IBKR")
        return self._ib.qualifyContracts(*contracts)

    # ==================== MARKET DATA ====================

    def get_stock_price(self, symbol: str) -> Optional[float]:
        """Get the current price for a stock."""
        if not self.ensure_connected():
            return None

        _ensure_ib_insync_imported()

        try:
            contract = self.create_stock_contract(symbol)
            self._ib.qualifyContracts(contract)

            ticker = self._ib.reqMktData(contract, '', False, False)
            self._ib.sleep(2)  # Wait for data

            price = ticker.marketPrice()
            self._ib.cancelMktData(contract)

            return price if not util.isNan(price) else None

        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {e}")
            return None

    def get_option_chain_expirations(self, symbol: str) -> List[str]:
        """Get available option expirations for a symbol."""
        if not self.ensure_connected():
            return []

        try:
            contract = self.create_stock_contract(symbol)
            self._ib.qualifyContracts(contract)

            chains = self._ib.reqSecDefOptParams(
                contract.symbol,
                '',
                contract.secType,
                contract.conId
            )

            # Get unique expirations from all chains
            expirations = set()
            for chain in chains:
                expirations.update(chain.expirations)

            return sorted(list(expirations))

        except Exception as e:
            logger.error(f"Error getting expirations for {symbol}: {e}")
            return []

    def get_option_chain_strikes(self, symbol: str, expiry: str) -> List[float]:
        """Get available strikes for a symbol and expiry."""
        if not self.ensure_connected():
            return []

        try:
            contract = self.create_stock_contract(symbol)
            self._ib.qualifyContracts(contract)

            chains = self._ib.reqSecDefOptParams(
                contract.symbol,
                '',
                contract.secType,
                contract.conId
            )

            # Find strikes for the given expiry
            strikes = set()
            for chain in chains:
                if expiry in chain.expirations:
                    strikes.update(chain.strikes)

            return sorted(list(strikes))

        except Exception as e:
            logger.error(f"Error getting strikes for {symbol} {expiry}: {e}")
            return []

    # ==================== POSITIONS (READ-ONLY) ====================

    def get_positions(self) -> List[dict]:
        """Get current positions from IBKR account."""
        if not self.ensure_connected():
            return []

        try:
            positions = self._ib.positions()
            return [
                {
                    'account': pos.account,
                    'symbol': pos.contract.symbol,
                    'sec_type': pos.contract.secType,
                    'strike': getattr(pos.contract, 'strike', None),
                    'expiry': getattr(pos.contract, 'lastTradeDateOrContractMonth', None),
                    'right': getattr(pos.contract, 'right', None),
                    'quantity': pos.position,
                    'avg_cost': pos.avgCost,
                    'con_id': pos.contract.conId
                }
                for pos in positions
            ]
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []

    def get_account_summary(self) -> dict:
        """Get account summary from IBKR."""
        if not self.ensure_connected():
            return {}

        try:
            account_values = self._ib.accountSummary()
            summary = {}
            for av in account_values:
                summary[av.tag] = {
                    'value': av.value,
                    'currency': av.currency
                }
            return summary
        except Exception as e:
            logger.error(f"Error getting account summary: {e}")
            return {}


# Convenience function to get the singleton client
def get_ibkr_client(settings: Optional[IBKRSettings] = None) -> IBKRClient:
    """Get the IBKR client singleton."""
    return IBKRClient.get_instance(settings)
