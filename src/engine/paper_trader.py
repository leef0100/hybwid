from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum
import logging
import json

logger = logging.getLogger(__name__)


class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class Order:
    """Represents a paper trading order"""

    def __init__(self, order_id: str, market_id: str, outcome: str, side: OrderSide,
                 size: float, price: float, timestamp: datetime = None):
        self.order_id = order_id
        self.market_id = market_id
        self.outcome = outcome
        self.side = side
        self.size = size
        self.price = price
        self.timestamp = timestamp or datetime.now()
        self.status = OrderStatus.PENDING
        self.filled_size = 0
        self.fill_price = 0

    def fill(self, fill_price: float):
        """Mark order as filled"""
        self.status = OrderStatus.FILLED
        self.filled_size = self.size
        self.fill_price = fill_price
        logger.info(f"Order {self.order_id} filled at {fill_price}")

    def to_dict(self) -> Dict:
        return {
            'order_id': self.order_id,
            'market_id': self.market_id,
            'outcome': self.outcome,
            'side': self.side.value,
            'size': self.size,
            'price': self.price,
            'timestamp': self.timestamp.isoformat(),
            'status': self.status.value,
            'filled_size': self.filled_size,
            'fill_price': self.fill_price
        }


class Position:
    """Represents a position in a market outcome"""

    def __init__(self, market_id: str, outcome: str):
        self.market_id = market_id
        self.outcome = outcome
        self.size = 0
        self.avg_price = 0
        self.realized_pnl = 0
        self.unrealized_pnl = 0

    def add_trade(self, size: float, price: float):
        """Add to position"""
        if self.size == 0:
            self.avg_price = price
        else:
            total_cost = (self.size * self.avg_price) + (size * price)
            self.size += size
            self.avg_price = total_cost / self.size if self.size > 0 else 0

    def reduce_trade(self, size: float, price: float):
        """Reduce position"""
        if size > self.size:
            logger.warning(f"Trying to reduce position by {size} but only have {self.size}")
            size = self.size

        pnl = size * (price - self.avg_price)
        self.realized_pnl += pnl
        self.size -= size

        if self.size == 0:
            self.avg_price = 0

    def update_unrealized_pnl(self, current_price: float):
        """Update unrealized PnL based on current market price"""
        if self.size > 0:
            self.unrealized_pnl = self.size * (current_price - self.avg_price)
        else:
            self.unrealized_pnl = 0

    def to_dict(self) -> Dict:
        return {
            'market_id': self.market_id,
            'outcome': self.outcome,
            'size': self.size,
            'avg_price': self.avg_price,
            'realized_pnl': self.realized_pnl,
            'unrealized_pnl': self.unrealized_pnl,
            'total_pnl': self.realized_pnl + self.unrealized_pnl
        }


class PaperTradingEngine:
    """Paper trading engine that simulates trades without real money"""

    def __init__(self, initial_capital: float):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: Dict[str, Position] = {}
        self.orders: List[Order] = []
        self.trade_history: List[Dict] = []
        self.order_counter = 0

    def get_position_key(self, market_id: str, outcome: str) -> str:
        """Generate unique key for position"""
        return f"{market_id}_{outcome}"

    def place_order(self, market_id: str, outcome: str, side: OrderSide,
                   size: float, price: float) -> Optional[Order]:
        """Place a paper trading order"""
        self.order_counter += 1
        order_id = f"ORDER_{self.order_counter}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        order = Order(order_id, market_id, outcome, side, size, price)

        cost = size * price
        if side == OrderSide.BUY and cost > self.cash:
            logger.warning(f"Insufficient cash for order. Need {cost}, have {self.cash}")
            order.status = OrderStatus.REJECTED
            return None

        position_key = self.get_position_key(market_id, outcome)
        if side == OrderSide.SELL:
            if position_key not in self.positions or self.positions[position_key].size < size:
                logger.warning(f"Insufficient position to sell. Trying to sell {size}")
                order.status = OrderStatus.REJECTED
                return None

        self.orders.append(order)
        logger.info(f"Order placed: {side.value} {size} @ {price} for {outcome}")
        return order

    def execute_order(self, order: Order, execution_price: float):
        """Execute a pending order"""
        if order.status != OrderStatus.PENDING:
            logger.warning(f"Order {order.order_id} is not pending")
            return

        position_key = self.get_position_key(order.market_id, order.outcome)

        if order.side == OrderSide.BUY:
            cost = order.size * execution_price
            self.cash -= cost

            if position_key not in self.positions:
                self.positions[position_key] = Position(order.market_id, order.outcome)

            self.positions[position_key].add_trade(order.size, execution_price)

        else:
            proceeds = order.size * execution_price
            self.cash += proceeds

            if position_key in self.positions:
                self.positions[position_key].reduce_trade(order.size, execution_price)

                if self.positions[position_key].size == 0:
                    del self.positions[position_key]

        order.fill(execution_price)

        self.trade_history.append({
            'timestamp': datetime.now().isoformat(),
            'order_id': order.order_id,
            'market_id': order.market_id,
            'outcome': order.outcome,
            'side': order.side.value,
            'size': order.size,
            'price': execution_price
        })

        logger.info(f"Order executed: {order.side.value} {order.size} @ {execution_price}")

    def update_positions(self, market_prices: Dict[str, Dict]):
        """Update unrealized PnL for all positions"""
        for position_key, position in self.positions.items():
            market_id = position.market_id
            outcome = position.outcome

            if market_id in market_prices and outcome in market_prices[market_id]:
                current_price = market_prices[market_id][outcome].get('mid', position.avg_price)
                position.update_unrealized_pnl(current_price)

    def get_portfolio_value(self) -> float:
        """Calculate total portfolio value"""
        position_value = sum(
            pos.size * pos.avg_price + pos.unrealized_pnl
            for pos in self.positions.values()
        )
        return self.cash + position_value

    def get_total_pnl(self) -> float:
        """Calculate total PnL"""
        return self.get_portfolio_value() - self.initial_capital

    def get_exposure(self) -> float:
        """Calculate total exposure as fraction of capital"""
        position_value = sum(pos.size * pos.avg_price for pos in self.positions.values())
        return position_value / self.initial_capital if self.initial_capital > 0 else 0

    def get_portfolio_summary(self) -> Dict:
        """Get summary of portfolio"""
        return {
            'timestamp': datetime.now().isoformat(),
            'initial_capital': self.initial_capital,
            'cash': self.cash,
            'portfolio_value': self.get_portfolio_value(),
            'total_pnl': self.get_total_pnl(),
            'total_pnl_pct': (self.get_total_pnl() / self.initial_capital * 100) if self.initial_capital > 0 else 0,
            'exposure': self.get_exposure(),
            'num_positions': len(self.positions),
            'num_trades': len(self.trade_history)
        }

    def get_all_positions(self) -> List[Dict]:
        """Get all current positions"""
        return [pos.to_dict() for pos in self.positions.values()]

    def save_state(self, filepath: str):
        """Save current state to file"""
        state = {
            'portfolio': self.get_portfolio_summary(),
            'positions': self.get_all_positions(),
            'trade_history': self.trade_history
        }
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)
        logger.info(f"State saved to {filepath}")
