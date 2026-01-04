"""
Polymarket Trading Bot - Live Dashboard

A real-time web dashboard showing:
- Live PnL and portfolio value
- Recent trades and positions
- Monitored markets
- Strategy performance
- Real-time alerts
"""

import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import time
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path

# Page config
st.set_page_config(
    page_title="Polymarket Trading Bot",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
    }
    .profit {
        color: #00ff00;
    }
    .loss {
        color: #ff4444;
    }
    .big-font {
        font-size: 24px !important;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Data paths
DATA_DIR = Path("data")
ALERTS_FILE = DATA_DIR / "alerts.jsonl"
STATE_FILE = DATA_DIR / "bot_state.json"

# Initialize session state
if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now()

def load_bot_state():
    """Load current bot state"""
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return None

def load_alerts(limit=100):
    """Load recent alerts"""
    if not ALERTS_FILE.exists():
        return []

    alerts = []
    try:
        with open(ALERTS_FILE, 'r') as f:
            for line in f:
                alerts.append(json.loads(line))
        return alerts[-limit:]  # Return last N alerts
    except:
        return []

def format_currency(value):
    """Format value as currency"""
    return f"${value:,.2f}"

def format_pnl(value):
    """Format PnL with color"""
    color = "profit" if value >= 0 else "loss"
    sign = "+" if value >= 0 else ""
    return f'<span class="{color}">{sign}{format_currency(value)}</span>'

def format_percent(value):
    """Format percentage with color"""
    color = "profit" if value >= 0 else "loss"
    sign = "+" if value >= 0 else ""
    return f'<span class="{color}">{sign}{value:.2f}%</span>'

# Header
st.title("🤖 Polymarket Trading Bot Dashboard")
st.markdown("**Live monitoring of arbitrage opportunities and trading performance**")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")

    auto_refresh = st.checkbox("Auto-refresh (5s)", value=True)
    show_all_markets = st.checkbox("Show all markets", value=False)

    st.markdown("---")
    st.header("📊 Quick Stats")

    state = load_bot_state()
    if state:
        st.metric("Bot Status", "🟢 Running" if state.get('running', False) else "🔴 Stopped")
        st.metric("Strategies", state.get('num_strategies', 0))
        st.metric("Monitored Markets", state.get('num_markets', 0))
    else:
        st.warning("Bot not running")

    st.markdown("---")
    st.markdown("### 🎯 Priority")
    st.markdown("1. ⚡ Short-term (15-60min)")
    st.markdown("2. 🏈 Sports win streaks")
    st.markdown("3. 🪙 Crypto (BTC/ETH/SOL)")
    st.markdown("4. 🎬 Entertainment")

# Main content
if state is None:
    st.error("⚠️ Bot is not running. Start the bot with: `python3 bot.py`")
    st.stop()

# Top metrics
col1, col2, col3, col4 = st.columns(4)

portfolio = state.get('portfolio', {})
initial_capital = state.get('initial_capital', 10000)
portfolio_value = portfolio.get('portfolio_value', initial_capital)
total_pnl = portfolio.get('total_pnl', 0)
total_pnl_pct = portfolio.get('total_pnl_pct', 0)
num_positions = portfolio.get('num_positions', 0)

with col1:
    st.metric(
        "Portfolio Value",
        format_currency(portfolio_value),
        f"{total_pnl_pct:+.2f}%"
    )

with col2:
    pnl_delta = total_pnl
    st.metric(
        "Total PnL",
        format_currency(total_pnl),
        f"{pnl_delta:+.2f}" if abs(pnl_delta) > 0 else "No change"
    )

with col3:
    st.metric(
        "Open Positions",
        num_positions
    )

with col4:
    cash = portfolio.get('cash', initial_capital)
    st.metric(
        "Available Cash",
        format_currency(cash)
    )

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Performance",
    "💼 Positions & Trades",
    "🎯 Markets",
    "🚨 Alerts",
    "📊 Strategies"
])

