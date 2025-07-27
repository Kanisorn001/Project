import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from fredapi import Fred 

# === กำหนดค่า YFinance ===
end_date = datetime.today()
start_date = end_date - timedelta(days=3650)

symbols = {
    'Gold_Price_USD': 'GC=F',
    'Silver_Price_USD': 'SI=F',
    'Crude_Oil_Price': 'CL=F',
    'SP500_Index': '^GSPC',
    'US_10Y_Treasury_Yield': '^TNX',
    'US_Dollar_Index_DXY': 'DX-Y.NYB',
    'Iron_Ore_Price': 'TIO=F'
}

# === กำหนดค่า FRED ===
# !!! แทนที่ 'YOUR_FRED_API_KEY' ด้วย API Key ของคุณ !!!
FRED_API_KEY = 'c574e2410fc6100cbde48b33fcdfaf31'
fred = Fred(api_key=FRED_API_KEY)

fred_series = {
    'Inflation_CPI': 'CPIAUCSL'
}

# === ฟังก์ชันดึงข้อมูล ===
def fetch_yahoo_data(symbols, start, end):
    print("Fetching data from Yahoo Finance...")
    df = yf.download(list(symbols.values()), start=start, end=end, progress=False)
    if not df.empty:
        df = df['Close'].rename(columns=dict(zip(symbols.values(), symbols.keys())))
    return df

# ----- ส่วนของฟังก์ชันที่ขาดไป -----
def fetch_fred_data(series_id, start):
    print(f"Fetching data from FRED for {series_id}...")
    name = list(series_id.keys())[0]
    sid = list(series_id.values())[0]
    series = fred.get_series(sid, observation_start=start)
    return pd.DataFrame(series, columns=[name])
# --------------------------------

# === กระบวนการหลัก ===
if __name__ == "__main__":
    # 1. ดึงข้อมูลจากทั้งสองแหล่ง
    df_yahoo = fetch_yahoo_data(symbols, start_date, end_date)
    df_fred = fetch_fred_data(fred_series, start_date) # <-- บรรทัดนี้จะทำงานได้เมื่อมีฟังก์ชันแล้ว

    if not df_yahoo.empty and not df_fred.empty:
        # 2. รวม DataFrames
        print("\nMerging Yahoo Finance and FRED data...")
        combined_df = pd.merge(df_yahoo, df_fred, left_index=True, right_index=True, how='outer')

        # 3. เติมข้อมูลที่ขาดหายไป
        combined_df.ffill(inplace=True)
        combined_df.dropna(inplace=True)

        # 4. ย้าย Date จาก Index มาเป็น Column
        combined_df.reset_index(inplace=True)
        combined_df.rename(columns={'index': 'Date'}, inplace=True)
        
        # 5. แสดงตัวอย่างและบันทึก
        print("\n--- Sample of Combined Data (First 5 rows) ---")
        print(combined_df.head(5))
        
        output_file = "gold_and_macro_data_final.csv"
        combined_df.to_csv(output_file, index=False)
        print(f"\n✅ Data successfully saved to {output_file}")

else:
    print("\n❌ Data fetching from one of the sources failed.")
