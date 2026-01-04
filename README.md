# Polymarket Paper Trading Bot

A comprehensive paper trading bot for Polymarket research and strategy development. This bot allows you to test trading strategies without risking real money.

## ⚠️ Disclaimer

This bot is for **RESEARCH AND EDUCATIONAL PURPOSES ONLY**. It simulates trades without executing real transactions. Always do your own research and understand the risks before trading with real money.

## Features

- 📊 **Paper Trading Engine** - Simulate trades without real money
- 🤖 **6 Trading Strategies** - Value, arbitrage, spread, cross-market, scalping, and high-frequency
- ⚡ **Short-Term Focus** - Specialized for 15min-1hr markets (live events, in-play betting)
- 🏈 **Sports Win Streak Analysis** - Detect overvalued/undervalued teams based on streaks
- 🪙 **Crypto Focus** - Specialized filtering for BTC, ETH, SOL markets
- 🎬 **Entertainment Markets** - Track sports, pop culture, and entertainment opportunities
- 📈 **Real-time Monitoring** - Track up to 40 markets with price history
- 📉 **Backtesting** - Test strategies on historical data
- 🛡️ **Risk Management** - Built-in position sizing and exposure limits
- 📊 **Performance Analytics** - Track and analyze portfolio performance
- 🔍 **Smart Market Discovery** - Priority: Short-term > Sports > Crypto > Entertainment
- ⚡ **Inefficiency Detection** - Statistical analysis to detect mispricing
- 🚨 **Real-time Alerts** - Get notified of arbitrage opportunities and signals
- 🔄 **Cross-Market Arbitrage** - Detect same events priced differently
- 📊 **Time-Based Filtering** - Extract and prioritize by time to resolution
- 🏆 **Sports Analytics** - Team performance, momentum, and streak tracking

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

### Try the Demo ⭐ NEW

See all the new features in action:

```bash
python demo_arbitrage_bot.py
```

This demo showcases:
- Market categorization (crypto vs entertainment)
- Inefficiency detection
- Cross-market arbitrage
- Scalping strategy
- Real-time alert system

### Run Live Paper Trading

```bash
python bot.py
```

This will:
- Discover active markets with sufficient volume
- **⚡ PRIORITIZE: Short-term markets (15min-1hr) resolving soon**
- **🏈 Focus on sports with win streak analysis**
- **🪙 Track crypto (BTC/ETH/SOL) volatility**
- Monitor up to 40 markets in real-time
- Detect inefficiencies and arbitrage opportunities
- Execute paper trades based on 6 strategies
- Generate real-time alerts for opportunities
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
├── bot.py                          # Main bot orchestrator
├── demo_arbitrage_bot.py           # ⭐ NEW: Feature demonstration
├── config.py                       # Configuration
├── requirements.txt                # Dependencies
│
├── src/
│   ├── api/
│   │   └── polymarket_client.py   # Polymarket API client
│   │
│   ├── engine/
│   │   ├── paper_trader.py        # Paper trading engine
│   │   ├── risk_manager.py        # Risk management
│   │   ├── market_monitor.py      # Real-time monitoring
│   │   └── backtester.py          # Backtesting framework
│   │
│   ├── strategies/
│   │   ├── value_strategy.py           # Value-based trading
│   │   ├── arbitrage_strategy.py       # YES/NO arbitrage
│   │   ├── cross_market_arbitrage.py   # ⭐ NEW: Cross-market detection
│   │   └── scalping_strategy.py        # ⭐ NEW: Momentum & mean reversion
│   │
│   ├── analytics/
│   │   ├── portfolio_tracker.py        # Performance tracking
│   │   └── inefficiency_detector.py    # ⭐ NEW: Statistical analysis
│   │
│   └── utils/
│       ├── logger.py                   # Logging setup
│       ├── market_categorizer.py       # ⭐ NEW: Market filtering
│       └── alert_system.py             # ⭐ NEW: Real-time alerts
│
├── examples/                      # Example scripts
├── data/                          # Output data and reports
│   └── alerts.jsonl              # ⭐ NEW: Alert log
└── logs/                          # Log files
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
Exploits mispricing between YES/NO outcomes in binary markets. When YES + NO prices don't sum to 1.0, there's a guaranteed profit opportunity.

Configuration:
```python
{
    'min_arb_edge': 0.02,    # Minimum arbitrage edge (2%)
    'position_size': 100,    # Position size per trade
}
```

### 3. Spread Arbitrage Strategy
Targets markets with wide bid-ask spreads for mean-reversion opportunities.

Configuration:
```python
{
    'min_spread': 0.05,      # Minimum spread width (5%)
    'position_size': 50,     # Position size per trade
}
```

