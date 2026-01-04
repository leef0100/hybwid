import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    POLYMARKET_API_KEY = os.getenv('POLYMARKET_API_KEY', '')
    POLYMARKET_SECRET = os.getenv('POLYMARKET_SECRET', '')
    POLYMARKET_PASSPHRASE = os.getenv('POLYMARKET_PASSPHRASE', '')

    INITIAL_CAPITAL = float(os.getenv('INITIAL_CAPITAL', 10000))
    MAX_POSITION_SIZE = float(os.getenv('MAX_POSITION_SIZE', 0.1))
    MAX_TOTAL_EXPOSURE = float(os.getenv('MAX_TOTAL_EXPOSURE', 0.5))

    ENABLE_BACKTESTING = os.getenv('ENABLE_BACKTESTING', 'true').lower() == 'true'
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

    POLYMARKET_API_URL = "https://clob.polymarket.com"
    GAMMA_MARKETS_ENDPOINT = "https://gamma-api.polymarket.com"
