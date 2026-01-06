# main.py
import os
import time
import threading
from typing import Dict, Any

import numpy as np
import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from statsmodels.tsa.arima.model import ARIMA, ARIMAResults


# ------------------------
# Config (ไม่ต้องย้ายไฟล์)
# ------------------------
DATA_PATH  = os.getenv("DATA_PATH", "gold_and_macro_data_final.csv")
MODEL_PATH = os.getenv("MODEL_PATH", "arima_Gold_High_order_2_1_0.pkl")
TARGET     = os.getenv("TARGET_COLUMN", "Gold_High")
ORDER      = tuple(int(x) for x in os.getenv("ARIMA_ORDER", "2,1,0").split(","))

HISTORY_WINDOW = int(os.getenv("HISTORY_WINDOW", "180"))
DEFAULT_STEPS  = int(os.getenv("FORECAST_STEPS", "7"))

ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",") if o.strip()]


# ------------------------
# In-memory cache/state
# ------------------------
STATE: Dict[str, Any] = {
    "lock": threading.Lock(),
    "model": None,          # ARIMAResults
    "data_mtime": None,
    "payload": None,
    "last_refresh_ts": None,
}


def load_series() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date").reset_index(drop=True)
    if TARGET not in df.columns:
        raise ValueError(f"TARGET_COLUMN '{TARGET}' not found in {DATA_PATH}")
    df[TARGET] = (
        df[TARGET].astype(float)
        .replace([np.inf, -np.inf], np.nan)
        .dropna()
    )
    return df


def ensure_model_up_to_date(series: np.ndarray) -> ARIMAResults:
    """
    ใช้ไฟล์ .pkl เป็น base model ตามที่คุณต้องการ
    แต่ถ้าข้อมูล CSV ยาวกว่าเดิม (มีข้อมูลใหม่) จะ refit ด้วย ORDER เดิม
    เพื่อให้โมเดล 'ทันข้อมูลล่าสุด' (เหมาะกับระบบที่อัปเดตทุกวัน)
    """
    res: ARIMAResults = STATE["model"]
    if res is None:
        res = ARIMAResults.load(MODEL_PATH)

    # ถ้าจำนวนข้อมูลเปลี่ยน -> refit ใหม่ด้วย order เดิม
    # (สำหรับ daily update ถือว่าเป็น “retrain แบบเบา” และได้ผลที่สอดคล้องกับข้อมูลล่าสุด)
    if getattr(res, "nobs", None) != len(series):
        res = ARIMA(series, order=ORDER).fit()

        # ตัวเลือก: เซฟทับ pkl เพื่อให้ไฟล์ใน deploy ใหม่ล่าสุดเสมอ (ไม่บังคับ)
        if os.getenv("SAVE_UPDATED_MODEL", "0") == "1":
            tmp_path = MODEL_PATH + ".tmp"
            res.save(tmp_path)
            os.replace(tmp_path, MODEL_PATH)

    return res


def build_payload(df: pd.DataFrame, res: ARIMAResults) -> Dict[str, Any]:
    series = df[TARGET].values
    n = len(series)

    # History window
    start = max(0, n - HISTORY_WINDOW)
    history = []
    for i in range(start, n):
        date_val = str(df["Date"].iloc[i].date()) if "Date" in df.columns else str(i)
        history.append({
            "date": date_val,
            "actual": float(series[i]),
        })

    # Forecast next steps
    steps = DEFAULT_STEPS
    fc = res.forecast(steps=steps)
    # ทำ “วันที่อนาคต” แบบง่าย: ถ้ามี Date ให้ +1 วันต่อเนื่อง (ไม่สนวันหยุด)
    future = []
    if "Date" in df.columns:
        last_date = df["Date"].iloc[-1]
        for k in range(steps):
            future.append({
                "date": str((last_date + pd.Timedelta(days=k+1)).date()),
                "pred": float(fc[k]),
            })
    else:
        for k in range(steps):
            future.append({"date": str(n + k), "pred": float(fc[k])})

    latest_date = str(df["Date"].iloc[-1].date()) if "Date" in df.columns else str(n - 1)
    payload = {
        "target": TARGET,
        "latest": {
            "date": latest_date,
            "actual": float(series[-1]),
        },
        "history": history,
        "forecast": future,
        "model": {
            "type": "ARIMA",
            "order": list(ORDER),
            "n_obs": int(getattr(res, "nobs", n)),
            "aic": float(getattr(res, "aic", np.nan)),
            "bic": float(getattr(res, "bic", np.nan)),
        },
        "meta": {
            "data_path": DATA_PATH,
            "model_path": MODEL_PATH,
            "refreshed_at": int(time.time()),
            "rows": int(n),
        }
    }
    return payload


def refresh_if_needed(force: bool = False):
    with STATE["lock"]:
        mtime = os.path.getmtime(DATA_PATH) if os.path.exists(DATA_PATH) else None
        if (not force) and (STATE["data_mtime"] == mtime) and (STATE["payload"] is not None):
            return

        df = load_series()
        series = df[TARGET].values
        res = ensure_model_up_to_date(series)

        STATE["model"] = res
        STATE["payload"] = build_payload(df, res)
        STATE["data_mtime"] = mtime
        STATE["last_refresh_ts"] = time.time()


# ------------------------
# FastAPI App
# ------------------------
app = FastAPI(title="Gold Forecast (ARIMA) API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS if ALLOWED_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    # โหลด pkl ตามที่คุณระบุ
    STATE["model"] = ARIMAResults.load(MODEL_PATH)
    refresh_if_needed(force=True)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/api/dashboard")
def dashboard():
    refresh_if_needed(force=False)
    return STATE["payload"]

@app.get("/api/forecast")
def forecast(steps: int = DEFAULT_STEPS):
    refresh_if_needed(force=False)
    res: ARIMAResults = STATE["model"]
    fc = res.forecast(steps=steps)
    return {"steps": steps, "pred": [float(x) for x in fc]}

