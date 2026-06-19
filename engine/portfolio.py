import pandas as pd
from .events import OrderEvent

class Portfolio:
    """
    The Portfolio class handles the positions and market
    value of all instruments at a resolution of a "bar",
    i.e. secondly, minutely, 5-min, 30-min, 60 min or EOD.
    """
    def __init__(self, bars, events, start_date, initial_capital=100000.0):
        self.bars = bars
        self.events = events
        self.symbol_list = self.bars.symbol_list
        self.start_date = start_date
        self.initial_capital = initial_capital

        self.all_positions = self.construct_all_positions()
        self.current_positions = dict((k, 0) for k in self.symbol_list)

        self.all_holdings = self.construct_all_holdings()
        self.current_holdings = self.construct_current_holdings()

        self.trades = [] # Keep track of completed trades

    def construct_all_positions(self):
        """
        Constructs the positions list using the start_date
        to determine when the time index will begin.
        """
        d = dict((k, 0) for k in self.symbol_list)
        d['datetime'] = self.start_date
        return [d]

    def construct_all_holdings(self):
        """
        Constructs the holdings list using the start_date
        to determine when the time index will begin.
        """
        d = dict((k, 0.0) for k in self.symbol_list)
        d['datetime'] = self.start_date
        d['cash'] = self.initial_capital
        d['commission'] = 0.0
        d['total'] = self.initial_capital
        return [d]

    def construct_current_holdings(self):
        """
        This constructs the dictionary which will hold the instantaneous
        value of the portfolio across all symbols.
        """
        d = dict((k, 0.0) for k in self.symbol_list)
        d['cash'] = self.initial_capital
        d['commission'] = 0.0
        d['total'] = self.initial_capital
        return d

    def update_timeindex(self, event):
        """
        Adds a new record to the positions matrix for the current
        market data bar. This reflects the PREVIOUS bar, i.e. all
        current market data at this stage is known (OHLCV).

        Makes use of a MarketEvent from the events queue.
        """
        try:
            latest_datetime = self.bars.get_latest_bar_datetime(self.symbol_list[0])
        except IndexError:
            return # empty symbol list
        except Exception as e:
            # Maybe data empty yet
            return

        # Update positions
        dp = dict((k, v) for k, v in self.current_positions.items())
        dp['datetime'] = latest_datetime
        self.all_positions.append(dp)

        # Update holdings
        dh = dict((k, v) for k, v in self.current_holdings.items())
        dh['datetime'] = latest_datetime
        dh['cash'] = self.current_holdings['cash']
        dh['commission'] = self.current_holdings['commission']
        dh['total'] = self.current_holdings['cash']

        for s in self.symbol_list:
            try:
                # Approximation to the real value
                market_value = self.current_positions[s] * self.bars.get_latest_bar_value(s, "close")
                dh[s] = market_value
                dh['total'] += market_value
            except Exception as e:
                pass # Symbol might not have data for this bar

        self.all_holdings.append(dh)

    def update_positions_from_fill(self, fill):
        """
        Takes a Fill object and updates the position matrix to
        reflect the new position.
        """
        fill_dir = 0
        if fill.direction == 'BUY':
            fill_dir = 1
        elif fill.direction == 'SELL':
            fill_dir = -1

        self.current_positions[fill.symbol] += fill_dir * fill.quantity

    def update_holdings_from_fill(self, fill):
        """
        Takes a Fill object and updates the holdings matrix to
        reflect the holdings value.
        """
        fill_dir = 0
        if fill.direction == 'BUY':
            fill_dir = 1
        elif fill.direction == 'SELL':
            fill_dir = -1

        # Update holdings list with new quantities
        fill_cost = self.bars.get_latest_bar_value(fill.symbol, "close")
        cost = fill_dir * fill_cost * fill.quantity
        self.current_holdings[fill.symbol] += cost
        self.current_holdings['commission'] += fill.commission
        self.current_holdings['cash'] -= (cost + fill.commission)
        self.current_holdings['total'] -= fill.commission

        # Log trade
        self.trades.append({
            'datetime': self.bars.get_latest_bar_datetime(fill.symbol),
            'symbol': fill.symbol,
            'direction': fill.direction,
            'quantity': fill.quantity,
            'price': fill_cost,
            'commission': fill.commission
        })

    def update_signal(self, event):
        """
        Acts on a SignalEvent to generate new orders
        based on the portfolio logic.
        """
        if event.type == 'SIGNAL':
            order_event = self.generate_naive_order(event)
            self.events.put(order_event)

    def generate_naive_order(self, signal):
        """
        Simply files an Order object as a constant quantity
        sizing of the signal object, without risk management or
        position sizing considerations.
        """
        order = None

        symbol = signal.symbol
        direction = signal.signal_type
        strength = signal.strength

        # naive fixed quantity for MVP
        mkt_quantity = 10
        cur_quantity = self.current_positions[symbol]
        order_type = 'MKT'

        if direction == 'LONG' and cur_quantity == 0:
            order = OrderEvent(symbol, order_type, mkt_quantity, 'BUY')
        elif direction == 'SHORT' and cur_quantity == 0:
            order = OrderEvent(symbol, order_type, mkt_quantity, 'SELL')
        elif direction == 'EXIT' and cur_quantity > 0:
            order = OrderEvent(symbol, order_type, abs(cur_quantity), 'SELL')
        elif direction == 'EXIT' and cur_quantity < 0:
            order = OrderEvent(symbol, order_type, abs(cur_quantity), 'BUY')

        return order

    def update_fill(self, event):
        """
        Updates the portfolio current positions and holdings
        from a FillEvent.
        """
        if event.type == 'FILL':
            self.update_positions_from_fill(event)
            self.update_holdings_from_fill(event)

    def create_equity_curve_dataframe(self):
        """
        Creates a pandas DataFrame from the all_holdings
        list of dictionaries.
        """
        curve = pd.DataFrame(self.all_holdings)
        curve.set_index('datetime', inplace=True)
        curve['returns'] = curve['total'].pct_change()
        curve['equity_curve'] = (1.0 + curve['returns']).cumprod()
        return curve
