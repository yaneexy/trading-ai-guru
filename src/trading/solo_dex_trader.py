import json
import asyncio
import websockets
import aiohttp
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List
import logging
from xrpl.clients import JsonRpcClient
from xrpl.models import Payment, AccountInfo
from xrpl.wallet import Wallet
from xrpl.core import addresscodec
import xrpl.constants

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SoloToken:
    currency: str
    issuer: str
    value: str
    name: str = ""
    logo: str = ""

@dataclass
class OrderBook:
    bids: List[Dict[str, Any]]
    asks: List[Dict[str, Any]]
    spread: float
    last_update: datetime

class SoloDEXTrader:
    def __init__(self, wallet_seed: str, node_url: str = "wss://s.devnet.rippletest.net:51233"):
        """
        Initialize Solo DEX trader
        
        Args:
            wallet_seed: The seed for the XRPL wallet
            node_url: URL of the XRPL node to connect to
        """
        self.wallet = Wallet.from_seed(wallet_seed)
        self.client = JsonRpcClient(node_url)
        self.orderbook: Optional[OrderBook] = None
        self.ws_client = None
        self.base_url = "https://api.sologenic.org/api/v1"
        
    async def connect_ws(self):
        """Connect to XRPL WebSocket"""
        self.ws_client = await websockets.connect(self.node_url)
        
    async def subscribe_orderbook(self, base_currency: str, quote_currency: str):
        """
        Subscribe to orderbook updates
        
        Args:
            base_currency: Base currency (e.g., 'XRP')
            quote_currency: Quote currency (e.g., 'SOLO')
        """
        subscribe_message = {
            "command": "subscribe",
            "books": [{
                "taker_gets": {"currency": base_currency},
                "taker_pays": {"currency": quote_currency},
                "snapshot": True
            }]
        }
        await self.ws_client.send(json.dumps(subscribe_message))
        
    async def get_token_info(self, currency_id: str) -> Optional[SoloToken]:
        """
        Get token information from Sologenic API
        
        Args:
            currency_id: Currency identifier
            
        Returns:
            SoloToken object if found, None otherwise
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/tokens/{currency_id}") as response:
                if response.status == 200:
                    data = await response.json()
                    return SoloToken(
                        currency=data["currency"],
                        issuer=data["issuer"],
                        value=data["value"],
                        name=data.get("name", ""),
                        logo=data.get("logo", "")
                    )
                return None
                
    async def get_orderbook(self, base_currency: str, quote_currency: str) -> OrderBook:
        """
        Get current orderbook for a trading pair
        
        Args:
            base_currency: Base currency (e.g., 'XRP')
            quote_currency: Quote currency (e.g., 'SOLO')
            
        Returns:
            OrderBook object with current market data
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/orderbook/{base_currency}/{quote_currency}"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return OrderBook(
                        bids=data["bids"],
                        asks=data["asks"],
                        spread=float(data["spread"]),
                        last_update=datetime.now()
                    )
                raise Exception(f"Failed to fetch orderbook: {response.status}")
                
    async def place_limit_order(
        self,
        side: str,
        base_currency: str,
        quote_currency: str,
        amount: float,
        price: float
    ) -> Dict[str, Any]:
        """
        Place a limit order on Solo DEX
        
        Args:
            side: 'buy' or 'sell'
            base_currency: Base currency (e.g., 'XRP')
            quote_currency: Quote currency (e.g., 'SOLO')
            amount: Amount to trade
            price: Limit price
            
        Returns:
            Transaction response
        """
        # Create offer object
        offer = {
            "TransactionType": "OfferCreate",
            "Account": self.wallet.classic_address,
            "TakerGets": self._format_currency_amount(
                base_currency if side == "sell" else quote_currency,
                amount if side == "sell" else amount * price
            ),
            "TakerPays": self._format_currency_amount(
                quote_currency if side == "sell" else base_currency,
                amount * price if side == "sell" else amount
            )
        }
        
        # Sign and submit transaction
        response = await self._submit_transaction(offer)
        return response
        
    async def place_market_order(
        self,
        side: str,
        base_currency: str,
        quote_currency: str,
        amount: float
    ) -> Dict[str, Any]:
        """
        Place a market order on Solo DEX
        
        Args:
            side: 'buy' or 'sell'
            base_currency: Base currency
            quote_currency: Quote currency
            amount: Amount to trade
            
        Returns:
            Transaction response
        """
        # Get current orderbook
        orderbook = await self.get_orderbook(base_currency, quote_currency)
        
        # Calculate market price (use first ask for buy, first bid for sell)
        price = float(orderbook.asks[0]["price"]) if side == "buy" else float(orderbook.bids[0]["price"])
        
        # Place limit order at market price
        return await self.place_limit_order(side, base_currency, quote_currency, amount, price)
        
    def _format_currency_amount(self, currency: str, amount: float) -> Dict[str, Any]:
        """Format currency amount for XRPL transaction"""
        if currency == "XRP":
            return str(int(amount * 1_000_000))  # Convert to drops
        return {
            "currency": currency,
            "issuer": self._get_currency_issuer(currency),
            "value": str(amount)
        }
        
    def _get_currency_issuer(self, currency: str) -> str:
        """Get issuer address for a currency"""
        # Add mapping of currencies to their issuers
        ISSUERS = {
            "SOLO": "rsoLo2S1kiGeCcn6hCUXVrCpGMWLrRrLZz",  # Sologenic issuer
            # Add more currencies as needed
        }
        return ISSUERS.get(currency, "")
        
    async def _submit_transaction(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Submit a transaction to the XRPL"""
        # Add common fields
        transaction.update({
            "Fee": "12",  # Standard fee in drops
            "Flags": xrpl.constants.TF_LIMIT_QUALITY,
            "LastLedgerSequence": None,  # Will be set by submit
            "Sequence": None,  # Will be set by submit
        })
        
        # Sign and submit
        response = await self.client.submit(transaction, self.wallet)
        return response
        
    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information and balances"""
        request = AccountInfo(
            account=self.wallet.classic_address,
            ledger_index="validated"
        )
        response = await self.client.request(request)
        return response.result
        
    async def close(self):
        """Close WebSocket connection"""
        if self.ws_client:
            await self.ws_client.close()
