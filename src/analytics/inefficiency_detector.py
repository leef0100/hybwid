"""Statistical inefficiency detection for market pricing anomalies"""

from typing import Dict, List, Tuple, Optional
from collections import defaultdict, deque
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class InefficiencyType:
    """Types of market inefficiencies"""
    PROBABILITY_SUM = "probability_sum"      # YES + NO != 1.0
    WIDE_SPREAD = "wide_spread"              # Excessive bid-ask spread
    STALE_PRICE = "stale_price"              # Price hasn't moved with news
    VOLUME_IMBALANCE = "volume_imbalance"    # One-sided order flow
    STATISTICAL_ARB = "statistical_arb"      # Mean reversion opportunity
    CORRELATION = "correlation"               # Related markets diverge


class Inefficiency:
    """Represents a detected market inefficiency"""

    def __init__(self, market_id: str, inefficiency_type: str,
                 severity: float, description: str, data: Dict = None):
        self.market_id = market_id
        self.type = inefficiency_type
        self.severity = severity  # 0 to 1
        self.description = description
        self.data = data or {}
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict:
        return {
            'market_id': self.market_id,
            'type': self.type,
            'severity': self.severity,
            'description': self.description,
            'data': self.data,
            'timestamp': self.timestamp.isoformat()
        }

    def __repr__(self):
        return f"Inefficiency({self.type}, severity={self.severity:.2f}, {self.description})"


