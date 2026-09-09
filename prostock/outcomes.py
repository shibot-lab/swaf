from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np

STORE_DIR = Path('.swaf_data')
STORE_FILE = STORE_DIR / 'signal_outcomes.json'


def _load() -> list[dict]:
    try:
        if not STORE_FILE.exists():
            return []
        return json.loads(STORE_FILE.read_text(encoding='utf-8'))
    except Exception:
        return []


def _save(rows: list[dict]) -> None:
    STORE_DIR.mkdir(parents=True, exist_ok=True)
    STORE_FILE.write_text(json.dumps(rows, ensure_ascii=False, indent=2, default=str), encoding='utf-8')


def records() -> list[dict]:
    return _load()


def add_records(rows: list[dict]) -> int:
    current = _load()
    existing = {r.get('id') for r in current}
    added = 0
    for row in rows:
        if row.get('id') in existing:
            continue
        current.append(row)
        existing.add(row.get('id'))
        added += 1
    _save(current)
    return added


def clear_records() -> None:
    _save([])


def evaluate_record(record: dict, history_loader, horizons=(1, 3, 5, 10)) -> dict:
    ticker = str(record['ticker'])
    entry = float(record['entry'])
    captured = pd.Timestamp(record['captured_at'])
    if captured.tzinfo is not None:
        captured = captured.tz_localize(None)
    df = history_loader(ticker, '1y')
    if df is None or df.empty:
        return {**record, 'status': 'NO_DATA'}
    idx = pd.DatetimeIndex(df.index)
    if idx.tz is not None:
        idx = idx.tz_localize(None)
    df = df.copy(); df.index = idx
    future = df[df.index > captured]
    if future.empty:
        return {**record, 'status': 'WAITING'}

    out = dict(record)
    out['status'] = 'TRACKING'
    out['bars_available'] = int(len(future))
    for h in horizons:
        if len(future) < h:
            out[f'return_{h}d_pct'] = np.nan
            continue
        window = future.iloc[:h]
        close = float(window.Close.iloc[-1])
        out[f'return_{h}d_pct'] = (close / entry - 1.0) * 100.0
        out[f'mfe_{h}d_pct'] = (float(window.High.max()) / entry - 1.0) * 100.0
        out[f'mae_{h}d_pct'] = (float(window.Low.min()) / entry - 1.0) * 100.0

    stop = float(record.get('stop_loss') or 0)
    target = float(record.get('target1') or 0)
    if stop > 0 and target > entry:
        state = 'OPEN'
        for ts, bar in future.iterrows():
            hit_tp = float(bar.High) >= target
            hit_sl = float(bar.Low) <= stop
            if hit_tp and hit_sl:
                state = 'BOTH_SAME_BAR'
                break
            if hit_tp:
                state = 'TP1_HIT'
                break
            if hit_sl:
                state = 'SL_HIT'
                break
        out['outcome'] = state
    else:
        out['outcome'] = 'NO_TARGETS'
    return out


def evaluate_all(history_loader, horizons=(1, 3, 5, 10)) -> pd.DataFrame:
    rows = [evaluate_record(r, history_loader, horizons) for r in _load()]
    return pd.DataFrame(rows)
