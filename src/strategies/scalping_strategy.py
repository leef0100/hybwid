"""Scalping strategy for short-term momentum and spread exploitation"""

from typing import Dict, List
from collections import deque
from datetime import datetime, timedelta
from src.strategies.base_strategy import BaseStrategy, Signal
import logging

logger = logging.getLogger(__name__)


class ScalpingStrategy(BaseStrategy):
    """
    High-frequency scalping strategy that exploits:
    1. Momentum: Rapid price movements in one direction
    2. Volume spikes: Unusual trading activity
    3. Spread compression: Tight bid-ask spreads
    4. Mean reversion: Quick reversals after sharp moves
    """

    def __init__(self, config: Dict = None):
        default_config = {
            'momentum_threshold': 0.03,     # 3% price movement triggers signal
            'volume_spike_multiple': 2.0,   # 2x average volume = spike
            'max_spread': 0.03,             # Only trade if spread < 3%
            'lookback_periods': 5,          # Compare to last 5 price updates
            'position_size': 50,            # Smaller size for quick scalps
            'min_edge': 0.02,               # Minimum 2% edge to enter
            'exit_target': 0.01,            # Take profit at 1%
            'stop_loss': 0.02,              # Stop loss at 2%
        }

        if config:
            default_config.update(config)

        super().__init__("ScalpingStrategy", default_config)

        # Track price history for each market
        self.price_history: Dict[str, deque] = {}
        self.volume_history: Dict[str, deque] = {}

    async def analyze(self, market: Dict, prices: Dict) -> List[Signal]:
        """
        Analyze market for scalping opportunities

        Looks for:
        - Momentum breakouts
        - Volume spikes
        - Tight spreads for quick execution
        """
        signals = []
        market_id = market.get('id')

        # Initialize history tracking
        if market_id not in self.price_history:
            self.price_history[market_id] = deque(maxlen=self.config['lookback_periods'])
            self.volume_history[market_id] = deque(maxlen=self.config['lookback_periods'])

        # Analyze each outcome
        for outcome, price_data in prices.items():
            bid = price_data.get('bid', 0)
            ask = price_data.get('ask', 0)
            mid = price_data.get('mid', 0)

            if not all([bid, ask, mid]):
                continue

            # Check spread - only scalp tight spreads
            spread = ask - bid
            if spread > self.config['max_spread']:
                continue

            # Track price
            self.price_history[market_id].append({
                'outcome': outcome,
                'mid': mid,
                'bid': bid,
                'ask': ask,
                'timestamp': datetime.now()
            })

            # Need history to detect momentum
            if len(self.price_history[market_id]) < 2:
                continue

            # Detect momentum
            momentum_signals = self._detect_momentum(market_id, outcome, price_data)
            signals.extend(momentum_signals)

            # Detect mean reversion opportunities
            reversion_signals = self._detect_mean_reversion(market_id, outcome, price_data)
            signals.extend(reversion_signals)

        return signals

    def _detect_momentum(self, market_id: str, outcome: str, current_price: Dict) -> List[Signal]:
        """
        Detect momentum breakouts

        Logic:
        - Calculate price change over lookback period
        - If momentum > threshold, ride the trend
        - Enter in direction of momentum
        """
        signals = []

        history = self.price_history[market_id]
        if len(history) < 2:
            return signals

        # Get prices for this specific outcome
        outcome_prices = [h for h in history if h['outcome'] == outcome]
        if len(outcome_prices) < 2:
            return signals

        # Calculate momentum
        first_price = outcome_prices[0]['mid']
        current_mid = current_price['mid']

        if first_price == 0:
            return signals

        momentum = (current_mid - first_price) / first_price

        # Check for strong momentum
        if abs(momentum) >= self.config['momentum_threshold']:
            # Positive momentum - buy
            if momentum > 0:
                action = 'BUY'
                entry_price = current_price['ask']
                confidence = min(0.8, abs(momentum) / self.config['momentum_threshold'] * 0.6)
                reason = f"Momentum breakout: +{momentum:.1%} over last {len(outcome_prices)} updates"

            # Negative momentum - sell (if we had it)
            else:
                action = 'SELL'
                entry_price = current_price['bid']
                confidence = min(0.8, abs(momentum) / self.config['momentum_threshold'] * 0.6)
                reason = f"Momentum breakdown: {momentum:.1%} over last {len(outcome_prices)} updates"

            signal = Signal(
                market_id=market_id,
                outcome=outcome,
                action=action,
                size=self.config['position_size'],
                price=entry_price,
                confidence=confidence,
                reason=reason
            )

            signals.append(signal)
            logger.info(f"Momentum signal: {reason}")

        return signals

    def _detect_mean_reversion(self, market_id: str, outcome: str, current_price: Dict) -> List[Signal]:
        """
        Detect mean reversion opportunities after sharp moves

        Logic:
        - If price moved sharply away from average, expect reversion
        - Buy if oversold, sell if overbought
        """
        signals = []

        history = self.price_history[market_id]
        if len(history) < self.config['lookback_periods']:
            return signals

        # Get prices for this specific outcome
        outcome_prices = [h for h in history if h['outcome'] == outcome]
        if len(outcome_prices) < 3:
            return signals

        # Calculate average price
        avg_price = sum(p['mid'] for p in outcome_prices) / len(outcome_prices)
        current_mid = current_price['mid']

        if avg_price == 0:
            return signals

        # Calculate deviation from average
        deviation = (current_mid - avg_price) / avg_price

        # Look for significant deviations (oversold/overbought)
        if abs(deviation) >= self.config['min_edge']:
            # Oversold - expect bounce back up
            if deviation < -self.config['min_edge']:
                action = 'BUY'
                entry_price = current_price['ask']
                confidence = min(0.75, abs(deviation) / 0.05 * 0.5)
                reason = f"Mean reversion: oversold {deviation:.1%} vs {len(outcome_prices)}-period avg"

            # Overbought - expect pullback
            elif deviation > self.config['min_edge']:
                action = 'SELL'
                entry_price = current_price['bid']
                confidence = min(0.75, abs(deviation) / 0.05 * 0.5)
                reason = f"Mean reversion: overbought +{deviation:.1%} vs {len(outcome_prices)}-period avg"
            else:
                return signals

            signal = Signal(
                market_id=market_id,
                outcome=outcome,
                action=action,
                size=self.config['position_size'],
                price=entry_price,
                confidence=confidence,
                reason=reason
            )

            signals.append(signal)
            logger.info(f"Mean reversion signal: {reason}")

        return signals

    def clear_history(self, market_id: str = None):
        """Clear price history for a market or all markets"""
        if market_id:
            if market_id in self.price_history:
                del self.price_history[market_id]
            if market_id in self.volume_history:
                del self.volume_history[market_id]
        else:
            self.price_history.clear()
            self.volume_history.clear()

        logger.info(f"Cleared scalping history for {market_id or 'all markets'}")
