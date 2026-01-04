"""High-frequency strategy for short-term markets (15min-1hr)"""

from typing import Dict, List
from collections import deque
from datetime import datetime
from src.strategies.base_strategy import BaseStrategy, Signal
from src.utils.time_filter import TimeBasedFilter
from src.analytics.sports_analytics import SportsAnalytics
import logging

logger = logging.getLogger(__name__)


class HighFrequencyStrategy(BaseStrategy):
    """
    Ultra-short-term trading strategy for markets resolving in <1 hour

    Focus areas:
    1. Live sports events (quarters, halftimes, etc.)
    2. Breaking news events
    3. Time-sensitive crypto price movements
    4. Entertainment/awards shows

    Key advantages of short-term markets:
    - Less time for prices to correct inefficiencies
    - Public reaction often overshoots
    - Quick profit realization
    - Lower event risk
    """

    def __init__(self, config: Dict = None):
        default_config = {
            'max_minutes': 60,            # Only trade markets <60 min
            'min_minutes': 5,             # Minimum 5 minutes to avoid last-second issues
            'urgency_boost': 0.2,         # Confidence boost for urgent markets
            'position_size': 75,          # Moderate size for quick trades
            'min_edge': 0.03,             # 3% minimum edge
            'max_spread': 0.04,           # 4% max spread (need liquidity)
            'use_sports_analysis': True,  # Use win streak analysis
        }

        if config:
            default_config.update(config)

        super().__init__("HighFrequency", default_config)

        self.time_filter = TimeBasedFilter({
            'max_minutes': self.config['max_minutes'],
            'min_minutes': self.config['min_minutes']
        })

        self.sports_analytics = SportsAnalytics() if self.config['use_sports_analysis'] else None

        # Track markets we've already analyzed (to avoid duplicates)
        self.analyzed_markets = set()

    async def analyze(self, market: Dict, prices: Dict) -> List[Signal]:
        """
        Analyze short-term market for opportunities

        Priority signals:
        1. Sports win streak inefficiencies
        2. Extreme time urgency with mispricing
        3. Sharp price movements near resolution
        """
        signals = []

        # Only trade short-term markets
        if not self.time_filter.is_short_term(market):
            return []

        market_id = market.get('id')

        # Avoid re-analyzing same market too frequently
        if market_id in self.analyzed_markets:
            return []

        self.analyzed_markets.add(market_id)

        # Get time to resolution
        minutes = self.time_filter.extract_time_to_resolution(market)
        urgency = self.time_filter.get_urgency_score(market)

        # 1. Sports win streak analysis
        if self.sports_analytics and self.sports_analytics.is_sports_market(market):
            sports_signals = self._analyze_sports_inefficiency(market, prices, minutes, urgency)
            signals.extend(sports_signals)

        # 2. Time urgency mispricing
        urgency_signals = self._analyze_time_urgency(market, prices, minutes, urgency)
        signals.extend(urgency_signals)

        # 3. Liquidity-based scalping
        liquidity_signals = self._analyze_liquidity(market, prices, minutes)
        signals.extend(liquidity_signals)

        return signals

    def _analyze_sports_inefficiency(self, market: Dict, prices: Dict,
                                    minutes: int, urgency: float) -> List[Signal]:
        """Detect sports win streak inefficiencies"""
        signals = []

        # NOTE: In production, you would fetch real team data from an API
        # For now, we'll use heuristics from the market question

        inefficiency = self.sports_analytics.detect_win_streak_inefficiency(
            market, prices, team_data=None
        )

        if not inefficiency:
            return []

        # Generate signal based on inefficiency type
        market_id = market.get('id')
        ineff_type = inefficiency.get('type')

        if 'overvalue' in ineff_type:
            # Hot streak overvalued - FADE (bet against)
            if 'No' in prices:
                signal = Signal(
                    market_id=market_id,
                    outcome='No',
                    action='BUY',
                    size=self.config['position_size'],
                    price=prices['No'].get('ask', 0),
                    confidence=min(0.85, 0.6 + urgency * self.config['urgency_boost']),
                    reason=f"Sports: {inefficiency.get('recommendation')} | {minutes}min to resolution"
                )
                signals.append(signal)

        elif 'undervalue' in ineff_type:
            # Cold streak undervalued - BUY
            if 'Yes' in prices:
                signal = Signal(
                    market_id=market_id,
                    outcome='Yes',
                    action='BUY',
                    size=self.config['position_size'],
                    price=prices['Yes'].get('ask', 0),
                    confidence=min(0.85, 0.6 + urgency * self.config['urgency_boost']),
                    reason=f"Sports: {inefficiency.get('recommendation')} | {minutes}min to resolution"
                )
                signals.append(signal)

        return signals

    def _analyze_time_urgency(self, market: Dict, prices: Dict,
                             minutes: int, urgency: float) -> List[Signal]:
        """
        Analyze time-sensitive mispricings

        Theory: As resolution approaches, inefficiencies compress.
        Markets with <15 min to resolution often have stale prices.
        """
        signals = []

        # Very urgent markets (< 15 min)
        if minutes <= 15:
            for outcome, price_data in prices.items():
                bid = price_data.get('bid', 0)
                ask = price_data.get('ask', 0)
                mid = price_data.get('mid', 0)

                if not all([bid, ask, mid]):
                    continue

                spread = ask - bid

                # Check for reasonable prices
                if 0.1 <= mid <= 0.9:
                    # Stale price detection: wide spread despite urgency
                    if spread > 0.05 and urgency > 0.8:
                        # Potential stale pricing - bet towards 0.5 (uncertainty)
                        if mid < 0.45:
                            signal = Signal(
                                market_id=market.get('id'),
                                outcome=outcome,
                                action='BUY',
                                size=self.config['position_size'] * 0.5,  # Smaller size
                                price=ask,
                                confidence=0.55,
                                reason=f"Urgent market ({minutes}min) - stale pricing detected"
                            )
                            signals.append(signal)

        return signals

    def _analyze_liquidity(self, market: Dict, prices: Dict, minutes: int) -> List[Signal]:
        """
        Liquidity-based scalping for short-term markets

        Look for tight spreads with good liquidity - can scalp the spread
        """
        signals = []

        for outcome, price_data in prices.items():
            bid = price_data.get('bid', 0)
            ask = price_data.get('ask', 0)

            if not all([bid, ask]):
                continue

            spread = ask - bid

            # Very tight spread + short time = scalping opportunity
            if spread <= 0.02 and minutes <= 30:  # 2% spread, <30 min
                # Buy at mid, sell at bid/ask
                mid = (bid + ask) / 2

                # Only if mid price is reasonable (not extreme)
                if 0.2 <= mid <= 0.8:
                    signal = Signal(
                        market_id=market.get('id'),
                        outcome=outcome,
                        action='BUY',
                        size=self.config['position_size'] * 0.75,
                        price=mid,  # Target mid-spread execution
                        confidence=0.5 + (0.02 - spread) * 10,  # Tighter spread = higher confidence
                        reason=f"Liquidity scalp: {spread:.1%} spread, {minutes}min resolution"
                    )
                    signals.append(signal)

        return signals

    def clear_cache(self):
        """Clear analyzed markets cache"""
        self.analyzed_markets.clear()
        logger.info("High-frequency strategy cache cleared")
