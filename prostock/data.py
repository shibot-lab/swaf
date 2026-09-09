from __future__ import annotations
import time
import pandas as pd
import yfinance as yf
import streamlit as st

@st.cache_data(ttl=300, show_spinner=False)
def history(ticker: str, period: str = "2y", interval: str = "1d") -> pd.DataFrame:
    df = yf.Ticker(ticker).history(period=period, interval=interval, auto_adjust=False)
    if df is None or df.empty:
        return pd.DataFrame()
    df = df.copy()
    if getattr(df.index, "tz", None) is not None:
        df.index = df.index.tz_localize(None)
    return df.dropna(subset=["Open","High","Low","Close"])

@st.cache_data(ttl=300, show_spinner=False)
def batch_history(tickers: tuple[str, ...], period: str = "3mo") -> dict[str,pd.DataFrame]:
    out = {}
    for i in range(0, len(tickers), 80):
        chunk = list(tickers[i:i+80])
        try:
            raw = yf.download(chunk, period=period, group_by="ticker", threads=False, progress=False, auto_adjust=False)
            if raw is None or raw.empty: continue
            if isinstance(raw.columns, pd.MultiIndex):
                for t in chunk:
                    if t in raw.columns.get_level_values(0):
                        x = raw[t].dropna(how="all")
                        if not x.empty: out[t] = x
            elif len(chunk) == 1:
                out[chunk[0]] = raw
        except Exception:
            time.sleep(0.2)
    return out

def info(ticker: str) -> dict:
    try: return yf.Ticker(ticker).info or {}
    except Exception: return {}
