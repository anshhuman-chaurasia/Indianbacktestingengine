import os
import pandas as pd
from datetime import date
from jugaad_data.nse import stock_df

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')

def fetch_and_save_data(symbol, start_date, end_date):
    """
    Fetches stock data using jugaad-data and saves it as a Parquet file.
    """
    try:
        df = stock_df(symbol=symbol, from_date=start_date, to_date=end_date, series="EQ")
        if df.empty:
            print(f"No data returned for {symbol}")
            return False

        # Format the dataframe
        df.rename(columns={
            'DATE': 'date',
            'OPEN': 'open',
            'HIGH': 'high',
            'LOW': 'low',
            'CLOSE': 'close',
            'VOLUME': 'volume'
        }, inplace=True)

        # Select required columns
        df = df[['date', 'open', 'high', 'low', 'close', 'volume']]

        # Sort by date ascending (jugaad-data returns descending usually)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)

        # Save to parquet
        parquet_path = os.path.join(DATA_DIR, f"{symbol}.parquet")
        df.to_parquet(parquet_path, engine='pyarrow', index=False)
        print(f"Successfully saved data for {symbol} to {parquet_path}")
        return True
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return False

def get_nifty500_symbols():
    """
    Returns a list of Nifty 500 symbols.
    For MVP, returning a small subset to test functionality quickly.
    """
    # For now, returning top 10 as Nifty 500 would take a while to download in MVP testing
    return ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "HINDUNILVR", "ITC", "SBIN", "BHARTIARTL", "KOTAKBANK"]

def download_data(universe="NIFTY500", start_date=date(2010, 1, 1), end_date=date.today()):
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    symbols = []
    if universe == "NIFTY500":
        symbols = get_nifty500_symbols()
    else:
        # Custom list or single symbol
        symbols = [universe] if isinstance(universe, str) else universe

    for symbol in symbols:
        fetch_and_save_data(symbol, start_date, end_date)

if __name__ == "__main__":
    # Test download for RELIANCE
    print("Testing download for RELIANCE...")
    download_data("RELIANCE", date(2023, 1, 1), date(2023, 12, 31))
