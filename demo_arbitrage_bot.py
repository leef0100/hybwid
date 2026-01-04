#!/usr/bin/env python3
"""
Demo script for the enhanced Polymarket arbitrage bot

Shows the new capabilities:
1. Crypto market filtering (BTC/ETH/SOL)
2. Cross-market arbitrage detection
3. Scalping strategy
4. Inefficiency detection
5. Real-time alerts
"""

import asyncio
from src.api import PolymarketClient
from src.utils.market_categorizer import MarketCategorizer, MarketCategory
from src.strategies.cross_market_arbitrage import CrossMarketArbitrage
from src.strategies.scalping_strategy import ScalpingStrategy
from src.analytics.inefficiency_detector import InefficiencyDetector
from src.utils.alert_system import AlertSystem
from src.utils import setup_logger

logger = setup_logger(level='INFO')


async def demo_market_categorization():
    """Demo 1: Market categorization and filtering"""
    print("\n" + "="*70)
    print("DEMO 1: Market Categorization (Crypto/Entertainment Focus)")
    print("="*70 + "\n")

    client = PolymarketClient()
    categorizer = MarketCategorizer()

    # Fetch markets
    markets = await client.get_markets(limit=100)

    # Categorize
    crypto_markets = []
    entertainment_markets = []

    for market in markets[:50]:
        category = categorizer.categorize(market)
        question = market.get('question', 'Unknown')

        if category in [MarketCategory.CRYPTO_BTC, MarketCategory.CRYPTO_ETH, MarketCategory.CRYPTO_SOL]:
            asset = categorizer.get_crypto_asset(market)
            crypto_markets.append((market, asset))
            print(f"🪙 [{asset}] {question[:70]}")

        elif category in [MarketCategory.ENTERTAINMENT, MarketCategory.SPORTS]:
            entertainment_markets.append(market)
            print(f"🎬 [ENT] {question[:70]}")

    print(f"\n✅ Found {len(crypto_markets)} crypto markets and {len(entertainment_markets)} entertainment markets")

    # Show distribution
    stats = categorizer.get_category_stats(markets[:50])
    print(f"\nCategory distribution: {stats}")

    client.close()
    return crypto_markets


async def demo_inefficiency_detection():
    """Demo 2: Inefficiency detection"""
    print("\n" + "="*70)
    print("DEMO 2: Market Inefficiency Detection")
    print("="*70 + "\n")

    client = PolymarketClient()
    detector = InefficiencyDetector()

    # Get some active markets
    markets = await client.get_markets(limit=10, active=True)

    inefficiencies_found = 0

    for market in markets:
        market_id = market.get('id')
        question = market.get('question', 'Unknown')

        # Get current prices
        prices = await client.get_market_prices(market_id)
        if not prices:
            continue

        # Detect inefficiencies
        ineffs = detector.detect_all(market, prices)

        if ineffs:
            print(f"\n📊 Market: {question[:60]}")
            for ineff in ineffs:
                severity_bar = "🔴" * int(ineff.severity * 5)
                print(f"   {severity_bar} [{ineff.type}] {ineff.description}")
                inefficiencies_found += 1

    print(f"\n✅ Detected {inefficiencies_found} inefficiencies across {len(markets)} markets")

    # Show stats
    stats = detector.get_inefficiency_stats()
    print(f"Stats: {stats}")

    client.close()


async def demo_cross_market_arbitrage():
    """Demo 3: Cross-market arbitrage detection"""
    print("\n" + "="*70)
    print("DEMO 3: Cross-Market Arbitrage Detection")
    print("="*70 + "\n")

    client = PolymarketClient()
    categorizer = MarketCategorizer()
    strategy = CrossMarketArbitrage()

    # Search for crypto markets
    btc_markets = await client.search_markets("bitcoin")

    print(f"Found {len(btc_markets)} BTC-related markets\n")

    # Process markets to build cache
    signals_found = []

    for market in btc_markets[:20]:
        market_id = market.get('id')
        question = market.get('question', 'Unknown')

        prices = await client.get_market_prices(market_id)
        if not prices:
            continue

        # Analyze for cross-market arbitrage
        signals = await strategy.analyze(market, prices)

        if signals:
            print(f"🎯 Arbitrage found!")
            print(f"   Market: {question[:60]}")
            for signal in signals:
                print(f"   Signal: {signal}")
                signals_found.append(signal)

    print(f"\n✅ Found {len(signals_found)} cross-market arbitrage opportunities")

    client.close()
    return signals_found


