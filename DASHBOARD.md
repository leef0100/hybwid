# 📊 Live Trading Dashboard

Beautiful web-based dashboard for monitoring your Polymarket trading bot in real-time.

## Features

- 📈 **Live Portfolio Chart** - See your PnL update in real-time
- 💼 **Positions & Trades** - Track all open positions and recent trades
- 🎯 **Market Monitor** - See all monitored markets with prices
- 🚨 **Real-Time Alerts** - Color-coded alerts for opportunities
- 📊 **Strategy Performance** - Compare strategy effectiveness
- 🔄 **Auto-Refresh** - Updates every 5 seconds

## Screenshots

The dashboard shows:
- Portfolio value with profit/loss
- Live PnL chart
- Open positions table
- Recent trades feed
- Monitored markets with categories
- Real-time alert stream
- Strategy performance metrics

## Setup

1. **Install dependencies** (if not already done):
```bash
pip3 install -r requirements.txt
```

This installs Streamlit and Plotly for the dashboard.

2. **That's it!** No additional configuration needed.

## Running the Dashboard

### Option 1: Two Terminals (Recommended)

**Terminal 1** - Run the bot:
```bash
python3 bot.py
```

**Terminal 2** - Run the dashboard:
```bash
streamlit run dashboard.py
```

The dashboard will open automatically at `http://localhost:8501`

### Option 2: Background Bot + Dashboard

Run the bot in background, then open dashboard:

```bash
# Run bot in background
nohup python3 bot.py > bot.log 2>&1 &

# Open dashboard
streamlit run dashboard.py
```

## Using the Dashboard

### Top Metrics
- **Portfolio Value** - Current total value with % change
- **Total PnL** - Profit/Loss since start
- **Open Positions** - Number of active positions
- **Available Cash** - Cash available for trading

### Tabs

#### 📈 Performance
- Portfolio value chart over time
- Win rate statistics
- Total trades executed
- Average trade size

#### 💼 Positions & Trades
- **Left**: All open positions with unrealized PnL
- **Right**: Recent trades with buy/sell indicators

#### 🎯 Markets
- All monitored markets
- Search and filter by category
- Shows time to resolution for short-term markets
- Current prices for each outcome
- Urgency indicators for markets <60 min

#### 🚨 Alerts
- Real-time alerts feed
- Color-coded by severity:
  - 🔴 Critical (>80% confidence)
  - 🟠 High (60-80%)
  - 🟡 Warning (40-60%)
  - 🟢 Info
- Filter by alert level
- Shows timestamp and details

#### 📊 Strategies
- Performance of each strategy
- Signals generated count
- Enabled/disabled status

### Settings (Sidebar)

- **Auto-refresh** - Toggle 5-second auto-refresh
- **Show all markets** - Show more than top 20
- Quick stats summary

### Tips

1. **Keep both running**: The bot generates data, the dashboard displays it
2. **Auto-refresh ON**: See updates in real-time (every 5 seconds)
3. **Filter alerts**: Focus on high/critical alerts for best opportunities
4. **Watch short-term markets**: Markets <60 min show urgency bars

## How It Works

1. Bot runs and trades
2. Bot saves state to `data/bot_state.json` every 5 minutes
3. Bot writes alerts to `data/alerts.jsonl` in real-time
4. Dashboard reads these files and displays them
5. Dashboard auto-refreshes every 5 seconds

## Troubleshooting

**Dashboard shows "Bot not running"**
- Make sure `python3 bot.py` is running in another terminal
- Wait 5 minutes for first snapshot
- Check if `data/bot_state.json` exists

**No alerts showing**
- Alerts appear as the bot finds opportunities
- Try running for 10-15 minutes
- Lower alert filters to see all levels

**Port already in use**
```bash
streamlit run dashboard.py --server.port 8502
```

**Dashboard not updating**
- Check "Auto-refresh" is enabled in sidebar
- Manually click "Refresh Now" button
- Make sure bot is still running

## Stopping

**Stop the bot:**
```bash
# Find the process
ps aux | grep bot.py

# Kill it (or just Ctrl+C in terminal)
kill <process_id>
```

**Stop the dashboard:**
Just close the browser tab, then press `Ctrl+C` in terminal

## Example Session

```bash
# Terminal 1
$ python3 bot.py
02:43:00 | INFO | Starting bot in LIVE mode
02:43:00 | INFO | Initial capital: $10,000.00
02:43:02 | INFO | Monitoring 12 markets
02:43:02 | INFO | 📊 Priority: ⚡Short-term > 🏈Sports > 🪙Crypto
# Bot runs continuously...

# Terminal 2
$ streamlit run dashboard.py

  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.1.x:8501

# Dashboard opens in browser automatically
```

## Advanced: Run on Server

If running on a remote server:

```bash
# SSH with port forwarding
ssh -L 8501:localhost:8501 user@your-server

# Then run dashboard on server
streamlit run dashboard.py
```

Access at `http://localhost:8501` on your local machine.

---

**Enjoy your live trading dashboard!** 🚀

Watch your bot find arbitrage opportunities and make trades in real-time with a beautiful, professional interface.
