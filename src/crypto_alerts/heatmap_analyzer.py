"""Heatmap Analyzer for liquidation data and key price levels"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from .coinglass_client import CoinglassClient

logger = logging.getLogger(__name__)


class HeatmapAnalyzer:
    """Analyzes liquidation heatmap data to identify key price levels and risks"""

    def __init__(self, client: CoinglassClient, liquidation_threshold: float = 50000000):
        """
        Args:
            client: CoinglassClient instance
            liquidation_threshold: Dollar threshold for significant liquidation levels (default $50M)
        """
        self.client = client
        self.liquidation_threshold = liquidation_threshold

    async def get_liquidation_heatmap(self, symbol: str, exchange: str = "Binance") -> Optional[Dict]:
        """Get liquidation heatmap data"""
        try:
            # Convert symbol format (BTC -> BTCUSDT)
            if not symbol.endswith('USDT'):
                symbol = f"{symbol}USDT"

            data = await self.client.get_liquidation_heatmap(symbol, exchange)
            if data:
                logger.info(f"Retrieved heatmap data for {symbol}")
                return data
            else:
                logger.warning(f"No heatmap data for {symbol}")
                return None
        except Exception as e:
            logger.error(f"Error fetching heatmap for {symbol}: {e}")
            return None

    async def get_liquidation_history(self, symbol: str, interval: str = "h1") -> Optional[Dict]:
        """Get liquidation history data"""
        try:
            data = await self.client.get_liquidation_history(symbol, time_type=interval)
            if data:
                logger.info(f"Retrieved liquidation history for {symbol}")
                return data
            return None
        except Exception as e:
            logger.error(f"Error fetching liquidation history for {symbol}: {e}")
            return None

    def _parse_liquidation_levels(self, heatmap_data: Dict) -> List[Dict]:
        """Parse heatmap data to extract key liquidation levels"""
        levels = []

        if not heatmap_data or 'data' not in heatmap_data:
            return levels

        try:
            data = heatmap_data['data']

            # Extract price levels and their liquidation amounts
            if isinstance(data, list):
                for level in data:
                    price = level.get('price', 0)
                    amount = level.get('amount', 0)
                    side = level.get('side', 'unknown')  # long or short liquidations

                    if price > 0 and amount > 0:
                        levels.append({
                            'price': price,
                            'amount': amount,
                            'side': side
                        })

            # Sort by liquidation amount (descending)
            levels.sort(key=lambda x: x['amount'], reverse=True)

        except Exception as e:
            logger.error(f"Error parsing liquidation levels: {e}")

        return levels

    def _identify_key_levels(self, levels: List[Dict], current_price: float) -> Dict:
        """Identify key support and resistance levels from liquidation data"""
        if not levels:
            return {
                'support_levels': [],
                'resistance_levels': []
            }

        support_levels = []
        resistance_levels = []

        for level in levels:
            price = level['price']
            amount = level['amount']

            # Only include significant levels
            if amount < self.liquidation_threshold:
                continue

            if price < current_price:
                # Below current price - support level
                support_levels.append({
                    'price': price,
                    'amount': amount,
                    'distance_pct': ((current_price - price) / current_price) * 100,
                    'side': level.get('side', 'unknown')
                })
            else:
                # Above current price - resistance level
                resistance_levels.append({
                    'price': price,
                    'amount': amount,
                    'distance_pct': ((price - current_price) / current_price) * 100,
                    'side': level.get('side', 'unknown')
                })

        # Sort support levels by price (descending - closest first)
        support_levels.sort(key=lambda x: x['price'], reverse=True)

        # Sort resistance levels by price (ascending - closest first)
        resistance_levels.sort(key=lambda x: x['price'])

        return {
            'support_levels': support_levels[:5],  # Top 5 support levels
            'resistance_levels': resistance_levels[:5]  # Top 5 resistance levels
        }

    def _analyze_liquidation_clusters(self, levels: List[Dict]) -> Dict:
        """Analyze clusters of liquidations to identify risk zones"""
        if not levels:
            return {
                'total_liquidation_risk': 0,
                'high_risk_zones': []
            }

        # Group levels by price proximity (within 5%)
        clusters = []
        used_indices = set()

        for i, level1 in enumerate(levels):
            if i in used_indices:
                continue

            cluster = {
                'center_price': level1['price'],
                'total_amount': level1['amount'],
                'levels': [level1]
            }

            for j, level2 in enumerate(levels[i+1:], start=i+1):
                if j in used_indices:
                    continue

                # Check if within 5% price range
                price_diff_pct = abs(level2['price'] - level1['price']) / level1['price'] * 100
                if price_diff_pct <= 5:
                    cluster['total_amount'] += level2['amount']
                    cluster['levels'].append(level2)
                    used_indices.add(j)

            clusters.append(cluster)
            used_indices.add(i)

        # Sort clusters by total amount
        clusters.sort(key=lambda x: x['total_amount'], reverse=True)

        # Identify high-risk zones
        high_risk_zones = []
        for cluster in clusters[:3]:  # Top 3 clusters
            if cluster['total_amount'] >= self.liquidation_threshold:
                high_risk_zones.append({
                    'price': cluster['center_price'],
                    'total_risk': cluster['total_risk'],
                    'num_levels': len(cluster['levels'])
                })

        total_risk = sum(level['amount'] for level in levels)

        return {
            'total_liquidation_risk': total_risk,
            'high_risk_zones': high_risk_zones,
            'num_clusters': len(clusters)
        }

    async def _get_current_price(self, symbol: str) -> float:
        """Estimate current price from recent OI or liquidation data"""
        try:
            # Try to get from liquidation history
            liq_data = await self.get_liquidation_history(symbol)
            if liq_data and 'data' in liq_data and liq_data['data']:
                # Use most recent liquidation price as proxy
                recent = liq_data['data'][-1]
                return recent.get('price', 0)

            return 0
        except Exception as e:
            logger.error(f"Error getting current price for {symbol}: {e}")
            return 0

    async def analyze_heatmap(self, symbol: str, current_price: Optional[float] = None) -> Dict:
        """
        Comprehensive heatmap analysis

        Returns:
            Dict with heatmap analysis including key levels, risks, and recommendations
        """
        # Get heatmap data
        heatmap_data = await self.get_liquidation_heatmap(symbol)
        if not heatmap_data:
            return {
                'symbol': symbol,
                'status': 'error',
                'message': 'Unable to fetch heatmap data'
            }

        # Get liquidation history
        liq_history = await self.get_liquidation_history(symbol)

        # If no current price provided, try to estimate
        if current_price is None:
            current_price = await self._get_current_price(symbol)

        if current_price == 0:
            logger.warning(f"Could not determine current price for {symbol}")

        # Parse liquidation levels
        levels = self._parse_liquidation_levels(heatmap_data)

        # Identify key support/resistance
        key_levels = self._identify_key_levels(levels, current_price) if current_price > 0 else {
            'support_levels': [],
            'resistance_levels': []
        }

        # Analyze clusters
        cluster_analysis = self._analyze_liquidation_clusters(levels)

        # Calculate 24h liquidations
        liquidations_24h = self._calculate_24h_liquidations(liq_history) if liq_history else {}

        # Generate insights
        insights = self._generate_insights(
            key_levels,
            cluster_analysis,
            liquidations_24h,
            current_price
        )

        result = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'current_price': current_price,
            'key_levels': key_levels,
            'cluster_analysis': cluster_analysis,
            'liquidations_24h': liquidations_24h,
            'insights': insights,
            'alert_level': self._determine_alert_level(cluster_analysis, liquidations_24h)
        }

        return result

    def _calculate_24h_liquidations(self, liq_history: Dict) -> Dict:
        """Calculate 24 hour liquidation statistics"""
        if not liq_history or 'data' not in liq_history:
            return {
                'total_long': 0,
                'total_short': 0,
                'total_amount': 0
            }

        try:
            data = liq_history['data']
            # Get last 24 hours
            recent_24h = data[-24:] if len(data) >= 24 else data

            total_long = sum(point.get('longLiquidation', 0) for point in recent_24h)
            total_short = sum(point.get('shortLiquidation', 0) for point in recent_24h)

            return {
                'total_long': total_long,
                'total_short': total_short,
                'total_amount': total_long + total_short,
                'long_short_ratio': total_long / total_short if total_short > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error calculating 24h liquidations: {e}")
            return {
                'total_long': 0,
                'total_short': 0,
                'total_amount': 0
            }

    def _generate_insights(self, key_levels: Dict, cluster_analysis: Dict,
                          liquidations_24h: Dict, current_price: float) -> List[str]:
        """Generate human-readable insights from analysis"""
        insights = []

        # Support/Resistance insights
        if key_levels.get('support_levels'):
            nearest_support = key_levels['support_levels'][0]
            insights.append(
                f"Nearest support at ${nearest_support['price']:.2f} "
                f"({nearest_support['distance_pct']:.2f}% below) with "
                f"${nearest_support['amount']/1e6:.1f}M in liquidations"
            )

        if key_levels.get('resistance_levels'):
            nearest_resistance = key_levels['resistance_levels'][0]
            insights.append(
                f"Nearest resistance at ${nearest_resistance['price']:.2f} "
                f"({nearest_resistance['distance_pct']:.2f}% above) with "
                f"${nearest_resistance['amount']/1e6:.1f}M in liquidations"
            )

        # Liquidation risk insights
        total_risk = cluster_analysis.get('total_liquidation_risk', 0)
        if total_risk > self.liquidation_threshold * 10:
            insights.append(
                f"High liquidation risk: ${total_risk/1e6:.1f}M in total liquidation levels"
            )

        # 24h liquidation insights
        if liquidations_24h.get('total_amount', 0) > self.liquidation_threshold:
            total_24h = liquidations_24h['total_amount']
            insights.append(
                f"Heavy liquidations in 24h: ${total_24h/1e6:.1f}M "
                f"(${liquidations_24h.get('total_long', 0)/1e6:.1f}M longs, "
                f"${liquidations_24h.get('total_short', 0)/1e6:.1f}M shorts)"
            )

        # Risk zone insights
        high_risk_zones = cluster_analysis.get('high_risk_zones', [])
        if high_risk_zones:
            insights.append(
                f"Identified {len(high_risk_zones)} high-risk liquidation zones"
            )

        return insights

    def _determine_alert_level(self, cluster_analysis: Dict, liquidations_24h: Dict) -> str:
        """Determine alert level based on liquidation data"""
        total_risk = cluster_analysis.get('total_liquidation_risk', 0)
        liquidations_total = liquidations_24h.get('total_amount', 0)

        # Check for critical conditions
        if liquidations_total > self.liquidation_threshold * 20:
            return 'critical'
        elif total_risk > self.liquidation_threshold * 50:
            return 'critical'
        elif liquidations_total > self.liquidation_threshold * 10:
            return 'high'
        elif total_risk > self.liquidation_threshold * 20:
            return 'high'
        elif liquidations_total > self.liquidation_threshold * 5:
            return 'medium'
        elif total_risk > self.liquidation_threshold * 10:
            return 'medium'
        elif liquidations_total > self.liquidation_threshold:
            return 'low'
        else:
            return 'info'

    async def monitor_multiple_assets(self, symbols: List[str]) -> List[Dict]:
        """Monitor heatmaps for multiple assets"""
        results = []
        for symbol in symbols:
            result = await self.analyze_heatmap(symbol)
            results.append(result)
        return results
