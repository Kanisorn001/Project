import streamlit as st
import pandas as pd
from datetime import timedelta

# ตั้งค่าหน้าเว็บ Streamlit
st.set_page_config(page_title="แดชบอร์ดราคาทองคำ", page_icon=":chart_with_upwards_trend:", layout="wide")

# โหลดข้อมูลราคาทองคำจาก CSV
df = pd.read_csv("gold_and_macro_data_final.csv", parse_dates=["Date"])
df = df[["Date", "Gold_Price_USD"]]  # ใช้เฉพาะคอลัมน์วันที่และราคาทองคำ

# ดึงราคาทองคำล่าสุดและการเปลี่ยนแปลงจากวันก่อนหน้า
latest_price = df["Gold_Price_USD"].iloc[-1]
prev_price = df["Gold_Price_USD"].iloc[-2]
price_diff = latest_price - prev_price
percent_change = (price_diff / prev_price) * 100

# ส่วนหัวและการ์ดแสดงราคาทองคำล่าสุด
st.title("📈 ราคาทองคำล่าสุด")
st.metric(
    label="ราคาทองคำล่าสุด (USD)",
    value=f"${latest_price:,.2f}",
    delta=f"{price_diff:,.2f} ({percent_change:.2f}%)"
)

# ตัวเลือกช่วงเวลาสำหรับกรองข้อมูล
period_options = ["7 วัน", "30 วัน", "90 วัน", "ทั้งหมด", "กำหนดช่วงเอง"]
period = st.radio("เลือกช่วงเวลา:", period_options, index=3, horizontal=True)

# คำนวณช่วงวันที่ตามตัวเลือกที่ผู้ใช้เลือก
end_date = df["Date"].max()
start_date = df["Date"].min()
if period == "7 วัน":
    start_date = end_date - timedelta(days=6)
elif period == "30 วัน":
    start_date = end_date - timedelta(days=29)
elif period == "90 วัน":
    start_date = end_date - timedelta(days=89)
elif period == "ทั้งหมด":
    start_date = df["Date"].min()
elif period == "กำหนดช่วงเอง":
    date_range = st.date_input(
        "เลือกช่วงวันที่:",
        value=(df["Date"].min(), df["Date"].max())
    )
    if len(date_range) == 2:
        start_date, end_date = date_range[0], date_range[1]
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)

# กรองข้อมูลตามช่วงวันที่ที่กำหนด
df_filtered = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)]

# แสดงกราฟและตารางในรูปแบบคอลัมน์เคียงกัน
col1, col2 = st.columns([2, 1])
with col1:
    st.subheader("แนวโน้มราคาทองคำย้อนหลัง")
    st.line_chart(df_filtered, x="Date", y="Gold_Price_USD", use_container_width=True)
with col2:
    st.subheader("ตารางราคาทองคำย้อนหลัง")
    st.dataframe(df_filtered.sort_values("Date", ascending=False),
                 hide_index=True, width="stretch")
