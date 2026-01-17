"""Coinglass API Client for fetching crypto derivatives data"""

import aiohttp
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class CoinglassClient:
    """Client for Coinglass API v2"""

    def __init__(self, api_key: str, base_url: str = "https://open-api.coinglass.com/public/v2"):
        self.api_key = api_key
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None

    async def _ensure_session(self):
        """Ensure aiohttp session exists"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()

    async def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make API request to Coinglass"""
        await self._ensure_session()

        url = f"{self.base_url}/{endpoint}"
        headers = {
            "CG-API-KEY": self.api_key,
            "Accept": "application/json"
        }

        try:
            async with self.session.get(url, headers=headers, params=params, ssl=False) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('success'):
                        return data.get('data', {})
                    else:
                        logger.error(f"API error: {data.get('msg', 'Unknown error')}")
                        return {}
                else:
                    logger.error(f"HTTP {response.status}: {await response.text()}")
                    return {}
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return {}

    async def get_supported_coins(self) -> List[str]:
        """Get list of supported coins"""
        data = await self._make_request("coins")
        return data.get('coins', []) if data else []

    async def get_open_interest(self, symbol: str, interval: str = "0") -> Dict:
        """
        Get open interest data for a symbol

        Args:
            symbol: Coin symbol (e.g., BTC, ETH, SOL)
            interval: Time interval (0=all, 1=1h, 2=4h, 3=12h, 4=24h)
        """
        endpoint = "openInterest"
        params = {
            "symbol": symbol,
            "interval": interval
        }
        return await self._make_request(endpoint, params)

    async def get_oi_history(self, symbol: str, exchange: str = "all", time_type: str = "h1") -> Dict:
        """
        Get open interest OHLC history

        Args:
            symbol: Coin symbol
            exchange: Exchange name or 'all'
            time_type: Time interval (m5, m15, m30, h1, h4, h12, h24)
        """
        endpoint = "ohlc-history"
        params = {
            "symbol": symbol,
            "exchange": exchange,
            "interval": time_type
        }
        return await self._make_request(endpoint, params)

    async def get_funding_rates(self, symbol: str) -> Dict:
        """Get funding rates for a symbol"""
        endpoint = "fundingRate"
        params = {"symbol": symbol}
        return await self._make_request(endpoint, params)

    async def get_liquidation_history(self, symbol: str, time_type: str = "h1") -> Dict:
        """
        Get liquidation data

        Args:
            symbol: Coin symbol
            time_type: Time interval (m5, m15, m30, h1, h4, h12, h24)
        """
        endpoint = "liquidation_history"
        params = {
            "symbol": symbol,
            "interval": time_type
        }
        return await self._make_request(endpoint, params)

    async def get_liquidation_heatmap(self, symbol: str, exchange: str = "Binance") -> Dict:
        """
        Get liquidation heatmap data

        Args:
            symbol: Trading pair (e.g., BTCUSDT, ETHUSDT, SOLUSDT)
            exchange: Exchange name
        """
        endpoint = "liquidation_heatmap"
        params = {
            "symbol": symbol,
            "exchange": exchange
        }
        return await self._make_request(endpoint, params)

    async def get_long_short_ratio(self, symbol: str, exchange: str = "all") -> Dict:
        """Get long/short ratio for a symbol"""
        endpoint = "longShortRatio"
        params = {
            "symbol": symbol,
            "exchange": exchange
        }
        return await self._make_request(endpoint, params)

    async def get_volume_ohlc(self, symbol: str, exchange: str = "all", interval: str = "h1") -> Dict:
        """
        Get volume OHLC data

        Args:
            symbol: Coin symbol
            exchange: Exchange name or 'all'
            interval: Time interval (m5, m15, m30, h1, h4, h12, h24)
        """
        endpoint = "volume-ohlc"
        params = {
            "symbol": symbol,
            "exchange": exchange,
            "interval": interval
        }
        return await self._make_request(endpoint, params)

    async def get_fear_greed_index(self) -> Dict:
        """Get crypto fear and greed index"""
        endpoint = "fearGreedIndex"
        return await self._make_request(endpoint)

    async def get_btc_dominance(self) -> Dict:
        """Get Bitcoin dominance data"""
        endpoint = "btcDominance"
        return await self._make_request(endpoint)

    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()

    async def __aenter__(self):
        """Async context manager entry"""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