### 4. Cross-Market Arbitrage ⭐ NEW
Detects when similar markets have different prices for essentially the same event. For example, if two markets ask "Will BTC hit $100k?" but have different prices, we can exploit the cheaper one.

Configuration:
```python
{
    'min_price_diff': 0.05,       # Minimum 5% price difference
    'similarity_threshold': 0.7,  # How similar questions need to be (70%)
    'position_size': 100,
    'max_markets_compare': 50     # Compare across 50 markets max
}
```

**How it works:**
- Builds a cache of similar markets
- Uses text similarity to find related events
- Compares prices and generates signals for underpriced markets
- Particularly effective for crypto markets with multiple time horizons

### 5. Scalping Strategy ⭐ NEW
High-frequency strategy that exploits short-term price movements and mean reversion.

Configuration:
```python
{
    'momentum_threshold': 0.03,    # 3% price movement triggers signal
    'volume_spike_multiple': 2.0,  # 2x average volume = spike
    'max_spread': 0.03,            # Only trade tight spreads (< 3%)
    'lookback_periods': 5,         # Compare to last 5 updates
    'position_size': 50,
    'min_edge': 0.02              # Minimum 2% edge
}
```

**How it works:**
- **Momentum Detection**: Buys into strong upward moves, sells into downward moves
- **Mean Reversion**: Fades extreme price deviations from recent average
- **Spread Filter**: Only trades liquid markets with tight spreads
- Tracks price history and calculates z-scores for statistical arbitrage

### 6. High-Frequency Strategy ⭐ NEW
Ultra-short-term strategy for markets resolving in 15-60 minutes. Ideal for live sports events, breaking news, and time-sensitive opportunities.

Configuration:
```python
{
    'max_minutes': 60,            # Only trade markets <60 min
    'min_minutes': 5,             # Minimum 5 min buffer
    'urgency_boost': 0.2,         # Confidence boost for urgent markets
    'position_size': 75,
    'min_edge': 0.03,             # 3% minimum edge
    'use_sports_analysis': True   # Enable win streak detection
}
```

**How it works:**
- **Time Extraction**: Automatically detects market resolution time from questions
- **Sports Win Streaks**: Detects teams on hot/cold streaks (3+ wins/losses)
  - **Hot streak** (3+ wins) = Team often OVERVALUED by public → **FADE** (bet against)
  - **Cold streak** (3+ losses) = Team often UNDERVALUED → **BUY**
  - Applies "regression to the mean" theory
- **Urgency Pricing**: Markets <15 min often have stale prices → opportunity
- **Liquidity Scalping**: Tight spreads (<2%) + short time = quick profit potential

**Example inefficiencies detected:**
```
Team with 5-game win streak priced at 0.75 (75%)
→ Fair value (regressed to mean): 0.60
→ Signal: FADE team, bet against (No outcome)
→ Edge: 15% overvaluation
```

## Market Categorization ⭐ NEW

The bot automatically categorizes markets into:

- **Crypto Markets**: BTC, ETH, SOL binary options and price predictions
- **Entertainment**: Movies, music, awards, celebrities
- **Sports**: NFL, NBA, MLB, FIFA, Olympics
- **Politics**: Elections, legislation, policy
- **Other**: General markets

The bot **prioritizes crypto and entertainment markets** during discovery, monitoring up to 10 of each category.

### Using the Categorizer

```python
from src.utils.market_categorizer import MarketCategorizer, MarketCategory

categorizer = MarketCategorizer()

# Categorize a market
category = categorizer.categorize(market)

# Check if crypto
is_crypto = categorizer.is_crypto_market(market)

# Get crypto asset (BTC, ETH, SOL)
asset = categorizer.get_crypto_asset(market)  # Returns 'BTC', 'ETH', 'SOL', or None

# Filter markets
crypto_markets = categorizer.filter_markets(
    markets,
    categories=[MarketCategory.CRYPTO_BTC, MarketCategory.CRYPTO_ETH],
    min_volume=10000
)
```

## Inefficiency Detection ⭐ NEW

Statistical analysis detects various market inefficiencies:

### Types of Inefficiencies

1. **Probability Sum** - YES + NO prices don't equal 1.0 (arbitrage!)
2. **Wide Spreads** - Excessive bid-ask spreads (> 5%)
3. **Statistical Arbitrage** - Price > 2 standard deviations from mean
4. **Volume Imbalance** - One-sided order flow (future feature)

### Using the Detector

