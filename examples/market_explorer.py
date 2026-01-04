#!/usr/bin/env python3
"""
Market explorer - browse and analyze Polymarket markets
"""
import asyncio
import sys
sys.path.append('..')

from config import Config
from src.api import PolymarketClient
from src.utils import setup_logger

logger = setup_logger()


async def explore_markets():
    """Explore available markets"""
    client = PolymarketClient(
        api_url=Config.POLYMARKET_API_URL,
        gamma_url=Config.GAMMA_MARKETS_ENDPOINT
    )

    print("\n=== POLYMARKET EXPLORER ===\n")

    markets = await client.get_markets(limit=20, active=True)

    print(f"Found {len(markets)} active markets:\n")

    for i, market in enumerate(markets, 1):
        question = market.get('question', 'N/A')
        volume = market.get('volume', 0)
        end_date = market.get('end_date_iso', 'N/A')

        print(f"{i}. {question[:70]}")
        print(f"   Volume: ${volume:,.0f} | Ends: {end_date}")
        print()

    if markets:
        market_id = markets[0].get('id')
        print(f"\n=== DETAILED VIEW: {markets[0].get('question')} ===\n")

        prices = await client.get_market_prices(market_id)
        if prices:
            print("Current Prices:")
            for outcome, price_data in prices.items():
                bid = price_data.get('bid', 0)
                ask = price_data.get('ask', 0)
                mid = price_data.get('mid', 0)
                print(f"  {outcome:10} | Bid: {bid:.3f} | Ask: {ask:.3f} | Mid: {mid:.3f}")

    client.close()


if __name__ == "__main__":
    asyncio.run(explore_markets())
