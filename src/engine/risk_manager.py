from typing import Dict, List, Optional
from .paper_trader import PaperTradingEngine, OrderSide
from src.strategies.base_strategy import Signal
import logging

logger = logging.getLogger(__name__)


class RiskManager:
    """Manages risk limits and validates trades before execution"""

    def __init__(self, config: Dict):
        self.max_position_size = config.get('max_position_size', 0.1)
        self.max_total_exposure = config.get('max_total_exposure', 0.5)
        self.max_loss_per_trade = config.get('max_loss_per_trade', 0.02)
        self.max_daily_loss = config.get('max_daily_loss', 0.1)
        self.max_positions = config.get('max_positions', 20)
        self.min_confidence = config.get('min_confidence', 0.3)

        self.daily_pnl = 0
        self.daily_trades = 0
        self.rejected_signals = 0

    def validate_signal(self, signal: Signal, engine: PaperTradingEngine) -> tuple[bool, str]:
        """
        Validate a signal against risk limits

        Returns:
            (is_valid, reason)
        """
        if signal.confidence < self.min_confidence:
            reason = f"Confidence {signal.confidence:.2f} below minimum {self.min_confidence}"
            logger.warning(f"Signal rejected: {reason}")
            self.rejected_signals += 1
            return False, reason

        if signal.action == 'BUY':
            cost = signal.size * signal.price

            max_position_value = engine.initial_capital * self.max_position_size
            if cost > max_position_value:
                reason = f"Position size ${cost:.2f} exceeds max ${max_position_value:.2f}"
                logger.warning(f"Signal rejected: {reason}")
                self.rejected_signals += 1
                return False, reason

            if cost > engine.cash:
                reason = f"Insufficient cash: need ${cost:.2f}, have ${engine.cash:.2f}"
                logger.warning(f"Signal rejected: {reason}")
                self.rejected_signals += 1
                return False, reason

            current_exposure = engine.get_exposure()
            new_exposure = current_exposure + (cost / engine.initial_capital)

            if new_exposure > self.max_total_exposure:
                reason = f"Total exposure {new_exposure:.2%} exceeds max {self.max_total_exposure:.2%}"
                logger.warning(f"Signal rejected: {reason}")
                self.rejected_signals += 1
                return False, reason

        if len(engine.positions) >= self.max_positions and signal.action == 'BUY':
            position_key = engine.get_position_key(signal.market_id, signal.outcome)
            if position_key not in engine.positions:
                reason = f"Max positions ({self.max_positions}) reached"
                logger.warning(f"Signal rejected: {reason}")
                self.rejected_signals += 1
                return False, reason

        daily_loss_limit = engine.initial_capital * self.max_daily_loss
        if self.daily_pnl < -daily_loss_limit:
            reason = f"Daily loss limit reached: ${abs(self.daily_pnl):.2f}"
            logger.warning(f"Signal rejected: {reason}")
            self.rejected_signals += 1
            return False, reason

        return True, "OK"

    def adjust_position_size(self, signal: Signal, engine: PaperTradingEngine) -> Signal:
        """
        Adjust position size to comply with risk limits

        Returns:
            Adjusted signal
        """
        cost = signal.size * signal.price
        max_position_value = engine.initial_capital * self.max_position_size

        if cost > max_position_value:
            adjusted_size = max_position_value / signal.price
            logger.info(f"Adjusting position size from {signal.size} to {adjusted_size}")
            signal.size = adjusted_size

        if cost > engine.cash:
            adjusted_size = engine.cash / signal.price
            logger.info(f"Adjusting position size from {signal.size} to {adjusted_size} (cash limit)")
            signal.size = adjusted_size

        return signal

    def update_daily_pnl(self, pnl: float):
        """Update daily PnL tracking"""
        self.daily_pnl = pnl
        logger.debug(f"Daily PnL updated: ${pnl:.2f}")

    def reset_daily_stats(self):
        """Reset daily statistics"""
        logger.info(f"Daily stats reset. PnL: ${self.daily_pnl:.2f}, Trades: {self.daily_trades}, Rejected: {self.rejected_signals}")
        self.daily_pnl = 0
        self.daily_trades = 0
        self.rejected_signals = 0

    def get_stats(self) -> Dict:
        """Get risk manager statistics"""
        return {
            'daily_pnl': self.daily_pnl,
            'daily_trades': self.daily_trades,
            'rejected_signals': self.rejected_signals,
            'max_position_size': self.max_position_size,
            'max_total_exposure': self.max_total_exposure,
            'max_daily_loss': self.max_daily_loss
        }


class PositionSizer:
    """Calculate optimal position sizes based on Kelly Criterion or other methods"""

    @staticmethod
    def kelly_criterion(edge: float, confidence: float, bankroll: float) -> float:
        """
        Calculate position size using Kelly Criterion

        Args:
            edge: Expected edge (e.g., 0.1 for 10% edge)
            confidence: Confidence in the signal (0-1)
            bankroll: Available capital

        Returns:
            Suggested position size
        """
        if edge <= 0 or confidence <= 0:
            return 0

        kelly_fraction = edge / (1 - edge)

        kelly_fraction *= confidence

        kelly_fraction = min(kelly_fraction, 0.25)

        return bankroll * kelly_fraction

    @staticmethod
    def fixed_fractional(bankroll: float, fraction: float = 0.02) -> float:
        """
        Fixed fractional position sizing

        Args:
            bankroll: Available capital
            fraction: Fraction of bankroll to risk (default 2%)

        Returns:
            Position size
        """
        return bankroll * fraction

    @staticmethod
    def risk_based(bankroll: float, max_loss: float, entry_price: float, stop_loss: float) -> float:
        """
        Position size based on max acceptable loss

        Args:
            bankroll: Available capital
            max_loss: Maximum loss willing to accept
            entry_price: Entry price
            stop_loss: Stop loss price

        Returns:
            Position size
        """
        if entry_price <= stop_loss:
            return 0

        risk_per_share = entry_price - stop_loss
        max_loss_dollars = bankroll * max_loss

        return max_loss_dollars / risk_per_share if risk_per_share > 0 else 0
