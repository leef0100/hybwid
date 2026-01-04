#!/usr/bin/env python3
"""
Simple backtest example
"""
import asyncio
import sys
sys.path.append('..')

from config import Config
from src.api import PolymarketClient
from src.strategies import ValueStrategy, ArbitrageStrategy
from src.engine.backtester import Backtester
from src.utils import setup_logger

logger = setup_logger()


async def main():
    """Run a simple backtest"""
    logger.info("Starting simple backtest example")

    client = PolymarketClient(
        api_url=Config.POLYMARKET_API_URL,
        gamma_url=Config.GAMMA_MARKETS_ENDPOINT
    )

    logger.info("Fetching markets...")
    markets = await client.get_markets(limit=100)
    market_ids = [m.get('id') for m in markets if m.get('id')]

    logger.info(f"Testing on {len(market_ids)} markets")

    value_strategy = ValueStrategy({
        'min_edge': 0.05,
        'position_size_pct': 0.02
    })

    arb_strategy = ArbitrageStrategy({
        'min_arb_edge': 0.02,
        'position_size': 100
    })

    backtester = Backtester(client, initial_capital=10000)

    results = await backtester.compare_strategies(
        [value_strategy, arb_strategy],
        market_ids[:30]
    )

    print("\n=== STRATEGY COMPARISON ===")
    for result in results:
        print(f"{result['strategy']:30} | Return: {result['total_return_pct']:6.2f}% | "
              f"Trades: {result['trades_executed']:3}")

    client.close()


if __name__ == "__main__":
    asyncio.run(main())
