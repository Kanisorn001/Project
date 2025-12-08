import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from fredapi import Fred 

end_date = datetime.today()
start_date = end_date - timedelta(days=3650)

YAHOO_TICKERS = [
    'GC=F',       # Gold
    'SI=F',       # Silver
    'CL=F',       # Crude Oil
    '^GSPC',      # S&P 500
    'TIO=F',      # Iron Ore (อาจมีปัญหา)
    '^TNX',       # 10Y Yield
    'DX-Y.NYB'    # Dollar Index
]

FRED_API_KEY = 'c574e2410fc6100cbde48b33fcdfaf31'
fred = Fred(api_key=FRED_API_KEY)

fred_series = {
    'Inflation_CPI': 'CPIAUCSL'
}

def fetch_yahoo_data(start, end):
    print("Fetching data from Yahoo Finance...")
    data = yf.download(
        YAHOO_TICKERS,
        start=start,
        end=end,
        progress=False,
        auto_adjust=False,
        threads=True
    )

    if data.empty:
        print("❌ Yahoo Finance returned empty DataFrame.")
        return pd.DataFrame()

    # ถ้า columns เป็น MultiIndex (ปกติ) เราจะ map แบบปลอดภัย
    df = pd.DataFrame(index=data.index)

    def safe_get(level0, ticker):
        try:
            return data[level0][ticker]
        except KeyError:
            print(f"⚠️ Missing column: {level0} - {ticker}")
            return pd.Series(index=data.index, dtype='float64')

    # Gold จาก GC=F
    df['Gold_Open']   = safe_get('Open',   'GC=F')
    df['Gold_High']   = safe_get('High',   'GC=F')
    df['Gold_Low']    = safe_get('Low',    'GC=F')
    df['Gold_Close']  = safe_get('Close',  'GC=F')
    df['Gold_Volume'] = safe_get('Volume', 'GC=F')

    # อื่น ๆ
    df['Silver_Price_USD']      = safe_get('Close', 'SI=F')
    df['Crude_Oil_Price']       = safe_get('Close', 'CL=F')
    df['SP500_Index']           = safe_get('Close', '^GSPC')
    df['Iron_Ore_Price']        = safe_get('Close', 'TIO=F')
    df['US_10Y_Treasury_Yield'] = safe_get('Close', '^TNX')
    df['US_Dollar_Index_DXY']   = safe_get('Close', 'DX-Y.NYB')

    # 🔸 ลบคอลัมน์ที่เป็น NaN ทั้งคอลัมน์ (เช่น Iron_Ore_Price ถ้า TIO=F ดึงไม่ได้เลย)
    all_nan_cols = [c for c in df.columns if df[c].isna().all()]
    if all_nan_cols:
        print("⚠️ Dropping all-NaN columns:", all_nan_cols)
        df.drop(columns=all_nan_cols, inplace=True)

    # ลบแถวที่ NaN ทุกคอลัมน์
    df.dropna(how='all', inplace=True)

    return df

def fetch_fred_data(series_id, start):
    print(f"Fetching data from FRED for {series_id}...")
    name = list(series_id.keys())[0]
    sid = list(series_id.values())[0]
    series = fred.get_series(sid, observation_start=start)
    df = pd.DataFrame(series, columns=[name])
    df.index = pd.to_datetime(df.index)
    return df

if __name__ == "__main__":
    df_yahoo = fetch_yahoo_data(start_date, end_date)
    df_fred = fetch_fred_data(fred_series, start_date)

    if not df_yahoo.empty and not df_fred.empty:
        print("\nMerging Yahoo Finance and FRED data...")
        combined_df = pd.merge(
            df_yahoo,
            df_fred,
            left_index=True,
            right_index=True,
            how='outer'
        )

        combined_df.ffill(inplace=True)

        # 🔸 แทนที่จะ dropna ทุกคอลัมน์ → ให้เน้นเฉพาะคอลัมน์สำคัญ
        # อย่างน้อยต้องมี Gold_Close ไม่เป็น NaN
        if 'Gold_Close' in combined_df.columns:
            combined_df.dropna(subset=['Gold_Close'], inplace=True)
        else:
            combined_df.dropna(how='all', inplace=True)

        combined_df.reset_index(inplace=True)
        combined_df.rename(columns={'index': 'Date'}, inplace=True)

        print("\n--- Sample of Combined Data (First 5 rows) ---")
        print(combined_df.head(5))
        print("\nShape:", combined_df.shape)

        output_file = "gold_and_macro_data_final.csv"
        combined_df.to_csv(output_file, index=False)
        print(f"\n✅ Data successfully saved to {output_file}")
    else:
        print("\n❌ Data fetching from one of the sources failed.")
