from __future__ import annotations
import re
from pathlib import Path
import pandas as pd
import streamlit as st

IDX_URL = "https://www.idx.co.id/primary/ListedCompany/GetCompanyProfiles"
CACHE_FILE = Path(".idx_cache/universe.csv")


def _fetch_idx():
    headers = {
        "accept": "application/json, text/plain, */*",
        "referer": "https://www.idx.co.id/id/perusahaan-tercatat/profil-perusahaan/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140 Safari/537.36",
    }
    try:
        from curl_cffi import requests
        r = requests.get(f"{IDX_URL}?start=0&length=9999", headers=headers, impersonate="chrome", timeout=30)
        r.raise_for_status()
        payload = r.json()
    except Exception:
        import requests
        r = requests.get(f"{IDX_URL}?start=0&length=9999", headers=headers, timeout=30)
        r.raise_for_status()
        payload = r.json()
    rows = payload.get("data", []) if isinstance(payload, dict) else []
    df = pd.DataFrame(rows)
    if df.empty or "KodeEmiten" not in df.columns:
        raise RuntimeError("IDX issuer directory returned no stock records")
    keep = ["KodeEmiten", "NamaEmiten", "Sektor", "SubSektor", "PapanPencatatan", "TanggalPencatatan", "Status", "EfekEmiten_Saham"]
    for c in keep:
        if c not in df.columns:
            df[c] = None
    df = df[df["EfekEmiten_Saham"].fillna(False).astype(bool)].copy()
    df["KodeEmiten"] = df["KodeEmiten"].astype(str).str.upper().str.strip()
    df = df[df["KodeEmiten"].str.match(r"^[A-Z]{4}$", na=False)]
    df = df.drop_duplicates("KodeEmiten").sort_values("KodeEmiten")
    return df[keep].reset_index(drop=True)


@st.cache_data(ttl=86400, show_spinner=False)
def get_universe(force_refresh: bool = False) -> pd.DataFrame:
    # Streamlit cache is cleared only by ttl; force refresh is intentionally handled
    # by bypassing the local disk cache while keeping the result cached afterward.
    try:
        if not force_refresh and CACHE_FILE.exists():
            age = pd.Timestamp.now().timestamp() - CACHE_FILE.stat().st_mtime
            if age < 86400:
                df = pd.read_csv(CACHE_FILE)
                if len(df) >= 500:
                    return df
    except Exception:
        pass

    try:
        df = _fetch_idx()
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(CACHE_FILE, index=False)
        return df
    except Exception:
        if CACHE_FILE.exists():
            try:
                return pd.read_csv(CACHE_FILE)
            except Exception:
                pass
        # Safe fallback: the bundled universe is intentionally small but keeps the app usable offline.
        from prostock.config import DEFAULT_TICKERS
        return pd.DataFrame({"KodeEmiten": [x.replace(".JK", "") for x in DEFAULT_TICKERS], "NamaEmiten": None, "Sektor": None})


def tickers(force_refresh: bool = False) -> list[str]:
    df = get_universe(force_refresh)
    return [f"{x}.JK" for x in df["KodeEmiten"].dropna().astype(str).tolist()]


def metadata(force_refresh: bool = False) -> pd.DataFrame:
    df = get_universe(force_refresh).copy()
    df["Ticker"] = df["KodeEmiten"].astype(str) + ".JK"
    return df
