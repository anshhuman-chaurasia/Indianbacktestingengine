import streamlit as st
import os
import queue
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
from textwrap import dedent
import sys

# Ensure engine can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from engine import HistoricParquetDataHandler, Portfolio, SimulatedExecutionHandler, Backtest, Strategy, SignalEvent, data_manager
from engine.analytics import generate_analytics

# --- CONFIG ---
DATA_DIR = data_manager.DATA_DIR

st.set_page_config(page_title="Indian Market Backtester", layout="wide")

st.title("Professional Indian Market Backtester")

# --- DEFAULT STRATEGY TEMPLATE ---
default_strategy_code = """
class UserStrategy(Strategy):
    \"\"\"
    A simple SMA Cross strategy example.
    Buy when Close > 5-day SMA.
    \"\"\"
    def __init__(self, bars, events):
        self.bars = bars
        self.events = events
        self.symbol_list = self.bars.symbol_list
        self.bought = {s: False for s in self.symbol_list}
        self.sma_period = 5

    def calculate_signals(self, event):
        if event.type == 'MARKET':
            for s in self.symbol_list:
                bars = self.bars.get_latest_bars_values(s, "close", N=self.sma_period)
                if bars is not None and len(bars) == self.sma_period:
                    current_close = bars[-1]
                    sma = sum(bars) / self.sma_period

                    if current_close > sma and not self.bought[s]:
                        # BUY
                        signal = SignalEvent(1, s, self.bars.get_latest_bar_datetime(s), 'LONG', 1.0)
                        self.events.put(signal)
                        self.bought[s] = True
                    elif current_close < sma and self.bought[s]:
                        # SELL
                        signal = SignalEvent(1, s, self.bars.get_latest_bar_datetime(s), 'EXIT', 1.0)
                        self.events.put(signal)
                        self.bought[s] = False
"""

# --- TABS ---
tab1, tab2 = st.tabs(["Backtest Strategy", "Data Manager"])

with tab2:
    st.header("Data Manager")
    st.write("Download historical data using `jugaad-data`. Saved as Parquet files locally.")

    col1, col2, col3 = st.columns(3)
    with col1:
        universe_choice = st.selectbox("Select Universe", ["RELIANCE (Test)", "NIFTY500 (MVP List)", "Custom"])
        custom_symbol = ""
        if universe_choice == "Custom":
            custom_symbol = st.text_input("Enter NSE Symbol", "TCS")

    with col2:
        start_date = st.date_input("Start Date", date(2023, 1, 1))
    with col3:
        end_date = st.date_input("End Date", date(2023, 12, 31))

    if st.button("Download Data"):
        with st.spinner("Downloading data..."):
            target = ""
            if universe_choice == "RELIANCE (Test)": target = "RELIANCE"
            elif universe_choice == "NIFTY500 (MVP List)": target = "NIFTY500"
            else: target = custom_symbol

            data_manager.download_data(target, start_date, end_date)
        st.success("Download complete!")

    # Show available data
    st.subheader("Available Local Data")
    if os.path.exists(DATA_DIR):
        files = [f for f in os.listdir(DATA_DIR) if f.endswith('.parquet')]
        if files:
            st.write(", ".join([f.replace('.parquet', '') for f in files]))
        else:
            st.write("No data downloaded yet.")
    else:
        st.write("Data directory does not exist yet.")

with tab1:
    col_code, col_settings = st.columns([2, 1])

    with col_settings:
        st.subheader("Settings")

        # Get available symbols
        available_symbols = []
        if os.path.exists(DATA_DIR):
            available_symbols = [f.replace('.parquet', '') for f in os.listdir(DATA_DIR) if f.endswith('.parquet')]

        if not available_symbols:
            st.warning("Please download data in the Data Manager tab first.")
            st.stop()

        selected_symbols = st.multiselect("Select Symbols for Backtest", available_symbols, default=available_symbols[:1])
        initial_capital = st.number_input("Initial Capital (₹)", value=100000, step=10000)

        run_button = st.button("Run Backtest", type="primary", use_container_width=True)

    with col_code:
        st.subheader("Strategy Code (Python)")
        strategy_code = st.text_area("Write your strategy class here. Must be named UserStrategy and inherit Strategy.",
                                     value=default_strategy_code, height=400)

    if run_button:
        if not selected_symbols:
            st.error("Select at least one symbol.")
        else:
            with st.spinner("Running Backtest..."):
                try:
                    # 1. Dynamically execute user code to get UserStrategy class
                    local_env = {
                        "Strategy": Strategy,
                        "SignalEvent": SignalEvent
                    }
                    exec(strategy_code, globals(), local_env)
                    UserStrategy = local_env.get("UserStrategy")

                    if UserStrategy is None:
                        st.error("Could not find `UserStrategy` class in code.")
                        st.stop()

                    # 2. Setup engine
                    events = queue.Queue()

                    # Get start date from first parquet file
                    first_file = os.path.join(DATA_DIR, f"{selected_symbols[0]}.parquet")
                    df_temp = pd.read_parquet(first_file)
                    bt_start_date = pd.to_datetime(df_temp['date'].iloc[0])

                    bars = HistoricParquetDataHandler(events, DATA_DIR, selected_symbols)
                    port = Portfolio(bars, events, bt_start_date, initial_capital=initial_capital)
                    broker = SimulatedExecutionHandler(events, bars)
                    strat = UserStrategy(bars, events)

                    # 3. Run backtest
                    bt = Backtest(bars, broker, port, strat)
                    bt.run()

                    # 4. Analytics
                    metrics, curve, drawdowns = generate_analytics(port)

                    # 5. Display Results
                    st.divider()
                    st.subheader("Backtest Results")

                    m_cols = st.columns(len(metrics))
                    for idx, (k, v) in enumerate(metrics.items()):
                        m_cols[idx].metric(label=k, value=v)

                    st.divider()

                    # Plots
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=curve.index, y=curve['equity_curve'], mode='lines', name='Equity Curve'))
                    fig.update_layout(title='Portfolio Equity Curve', xaxis_title='Date', yaxis_title='Normalized Equity', template="plotly_white")
                    st.plotly_chart(fig, use_container_width=True)

                    fig_dd = go.Figure()
                    fig_dd.add_trace(go.Scatter(x=drawdowns.index, y=drawdowns, mode='lines', name='Drawdown', fill='tozeroy', marker_color='red'))
                    fig_dd.update_layout(title='Drawdown', xaxis_title='Date', yaxis_title='Drawdown %', template="plotly_white")
                    st.plotly_chart(fig_dd, use_container_width=True)

                except Exception as e:
                    st.error(f"Error during backtest: {str(e)}")
