"""Cross-market arbitrage strategy for detecting mispricing across similar markets"""

from typing import Dict, List
from src.strategies.base_strategy import BaseStrategy, Signal
from src.utils.market_categorizer import MarketCategorizer
import logging

logger = logging.getLogger(__name__)


class CrossMarketArbitrage(BaseStrategy):
    """
    Detects arbitrage opportunities across similar markets

    Example: If two markets ask "Will BTC hit $100k by EOY?" but have different prices,
    we can buy the cheaper one and sell the more expensive one (or just buy the underpriced one).
    """

    def __init__(self, config: Dict = None):
        default_config = {
            'min_price_diff': 0.05,      # Minimum 5% price difference
            'similarity_threshold': 0.7,  # How similar questions need to be
            'position_size': 100,         # Base position size
            'max_markets_compare': 50,    # Max markets to compare at once
        }

        if config:
            default_config.update(config)

        super().__init__("CrossMarketArbitrage", default_config)
        self.categorizer = MarketCategorizer()
        self.market_cache: Dict[str, Dict] = {}  # Store market data for comparison

    async def analyze(self, market: Dict, prices: Dict) -> List[Signal]:
        """
        Analyze a market for cross-market arbitrage opportunities

        This strategy needs to compare across multiple markets, so it builds
        a cache and looks for opportunities when similar markets are found.
        """
        signals = []

        # Store market in cache
        market_id = market.get('id')
        self.market_cache[market_id] = {
            'market': market,
            'prices': prices
        }

        # Clean old cache entries (keep last N markets)
        max_cache = self.config['max_markets_compare']
        if len(self.market_cache) > max_cache:
            # Remove oldest entries
            oldest_keys = list(self.market_cache.keys())[:-max_cache]
            for key in oldest_keys:
                del self.market_cache[key]

        # Find similar markets in cache
        similar_markets = self._find_similar_cached_markets(market)

        if not similar_markets:
            return []

        # Compare prices across similar markets
        for similar_market_id, similarity_score in similar_markets:
            similar_data = self.market_cache[similar_market_id]
            similar_market = similar_data['market']
            similar_prices = similar_data['prices']

            # Generate arbitrage signals
            arb_signals = self._compare_markets(
                market, prices,
                similar_market, similar_prices,
                similarity_score
            )
            signals.extend(arb_signals)

        return signals

    def _find_similar_cached_markets(self, market: Dict) -> List[tuple]:
        """
        Find similar markets in cache

        Returns:
            List of (market_id, similarity_score) tuples
        """
        from difflib import SequenceMatcher

        market_id = market.get('id')
        question = market.get('question', '').lower()
        category = self.categorizer.categorize(market)

        similar = []

        for cached_id, cached_data in self.market_cache.items():
            if cached_id == market_id:
                continue

            cached_market = cached_data['market']
            cached_category = self.categorizer.categorize(cached_market)

            # Must be in same category
            if cached_category != category:
                continue

            cached_question = cached_market.get('question', '').lower()

            # Calculate similarity
            similarity = SequenceMatcher(None, question, cached_question).ratio()

            if similarity >= self.config['similarity_threshold']:
                similar.append((cached_id, similarity))

        return similar

    def _compare_markets(self, market1: Dict, prices1: Dict,
                        market2: Dict, prices2: Dict,
                        similarity: float) -> List[Signal]:
        """
        Compare two similar markets and generate arbitrage signals
        """
        signals = []

        # For binary markets, compare YES outcome prices
        if 'Yes' in prices1 and 'Yes' in prices2:
            price1_ask = prices1['Yes']['ask']
            price2_ask = prices2['Yes']['ask']

            # Skip if no valid prices
            if price1_ask == 0 or price2_ask == 0:
                return []

            price_diff = abs(price1_ask - price2_ask)
            price_diff_pct = price_diff / min(price1_ask, price2_ask)

            if price_diff_pct >= self.config['min_price_diff']:
                # Buy the cheaper market
                if price1_ask < price2_ask:
                    cheaper_market = market1
                    cheaper_price = price1_ask
                    cheaper_outcome = 'Yes'
                else:
                    cheaper_market = market2
                    cheaper_price = price2_ask
                    cheaper_outcome = 'Yes'

                edge = price_diff_pct
                confidence = min(0.9, similarity * (1 + edge))

                signal = Signal(
                    market_id=cheaper_market.get('id'),
                    outcome=cheaper_outcome,
                    action='BUY',
                    size=self.config['position_size'],
                    price=cheaper_price,
                    confidence=confidence,
                    reason=f"Cross-market arbitrage: {price_diff_pct:.1%} cheaper than similar market (similarity: {similarity:.1%})"
                )

                signals.append(signal)
                logger.info(f"Cross-market arbitrage found: {signal.reason}")

        return signals

    def clear_cache(self):
        """Clear the market cache"""
        self.market_cache.clear()
        logger.info("Cross-market arbitrage cache cleared")
