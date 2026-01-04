# Polymarket Paper Trading Bot

A comprehensive paper trading bot for Polymarket research and strategy development. This bot allows you to test trading strategies without risking real money.

## ⚠️ Disclaimer

This bot is for **RESEARCH AND EDUCATIONAL PURPOSES ONLY**. It simulates trades without executing real transactions. Always do your own research and understand the risks before trading with real money.

## Features

- 📊 **Paper Trading Engine** - Simulate trades without real money
- 🤖 **Multiple Strategies** - Value-based, arbitrage, and spread strategies
- 📈 **Real-time Monitoring** - Track markets in real-time
- 📉 **Backtesting** - Test strategies on historical data
- 🛡️ **Risk Management** - Built-in position sizing and exposure limits
- 📊 **Performance Analytics** - Track and analyze portfolio performance
- 🔍 **Market Discovery** - Automatically find interesting markets

## Installation

1. Clone the repository:
```bash
git clone <repo-url>
cd hybwid
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your settings (no API keys needed for paper trading)
```

## Quick Start

### Run Live Paper Trading

```bash
python bot.py
```

This will:
- Discover active markets with sufficient volume
- Monitor markets in real-time
- Execute paper trades based on strategies
- Track portfolio performance

### Run Backtest

```bash
python bot.py backtest
```

This will test your strategies on historical market data.

### Explore Markets

```bash
python examples/market_explorer.py
```

Browse available markets and see current prices.

### Simple Backtest Example

```bash
python examples/simple_backtest.py
```

Compare different strategies on a sample of markets.

## Configuration

Edit `.env` or `config.py` to adjust:

- `INITIAL_CAPITAL` - Starting capital for paper trading (default: $10,000)
- `MAX_POSITION_SIZE` - Maximum position size as fraction of capital (default: 0.1 = 10%)
- `MAX_TOTAL_EXPOSURE` - Maximum total exposure (default: 0.5 = 50%)
- `LOG_LEVEL` - Logging verbosity (DEBUG, INFO, WARNING, ERROR)

## Project Structure

```
hybwid/
├── bot.py                 # Main bot orchestrator
├── config.py              # Configuration
├── requirements.txt       # Dependencies
│
├── src/
│   ├── api/              # Polymarket API client
│   ├── engine/           # Trading engine, risk management
│   ├── strategies/       # Trading strategies
│   ├── analytics/        # Performance tracking
│   └── utils/            # Utilities and logging
│
├── examples/             # Example scripts
├── data/                 # Output data and reports
└── logs/                 # Log files
```

## Strategies

### 1. Value Strategy
Identifies undervalued outcomes based on price discrepancies.

Configuration:
```python
{
    'min_edge': 0.05,        # Minimum edge to trade (5%)
    'max_price': 0.7,        # Maximum price to buy
    'min_price': 0.1,        # Minimum price to buy
}
```

### 2. Arbitrage Strategy
Exploits mispricing between YES/NO outcomes in binary markets.

Configuration:
```python
{
    'min_arb_edge': 0.02,    # Minimum arbitrage edge (2%)
    'position_size': 100,    # Position size per trade
}
```

### 3. Spread Arbitrage Strategy
Targets markets with wide bid-ask spreads.

Configuration:
```python
{
    'min_spread': 0.05,      # Minimum spread width (5%)
    'position_size': 50,     # Position size per trade
}
```

## Creating Custom Strategies

Extend the `BaseStrategy` class:

```python
from src.strategies.base_strategy import BaseStrategy, Signal

class MyStrategy(BaseStrategy):
    def __init__(self, config=None):
        super().__init__("MyStrategy", config)

    async def analyze(self, market, prices):
        signals = []

        # Your strategy logic here
        # Generate Signal objects for trades

        return signals
```

## Risk Management

The bot includes built-in risk management:

- **Position Size Limits** - Maximum capital per position
- **Exposure Limits** - Maximum total market exposure
- **Daily Loss Limits** - Stop trading after daily loss threshold
- **Maximum Positions** - Limit number of concurrent positions
- **Confidence Thresholds** - Only trade high-confidence signals

## Output

The bot generates:

- **Portfolio Reports** (`data/portfolio_report_*.json`) - Performance metrics
- **Final State** (`data/final_state_*.json`) - Portfolio snapshot
- **Logs** (`logs/bot_*.log`) - Detailed execution logs

## Development

### Running Tests

```bash
# TODO: Add tests
pytest tests/
```

### Adding New Features

1. Create new strategy in `src/strategies/`
2. Add to strategy list in `bot.py`
3. Configure parameters in `.env` or strategy config

## Troubleshooting

**No markets found:**
- Check internet connection
- Polymarket API may be down
- Lower `min_volume` in market discovery

**No trades executing:**
- Strategies may not find opportunities
- Adjust strategy parameters (lower `min_edge`, `min_arb_edge`)
- Check risk management limits

**High rejection rate:**
- Risk limits may be too strict
- Increase `MAX_POSITION_SIZE` or `MAX_TOTAL_EXPOSURE`
- Lower `min_confidence` threshold

## Contributing

This is a research project. Feel free to:
- Add new strategies
- Improve risk management
- Add performance metrics
- Enhance backtesting capabilities

## License

MIT License - See LICENSE file

## Resources

- [Polymarket Documentation](https://docs.polymarket.com/)
- [Polymarket API](https://docs.polymarket.com/)
- [CLOB API Documentation](https://docs.polymarket.com/)

---

**Remember:** This is paper trading only. No real money is at risk. Use this to learn, research, and test strategies before considering real trading.