import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# กำหนดวันที่ย้อนหลัง 10 ปี
end_date = datetime.today()
start_date = end_date - timedelta(days=3650)

# Key คือชื่อที่เราต้องการ และ Value คือ Ticker ที่ถูกต้อง
symbols = {
    'Gold_Price_USD': 'GC=F',
    'Silver_Price_USD': 'SI=F',
    'Crude_Oil_Price': 'CL=F',
    'SP500_Index': '^GSPC',
    'US_10Y_Treasury_Yield': '^TNX',
    'US_Dollar_Index_DXY': 'DX-Y.NYB',
    'GLD_ETF_Price': 'GLD'
}

# ดึงข้อมูล
def fetch_data(symbols, start, end):
    data = {}
    print("Starting data fetch...")
    for name, ticker in symbols.items():
        print(f"Fetching: {name} ({ticker})")
        try:
            df = yf.download(ticker, start=start, end=end, progress=False)
            
            if not df.empty:
                df = df[['Close']].rename(columns={'Close': name})
                data[name] = df
            else:
                print(f"  Warning: No data returned for {name} ({ticker})")

        except Exception as e:
            print(f"  Error fetching {name} ({ticker}): {e}")
            
    return data

raw_data_dict = fetch_data(symbols, start_date, end_date)

# รวม DataFrames ทั้งหมดเข้าด้วยกัน
if raw_data_dict:
    df = pd.concat(raw_data_dict.values(), axis=1)

    # เติมข้อมูลที่ขาดหายไป (NaN) ด้วยข้อมูลของวันก่อนหน้า
    df.ffill(inplace=True)

    # 1. ย้าย Date จาก Index มาเป็น Column ใหม่
    df.reset_index(inplace=True)
    df.rename(columns={'index': 'Date'}, inplace=True)


    # แสดงตัวอย่าง
    print("\n--- Sample of Combined Data (First 5 rows) ---")
    df.head(5)

    # 3. บันทึกข้อมูลเป็น CSV โดยไม่เอารหัส Index (0,1,2,...) ติดไปด้วย
    df.to_csv("gold_and_macro_data_final.csv", index=False)
    print("\n✅ Data successfully saved to gold_and_macro_data_final.csv")

else:
    print("\n❌ No data was fetched. The final DataFrame is empty.")