class InefficiencyDetector:
    """
    Detects various types of market inefficiencies using statistical analysis
    """

    def __init__(self, config: Dict = None):
        self.config = config or {}

        # Thresholds
        self.prob_sum_threshold = self.config.get('prob_sum_threshold', 0.02)  # 2%
        self.wide_spread_threshold = self.config.get('wide_spread_threshold', 0.05)  # 5%
        self.stale_threshold_mins = self.config.get('stale_threshold_mins', 30)  # 30 min

        # History tracking
        self.price_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.inefficiency_history: Dict[str, List[Inefficiency]] = defaultdict(list)

    def detect_all(self, market: Dict, prices: Dict) -> List[Inefficiency]:
        """
        Run all inefficiency detection checks

        Args:
            market: Market data
            prices: Current prices

        Returns:
            List of detected inefficiencies
        """
        inefficiencies = []

        # 1. Probability sum check (YES + NO should = 1.0)
        prob_sum_ineff = self._check_probability_sum(market, prices)
        if prob_sum_ineff:
            inefficiencies.append(prob_sum_ineff)

        # 2. Wide spread check
        spread_ineff = self._check_wide_spreads(market, prices)
        inefficiencies.extend(spread_ineff)

        # 3. Statistical arbitrage (mean reversion)
        stat_arb_ineff = self._check_statistical_arb(market, prices)
        inefficiencies.extend(stat_arb_ineff)

        # 4. Volume imbalance
        volume_ineff = self._check_volume_imbalance(market, prices)
        if volume_ineff:
            inefficiencies.append(volume_ineff)

        # Store in history
        if inefficiencies:
            market_id = market.get('id')
            self.inefficiency_history[market_id].extend(inefficiencies)

            # Log significant inefficiencies
            for ineff in inefficiencies:
                if ineff.severity >= 0.5:
                    logger.info(f"Significant inefficiency detected: {ineff}")

        return inefficiencies

    def _check_probability_sum(self, market: Dict, prices: Dict) -> Optional[Inefficiency]:
        """
        Check if YES + NO probabilities sum to ~1.0

        In efficient markets, buying YES at ask + buying NO at ask should cost ~1.0
        If sum < 1.0: arbitrage opportunity (buy both)
        If sum > 1.0: market maker spread (normal)
        """
        if 'Yes' not in prices or 'No' not in prices:
            return None

        yes_ask = prices['Yes'].get('ask', 0)
        no_ask = prices['No'].get('ask', 0)

        if not yes_ask or not no_ask:
            return None

        total = yes_ask + no_ask
        deviation = abs(total - 1.0)

        if deviation > self.prob_sum_threshold:
            market_id = market.get('id')

            # Less than 1.0 = arbitrage
            if total < 1.0:
                severity = min(1.0, deviation / 0.05)  # Max at 5% deviation
                description = f"Probability sum = {total:.4f} (< 1.0) - Arbitrage opportunity!"
            else:
                severity = min(0.7, deviation / 0.10)
                description = f"Probability sum = {total:.4f} (> 1.0) - Wide maker spread"

            return Inefficiency(
                market_id=market_id,
                inefficiency_type=InefficiencyType.PROBABILITY_SUM,
                severity=severity,
                description=description,
                data={'yes_ask': yes_ask, 'no_ask': no_ask, 'sum': total}
            )

        return None

    def _check_wide_spreads(self, market: Dict, prices: Dict) -> List[Inefficiency]:
        """Check for unusually wide bid-ask spreads"""
        inefficiencies = []
        market_id = market.get('id')

        for outcome, price_data in prices.items():
            bid = price_data.get('bid', 0)
            ask = price_data.get('ask', 0)

            if not bid or not ask:
                continue

            spread = ask - bid
            mid = (bid + ask) / 2

            # Spread as percentage of mid price
            if mid > 0:
                spread_pct = spread / mid

                if spread_pct > self.wide_spread_threshold:
                    severity = min(1.0, spread_pct / 0.20)  # Max at 20% spread

                    ineff = Inefficiency(
                        market_id=market_id,
                        inefficiency_type=InefficiencyType.WIDE_SPREAD,
                        severity=severity,
                        description=f"{outcome}: Wide spread of {spread_pct:.1%} (bid={bid:.3f}, ask={ask:.3f})",
                        data={'outcome': outcome, 'spread_pct': spread_pct, 'bid': bid, 'ask': ask}
                    )
                    inefficiencies.append(ineff)

        return inefficiencies

    def _check_statistical_arb(self, market: Dict, prices: Dict) -> List[Inefficiency]:
        """
        Check for statistical arbitrage opportunities (mean reversion)

        Logic:
        - Track price history
        - Calculate mean and standard deviation
        - Flag when price is > 2 std dev from mean
        """
        inefficiencies = []
        market_id = market.get('id')

        # Store current prices in history
        for outcome, price_data in prices.items():
            mid = price_data.get('mid', 0)
            if mid:
                self.price_history[f"{market_id}:{outcome}"].append({
                    'mid': mid,
                    'timestamp': datetime.now()
                })

        # Need enough history
        for outcome, price_data in prices.items():
            history_key = f"{market_id}:{outcome}"
            history = self.price_history[history_key]

            if len(history) < 10:  # Need at least 10 data points
                continue

            # Calculate statistics
            prices_list = [p['mid'] for p in history]
            mean = sum(prices_list) / len(prices_list)
            variance = sum((p - mean) ** 2 for p in prices_list) / len(prices_list)
            std_dev = variance ** 0.5

            if std_dev == 0:
                continue

            # Check current price deviation
            current_mid = price_data.get('mid', 0)
            z_score = (current_mid - mean) / std_dev

            # Flag if > 2 standard deviations
            if abs(z_score) > 2.0:
                severity = min(1.0, abs(z_score) / 4.0)  # Max at 4 std dev

                direction = "overbought" if z_score > 0 else "oversold"
                description = f"{outcome}: Statistical arbitrage - {direction} at {z_score:.1f} std dev from mean"

                ineff = Inefficiency(
                    market_id=market_id,
                    inefficiency_type=InefficiencyType.STATISTICAL_ARB,
                    severity=severity,
                    description=description,
                    data={
                        'outcome': outcome,
                        'z_score': z_score,
                        'current': current_mid,
                        'mean': mean,
                        'std_dev': std_dev
                    }
                )
                inefficiencies.append(ineff)

        return inefficiencies

    def _check_volume_imbalance(self, market: Dict, prices: Dict) -> Optional[Inefficiency]:
        """
        Check for significant volume imbalances (one-sided order flow)

        Note: This requires order book depth data, which may not always be available
        """
        # TODO: Implement when order book depth is available
        return None

    def get_inefficiency_stats(self, market_id: str = None) -> Dict:
        """Get statistics about detected inefficiencies"""
        if market_id:
            ineffs = self.inefficiency_history.get(market_id, [])
        else:
            ineffs = []
            for market_ineffs in self.inefficiency_history.values():
                ineffs.extend(market_ineffs)

        if not ineffs:
            return {'total': 0}

        # Count by type
        by_type = defaultdict(int)
        for ineff in ineffs:
            by_type[ineff.type] += 1

        # Calculate average severity
        avg_severity = sum(ineff.severity for ineff in ineffs) / len(ineffs)

        return {
            'total': len(ineffs),
            'by_type': dict(by_type),
            'avg_severity': avg_severity,
            'max_severity': max(ineff.severity for ineff in ineffs)
        }

    def get_recent_inefficiencies(self, minutes: int = 60, min_severity: float = 0.5) -> List[Inefficiency]:
        """Get recent significant inefficiencies"""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        recent = []

        for market_ineffs in self.inefficiency_history.values():
            for ineff in market_ineffs:
                if ineff.timestamp >= cutoff and ineff.severity >= min_severity:
                    recent.append(ineff)

        # Sort by severity (highest first)
        recent.sort(key=lambda x: x.severity, reverse=True)

        return recent
