#!/usr/bin/env python3
"""
Crypto Alert Bot - Daily alerts for BTC, ETH, and SOL

Monitors:
- Open Interest surges
- Volume spikes
- Liquidation heatmaps
- Crypto news (political, market, general)

Data source: Coinglass API
"""

import asyncio
import signal
import sys
from datetime import datetime, time as datetime_time
from typing import List
import logging

from crypto_config import CryptoAlertConfig
from src.crypto_alerts import (
    CoinglassClient,
    OpenInterestMonitor,
    VolumeMonitor,
    HeatmapAnalyzer,
    NewsAggregator,
    AlertManager
)
from src.utils import setup_logger

logger = setup_logger(level=CryptoAlertConfig.LOG_LEVEL)


class CryptoAlertBot:
    """Main crypto alert bot orchestrator"""

    def __init__(self):
        self.config = CryptoAlertConfig
        self.running = False

        # Initialize components
        self.client = CoinglassClient(
            api_key=self.config.COINGLASS_API_KEY,
            base_url=self.config.COINGLASS_API_URL
        )

        self.oi_monitor = OpenInterestMonitor(
            client=self.client,
            surge_threshold=self.config.OI_SURGE_THRESHOLD
        )

        self.volume_monitor = VolumeMonitor(
            client=self.client,
            spike_threshold=self.config.VOLUME_SURGE_THRESHOLD
        )

        self.heatmap_analyzer = HeatmapAnalyzer(
            client=self.client,
            liquidation_threshold=self.config.LIQUIDATION_THRESHOLD
        )

        self.news_aggregator = NewsAggregator(
            max_items=self.config.MAX_NEWS_ITEMS
        )

        self.alert_manager = AlertManager(config=self.config)

        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signal"""
        logger.info("Shutdown signal received")
        self.running = False

    async def collect_all_data(self, symbols: List[str]) -> dict:
        """Collect all data for the monitored assets"""
        logger.info(f"Collecting data for: {', '.join(symbols)}")

        # Collect OI data
        logger.info("Analyzing Open Interest...")
        oi_data = await self.oi_monitor.monitor_multiple_assets(symbols)

        # Collect Volume data
        logger.info("Analyzing Volume...")
        volume_data = await self.volume_monitor.monitor_multiple_assets(symbols)

        # Collect Heatmap data
        logger.info("Analyzing Liquidation Heatmaps...")
        heatmap_data = await self.heatmap_analyzer.monitor_multiple_assets(symbols)

        # Collect News
        logger.info("Aggregating News...")
        news_data = await self.news_aggregator.get_all_news(symbols)

        return {
            'oi_data': oi_data,
            'volume_data': volume_data,
            'heatmap_data': heatmap_data,
            'news_data': news_data
        }

    async def generate_and_send_report(self):
        """Generate daily report and send via all enabled channels"""
        try:
            logger.info("=" * 80)
            logger.info("Starting Daily Report Generation")
            logger.info("=" * 80)

            # Collect all data
            all_data = await self.collect_all_data(self.config.MONITORED_ASSETS)

            # Generate report
            logger.info("Generating report...")
            report = self.alert_manager.generate_daily_report(
                oi_data=all_data['oi_data'],
                volume_data=all_data['volume_data'],
                heatmap_data=all_data['heatmap_data'],
                news_data=all_data['news_data']
            )

            # Save report
            self.alert_manager.save_report(report)

            # Send alerts
            logger.info("Sending alerts...")
            subject = f"Crypto Alert - {datetime.now().strftime('%Y-%m-%d')}"
            await self.alert_manager.send_alert(report, subject)

            logger.info("✅ Report generation and delivery complete")

        except Exception as e:
            logger.error(f"Error generating report: {e}", exc_info=True)

    async def check_critical_alerts(self):
        """Check for critical alerts and send immediate notifications"""
        try:
            all_data = await self.collect_all_data(self.config.MONITORED_ASSETS)

            critical_alerts = []

            # Check OI surges
            for oi in all_data['oi_data']:
                if oi.get('alert_level') in ['critical', 'high'] and oi.get('is_surge'):
                    symbol = oi['symbol']
                    change = oi['change_percent']
                    critical_alerts.append(
                        f"🚨 {symbol} OI SURGE: {change:+.2f}%"
                    )

            # Check Volume spikes
            for vol in all_data['volume_data']:
                if vol.get('alert_level') in ['critical', 'high'] and vol.get('is_spike'):
                    symbol = vol['symbol']
                    change = vol['change_percent']
                    critical_alerts.append(
                        f"🚨 {symbol} VOLUME SPIKE: {change:+.2f}%"
                    )

            # Check Liquidation events
            for hm in all_data['heatmap_data']:
                if hm.get('alert_level') in ['critical', 'high']:
                    symbol = hm['symbol']
                    liq_24h = hm.get('liquidations_24h', {}).get('total_amount', 0)
                    if liq_24h > self.config.LIQUIDATION_THRESHOLD * 10:
                        critical_alerts.append(
                            f"🚨 {symbol} HIGH LIQUIDATIONS: ${liq_24h/1e6:.1f}M in 24h"
                        )

            # Send critical alerts
            if critical_alerts:
                message = "⚠️ CRITICAL CRYPTO ALERTS ⚠️\n\n" + "\n".join(critical_alerts)
                logger.warning(f"Critical alerts detected: {len(critical_alerts)}")
                await self.alert_manager.send_alert(message, "CRITICAL Crypto Alert")

        except Exception as e:
            logger.error(f"Error checking critical alerts: {e}", exc_info=True)

    async def run_once(self):
        """Run the bot once (for testing or manual execution)"""
        logger.info("Running crypto alert bot (single run)")
        await self.generate_and_send_report()

    async def run_scheduled(self):
        """Run bot on a schedule"""
        logger.info("Starting crypto alert bot in scheduled mode")
        logger.info(f"Monitored assets: {', '.join(self.config.MONITORED_ASSETS)}")
        logger.info(f"Check interval: {self.config.CHECK_INTERVAL} seconds")
        logger.info(f"Daily report time: {self.config.DAILY_REPORT_TIME}")

        self.running = True

        # Parse daily report time
        report_hour, report_minute = map(int, self.config.DAILY_REPORT_TIME.split(':'))
        daily_report_sent = False

        while self.running:
            try:
                current_time = datetime.now()
                current_hour = current_time.hour
                current_minute = current_time.minute

                # Check if it's time for daily report
                if current_hour == report_hour and current_minute == report_minute:
                    if not daily_report_sent:
                        logger.info("📅 Time for daily report")
                        await self.generate_and_send_report()
                        daily_report_sent = True
                else:
                    # Reset flag when we're past the report time
                    if daily_report_sent and (current_hour != report_hour or current_minute != report_minute):
                        daily_report_sent = False

                # Check for critical alerts (every cycle)
                await self.check_critical_alerts()

                # Wait for next check
                logger.info(f"Waiting {self.config.CHECK_INTERVAL} seconds until next check...")
                await asyncio.sleep(self.config.CHECK_INTERVAL)

            except asyncio.CancelledError:
                logger.info("Bot task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                await asyncio.sleep(60)  # Wait a minute before retrying

        await self._shutdown()

    async def _shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down crypto alert bot...")

        # Close all connections
        await self.client.close()
        await self.news_aggregator.close()
        await self.alert_manager.close()

        logger.info("Shutdown complete")


async def main():
    """Main entry point"""
    bot = CryptoAlertBot()

    # Check command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == 'once':
            # Run once
            await bot.run_once()
        elif command == 'test':
            # Test mode - run all checks and print report
            logger.info("Running in TEST mode")
            await bot.run_once()
        else:
            logger.error(f"Unknown command: {command}")
            logger.info("Usage: python crypto_alert_bot.py [once|test]")
            logger.info("  once  - Run once and exit")
            logger.info("  test  - Run in test mode")
            logger.info("  (no args) - Run in scheduled mode")
            sys.exit(1)
    else:
        # Run in scheduled mode
        await bot.run_scheduled()


if __name__ == "__main__":
    try:
        print("""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║              🚀 CRYPTO ALERT BOT 🚀                          ║
║                                                               ║
║  Monitoring: BTC, ETH, SOL                                   ║
║  Data Source: Coinglass                                      ║
║                                                               ║
║  Features:                                                    ║
║    📊 Open Interest Surge Detection                          ║
║    📈 Volume Spike Analysis                                  ║
║    🔥 Liquidation Heatmap Monitoring                         ║
║    📰 News Aggregation (Crypto, Political, Market)           ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
        """)

        asyncio.run(main())

    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
