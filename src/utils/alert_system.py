"""Real-time alert system for trading opportunities and inefficiencies"""

from typing import Dict, List, Callable, Optional
from datetime import datetime
from collections import defaultdict
import logging
import json

logger = logging.getLogger(__name__)


class AlertLevel:
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    HIGH = "high"
    CRITICAL = "critical"


class Alert:
    """Represents a trading alert"""

    def __init__(self, title: str, message: str, level: str = AlertLevel.INFO,
                 market_id: str = None, data: Dict = None):
        self.title = title
        self.message = message
        self.level = level
        self.market_id = market_id
        self.data = data or {}
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict:
        return {
            'title': self.title,
            'message': self.message,
            'level': self.level,
            'market_id': self.market_id,
            'data': self.data,
            'timestamp': self.timestamp.isoformat()
        }

    def __repr__(self):
        return f"[{self.level.upper()}] {self.title}: {self.message}"


class AlertSystem:
    """
    Alert system for notifying about trading opportunities

    Supports multiple alert channels:
    - Console logging
    - File output
    - Webhook notifications (future)
    """

    def __init__(self, config: Dict = None):
        self.config = config or {}

        # Alert thresholds
        self.min_severity = self.config.get('min_severity', 0.5)
        self.min_edge = self.config.get('min_edge', 0.03)  # 3% minimum edge

        # Alert history
        self.alerts: List[Alert] = []
        self.alert_counts = defaultdict(int)

        # Alert handlers
        self.handlers: List[Callable] = []

        # Add default console handler
        self.add_handler(self._console_handler)

        # File output
        self.log_file = self.config.get('log_file', 'data/alerts.jsonl')
        if self.log_file:
            self.add_handler(self._file_handler)

    def add_handler(self, handler: Callable):
        """Add a custom alert handler function"""
        self.handlers.append(handler)

    def alert(self, title: str, message: str, level: str = AlertLevel.INFO,
              market_id: str = None, data: Dict = None):
        """
        Send an alert

        Args:
            title: Alert title
            message: Alert message
            level: Severity level (info, warning, high, critical)
            market_id: Related market ID
            data: Additional data
        """
        alert = Alert(title, message, level, market_id, data)
        self.alerts.append(alert)
        self.alert_counts[level] += 1

        # Call all handlers
        for handler in self.handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")

    def alert_arbitrage(self, market: Dict, edge: float, details: str):
        """Alert about arbitrage opportunity"""
        market_id = market.get('id')
        question = market.get('question', 'Unknown')

        # Determine severity based on edge size
        if edge >= 0.10:  # 10%+
            level = AlertLevel.CRITICAL
        elif edge >= 0.05:  # 5%+
            level = AlertLevel.HIGH
        else:
            level = AlertLevel.WARNING

        self.alert(
            title=f"Arbitrage: {edge:.1%} edge",
            message=f"{question}\n{details}",
            level=level,
            market_id=market_id,
            data={'edge': edge, 'type': 'arbitrage'}
        )

    def alert_inefficiency(self, inefficiency):
        """Alert about market inefficiency"""
        # Determine level based on severity
        if inefficiency.severity >= 0.8:
            level = AlertLevel.CRITICAL
        elif inefficiency.severity >= 0.6:
            level = AlertLevel.HIGH
        elif inefficiency.severity >= 0.4:
            level = AlertLevel.WARNING
        else:
            level = AlertLevel.INFO

        self.alert(
            title=f"Inefficiency: {inefficiency.type}",
            message=inefficiency.description,
            level=level,
            market_id=inefficiency.market_id,
            data=inefficiency.data
        )

    def alert_signal(self, signal, strategy_name: str):
        """Alert about trading signal"""
        # Only alert on high-confidence signals
        if signal.confidence < self.min_severity:
            return

        # Determine level
        if signal.confidence >= 0.8:
            level = AlertLevel.HIGH
        elif signal.confidence >= 0.6:
            level = AlertLevel.WARNING
        else:
            level = AlertLevel.INFO

        self.alert(
            title=f"Signal: {strategy_name}",
            message=f"{signal.action} {signal.outcome} @ {signal.price:.3f}\n{signal.reason}",
            level=level,
            market_id=signal.market_id,
            data={
                'strategy': strategy_name,
                'action': signal.action,
                'outcome': signal.outcome,
                'price': signal.price,
                'size': signal.size,
                'confidence': signal.confidence
            }
        )

    def alert_crypto_opportunity(self, market: Dict, asset: str, details: str):
        """Alert about crypto-specific opportunity"""
        self.alert(
            title=f"Crypto Alert: {asset}",
            message=f"{market.get('question', 'Unknown')}\n{details}",
            level=AlertLevel.HIGH,
            market_id=market.get('id'),
            data={'asset': asset, 'type': 'crypto'}
        )

    def _console_handler(self, alert: Alert):
        """Log alert to console"""
        # Color coding (if terminal supports it)
        colors = {
            AlertLevel.INFO: '\033[37m',      # White
            AlertLevel.WARNING: '\033[33m',   # Yellow
            AlertLevel.HIGH: '\033[93m',      # Bright yellow
            AlertLevel.CRITICAL: '\033[91m',  # Bright red
        }
        reset = '\033[0m'

        color = colors.get(alert.level, reset)
        print(f"{color}[{alert.timestamp.strftime('%H:%M:%S')}] {alert}{reset}")

    def _file_handler(self, alert: Alert):
        """Write alert to file"""
        try:
            import os
            os.makedirs(os.path.dirname(self.log_file), exist_ok=True)

            with open(self.log_file, 'a') as f:
                f.write(json.dumps(alert.to_dict()) + '\n')
        except Exception as e:
            logger.error(f"Failed to write alert to file: {e}")

    def get_stats(self) -> Dict:
        """Get alert statistics"""
        return {
            'total_alerts': len(self.alerts),
            'by_level': dict(self.alert_counts),
            'recent_count': len([a for a in self.alerts[-100:]]),  # Last 100
        }

    def get_recent_alerts(self, count: int = 10, level: str = None) -> List[Alert]:
        """Get recent alerts"""
        alerts = self.alerts

        if level:
            alerts = [a for a in alerts if a.level == level]

        return alerts[-count:]

    def clear_old_alerts(self, keep_last: int = 1000):
        """Clear old alerts to prevent memory bloat"""
        if len(self.alerts) > keep_last:
            removed = len(self.alerts) - keep_last
            self.alerts = self.alerts[-keep_last:]
            logger.info(f"Cleared {removed} old alerts")
