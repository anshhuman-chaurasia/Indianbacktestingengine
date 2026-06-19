from jugaad_data.nse import stock_df
from datetime import date
df = stock_df(symbol="RELIANCE", from_date=date(2023,1,1), to_date=date(2023,1,10), series="EQ")
print(df.columns)
