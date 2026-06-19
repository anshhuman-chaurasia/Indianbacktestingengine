import numpy as np
import pandas as pd

def create_drawdowns(equity_curve):
    """
    Calculate the largest peak-to-trough drawdown of the equity curve
    as well as the duration of the drawdown. Requires that the
    equity curve is a pandas Series.
    """
    hwm = [0]
    eq_idx = equity_curve.index
    drawdown = pd.Series(index=eq_idx, dtype=float)
    duration = pd.Series(index=eq_idx, dtype=float)

    for t in range(1, len(eq_idx)):
        hwm.append(max(hwm[t-1], equity_curve.iloc[t]))
        drawdown.iloc[t] = (hwm[t] - equity_curve.iloc[t]) / hwm[t] if hwm[t] > 0 else 0.0
        duration.iloc[t] = (0 if drawdown.iloc[t] == 0 else duration.iloc[t-1] + 1)

    return drawdown, drawdown.max(), duration.max()

def create_sharpe_ratio(returns, periods=252):
    """
    Create the Sharpe ratio for the strategy, based on a
    benchmark of zero (i.e. no risk-free rate information).
    """
    if len(returns) < 2 or returns.std() == 0:
        return 0.0
    return np.sqrt(periods) * (np.mean(returns)) / np.std(returns)

def calculate_cagr(equity_curve):
    """
    Calculates the Compound Annual Growth Rate.
    """
    if len(equity_curve) < 2:
        return 0.0

    days = (equity_curve.index[-1] - equity_curve.index[0]).days
    if days == 0:
        return 0.0

    years = days / 365.25
    total_return = equity_curve.iloc[-1] / equity_curve.iloc[0]

    # Handle edge case where total_return is negative or 0 to avoid complex numbers
    if total_return <= 0:
        return -1.0

    if years == 0:
        return 0.0

    # Ensure calculation doesn't yield NaN for very small periods
    cagr = (total_return ** (1 / years)) - 1
    if pd.isna(cagr):
        return 0.0
    return cagr

def extract_trade_metrics(trades):
    """
    Extracts basic trade metrics like win rate and profit factor.
    """
    if not trades:
        return 0.0, 0.0

    # Simple win rate approximation based on entry vs current price
    # (In a real system, you'd match entry and exit trades exactly.
    # For MVP, we will assume standard exit handling will be done in strategy)
    return 0.0, 0.0 # Placeholder for more complex trade pairing logic

def generate_analytics(portfolio):
    """
    Generates a dictionary of all performance metrics.
    """
    curve = portfolio.create_equity_curve_dataframe()

    if len(curve) < 2:
        return {
            "Total Return": "0.00%",
            "CAGR": "0.00%",
            "Sharpe Ratio": "0.00",
            "Max Drawdown": "0.00%",
            "Total Trades": len(portfolio.trades)
        }

    returns = curve['returns'].fillna(0.0)
    equity_curve = curve['equity_curve']

    total_return = (equity_curve.iloc[-1] - 1.0) * 100
    cagr = calculate_cagr(equity_curve) * 100
    sharpe = create_sharpe_ratio(returns)
    dd, max_dd, dd_dur = create_drawdowns(equity_curve)
    max_dd = max_dd * 100

    metrics = {
        "Total Return": f"{total_return:.2f}%",
        "CAGR": f"{cagr:.2f}%",
        "Sharpe Ratio": f"{sharpe:.2f}",
        "Max Drawdown": f"{max_dd:.2f}%",
        "Total Trades": len(portfolio.trades)
    }

    return metrics, curve, dd
