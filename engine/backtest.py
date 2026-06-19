import queue
import time
from .events import MarketEvent, SignalEvent, OrderEvent, FillEvent

class Backtest:
    """
    Enscapsulates the settings and components for carrying out
    an event-driven backtest.
    """
    def __init__(self, data_handler, execution_handler, portfolio, strategy):
        self.data_handler = data_handler
        self.execution_handler = execution_handler
        self.portfolio = portfolio
        self.strategy = strategy
        self.events = portfolio.events

        self.signals = 0
        self.orders = 0
        self.fills = 0
        self.num_strats = 1

    def run(self):
        """
        Executes the backtest.
        """
        i = 0
        while True:
            i += 1
            # Update the market bars
            if self.data_handler.continue_backtest == True:
                self.data_handler.update_bars()
            else:
                break

            # Handle the events
            while True:
                try:
                    event = self.events.get(False)
                except queue.Empty:
                    break
                else:
                    if event is not None:
                        if event.type == 'MARKET':
                            self.strategy.calculate_signals(event)
                            self.portfolio.update_timeindex(event)

                        elif event.type == 'SIGNAL':
                            self.signals += 1
                            self.portfolio.update_signal(event)

                        elif event.type == 'ORDER':
                            self.orders += 1
                            self.execution_handler.execute_order(event)

                        elif event.type == 'FILL':
                            self.fills += 1
                            self.portfolio.update_fill(event)

        print("Backtest finished.")
        print(f"Signals: {self.signals}")
        print(f"Orders: {self.orders}")
        print(f"Fills: {self.fills}")
