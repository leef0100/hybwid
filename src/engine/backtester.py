from typing import Dict, List
from datetime import datetime, timedelta
import logging
import asyncio
from .paper_trader import PaperTradingEngine, OrderSide
from src.strategies.base_strategy import BaseStrategy

logger = logging.getLogger(__name__)


class Backtester:
    """Backtest trading strategies on historical data"""

    def __init__(self, api_client, initial_capital: float):
        self.api_client = api_client
        self.initial_capital = initial_capital
        self.results: List[Dict] = []

    async def backtest_strategy(self, strategy: BaseStrategy, market_ids: List[str],
                                start_date: datetime = None, end_date: datetime = None) -> Dict:
        """
        Backtest a strategy on historical data

        Args:
            strategy: Trading strategy to test
            market_ids: List of market IDs to test on
            start_date: Start date for backtest
            end_date: End date for backtest

        Returns:
            Backtest results
        """
        logger.info(f"Starting backtest for {strategy.name}")

        engine = PaperTradingEngine(self.initial_capital)
        trades_executed = 0
        signals_generated = 0

        for market_id in market_ids:
            try:
                market = await self.api_client.get_market_by_id(market_id)
                if not market:
                    continue

                prices = await self.api_client.get_market_prices(market_id)
                if not prices:
                    continue

                signals = await strategy.generate_signals(market, prices)
                signals_generated += len(signals)

                for signal in signals:
                    side = OrderSide.BUY if signal.action == 'BUY' else OrderSide.SELL

                    order = engine.place_order(
                        market_id=signal.market_id,
                        outcome=signal.outcome,
                        side=side,
                        size=signal.size,
                        price=signal.price
                    )

                    if order:
                        engine.execute_order(order, signal.price)
                        trades_executed += 1

                market_prices_dict = {market_id: prices}
                engine.update_positions(market_prices_dict)

            except Exception as e:
                logger.error(f"Error backtesting market {market_id}: {e}")
                continue

        portfolio_summary = engine.get_portfolio_summary()

        results = {
            'strategy': strategy.name,
            'initial_capital': self.initial_capital,
            'final_value': portfolio_summary['portfolio_value'],
            'total_return': portfolio_summary['total_pnl'],
            'total_return_pct': portfolio_summary['total_pnl_pct'],
            'signals_generated': signals_generated,
            'trades_executed': trades_executed,
            'final_positions': len(engine.positions),
            'markets_tested': len(market_ids),
            'timestamp': datetime.now().isoformat()
        }

        logger.info(f"Backtest complete. Return: {results['total_return_pct']:.2f}%")
        self.results.append(results)

        return results

    async def compare_strategies(self, strategies: List[BaseStrategy],
                                 market_ids: List[str]) -> List[Dict]:
        """
        Compare multiple strategies on the same data

        Args:
            strategies: List of strategies to compare
            market_ids: Markets to test on

        Returns:
            List of results for each strategy
        """
        results = []

        for strategy in strategies:
            result = await self.backtest_strategy(strategy, market_ids)
            results.append(result)

        results.sort(key=lambda x: x['total_return_pct'], reverse=True)

        logger.info(f"Strategy comparison complete. Best: {results[0]['strategy']} ({results[0]['total_return_pct']:.2f}%)")

        return results

    def print_results(self, results: Dict = None):
        """Print backtest results"""
        if results is None and self.results:
            results = self.results[-1]

        if not results:
            print("No backtest results available")
            return

        print("\n" + "="*60)
        print(" BACKTEST RESULTS")
        print("="*60)
        print(f"Strategy:            {results['strategy']}")
        print(f"Initial Capital:     ${results['initial_capital']:,.2f}")
        print(f"Final Value:         ${results['final_value']:,.2f}")
        print(f"Total Return:        {results['total_return_pct']:.2f}%")
        print(f"Signals Generated:   {results['signals_generated']}")
        print(f"Trades Executed:     {results['trades_executed']}")
        print(f"Markets Tested:      {results['markets_tested']}")
        print("="*60 + "\n")


class WalkForwardOptimizer:
    """Perform walk-forward optimization on strategies"""

    def __init__(self, api_client, initial_capital: float):
        self.api_client = api_client
        self.initial_capital = initial_capital

    async def optimize(self, strategy_class, param_grid: Dict,
                      market_ids: List[str], train_size: int = 100,
                      test_size: int = 50) -> Dict:
        """
        Perform walk-forward optimization

        Args:
            strategy_class: Strategy class to optimize
            param_grid: Grid of parameters to test
            market_ids: Markets to use
            train_size: Number of markets for training
            test_size: Number of markets for testing

        Returns:
            Best parameters and results
        """
        best_params = None
        best_return = float('-inf')

        train_markets = market_ids[:train_size]
        test_markets = market_ids[train_size:train_size + test_size]

        for params in self._generate_param_combinations(param_grid):
            strategy = strategy_class(config=params)
            backtester = Backtester(self.api_client, self.initial_capital)

            train_result = await backtester.backtest_strategy(strategy, train_markets)

            if train_result['total_return_pct'] > best_return:
                best_return = train_result['total_return_pct']
                best_params = params

        strategy = strategy_class(config=best_params)
        backtester = Backtester(self.api_client, self.initial_capital)
        test_result = await backtester.backtest_strategy(strategy, test_markets)

        return {
            'best_params': best_params,
            'train_return': best_return,
            'test_return': test_result['total_return_pct']
        }

    def _generate_param_combinations(self, param_grid: Dict) -> List[Dict]:
        """Generate all combinations of parameters"""
        keys = list(param_grid.keys())
        values = list(param_grid.values())

        combinations = []
        self._recursive_combinations(keys, values, 0, {}, combinations)

        return combinations

    def _recursive_combinations(self, keys, values, index, current, combinations):
        """Recursively generate parameter combinations"""
        if index == len(keys):
            combinations.append(current.copy())
            return

        for value in values[index]:
            current[keys[index]] = value
            self._recursive_combinations(keys, values, index + 1, current, combinations)
