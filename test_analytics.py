import queue
import datetime
import pandas as pd
from engine import HistoricParquetDataHandler, Portfolio, SimulatedExecutionHandler, Backtest, Strategy, SignalEvent
from engine.analytics import generate_analytics

class TestStrategy(Strategy):
    def __init__(self, bars, events):
        self.bars = bars
        self.events = events
        self.symbol_list = self.bars.symbol_list
        self.bought = {s: False for s in self.symbol_list}

    def calculate_signals(self, event):
        if event.type == 'MARKET':
            for s in self.symbol_list:
                bars = self.bars.get_latest_bars_values(s, "close", N=1)
                if bars is not None and len(bars) > 0:
                    if not self.bought[s]:
                        signal = SignalEvent(1, s, self.bars.get_latest_bar_datetime(s), 'LONG', 1.0)
                        self.events.put(signal)
                        self.bought[s] = True

events = queue.Queue()
symbols = ["RELIANCE"]
start_date = pd.to_datetime("2023-01-01")

bars = HistoricParquetDataHandler(events, "data", symbols)
port = Portfolio(bars, events, start_date)
broker = SimulatedExecutionHandler(events, bars)
strat = TestStrategy(bars, events)

bt = Backtest(bars, broker, port, strat)
bt.run()

metrics, curve, dd = generate_analytics(port)
print(metrics)