async def demo_scalping_strategy():
    """Demo 4: Scalping strategy"""
    print("\n" + "="*70)
    print("DEMO 4: Scalping Strategy (Momentum & Mean Reversion)")
    print("="*70 + "\n")

    client = PolymarketClient()
    strategy = ScalpingStrategy({
        'momentum_threshold': 0.02,  # 2% for demo
        'min_edge': 0.01
    })

    # Get some active markets
    markets = await client.get_markets(limit=10, active=True)

    signals_found = []

    # Simulate multiple price updates
    for update_round in range(3):
        print(f"\n--- Price Update Round {update_round + 1} ---")

        for market in markets:
            market_id = market.get('id')
            prices = await client.get_market_prices(market_id)

            if not prices:
                continue

            # Analyze for scalping opportunities
            signals = await strategy.analyze(market, prices)

            if signals:
                question = market.get('question', 'Unknown')[:50]
                print(f"⚡ Scalp opportunity: {question}")
                for signal in signals:
                    print(f"   {signal}")
                    signals_found.append(signal)

        await asyncio.sleep(2)  # Wait between updates

    print(f"\n✅ Generated {len(signals_found)} scalping signals across 3 price updates")

    client.close()


async def demo_alert_system():
    """Demo 5: Alert system"""
    print("\n" + "="*70)
    print("DEMO 5: Real-Time Alert System")
    print("="*70 + "\n")

    alert_system = AlertSystem()

    # Simulate various alerts
    alert_system.alert(
        title="Market Discovery",
        message="Found 15 BTC markets with volume > 10k",
        level="info"
    )

    alert_system.alert_crypto_opportunity(
        market={'id': 'btc-100k', 'question': 'Will BTC hit $100k by EOY?'},
        asset='BTC',
        details="Strong arbitrage opportunity detected: 8% edge"
    )

    alert_system.alert(
        title="High Confidence Signal",
        message="Arbitrage opportunity: BUY both YES and NO for guaranteed profit",
        level="critical",
        data={'edge': 0.08, 'confidence': 0.95}
    )

    # Show stats
    stats = alert_system.get_stats()
    print(f"\n✅ Alert system stats: {stats}")

    recent = alert_system.get_recent_alerts(10)
    print(f"\nRecent alerts ({len(recent)}):")
    for alert in recent:
        print(f"  {alert}")


async def main():
    """Run all demos"""
    print("\n" + "🚀"*35)
    print("POLYMARKET ARBITRAGE BOT - ENHANCED FEATURES DEMO")
    print("🚀"*35)

    try:
        # Run demos
        await demo_market_categorization()
        await asyncio.sleep(1)

        await demo_inefficiency_detection()
        await asyncio.sleep(1)

        await demo_cross_market_arbitrage()
        await asyncio.sleep(1)

        await demo_scalping_strategy()
        await asyncio.sleep(1)

        await demo_alert_system()

        print("\n" + "="*70)
        print("✅ All demos completed successfully!")
        print("="*70)
        print("\nTo run the full bot:")
        print("  python bot.py              # Live trading mode")
        print("  python bot.py backtest     # Backtest mode")
        print("\nThe bot now includes:")
        print("  ✅ Crypto market filtering (BTC/ETH/SOL)")
        print("  ✅ Cross-market arbitrage detection")
        print("  ✅ Scalping strategy (momentum + mean reversion)")
        print("  ✅ Statistical inefficiency detection")
        print("  ✅ Real-time alert system")

    except Exception as e:
        logger.error(f"Demo error: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