```python
from src.analytics.inefficiency_detector import InefficiencyDetector

detector = InefficiencyDetector()

# Detect all inefficiencies
inefficiencies = detector.detect_all(market, prices)

for ineff in inefficiencies:
    print(f"Type: {ineff.type}")
    print(f"Severity: {ineff.severity}")  # 0 to 1
    print(f"Description: {ineff.description}")

# Get stats
stats = detector.get_inefficiency_stats()
print(stats)  # {'total': 45, 'by_type': {...}, 'avg_severity': 0.65}

# Get recent high-severity inefficiencies
recent = detector.get_recent_inefficiencies(minutes=60, min_severity=0.7)
```

## Time-Based Filtering ⭐ NEW

The bot automatically extracts time to resolution from market questions and prioritizes short-term markets.

### Supported Time Patterns

- **Specific times**: "by 3:00 PM", "at 12:30"
- **Minutes**: "in 15 minutes", "next 30 minutes"
- **Hours**: "in 1 hour", "within 2 hours"
- **Game periods**: "first quarter", "halftime", "2nd half"
- **Relative times**: "half hour", "quarter hour"

### Time Intervals

Markets are categorized by resolution time:
- **15min**: Ultra-urgent opportunities
- **30min**: High-frequency trades
- **1hour**: Short-term positions
- **2-4 hours**: Medium-term
- **1 day+**: Long-term (lower priority)

### Using the Time Filter

```python
from src.utils.time_filter import TimeBasedFilter

time_filter = TimeBasedFilter({'max_minutes': 60, 'min_minutes': 5})

# Check if market is short-term
is_short_term = time_filter.is_short_term(market)

# Get time to resolution
minutes = time_filter.extract_time_to_resolution(market)

# Calculate urgency score (0-1)
urgency = time_filter.get_urgency_score(market)  # Higher = more urgent

# Filter markets
short_term_markets = time_filter.filter_short_term_markets(all_markets)
```

## Sports Win Streak Analytics ⭐ NEW

Sophisticated sports analytics that detect market inefficiencies based on team performance and public betting psychology.

### Win Streak Theory

**The Problem**: Public overreacts to win/loss streaks
- Team wins 5 games in a row → Public overvalues them
- Team loses 5 games → Public undervalues them

**The Opportunity**: Regression to the mean
- Hot streaks end (team regresses to true skill level)
- Cold streaks end (variance evens out)
- Markets overprice streaks → **exploitable edge**

### How It Works

```python
from src.analytics.sports_analytics import SportsAnalytics

sports = SportsAnalytics({
    'hot_streak_threshold': 3,          # 3+ wins = hot
    'cold_streak_threshold': 3,          # 3+ losses = cold
    'streak_overvalue_threshold': 0.15   # 15% overvaluation threshold
})

# Detect inefficiency
inefficiency = sports.detect_win_streak_inefficiency(market, prices)

if inefficiency:
    print(inefficiency['recommendation'])
    # Output: "FADE Lakers (hot streak overvalued)"
    # or: "BUY Bulls (cold streak undervalued)"
```

### Example Scenarios

**Scenario 1: Hot Streak Overvalue**
```
Team: Lakers (5-game win streak)
Market price: 0.75 (75% implied probability to win)
True win rate: 0.60 (60% long-term average)
Regressed fair value: 0.55 (regression to mean)
→ Overvalued by 20%
→ Signal: FADE Lakers (bet No or bet opponent)
```

**Scenario 2: Cold Streak Undervalue**
```
Team: Celtics (4-game losing streak)
Market price: 0.30 (30% implied probability)
True win rate: 0.55 (55% long-term average)
Regressed fair value: 0.525
→ Undervalued by 22.5%
→ Signal: BUY Celtics (bet Yes)
```

### Supported Analysis

- **Win streak detection**: Identifies 3+ game winning streaks
- **Loss streak detection**: Identifies 3+ game losing streaks
- **Momentum shifts**: Sharp price movements indicating news
- **Team extraction**: Automatically extracts team names from questions
- **League detection**: NFL, NBA, MLB, NHL, EPL, Champions League, etc.

## Real-Time Alerts ⭐ NEW

Get notified of trading opportunities in real-time with color-coded alerts.

### Alert Levels
- 🟢 **INFO**: General information
- 🟡 **WARNING**: Moderate opportunities (confidence 40-60%)
- 🟠 **HIGH**: Strong signals (confidence 60-80%)
- 🔴 **CRITICAL**: Exceptional opportunities (confidence > 80%)

Alerts are:
- Logged to console with color coding
- Saved to `data/alerts.jsonl` for analysis
- Categorized by type (arbitrage, inefficiency, crypto, signals)

### Example Output
```
[12:34:56] 🔴 [CRITICAL] Arbitrage: 8.2% edge
           Will BTC hit $100k by EOY?
           Probability sum = 0.918 (< 1.0) - Arbitrage opportunity!

[12:35:12] 🟠 [HIGH] Crypto Alert: BTC
           BUY Yes @ 0.543 (85% confidence)
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