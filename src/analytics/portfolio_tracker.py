from typing import Dict, List
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class PortfolioTracker:
    """Track and analyze portfolio performance over time"""

    def __init__(self, output_dir: str = "data"):
        self.output_dir = output_dir
        self.snapshots: List[Dict] = []
        self.trades: List[Dict] = []

    def add_snapshot(self, portfolio_summary: Dict, positions: List[Dict]):
        """Add a portfolio snapshot"""
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'portfolio': portfolio_summary,
            'positions': positions
        }
        self.snapshots.append(snapshot)

    def add_trade(self, trade: Dict):
        """Record a trade"""
        self.trades.append({
            **trade,
            'timestamp': datetime.now().isoformat()
        })

    def get_performance_metrics(self) -> Dict:
        """Calculate performance metrics"""
        if not self.snapshots:
            return {}

        first_snapshot = self.snapshots[0]
        last_snapshot = self.snapshots[-1]

        initial_capital = first_snapshot['portfolio']['initial_capital']
        final_value = last_snapshot['portfolio']['portfolio_value']
        total_return = (final_value - initial_capital) / initial_capital

        returns = []
        for i in range(1, len(self.snapshots)):
            prev_value = self.snapshots[i-1]['portfolio']['portfolio_value']
            curr_value = self.snapshots[i]['portfolio']['portfolio_value']
            returns.append((curr_value - prev_value) / prev_value if prev_value > 0 else 0)

        import numpy as np
        sharpe_ratio = 0
        if len(returns) > 1:
            mean_return = np.mean(returns)
            std_return = np.std(returns)
            sharpe_ratio = (mean_return / std_return * np.sqrt(252)) if std_return > 0 else 0

        max_drawdown = self._calculate_max_drawdown()

        win_trades = [t for t in self.trades if 'pnl' in t and t['pnl'] > 0]
        lose_trades = [t for t in self.trades if 'pnl' in t and t['pnl'] < 0]
        win_rate = len(win_trades) / len(self.trades) if self.trades else 0

        return {
            'initial_capital': initial_capital,
            'final_value': final_value,
            'total_return': total_return,
            'total_return_pct': total_return * 100,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'max_drawdown_pct': max_drawdown * 100,
            'total_trades': len(self.trades),
            'winning_trades': len(win_trades),
            'losing_trades': len(lose_trades),
            'win_rate': win_rate,
            'win_rate_pct': win_rate * 100
        }

    def _calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown"""
        if not self.snapshots:
            return 0

        peak = self.snapshots[0]['portfolio']['portfolio_value']
        max_dd = 0

        for snapshot in self.snapshots:
            value = snapshot['portfolio']['portfolio_value']
            if value > peak:
                peak = value
            dd = (peak - value) / peak if peak > 0 else 0
            max_dd = max(max_dd, dd)

        return max_dd

    def save_report(self, filename: str = None):
        """Save performance report to file"""
        if filename is None:
            filename = f"{self.output_dir}/portfolio_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        report = {
            'generated_at': datetime.now().isoformat(),
            'performance_metrics': self.get_performance_metrics(),
            'snapshots': self.snapshots[-10:],
            'recent_trades': self.trades[-20:]
        }

        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"Portfolio report saved to {filename}")

    def print_summary(self):
        """Print portfolio summary to console"""
        metrics = self.get_performance_metrics()

        print("\n" + "="*60)
        print(" PORTFOLIO PERFORMANCE SUMMARY")
        print("="*60)
        print(f"Initial Capital:     ${metrics.get('initial_capital', 0):,.2f}")
        print(f"Final Value:         ${metrics.get('final_value', 0):,.2f}")
        print(f"Total Return:        {metrics.get('total_return_pct', 0):.2f}%")
        print(f"Sharpe Ratio:        {metrics.get('sharpe_ratio', 0):.2f}")
        print(f"Max Drawdown:        {metrics.get('max_drawdown_pct', 0):.2f}%")
        print(f"Total Trades:        {metrics.get('total_trades', 0)}")
        print(f"Win Rate:            {metrics.get('win_rate_pct', 0):.2f}%")
        print("="*60 + "\n")
