"""Alert Manager for generating and sending crypto alerts"""

import aiohttp
import logging
import smtplib
import json
from typing import Dict, List, Optional
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


class AlertManager:
    """Manages alert generation and delivery via multiple channels"""

    def __init__(self, config):
        """
        Args:
            config: CryptoAlertConfig instance
        """
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None

    async def _ensure_session(self):
        """Ensure aiohttp session exists"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()

    def generate_daily_report(
        self,
        oi_data: List[Dict],
        volume_data: List[Dict],
        heatmap_data: List[Dict],
        news_data: Dict[str, List[Dict]]
    ) -> str:
        """
        Generate comprehensive daily report

        Args:
            oi_data: Open Interest analysis results
            volume_data: Volume analysis results
            heatmap_data: Heatmap analysis results
            news_data: News aggregation results

        Returns:
            Formatted report string
        """
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("📊 CRYPTO ALERT BOT - DAILY REPORT")
        report_lines.append(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        report_lines.append("=" * 80)
        report_lines.append("")

        # Executive Summary
        report_lines.append("📋 EXECUTIVE SUMMARY")
        report_lines.append("-" * 80)
        critical_alerts = self._count_critical_alerts(oi_data, volume_data, heatmap_data)
        report_lines.append(f"   Critical Alerts: {critical_alerts['critical']}")
        report_lines.append(f"   High Alerts: {critical_alerts['high']}")
        report_lines.append(f"   Medium Alerts: {critical_alerts['medium']}")
        report_lines.append("")

        # Open Interest Section
        report_lines.append("🔍 OPEN INTEREST ANALYSIS")
        report_lines.append("-" * 80)
        for oi in oi_data:
            if oi.get('status') == 'error':
                continue

            symbol = oi['symbol']
            change_pct = oi.get('change_percent', 0)
            alert_level = oi.get('alert_level', 'info')
            trend = oi.get('trend', 'unknown')

            emoji = self._get_alert_emoji(alert_level)
            direction_emoji = "📈" if change_pct > 0 else "📉"

            report_lines.append(f"{emoji} {symbol}:")
            report_lines.append(f"   {direction_emoji} Change: {change_pct:+.2f}%")
            report_lines.append(f"   Trend: {trend.upper()}")
            report_lines.append(f"   Current OI: ${oi.get('current_oi', 0):,.0f}")

            if oi.get('is_surge'):
                report_lines.append(f"   ⚠️  OI SURGE DETECTED!")

            report_lines.append("")

        # Volume Section
        report_lines.append("📊 VOLUME ANALYSIS")
        report_lines.append("-" * 80)
        for vol in volume_data:
            if vol.get('status') == 'error':
                continue

            symbol = vol['symbol']
            change_pct = vol.get('change_percent', 0)
            alert_level = vol.get('alert_level', 'info')
            trend = vol.get('trend', 'unknown')
            volume_score = vol.get('volume_score', 0)

            emoji = self._get_alert_emoji(alert_level)

            report_lines.append(f"{emoji} {symbol}:")
            report_lines.append(f"   Change: {change_pct:+.2f}%")
            report_lines.append(f"   Trend: {trend.upper()}")
            report_lines.append(f"   24h Volume: ${vol.get('volume_24h', 0):,.0f}")
            report_lines.append(f"   Volume Score: {volume_score}/100")

            if vol.get('is_spike'):
                report_lines.append(f"   ⚠️  VOLUME SPIKE DETECTED!")

            report_lines.append("")

        # Heatmap Section
        report_lines.append("🔥 LIQUIDATION HEATMAP ANALYSIS")
        report_lines.append("-" * 80)
        for hm in heatmap_data:
            if hm.get('status') == 'error':
                continue

            symbol = hm['symbol']
            alert_level = hm.get('alert_level', 'info')
            current_price = hm.get('current_price', 0)

            emoji = self._get_alert_emoji(alert_level)

            report_lines.append(f"{emoji} {symbol}:")
            if current_price > 0:
                report_lines.append(f"   Current Price: ${current_price:,.2f}")

            # Key levels
            key_levels = hm.get('key_levels', {})
            support_levels = key_levels.get('support_levels', [])
            resistance_levels = key_levels.get('resistance_levels', [])

            if support_levels:
                nearest_support = support_levels[0]
                report_lines.append(
                    f"   📍 Nearest Support: ${nearest_support['price']:,.2f} "
                    f"({nearest_support['distance_pct']:.2f}% away)"
                )

            if resistance_levels:
                nearest_resistance = resistance_levels[0]
                report_lines.append(
                    f"   📍 Nearest Resistance: ${nearest_resistance['price']:,.2f} "
                    f"({nearest_resistance['distance_pct']:.2f}% away)"
                )

            # 24h liquidations
            liq_24h = hm.get('liquidations_24h', {})
            total_liq = liq_24h.get('total_amount', 0)
            if total_liq > 0:
                report_lines.append(
                    f"   💥 24h Liquidations: ${total_liq/1e6:.1f}M "
                    f"(Longs: ${liq_24h.get('total_long', 0)/1e6:.1f}M, "
                    f"Shorts: ${liq_24h.get('total_short', 0)/1e6:.1f}M)"
                )

            # Insights
            insights = hm.get('insights', [])
            if insights:
                report_lines.append("   💡 Insights:")
                for insight in insights[:3]:
                    report_lines.append(f"      • {insight}")

            report_lines.append("")

        # News Section
        report_lines.append("📰 NEWS & UPDATES")
        report_lines.append("-" * 80)

        # Political news
        political_news = news_data.get('political', [])
        if political_news:
            report_lines.append("🏛️  Political & Regulatory:")
            for item in political_news[:5]:
                report_lines.append(f"   • {item.get('title', '')}")
                report_lines.append(f"     {item.get('url', '')}")
            report_lines.append("")

        # Market news
        market_news = news_data.get('market', [])
        if market_news:
            report_lines.append("📈 Market Updates:")
            for item in market_news[:5]:
                sentiment = item.get('sentiment', '')
                emoji = "📈" if sentiment == "positive" else "📉" if sentiment == "negative" else "📊"
                report_lines.append(f"   {emoji} {item.get('title', '')}")
                report_lines.append(f"     {item.get('url', '')}")
            report_lines.append("")

        # General crypto news
        crypto_news = news_data.get('crypto', [])
        if crypto_news:
            report_lines.append("🪙 Crypto News:")
            for item in crypto_news[:5]:
                report_lines.append(f"   • {item.get('title', '')}")
                report_lines.append(f"     {item.get('url', '')}")
            report_lines.append("")

        # Footer
        report_lines.append("=" * 80)
        report_lines.append("🤖 Generated by Crypto Alert Bot")
        report_lines.append("=" * 80)

        return "\n".join(report_lines)

    def _count_critical_alerts(
        self,
        oi_data: List[Dict],
        volume_data: List[Dict],
        heatmap_data: List[Dict]
    ) -> Dict[str, int]:
        """Count alerts by severity level"""
        counts = {
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
            'info': 0
        }

        all_data = oi_data + volume_data + heatmap_data

        for item in all_data:
            alert_level = item.get('alert_level', 'info')
            if alert_level in counts:
                counts[alert_level] += 1

        return counts

    def _get_alert_emoji(self, alert_level: str) -> str:
        """Get emoji for alert level"""
        emoji_map = {
            'critical': '🚨',
            'high': '⚠️',
            'medium': '⚡',
            'low': 'ℹ️',
            'info': '📊'
        }
        return emoji_map.get(alert_level, '📊')

    async def send_telegram_alert(self, message: str) -> bool:
        """Send alert via Telegram"""
        if not self.config.ENABLE_TELEGRAM:
            return False

        if not self.config.TELEGRAM_BOT_TOKEN or not self.config.TELEGRAM_CHAT_ID:
            logger.warning("Telegram credentials not configured")
            return False

        await self._ensure_session()

        url = f"https://api.telegram.org/bot{self.config.TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': self.config.TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'Markdown',
            'disable_web_page_preview': True
        }

        try:
            async with self.session.post(url, json=payload, ssl=False) as response:
                if response.status == 200:
                    logger.info("Telegram alert sent successfully")
                    return True
                else:
                    logger.error(f"Telegram API error: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Error sending Telegram alert: {e}")
            return False

    async def send_discord_alert(self, message: str) -> bool:
        """Send alert via Discord webhook"""
        if not self.config.ENABLE_DISCORD:
            return False

        if not self.config.DISCORD_WEBHOOK_URL:
            logger.warning("Discord webhook URL not configured")
            return False

        await self._ensure_session()

        payload = {
            'content': message[:2000]  # Discord has a 2000 char limit
        }

        try:
            async with self.session.post(
                self.config.DISCORD_WEBHOOK_URL,
                json=payload,
                ssl=False
            ) as response:
                if response.status in [200, 204]:
                    logger.info("Discord alert sent successfully")
                    return True
                else:
                    logger.error(f"Discord webhook error: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Error sending Discord alert: {e}")
            return False

    def send_email_alert(self, subject: str, body: str) -> bool:
        """Send alert via email"""
        if not self.config.ENABLE_EMAIL:
            return False

        if not all([
            self.config.EMAIL_FROM,
            self.config.EMAIL_TO,
            self.config.EMAIL_PASSWORD
        ]):
            logger.warning("Email credentials not configured")
            return False

        try:
            msg = MIMEMultipart()
            msg['From'] = self.config.EMAIL_FROM
            msg['To'] = self.config.EMAIL_TO
            msg['Subject'] = subject

            msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP(self.config.EMAIL_SMTP_SERVER, self.config.EMAIL_SMTP_PORT)
            server.starttls()
            server.login(self.config.EMAIL_FROM, self.config.EMAIL_PASSWORD)
            server.send_message(msg)
            server.quit()

            logger.info("Email alert sent successfully")
            return True

        except Exception as e:
            logger.error(f"Error sending email alert: {e}")
            return False

    def print_to_console(self, report: str):
        """Print alert to console"""
        if self.config.ENABLE_CONSOLE:
            print("\n" + report + "\n")
            logger.info("Report printed to console")

    async def send_alert(self, report: str, subject: str = "Crypto Alert"):
        """Send alert via all enabled channels"""
        # Console
        self.print_to_console(report)

        # Telegram
        if self.config.ENABLE_TELEGRAM:
            await self.send_telegram_alert(report)

        # Discord
        if self.config.ENABLE_DISCORD:
            await self.send_discord_alert(report)

        # Email
        if self.config.ENABLE_EMAIL:
            self.send_email_alert(subject, report)

    def save_report(self, report: str, filename: Optional[str] = None):
        """Save report to file"""
        import os

        # Ensure data directory exists
        os.makedirs(self.config.DATA_DIR, exist_ok=True)

        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{self.config.DATA_DIR}/report_{timestamp}.txt"

        try:
            with open(filename, 'w') as f:
                f.write(report)
            logger.info(f"Report saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving report: {e}")

    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
