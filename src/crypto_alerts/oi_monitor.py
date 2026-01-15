"""Open Interest Monitor for detecting OI surges and changes"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from .coinglass_client import CoinglassClient

logger = logging.getLogger(__name__)


class OpenInterestMonitor:
    """Monitors Open Interest changes and detects significant surges"""

    def __init__(self, client: CoinglassClient, surge_threshold: float = 10.0):
        """
        Args:
            client: CoinglassClient instance
            surge_threshold: Percentage change to consider as a surge (default 10%)
        """
        self.client = client
        self.surge_threshold = surge_threshold
        self.previous_data: Dict[str, float] = {}

    async def get_current_oi(self, symbol: str) -> Optional[Dict]:
        """Get current open interest for a symbol"""
        try:
            data = await self.client.get_open_interest(symbol)
            if data:
                logger.info(f"Retrieved OI for {symbol}")
                return data
            else:
                logger.warning(f"No OI data for {symbol}")
                return None
        except Exception as e:
            logger.error(f"Error fetching OI for {symbol}: {e}")
            return None

    async def get_oi_history(self, symbol: str, interval: str = "h1") -> Optional[Dict]:
        """Get OI history for trend analysis"""
        try:
            data = await self.client.get_oi_history(symbol, exchange="all", time_type=interval)
            return data
        except Exception as e:
            logger.error(f"Error fetching OI history for {symbol}: {e}")
            return None

    def calculate_oi_change(self, current_oi: float, previous_oi: float) -> Dict:
        """Calculate OI change statistics"""
        if previous_oi == 0:
            return {
                'change_absolute': 0,
                'change_percent': 0,
                'is_surge': False
            }

        change_abs = current_oi - previous_oi
        change_pct = (change_abs / previous_oi) * 100

        return {
            'change_absolute': change_abs,
            'change_percent': change_pct,
            'is_surge': abs(change_pct) >= self.surge_threshold
        }

    async def analyze_oi_surge(self, symbol: str) -> Dict:
        """
        Analyze OI for surges and changes

        Returns:
            Dict with surge analysis including current OI, changes, and alerts
        """
        current_data = await self.get_current_oi(symbol)
        if not current_data:
            return {
                'symbol': symbol,
                'status': 'error',
                'message': 'Unable to fetch OI data'
            }

        # Extract total OI
        total_oi = 0
        exchanges_data = []

        if isinstance(current_data, dict):
            # Parse OI data by exchange
            for exchange, oi_value in current_data.items():
                if isinstance(oi_value, (int, float)):
                    total_oi += oi_value
                    exchanges_data.append({
                        'exchange': exchange,
                        'oi': oi_value
                    })

        # Check for surge
        previous_oi = self.previous_data.get(symbol, 0)
        change_stats = self.calculate_oi_change(total_oi, previous_oi)

        # Update previous data
        self.previous_data[symbol] = total_oi

        # Get historical data for trend
        history = await self.get_oi_history(symbol)
        trend = self._analyze_trend(history) if history else 'unknown'

        result = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'current_oi': total_oi,
            'previous_oi': previous_oi,
            'change_absolute': change_stats['change_absolute'],
            'change_percent': change_stats['change_percent'],
            'is_surge': change_stats['is_surge'],
            'trend': trend,
            'exchanges': sorted(exchanges_data, key=lambda x: x['oi'], reverse=True)[:5],
            'alert_level': self._determine_alert_level(change_stats['change_percent'])
        }

        if change_stats['is_surge']:
            direction = 'increased' if change_stats['change_percent'] > 0 else 'decreased'
            logger.info(f"🚨 OI SURGE for {symbol}: {direction} by {abs(change_stats['change_percent']):.2f}%")

        return result

    def _analyze_trend(self, history: Dict) -> str:
        """Analyze OI trend from historical data"""
        if not history or 'data' not in history:
            return 'unknown'

        try:
            data_points = history['data']
            if len(data_points) < 2:
                return 'insufficient_data'

            # Get last 10 data points for trend
            recent_points = data_points[-10:]
            values = [point.get('o', 0) for point in recent_points if 'o' in point]

            if len(values) < 2:
                return 'insufficient_data'

            # Simple trend analysis
            first_half_avg = sum(values[:len(values)//2]) / (len(values)//2)
            second_half_avg = sum(values[len(values)//2:]) / (len(values) - len(values)//2)

            change = ((second_half_avg - first_half_avg) / first_half_avg) * 100 if first_half_avg > 0 else 0

            if change > 5:
                return 'strongly_bullish'
            elif change > 2:
                return 'bullish'
            elif change < -5:
                return 'strongly_bearish'
            elif change < -2:
                return 'bearish'
            else:
                return 'neutral'

        except Exception as e:
            logger.error(f"Error analyzing trend: {e}")
            return 'unknown'

    def _determine_alert_level(self, change_percent: float) -> str:
        """Determine alert level based on change percentage"""
        abs_change = abs(change_percent)

        if abs_change >= 20:
            return 'critical'
        elif abs_change >= 15:
            return 'high'
        elif abs_change >= 10:
            return 'medium'
        elif abs_change >= 5:
            return 'low'
        else:
            return 'info'

    async def monitor_multiple_assets(self, symbols: List[str]) -> List[Dict]:
        """Monitor OI for multiple assets"""
        results = []
        for symbol in symbols:
            result = await self.analyze_oi_surge(symbol)
            results.append(result)
        return results

    def reset_baseline(self):
        """Reset previous data baseline"""
        self.previous_data = {}
        logger.info("OI baseline reset")
