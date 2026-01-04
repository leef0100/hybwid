from typing import Dict, List
from .base_strategy import BaseStrategy, Signal
import logging

logger = logging.getLogger(__name__)


class ValueStrategy(BaseStrategy):
    """
    Simple value strategy that looks for mispriced markets
    Buys outcomes that appear undervalued based on threshold
    """

    def __init__(self, config: Dict = None):
        super().__init__("ValueStrategy", config)

        self.min_edge = config.get('min_edge', 0.05)
        self.max_price = config.get('max_price', 0.7)
        self.min_price = config.get('min_price', 0.1)
        self.position_size_pct = config.get('position_size_pct', 0.02)

    async def analyze(self, market: Dict, prices: Dict) -> List[Signal]:
        """
        Analyze market for value opportunities

        Logic:
        - Look for YES outcomes priced below expected probability
        - Look for NO outcomes (implied by YES > 0.5) that are underpriced
        """
        signals = []

        question = market.get('question', '')
        market_id = market.get('id', '')

        for outcome, price_data in prices.items():
            mid_price = price_data.get('mid', 0)
            bid_price = price_data.get('bid', 0)
            ask_price = price_data.get('ask', 0)

            if not ask_price or ask_price <= 0:
                continue

            if ask_price < self.min_price or ask_price > self.max_price:
                continue

            fair_value = self._estimate_fair_value(market, outcome)

            if fair_value is None:
                continue

            edge = fair_value - ask_price

            if edge >= self.min_edge:
                size = self._calculate_position_size(edge)
                confidence = min(edge / 0.2, 1.0)

                signal = Signal(
                    market_id=market_id,
                    outcome=outcome,
                    action='BUY',
                    size=size,
                    price=ask_price,
                    confidence=confidence,
                    reason=f"Value play: Fair={fair_value:.3f}, Ask={ask_price:.3f}, Edge={edge:.3f}"
                )
                signals.append(signal)
                logger.info(f"Value signal: {signal}")

        return signals

    def _estimate_fair_value(self, market: Dict, outcome: str) -> float:
        """
        Estimate fair value for an outcome
        This is simplified - in production you'd use more sophisticated models
        """
        end_date = market.get('end_date_iso')
        volume = market.get('volume', 0)

        if volume < 1000:
            return None

        return 0.5

    def _calculate_position_size(self, edge: float) -> float:
        """Calculate position size based on edge"""
        base_size = 100

        size_multiplier = min(edge / self.min_edge, 3.0)

        return base_size * size_multiplier
