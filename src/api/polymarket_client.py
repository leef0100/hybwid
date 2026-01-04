import requests
import aiohttp
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class PolymarketClient:
    """Client for interacting with Polymarket API"""

    def __init__(self, api_url: str = "https://clob.polymarket.com", gamma_url: str = "https://gamma-api.polymarket.com"):
        self.api_url = api_url
        self.gamma_url = gamma_url
        self.session = requests.Session()

    async def get_markets(self, limit: int = 100, offset: int = 0, active: bool = True) -> List[Dict]:
        """Fetch available markets"""
        try:
            params = {
                'limit': limit,
                'offset': offset,
                'active': str(active).lower()
            }
            url = f"{self.gamma_url}/markets"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Fetched {len(data)} markets")
                        return data
                    else:
                        logger.error(f"Failed to fetch markets: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error fetching markets: {e}")
            return []

    async def get_market_by_id(self, market_id: str) -> Optional[Dict]:
        """Fetch specific market by ID"""
        try:
            url = f"{self.gamma_url}/markets/{market_id}"

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Failed to fetch market {market_id}: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error fetching market {market_id}: {e}")
            return None

    async def get_order_book(self, token_id: str) -> Optional[Dict]:
        """Fetch order book for a token"""
        try:
            url = f"{self.api_url}/book"
            params = {'token_id': token_id}

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Failed to fetch order book for {token_id}: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error fetching order book for {token_id}: {e}")
            return None

    async def get_market_prices(self, market_id: str) -> Optional[Dict]:
        """Get current prices for a market"""
        try:
            market = await self.get_market_by_id(market_id)
            if not market:
                return None

            prices = {}
            for token in market.get('tokens', []):
                token_id = token.get('token_id')
                if token_id:
                    orderbook = await self.get_order_book(token_id)
                    if orderbook:
                        bids = orderbook.get('bids', [])
                        asks = orderbook.get('asks', [])

                        best_bid = float(bids[0]['price']) if bids else 0
                        best_ask = float(asks[0]['price']) if asks else 0

                        prices[token.get('outcome', 'unknown')] = {
                            'bid': best_bid,
                            'ask': best_ask,
                            'mid': (best_bid + best_ask) / 2 if best_bid and best_ask else 0,
                            'token_id': token_id
                        }

            return prices
        except Exception as e:
            logger.error(f"Error getting market prices for {market_id}: {e}")
            return None

    async def search_markets(self, query: str) -> List[Dict]:
        """Search for markets by query string"""
        try:
            markets = await self.get_markets(limit=1000)
            results = []

            query_lower = query.lower()
            for market in markets:
                question = market.get('question', '').lower()
                description = market.get('description', '').lower()

                if query_lower in question or query_lower in description:
                    results.append(market)

            logger.info(f"Found {len(results)} markets matching '{query}'")
            return results
        except Exception as e:
            logger.error(f"Error searching markets: {e}")
            return []

    async def get_market_trades(self, market_id: str, limit: int = 100) -> List[Dict]:
        """Fetch recent trades for a market"""
        try:
            url = f"{self.gamma_url}/markets/{market_id}/trades"
            params = {'limit': limit}

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Failed to fetch trades for {market_id}: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error fetching trades for {market_id}: {e}")
            return []

    def close(self):
        """Close the session"""
        self.session.close()
