from typing import Dict, List
from .base_strategy import BaseStrategy, Signal
import logging

logger = logging.getLogger(__name__)


class ArbitrageStrategy(BaseStrategy):
    """
    Arbitrage strategy that looks for mispricing between outcomes
    In binary markets, YES + NO should equal ~1.0
    """

    def __init__(self, config: Dict = None):
        super().__init__("ArbitrageStrategy", config)

        self.min_arb_edge = config.get('min_arb_edge', 0.02)
        self.position_size = config.get('position_size', 100)
        self.max_total_price = config.get('max_total_price', 0.98)

    async def analyze(self, market: Dict, prices: Dict) -> List[Signal]:
        """
        Look for arbitrage opportunities

        In binary markets:
        - If YES_ask + NO_ask < 1.0 - min_edge, buy both (guaranteed profit)
        - If YES_bid + NO_bid > 1.0 + min_edge, sell both (if we have positions)
        """
        signals = []
        market_id = market.get('id', '')

        outcomes = list(prices.keys())
        if len(outcomes) != 2:
            return signals

        outcome_a = outcomes[0]
        outcome_b = outcomes[1]

        price_a = prices[outcome_a]
        price_b = prices[outcome_b]

        ask_a = price_a.get('ask', 0)
        ask_b = price_b.get('ask', 0)
        bid_a = price_a.get('bid', 0)
        bid_b = price_b.get('bid', 0)

        if ask_a and ask_b:
            total_cost = ask_a + ask_b
            arb_edge = 1.0 - total_cost

            if arb_edge >= self.min_arb_edge and total_cost <= self.max_total_price:
                confidence = min(arb_edge / 0.05, 1.0)

                signals.append(Signal(
                    market_id=market_id,
                    outcome=outcome_a,
                    action='BUY',
                    size=self.position_size,
                    price=ask_a,
                    confidence=confidence,
                    reason=f"Arbitrage: Total cost={total_cost:.3f}, Edge={arb_edge:.3f}"
                ))

                signals.append(Signal(
                    market_id=market_id,
                    outcome=outcome_b,
                    action='BUY',
                    size=self.position_size,
                    price=ask_b,
                    confidence=confidence,
                    reason=f"Arbitrage: Total cost={total_cost:.3f}, Edge={arb_edge:.3f}"
                ))

                logger.info(f"Arbitrage opportunity found: {outcome_a}@{ask_a:.3f} + {outcome_b}@{ask_b:.3f} = {total_cost:.3f}")

        return signals


class SpreadArbitrageStrategy(BaseStrategy):
    """
    Look for opportunities where bid-ask spread is too wide
    """

    def __init__(self, config: Dict = None):
        super().__init__("SpreadArbitrageStrategy", config)

        self.min_spread = config.get('min_spread', 0.05)
        self.position_size = config.get('position_size', 50)

    async def analyze(self, market: Dict, prices: Dict) -> List[Signal]:
        """
        Look for wide spreads that can be exploited
        """
        signals = []
        market_id = market.get('id', '')

        for outcome, price_data in prices.items():
            bid = price_data.get('bid', 0)
            ask = price_data.get('ask', 0)

            if not bid or not ask:
                continue

            spread = ask - bid
            mid = (bid + ask) / 2

            if spread >= self.min_spread and mid > 0.2 and mid < 0.8:
                confidence = min(spread / 0.1, 1.0)

                signal = Signal(
                    market_id=market_id,
                    outcome=outcome,
                    action='BUY',
                    size=self.position_size,
                    price=bid + (spread * 0.3),
                    confidence=confidence,
                    reason=f"Wide spread: {spread:.3f}, targeting {bid + (spread * 0.3):.3f}"
                )
                signals.append(signal)

        return signals