with tab1:
    st.header("Portfolio Performance")

    # PnL Chart
    snapshots = state.get('portfolio_snapshots', [])
    if snapshots and len(snapshots) > 1:
        df_snapshots = pd.DataFrame(snapshots)
        df_snapshots['timestamp'] = pd.to_datetime(df_snapshots['timestamp'])

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_snapshots['timestamp'],
            y=df_snapshots['portfolio_value'],
            mode='lines+markers',
            name='Portfolio Value',
            line=dict(color='#1f77b4', width=2),
            fill='tozeroy',
            fillcolor='rgba(31, 119, 180, 0.1)'
        ))

        fig.update_layout(
            title="Portfolio Value Over Time",
            xaxis_title="Time",
            yaxis_title="Value ($)",
            hovermode='x unified',
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Not enough data for chart. Keep the bot running to see performance trends.")

    # Performance metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("Win Rate")
        trades = state.get('trades', [])
        if trades:
            winning_trades = sum(1 for t in trades if t.get('pnl', 0) > 0)
            win_rate = (winning_trades / len(trades)) * 100
            st.metric("Win Rate", f"{win_rate:.1f}%")
        else:
            st.metric("Win Rate", "N/A")

    with col2:
        st.subheader("Total Trades")
        st.metric("Trades Executed", len(trades))

    with col3:
        st.subheader("Avg Trade Size")
        if trades:
            avg_size = sum(t.get('size', 0) for t in trades) / len(trades)
            st.metric("Avg Size", f"{avg_size:.0f} shares")
        else:
            st.metric("Avg Size", "N/A")

with tab2:
    st.header("Positions & Recent Trades")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Open Positions")
        positions = state.get('positions', [])

        if positions:
            df_positions = pd.DataFrame(positions)
            df_positions['unrealized_pnl'] = df_positions['unrealized_pnl'].apply(lambda x: f"${x:,.2f}")
            df_positions['size'] = df_positions['size'].astype(int)

            st.dataframe(
                df_positions[['market_id', 'outcome', 'size', 'avg_price', 'unrealized_pnl']],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No open positions")

    with col2:
        st.subheader("💸 Recent Trades")
        trades = state.get('trades', [])[-10:]  # Last 10 trades

        if trades:
            df_trades = pd.DataFrame(trades)
            df_trades['timestamp'] = pd.to_datetime(df_trades['timestamp']).dt.strftime('%H:%M:%S')

            # Color code by action
            def color_action(val):
                color = '#00ff00' if val == 'BUY' else '#ff4444'
                return f'background-color: {color}; color: white'

            styled_df = df_trades[['timestamp', 'action', 'outcome', 'size', 'price']].style.applymap(
                color_action,
                subset=['action']
            )

            st.dataframe(styled_df, use_container_width=True, hide_index=True)
        else:
            st.info("No trades yet")

with tab3:
    st.header("🎯 Monitored Markets")

    markets = state.get('markets', [])

    if markets:
        # Filter options
        col1, col2 = st.columns([3, 1])
        with col1:
            search = st.text_input("🔍 Search markets", "")
        with col2:
            category_filter = st.selectbox(
                "Category",
                ["All", "Crypto", "Sports", "Short-term (<60min)"]
            )

        # Filter markets
        filtered_markets = markets
        if search:
            filtered_markets = [m for m in filtered_markets if search.lower() in m.get('question', '').lower()]

        if category_filter == "Crypto":
            filtered_markets = [m for m in filtered_markets if m.get('category', '').startswith('crypto')]
        elif category_filter == "Sports":
            filtered_markets = [m for m in filtered_markets if m.get('category') == 'sports']
        elif category_filter == "Short-term (<60min)":
            filtered_markets = [m for m in filtered_markets if m.get('is_short_term', False)]

        # Display markets
        for market in filtered_markets[:20 if not show_all_markets else None]:
            with st.expander(f"📊 {market.get('question', 'Unknown')}"):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.write(f"**Category:** {market.get('category', 'unknown')}")
                    st.write(f"**Volume:** ${market.get('volume', 0):,.0f}")

                with col2:
                    if market.get('is_short_term'):
                        minutes = market.get('time_to_resolution', 0)
                        st.write(f"**⚡ Time left:** {minutes} min")
                        urgency = market.get('urgency_score', 0)
                        st.progress(urgency, text=f"Urgency: {urgency:.0%}")
                    else:
                        st.write("**Type:** Long-term")

                with col3:
                    prices = market.get('prices', {})
                    if prices:
                        st.write("**Current Prices:**")
                        for outcome, price in prices.items():
                            st.write(f"  {outcome}: ${price:.3f}")
    else:
        st.info("No markets being monitored. Check if bot is running.")

with tab4:
    st.header("🚨 Real-Time Alerts")

    alerts = load_alerts(limit=50)

    if alerts:
        # Filter by level
        level_filter = st.multiselect(
            "Alert Level",
            ["info", "warning", "high", "critical"],
            default=["high", "critical"]
        )

        filtered_alerts = [a for a in alerts if a.get('level') in level_filter]

        # Display alerts
        for alert in reversed(filtered_alerts):  # Most recent first
            level = alert.get('level', 'info')

            # Emoji and color by level
            level_emoji = {
                'info': '🟢',
                'warning': '🟡',
                'high': '🟠',
                'critical': '🔴'
            }

            level_color = {
                'info': '#28a745',
                'warning': '#ffc107',
                'high': '#fd7e14',
                'critical': '#dc3545'
            }

            emoji = level_emoji.get(level, '⚪')
            color = level_color.get(level, '#6c757d')

            timestamp = datetime.fromisoformat(alert.get('timestamp', ''))
            time_str = timestamp.strftime('%H:%M:%S')

            st.markdown(
                f"""
                <div style="border-left: 4px solid {color}; padding: 10px; margin: 10px 0; background-color: #f8f9fa;">
                    <strong>{emoji} [{time_str}] {alert.get('title', 'Alert')}</strong><br>
                    {alert.get('message', '')}
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.info("No alerts yet. Alerts will appear here as the bot finds opportunities.")

with tab5:
    st.header("📊 Strategy Performance")

    strategies = state.get('strategies', [])

    if strategies:
        df_strategies = pd.DataFrame(strategies)

        # Strategy metrics
        col1, col2 = st.columns(2)

        with col1:
            # Signals generated chart
            fig = px.bar(
                df_strategies,
                x='name',
                y='signals_generated',
                title='Signals Generated by Strategy',
                labels={'signals_generated': 'Signals', 'name': 'Strategy'}
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Strategy status
            st.subheader("Strategy Status")
            for _, strategy in df_strategies.iterrows():
                status = "🟢 Enabled" if strategy.get('enabled', False) else "🔴 Disabled"
                st.write(f"**{strategy['name']}:** {status}")
                st.write(f"  Signals: {strategy.get('signals_generated', 0)}")
                st.write("---")
    else:
        st.info("No strategy data available")

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    last_update = state.get('last_update', 'Unknown')
    st.caption(f"Last update: {last_update}")

with col2:
    st.caption("Refresh rate: 5 seconds")

with col3:
    if st.button("🔄 Refresh Now"):
        st.rerun()

# Auto-refresh
if auto_refresh:
    time.sleep(5)
    st.rerun()
