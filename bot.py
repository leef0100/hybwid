import asyncio
from typing import List
from datetime import datetime
import signal
import sys

from config import Config
from src.api import PolymarketClient
from src.engine import PaperTradingEngine, OrderSide
from src.engine.risk_manager import RiskManager
from src.engine.market_monitor import MarketMonitor
from src.strategies import ValueStrategy, ArbitrageStrategy, SpreadArbitrageStrategy
from src.strategies.cross_market_arbitrage import CrossMarketArbitrage
from src.strategies.scalping_strategy import ScalpingStrategy
from src.analytics import PortfolioTracker
from src.analytics.inefficiency_detector import InefficiencyDetector
from src.utils import setup_logger
from src.utils.market_categorizer import MarketCategorizer, MarketCategory
from src.utils.alert_system import AlertSystem

logger = setup_logger(level=Config.LOG_LEVEL)


class PolymarketBot:
    """Main bot orchestrator"""

    def __init__(self):
        self.config = Config
        self.client = PolymarketClient(
            api_url=Config.POLYMARKET_API_URL,
            gamma_url=Config.GAMMA_MARKETS_ENDPOINT
        )
        self.engine = PaperTradingEngine(Config.INITIAL_CAPITAL)
        self.risk_manager = RiskManager({
            'max_position_size': Config.MAX_POSITION_SIZE,
            'max_total_exposure': Config.MAX_TOTAL_EXPOSURE
        })
        self.monitor = MarketMonitor(self.client, update_interval=60)
        self.tracker = PortfolioTracker()

        # New components
        self.categorizer = MarketCategorizer()
        self.inefficiency_detector = InefficiencyDetector()
        self.alert_system = AlertSystem()

        self.strategies = []
        self.running = False

        self._setup_strategies()
        self._setup_signal_handlers()

    def _setup_strategies(self):
        """Initialize trading strategies"""
        # Original strategies
        self.strategies.append(ValueStrategy({
            'min_edge': 0.05,
            'max_price': 0.7,
            'min_price': 0.1,
            'position_size_pct': 0.02
        }))

        self.strategies.append(ArbitrageStrategy({
            'min_arb_edge': 0.02,
            'position_size': 100
        }))

        self.strategies.append(SpreadArbitrageStrategy({
            'min_spread': 0.05,
            'position_size': 50
        }))

        # New strategies for enhanced arbitrage detection
        self.strategies.append(CrossMarketArbitrage({
            'min_price_diff': 0.05,       # 5% price difference between similar markets
            'similarity_threshold': 0.7,   # How similar markets need to be
            'position_size': 100,
            'max_markets_compare': 50
        }))

        self.strategies.append(ScalpingStrategy({
            'momentum_threshold': 0.03,    # 3% price movement
            'volume_spike_multiple': 2.0,  # 2x average volume
            'max_spread': 0.03,            # Only scalp tight spreads
            'lookback_periods': 5,
            'position_size': 50,
            'min_edge': 0.02
        }))

        logger.info(f"Initialized {len(self.strategies)} strategies")
        logger.info("✨ Enhanced with Cross-Market Arbitrage and Scalping strategies")

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signal"""
        logger.info("Shutdown signal received")
        self.running = False

    async def on_market_update(self, market: dict, prices: dict):
        """Callback when market is updated"""
        market_id = market.get('id')

        # Detect market inefficiencies
        inefficiencies = self.inefficiency_detector.detect_all(market, prices)
        for ineff in inefficiencies:
            if ineff.severity >= 0.5:  # Only alert on significant inefficiencies
                self.alert_system.alert_inefficiency(ineff)

        # Check if this is a crypto market
        category = self.categorizer.categorize(market)
        crypto_asset = self.categorizer.get_crypto_asset(market)

        # Run strategies
        for strategy in self.strategies:
            signals = await strategy.generate_signals(market, prices)

            for signal in signals:
                # Alert on high-confidence signals
                self.alert_system.alert_signal(signal, strategy.name)

                # Additional alert for crypto opportunities
                if crypto_asset and signal.confidence >= 0.6:
                    self.alert_system.alert_crypto_opportunity(
                        market, crypto_asset,
                        f"{signal.action} {signal.outcome} @ {signal.price:.3f} ({signal.confidence:.0%} confidence)"
                    )

                is_valid, reason = self.risk_manager.validate_signal(signal, self.engine)

                if is_valid:
                    signal = self.risk_manager.adjust_position_size(signal, self.engine)

                    side = OrderSide.BUY if signal.action == 'BUY' else OrderSide.SELL
                    order = self.engine.place_order(
                        market_id=signal.market_id,
                        outcome=signal.outcome,
                        side=side,
                        size=signal.size,
                        price=signal.price
                    )

                    if order:
                        self.engine.execute_order(order, signal.price)
                        logger.info(f"✅ Executed: {signal}")

                        self.tracker.add_trade(order.to_dict())
                else:
                    logger.warning(f"❌ Signal rejected: {reason}")

        market_prices = {market_id: prices}
        self.engine.update_positions(market_prices)

    async def discover_and_monitor_markets(self):
        """Discover interesting markets and start monitoring"""
        logger.info("Discovering markets...")

        # Get all active markets
        all_markets = await self.client.get_markets(limit=500, active=True)

        # Filter by volume
        filtered_markets = [m for m in all_markets if m.get('volume', 0) >= 5000]

        # Categorize markets
        crypto_markets = []
        entertainment_markets = []
        other_markets = []

        for market in filtered_markets:
            category = self.categorizer.categorize(market)

            if category in [MarketCategory.CRYPTO_BTC, MarketCategory.CRYPTO_ETH, MarketCategory.CRYPTO_SOL]:
                crypto_markets.append(market)
            elif category == MarketCategory.ENTERTAINMENT or category == MarketCategory.SPORTS:
                entertainment_markets.append(market)
            else:
                other_markets.append(market)

        logger.info(f"Found {len(crypto_markets)} crypto markets, {len(entertainment_markets)} entertainment markets, {len(other_markets)} other markets")

        # Prioritize crypto and entertainment markets
        prioritized = crypto_markets[:10] + entertainment_markets[:10] + other_markets[:10]

        # Get category stats
        stats = self.categorizer.get_category_stats(prioritized)
        logger.info(f"Market distribution: {stats}")

        # Add to monitor
        for market in prioritized[:30]:  # Monitor up to 30 markets
            self.monitor.add_market(market.get('id'))

        logger.info(f"Monitoring {len(self.monitor.monitored_markets)} markets (prioritizing crypto & entertainment)")

    async def run_live(self):
        """Run bot in live mode"""
        logger.info("Starting bot in LIVE mode")
        logger.info(f"Initial capital: ${self.engine.initial_capital:,.2f}")

        await self.discover_and_monitor_markets()

        self.monitor.add_callback(self.on_market_update)

        self.running = True
        monitor_task = asyncio.create_task(self.monitor.start())

        snapshot_interval = 300
        last_snapshot = datetime.now()

        while self.running:
            await asyncio.sleep(10)

            if (datetime.now() - last_snapshot).total_seconds() >= snapshot_interval:
                self._take_snapshot()
                last_snapshot = datetime.now()

        monitor_task.cancel()
        await self._shutdown()

    async def run_backtest(self, num_markets: int = 100):
        """Run bot in backtest mode"""
        logger.info("Starting bot in BACKTEST mode")

        from src.engine.backtester import Backtester

        markets = await self.client.get_markets(limit=num_markets)
        market_ids = [m.get('id') for m in markets if m.get('id')]

        for strategy in self.strategies:
            backtester = Backtester(self.client, Config.INITIAL_CAPITAL)
            result = await backtester.backtest_strategy(strategy, market_ids[:50])
            backtester.print_results(result)

    def _take_snapshot(self):
        """Take portfolio snapshot"""
        summary = self.engine.get_portfolio_summary()
        positions = self.engine.get_all_positions()

        self.tracker.add_snapshot(summary, positions)

        logger.info(f"💰 Portfolio: ${summary['portfolio_value']:,.2f} | "
                   f"PnL: ${summary['total_pnl']:,.2f} ({summary['total_pnl_pct']:.2f}%) | "
                   f"Positions: {summary['num_positions']}")

    async def _shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down bot...")

        self.monitor.stop()

        self._take_snapshot()
        self.tracker.print_summary()

        # Print inefficiency stats
        ineff_stats = self.inefficiency_detector.get_inefficiency_stats()
        logger.info(f"Inefficiencies detected: {ineff_stats}")

        # Print alert stats
        alert_stats = self.alert_system.get_stats()
        logger.info(f"Alerts generated: {alert_stats}")

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.engine.save_state(f"data/final_state_{timestamp}.json")
        self.tracker.save_report(f"data/final_report_{timestamp}.json")

        self.client.close()

        logger.info("Bot shutdown complete")


async def main():
    """Main entry point"""
    bot = PolymarketBot()

    if len(sys.argv) > 1 and sys.argv[1] == 'backtest':
        await bot.run_backtest()
    else:
        await bot.run_live()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
