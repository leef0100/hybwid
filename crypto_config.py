import os
from dotenv import load_dotenv

load_dotenv()


class CryptoAlertConfig:
    """Configuration for Crypto Alert Bot"""

    # Coinglass API Configuration
    COINGLASS_API_KEY = os.getenv('COINGLASS_API_KEY', '')
    COINGLASS_API_URL = "https://open-api.coinglass.com/public/v2"

    # Assets to Monitor
    MONITORED_ASSETS = ['BTC', 'ETH', 'SOL']

    # Alert Thresholds
    OI_SURGE_THRESHOLD = float(os.getenv('OI_SURGE_THRESHOLD', 10.0))  # 10% change
    VOLUME_SURGE_THRESHOLD = float(os.getenv('VOLUME_SURGE_THRESHOLD', 20.0))  # 20% change
    LIQUIDATION_THRESHOLD = float(os.getenv('LIQUIDATION_THRESHOLD', 50000000))  # $50M in liquidations

    # Monitoring Settings
    CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', 3600))  # Check every hour (in seconds)
    DAILY_REPORT_TIME = os.getenv('DAILY_REPORT_TIME', '09:00')  # Daily report at 9 AM
    LOOKBACK_PERIOD = int(os.getenv('LOOKBACK_PERIOD', 24))  # Hours to look back

    # News Settings
    NEWS_SOURCES = os.getenv('NEWS_SOURCES', 'crypto,politics,market').split(',')
    MAX_NEWS_ITEMS = int(os.getenv('MAX_NEWS_ITEMS', 10))

    # Notification Settings
    ENABLE_EMAIL = os.getenv('ENABLE_EMAIL', 'false').lower() == 'true'
    ENABLE_TELEGRAM = os.getenv('ENABLE_TELEGRAM', 'false').lower() == 'true'
    ENABLE_DISCORD = os.getenv('ENABLE_DISCORD', 'false').lower() == 'true'
    ENABLE_CONSOLE = os.getenv('ENABLE_CONSOLE', 'true').lower() == 'true'

    # Telegram Settings
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

    # Discord Settings
    DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL', '')

    # Email Settings
    EMAIL_SMTP_SERVER = os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com')
    EMAIL_SMTP_PORT = int(os.getenv('EMAIL_SMTP_PORT', 587))
    EMAIL_FROM = os.getenv('EMAIL_FROM', '')
    EMAIL_TO = os.getenv('EMAIL_TO', '')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')

    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

    # Data Storage
    DATA_DIR = os.getenv('DATA_DIR', 'data/crypto_alerts')
    CACHE_DIR = os.getenv('CACHE_DIR', 'data/crypto_alerts/cache')
