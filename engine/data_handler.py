import pandas as pd
import os
from .events import MarketEvent

class DataHandler:
    """
    DataHandler is an abstract base class providing an interface for
    all subsequent (inherited) data handlers (both live and historic).
    """
    def get_latest_bar(self, symbol):
        raise NotImplementedError("Should implement get_latest_bar()")

    def get_latest_bars(self, symbol, N=1):
        raise NotImplementedError("Should implement get_latest_bars()")

    def get_latest_bar_datetime(self, symbol):
        raise NotImplementedError("Should implement get_latest_bar_datetime()")

    def get_latest_bar_value(self, symbol, val_type):
        raise NotImplementedError("Should implement get_latest_bar_value()")

    def get_latest_bars_values(self, symbol, val_type, N=1):
        raise NotImplementedError("Should implement get_latest_bars_values()")

    def update_bars(self):
        raise NotImplementedError("Should implement update_bars()")


class HistoricParquetDataHandler(DataHandler):
    """
    HistoricParquetDataHandler is designed to read Parquet files for
    each requested symbol from disk and provide an interface
    to obtain the "latest" bar in a manner identical to a live
    trading interface.
    """
    def __init__(self, events, parquet_dir, symbol_list):
        self.events = events
        self.parquet_dir = parquet_dir
        self.symbol_list = symbol_list

        self.symbol_data = {}
        self.latest_symbol_data = {}
        self.continue_backtest = True

        self._load_data()

    def _load_data(self):
        """
        Load parquet files into memory
        """
        comb_index = None
        for s in self.symbol_list:
            filepath = os.path.join(self.parquet_dir, f"{s}.parquet")
            if not os.path.exists(filepath):
                print(f"File {filepath} does not exist.")
                continue

            # Load parquet
            df = pd.read_parquet(filepath)
            df.set_index('date', inplace=True)
            df.sort_index(inplace=True)

            # Ensure index is datetime
            df.index = pd.to_datetime(df.index)

            self.symbol_data[s] = df
            self.symbol_data[s] = self.symbol_data[s].iterrows()

            if comb_index is None:
                comb_index = df.index
            else:
                comb_index.union(df.index)

            self.latest_symbol_data[s] = []

    def _get_new_bar(self, symbol):
        """
        Returns the latest bar from the data feed.
        """
        try:
            return next(self.symbol_data[symbol])
        except StopIteration:
            return None

    def get_latest_bar(self, symbol):
        """
        Returns the last bar from the latest_symbol list.
        """
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("That symbol is not available in the historical data set.")
            raise
        else:
            return bars_list[-1]

    def get_latest_bars(self, symbol, N=1):
        """
        Returns the last N bars from the latest_symbol list.
        """
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("That symbol is not available in the historical data set.")
            raise
        else:
            return bars_list[-N:]

    def get_latest_bar_datetime(self, symbol):
        """
        Returns a Python datetime object for the last bar.
        """
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("That symbol is not available in the historical data set.")
            raise
        else:
            return bars_list[-1][0]

    def get_latest_bar_value(self, symbol, val_type):
        """
        Returns one of the Open, High, Low, Close, Volume
        values from the pandas Bar series object.
        """
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("That symbol is not available in the historical data set.")
            raise
        else:
            return getattr(bars_list[-1][1], val_type)

    def get_latest_bars_values(self, symbol, val_type, N=1):
        """
        Returns the last N bar values from the
        latest_symbol list.
        """
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("That symbol is not available in the historical data set.")
            raise
        else:
            return [getattr(b[1], val_type) for b in bars_list[-N:]]

    def update_bars(self):
        """
        Pushes the latest bar to the latest_symbol_data structure
        for all symbols in the symbol list.
        """
        for s in self.symbol_list:
            if s not in self.symbol_data:
                continue
            try:
                bar = next(self.symbol_data[s])
            except StopIteration:
                self.continue_backtest = False
            else:
                if bar is not None:
                    self.latest_symbol_data[s].append(bar)

        # Fire a MarketEvent
        if self.continue_backtest:
            self.events.put(MarketEvent())