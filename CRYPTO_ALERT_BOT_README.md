# 🚀 Crypto Alert Bot

A comprehensive cryptocurrency alert system that monitors Bitcoin (BTC), Ethereum (ETH), and Solana (SOL) for significant market events and delivers daily reports.

## ⚡ Features

### Market Monitoring
- **📊 Open Interest (OI) Surge Detection** - Tracks OI changes across exchanges and alerts on significant surges
- **📈 Volume Spike Analysis** - Monitors trading volume and detects unusual activity
- **🔥 Liquidation Heatmap Analysis** - Identifies key support/resistance levels and liquidation risk zones
- **📰 News Aggregation** - Collects crypto, political, and market news from multiple sources

### Data Source
- **Coinglass API** - Professional-grade crypto derivatives data including:
  - Futures Open Interest
  - Trading Volume
  - Liquidation Events
  - Liquidation Heatmaps
  - Funding Rates
  - Long/Short Ratios

### Alert Delivery
- **Console Output** - Real-time console display (enabled by default)
- **Telegram** - Push notifications to your Telegram
- **Discord** - Webhook alerts to Discord channels
- **Email** - Email reports via SMTP

## 📋 Requirements

- Python 3.8+
- Coinglass API Key (get one at [coinglass.com](https://www.coinglass.com))
- Optional: Telegram Bot Token, Discord Webhook, or SMTP credentials for notifications

## 🚀 Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your settings
```

3. Set up your Coinglass API key:
```bash
# In .env file
COINGLASS_API_KEY=your_api_key_here
```

## ⚙️ Configuration

Edit `.env` file to customize settings:

### Alert Thresholds
```bash
OI_SURGE_THRESHOLD=10.0          # % change to trigger OI alert (default: 10%)
VOLUME_SURGE_THRESHOLD=20.0      # % change to trigger volume alert (default: 20%)
LIQUIDATION_THRESHOLD=50000000   # $ threshold for liquidation alerts (default: $50M)
```

### Monitoring Settings
```bash
CHECK_INTERVAL=3600              # Seconds between checks (default: 1 hour)
DAILY_REPORT_TIME=09:00          # Time for daily report (24h format)
LOOKBACK_PERIOD=24               # Hours to analyze (default: 24h)
```

### Notification Channels
Enable/disable notification channels:
```bash
ENABLE_CONSOLE=true              # Console output (always recommended)
ENABLE_TELEGRAM=false            # Telegram notifications
ENABLE_DISCORD=false             # Discord webhook
ENABLE_EMAIL=false               # Email alerts
```

### Telegram Setup
1. Create a bot via [@BotFather](https://t.me/botfather)
2. Get your chat ID via [@userinfobot](https://t.me/userinfobot)
3. Configure in `.env`:
```bash
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
ENABLE_TELEGRAM=true
```

### Discord Setup
1. Create a webhook in your Discord server
2. Configure in `.env`:
```bash
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
ENABLE_DISCORD=true
```

### Email Setup
```bash
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_FROM=your_email@gmail.com
EMAIL_TO=recipient@example.com
EMAIL_PASSWORD=your_app_password
ENABLE_EMAIL=true
```

Note: For Gmail, use [App Passwords](https://support.google.com/accounts/answer/185833)

## 🎯 Usage

### Run Once (Single Report)
Generate and send one report immediately:
```bash
python crypto_alert_bot.py once
```

### Test Mode
Run in test mode to verify configuration:
```bash
python crypto_alert_bot.py test
```

### Scheduled Mode (Recommended)
Run continuously with periodic checks and daily reports:
```bash
python crypto_alert_bot.py
```

This will:
- Check for critical alerts every hour (configurable)
- Generate a comprehensive daily report at 9:00 AM (configurable)
- Send immediate alerts for critical events

### Run as Background Service

#### Using nohup (Linux/Mac):
```bash
nohup python crypto_alert_bot.py > crypto_bot.log 2>&1 &
```

#### Using systemd (Linux):
Create `/etc/systemd/system/crypto-alert-bot.service`:
```ini
[Unit]
Description=Crypto Alert Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/hybwid
ExecStart=/usr/bin/python3 /path/to/hybwid/crypto_alert_bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable crypto-alert-bot
sudo systemctl start crypto-alert-bot
sudo systemctl status crypto-alert-bot
```

## 📊 Sample Report

```
================================================================================
📊 CRYPTO ALERT BOT - DAILY REPORT
🕐 2026-01-15 09:00:00 UTC
================================================================================

📋 EXECUTIVE SUMMARY
--------------------------------------------------------------------------------
   Critical Alerts: 2
   High Alerts: 3
   Medium Alerts: 1

🔍 OPEN INTEREST ANALYSIS
--------------------------------------------------------------------------------
🚨 BTC:
   📈 Change: +12.50%
   Trend: STRONGLY_BULLISH
   Current OI: $45,234,567,890
   ⚠️  OI SURGE DETECTED!

⚡ ETH:
   📉 Change: -3.20%
   Trend: NEUTRAL
   Current OI: $18,456,789,012

📊 VOLUME ANALYSIS
--------------------------------------------------------------------------------
🚨 BTC:
   Change: +35.20%
   Trend: SURGING
   24h Volume: $125,456,789,012
   Volume Score: 85/100
   ⚠️  VOLUME SPIKE DETECTED!

🔥 LIQUIDATION HEATMAP ANALYSIS
--------------------------------------------------------------------------------
⚠️ BTC:
   Current Price: $43,250.00
   📍 Nearest Support: $42,500.00 (1.74% away)
   📍 Nearest Resistance: $44,000.00 (1.73% away)
   💥 24h Liquidations: $85.5M (Longs: $45.2M, Shorts: $40.3M)
   💡 Insights:
      • High liquidation risk: $250.5M in total liquidation levels
      • Heavy liquidations in 24h: $85.5M
      • Identified 3 high-risk liquidation zones

📰 NEWS & UPDATES
--------------------------------------------------------------------------------
🏛️  Political & Regulatory:
   • SEC Announces New Crypto Framework for 2026
     https://...

📈 Market Updates:
   📈 Bitcoin Surges Past $43K on Institutional Demand
     https://...

================================================================================
🤖 Generated by Crypto Alert Bot
================================================================================
```

## 📁 Output

The bot generates and saves:

- **Reports** - `data/crypto_alerts/report_YYYYMMDD_HHMMSS.txt`
- **Logs** - `logs/bot_*.log`
- **Cache** - `data/crypto_alerts/cache/` (API response caching)

## 🔧 Monitored Metrics

### Open Interest
- Total OI across all exchanges
- OI change percentage
- Trend analysis (bullish/bearish)
- Exchange-specific breakdown
- Alert levels (critical/high/medium/low/info)

### Volume
- Current volume vs baseline
- 24-hour total volume
- Volume trend (surging/increasing/stable/decreasing)
- Volume score (0-100)
- Spike detection

### Liquidations & Heatmap
- Liquidation levels and amounts
- Support and resistance identification
- Risk zone detection
- 24-hour liquidation totals
- Long vs short liquidation ratio
- Price distance calculations

### News
- **Crypto News** - General cryptocurrency news
- **Political News** - Regulatory and government-related news
- **Market Updates** - Price movements and trading activity
- Sources: CryptoPanic, CoinDesk, Cointelegraph

## 🎨 Alert Levels

Alerts are categorized by severity:

- 🚨 **Critical** - Immediate attention required (>20% change)
- ⚠️ **High** - Significant event (10-20% change)
- ⚡ **Medium** - Notable activity (5-10% change)
- ℹ️ **Low** - Minor change (<5% change)
- 📊 **Info** - General information

## 🔐 Security Notes

- Never commit your `.env` file with real credentials
- Use app-specific passwords for email (not your main password)
- Rotate API keys regularly
- Store credentials securely
- Use environment variables in production

## 🐛 Troubleshooting

### API Errors
- Verify your Coinglass API key is valid
- Check API rate limits
- Ensure internet connectivity

### No Data Received
- Confirm symbols are supported (BTC, ETH, SOL)
- Check Coinglass API status
- Review logs in `logs/` directory

### Notification Issues
- **Telegram**: Verify bot token and chat ID
- **Discord**: Check webhook URL validity
- **Email**: Confirm SMTP settings and app password

### Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

## 📚 API Documentation

- [Coinglass API Docs](https://docs.coinglass.com/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Discord Webhooks](https://discord.com/developers/docs/resources/webhook)

## 🤝 Contributing

This is part of the hybwid research project. Contributions welcome:
- Add new data sources
- Improve alert logic
- Add new notification channels
- Enhance heatmap analysis

## ⚠️ Disclaimer

This bot is for **INFORMATIONAL AND RESEARCH PURPOSES ONLY**.

- Not financial advice
- Market data may have delays
- Always do your own research (DYOR)
- Cryptocurrency trading carries risk
- Past performance ≠ future results

## 📝 License

MIT License - See LICENSE file

## 🔗 Related Projects

- Main bot: `bot.py` (Polymarket paper trading bot)
- Market Explorer: `examples/market_explorer.py`
- Backtester: `examples/simple_backtest.py`

---

**Built with ❤️ using Coinglass API**

For questions or issues, check the logs or open an issue in the repository.
