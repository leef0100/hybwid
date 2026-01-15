"""Volume Monitor for detecting volume spikes and unusual activity"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from .coinglass_client import CoinglassClient

logger = logging.getLogger(__name__)


class VolumeMonitor:
    """Monitors trading volume changes and detects significant spikes"""

    def __init__(self, client: CoinglassClient, spike_threshold: float = 20.0):
        """
        Args:
            client: CoinglassClient instance
            spike_threshold: Percentage change to consider as a spike (default 20%)
        """
        self.client = client
        self.spike_threshold = spike_threshold
        self.baseline_volumes: Dict[str, float] = {}

    async def get_volume_data(self, symbol: str, interval: str = "h1") -> Optional[Dict]:
        """Get volume OHLC data for a symbol"""
        try:
            data = await self.client.get_volume_ohlc(symbol, exchange="all", interval=interval)
            if data:
                logger.info(f"Retrieved volume data for {symbol}")
                return data
            else:
                logger.warning(f"No volume data for {symbol}")
                return None
        except Exception as e:
            logger.error(f"Error fetching volume for {symbol}: {e}")
            return None

    def calculate_volume_change(self, current_volume: float, baseline_volume: float) -> Dict:
        """Calculate volume change statistics"""
        if baseline_volume == 0:
            return {
                'change_absolute': 0,
                'change_percent': 0,
                'is_spike': False
            }

        change_abs = current_volume - baseline_volume
        change_pct = (change_abs / baseline_volume) * 100

        return {
            'change_absolute': change_abs,
            'change_percent': change_pct,
            'is_spike': change_pct >= self.spike_threshold
        }

    def _calculate_baseline(self, historical_data: List) -> float:
        """Calculate baseline volume from historical data (average of recent periods)"""
        if not historical_data or len(historical_data) < 2:
            return 0

        # Use last 24 data points (excluding the most recent) for baseline
        baseline_points = historical_data[-25:-1] if len(historical_data) >= 25 else historical_data[:-1]

        volumes = []
        for point in baseline_points:
            # Get volume from 'v' field
            vol = point.get('v', 0)
            if vol > 0:
                volumes.append(vol)

        return sum(volumes) / len(volumes) if volumes else 0

    def _get_current_volume(self, data: Dict) -> float:
        """Extract current volume from API response"""
        if not data or 'data' not in data:
            return 0

        data_points = data['data']
        if not data_points:
            return 0

        # Get most recent volume
        latest = data_points[-1]
        return latest.get('v', 0)

    async def analyze_volume_spike(self, symbol: str) -> Dict:
        """
        Analyze volume for spikes and unusual activity

        Returns:
            Dict with volume analysis including current volume, changes, and alerts
        """
        volume_data = await self.get_volume_data(symbol, interval="h1")
        if not volume_data or 'data' not in volume_data:
            return {
                'symbol': symbol,
                'status': 'error',
                'message': 'Unable to fetch volume data'
            }

        historical_data = volume_data['data']
        current_volume = self._get_current_volume(volume_data)

        # Calculate baseline from historical data
        baseline_volume = self._calculate_baseline(historical_data)

        # Use stored baseline if available, otherwise use calculated baseline
        if symbol in self.baseline_volumes:
            baseline = self.baseline_volumes[symbol]
        else:
            baseline = baseline_volume
            self.baseline_volumes[symbol] = baseline

        # Calculate change
        change_stats = self.calculate_volume_change(current_volume, baseline)

        # Analyze volume trend
        trend = self._analyze_volume_trend(historical_data)

        # Calculate 24h volume
        volume_24h = self._calculate_24h_volume(historical_data)

        result = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'current_volume': current_volume,
            'baseline_volume': baseline,
            'volume_24h': volume_24h,
            'change_absolute': change_stats['change_absolute'],
            'change_percent': change_stats['change_percent'],
            'is_spike': change_stats['is_spike'],
            'trend': trend,
            'alert_level': self._determine_alert_level(change_stats['change_percent']),
            'volume_score': self._calculate_volume_score(current_volume, baseline, trend)
        }

        if change_stats['is_spike']:
            logger.info(f"🚨 VOLUME SPIKE for {symbol}: increased by {change_stats['change_percent']:.2f}%")

        return result

    def _calculate_24h_volume(self, historical_data: List) -> float:
        """Calculate 24 hour total volume"""
        if not historical_data:
            return 0

        # Get last 24 data points (assuming h1 interval)
        recent_24h = historical_data[-24:] if len(historical_data) >= 24 else historical_data

        total_volume = sum(point.get('v', 0) for point in recent_24h)
        return total_volume

    def _analyze_volume_trend(self, historical_data: List) -> str:
        """Analyze volume trend from historical data"""
        if not historical_data or len(historical_data) < 6:
            return 'insufficient_data'

        try:
            # Get last 12 hours of data
            recent_data = historical_data[-12:]
            volumes = [point.get('v', 0) for point in recent_data]

            if len(volumes) < 6:
                return 'insufficient_data'

            # Compare recent volumes to older volumes
            first_half_avg = sum(volumes[:6]) / 6
            second_half_avg = sum(volumes[6:]) / 6

            if first_half_avg == 0:
                return 'unknown'

            change = ((second_half_avg - first_half_avg) / first_half_avg) * 100

            if change > 30:
                return 'surging'
            elif change > 15:
                return 'increasing'
            elif change < -30:
                return 'collapsing'
            elif change < -15:
                return 'decreasing'
            else:
                return 'stable'

        except Exception as e:
            logger.error(f"Error analyzing volume trend: {e}")
            return 'unknown'

    def _determine_alert_level(self, change_percent: float) -> str:
        """Determine alert level based on change percentage"""
        if change_percent >= 50:
            return 'critical'
        elif change_percent >= 35:
            return 'high'
        elif change_percent >= 20:
            return 'medium'
        elif change_percent >= 10:
            return 'low'
        else:
            return 'info'

    def _calculate_volume_score(self, current: float, baseline: float, trend: str) -> float:
        """
        Calculate a volume score (0-100) based on multiple factors

        Higher score indicates more unusual/significant volume activity
        """
        if baseline == 0:
            return 0

        # Base score from volume ratio
        ratio = current / baseline
        base_score = min(ratio * 20, 50)  # Cap at 50 points

        # Trend bonus
        trend_bonus = {
            'surging': 30,
            'increasing': 20,
            'stable': 10,
            'decreasing': 5,
            'collapsing': 0,
            'unknown': 5,
            'insufficient_data': 0
        }.get(trend, 5)

        # Recent activity bonus (if current volume is very high)
        activity_bonus = min((current / baseline - 1) * 10, 20) if ratio > 1 else 0

        total_score = min(base_score + trend_bonus + activity_bonus, 100)
        return round(total_score, 2)

    async def monitor_multiple_assets(self, symbols: List[str]) -> List[Dict]:
        """Monitor volume for multiple assets"""
        results = []
        for symbol in symbols:
            result = await self.analyze_volume_spike(symbol)
            results.append(result)
        return results

    def update_baseline(self, symbol: str, new_baseline: float):
        """Manually update baseline volume for a symbol"""
        self.baseline_volumes[symbol] = new_baseline
        logger.info(f"Updated baseline volume for {symbol}: {new_baseline}")

    def reset_baselines(self):
        """Reset all baseline volumes"""
        self.baseline_volumes = {}
        logger.info("Volume baselines reset")
