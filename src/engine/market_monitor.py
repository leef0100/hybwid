import asyncio
from typing import Dict, List, Callable
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MarketMonitor:
    """Monitor markets in real-time and trigger callbacks"""

    def __init__(self, api_client, update_interval: int = 60):
        self.api_client = api_client
        self.update_interval = update_interval
        self.monitored_markets: List[str] = []
        self.callbacks: List[Callable] = []
        self.running = False
        self.market_cache: Dict[str, Dict] = {}

    def add_market(self, market_id: str):
        """Add a market to monitor"""
        if market_id not in self.monitored_markets:
            self.monitored_markets.append(market_id)
            logger.info(f"Added market {market_id} to monitoring")

    def remove_market(self, market_id: str):
        """Remove a market from monitoring"""
        if market_id in self.monitored_markets:
            self.monitored_markets.remove(market_id)
            logger.info(f"Removed market {market_id} from monitoring")

    def add_callback(self, callback: Callable):
        """Add a callback function to be called on market updates"""
        self.callbacks.append(callback)

    async def start(self):
        """Start monitoring markets"""
        self.running = True
        logger.info(f"Market monitor started. Monitoring {len(self.monitored_markets)} markets")

        while self.running:
            try:
                await self._update_markets()
                await asyncio.sleep(self.update_interval)
            except Exception as e:
                logger.error(f"Error in market monitor: {e}")
                await asyncio.sleep(self.update_interval)

    async def _update_markets(self):
        """Update all monitored markets"""
        for market_id in self.monitored_markets:
            try:
                market = await self.api_client.get_market_by_id(market_id)
                if not market:
                    continue

                prices = await self.api_client.get_market_prices(market_id)
                if not prices:
                    continue

                self.market_cache[market_id] = {
                    'market': market,
                    'prices': prices,
                    'timestamp': datetime.now()
                }

                for callback in self.callbacks:
                    try:
                        await callback(market, prices)
                    except Exception as e:
                        logger.error(f"Error in callback: {e}")

            except Exception as e:
                logger.error(f"Error updating market {market_id}: {e}")

    def stop(self):
        """Stop monitoring"""
        self.running = False
        logger.info("Market monitor stopped")

    async def discover_markets(self, filters: Dict = None) -> List[str]:
        """
        Discover interesting markets to monitor

        Args:
            filters: Dictionary of filters (e.g., min_volume, categories)

        Returns:
            List of market IDs
        """
        markets = await self.api_client.get_markets(limit=500)

        min_volume = filters.get('min_volume', 1000) if filters else 1000
        categories = filters.get('categories', []) if filters else []
        active_only = filters.get('active_only', True) if filters else True

        interesting_markets = []

        for market in markets:
            volume = market.get('volume', 0)
            active = market.get('active', False)
            category = market.get('category', '')

            if active_only and not active:
                continue

            if volume < min_volume:
                continue

            if categories and category not in categories:
                continue

            interesting_markets.append(market.get('id'))

        logger.info(f"Discovered {len(interesting_markets)} interesting markets")
        return interesting_markets
