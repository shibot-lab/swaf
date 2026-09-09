import uuid
from datetime import datetime
import numpy as np
import pandas as pd
import streamlit as st

from prostock.data import history
from prostock.signals import setup
from prostock.outcomes import add_records, clear_records, evaluate_all, records

st.set_page_config(page_title='Signal Outcome Tracker', page_icon='🎯', layout='wide')

st.title('🎯 Signal Outcome Tracker')
st.caption('Tahap berikutnya dari scanner: bukan hanya mencari sinyal, tetapi mengukur apakah sinyal benar-benar bekerja.')


def _now():
    return datetime.now().replace(microsecond=0).isoformat(sep=' ')


def _capture_rows(selected: pd.DataFrame) -> list[dict]:
    captured_at = _now()
    rows = []
    for _, r in selected.iterrows():
        ticker = str(r['Ticker'])
        try:
            df = history(ticker, '6mo')
            if df is None or len(df) < 60:
                continue
            z = setup(df)
            rows.append({
                'id': f"{ticker}-{captured_at}-{uuid.uuid4().hex[:8]}",
                'ticker': ticker,
                'captured_at': captured_at,
                'entry': float(r['Price']),
                'score': float(r.get('Score', np.nan)),
                'final_score': float(r.get('Final Score', r.get('Score', np.nan))),
                'signal': str(r.get('Signal', '')),
                'trend': str(r.get('Trend', '')),
                'pattern': str(r.get('Pattern', '')),
                'rsi': float(r.get('RSI', np.nan)),
                'vol_ratio': float(r.get('Vol x', np.nan)),
                'mover': float(r.get('Mover', np.nan)),
                'ai_pct': float(r.get('AI %', np.nan)),
                'stop_loss': float(z['stop_loss']),
                'target1': float(z['target1']),
                'target2': float(z['target2']),
            })
        except Exception:
            continue
    return rows

scanner = st.session_state.get('scanner_result')
if isinstance(scanner, pd.DataFrame) and not scanner.empty:
    st.subheader('1. Capture kandidat dari scanner')
    view = scanner.copy()
    view.insert(0, 'Track', False)
    tracked_ids = st.multiselect(
        'Pilih ticker yang ingin dilacak',
        view['Ticker'].tolist(),
        default=view['Ticker'].head(min(10, len(view))).tolist(),
        help='Biasanya cukup 5–10 kandidat terbaik agar evaluasi tetap fokus.'
    )
    selected = view[view['Ticker'].isin(tracked_ids)].copy()
    if not selected.empty:
        st.dataframe(selected.drop(columns=['Track']), use_container_width=True, hide_index=True)
    if st.button('🎯 Track Selected Candidates', type='primary', disabled=selected.empty):
        added = add_records(_capture_rows(selected))
        st.success(f'{added} kandidat masuk ke Outcome Tracker.')
else:
    st.info('Belum ada hasil scanner di sesi ini. Jalankan Pro Scanner terlebih dahulu, lalu kembali ke halaman ini.')

st.divider()
st.subheader('2. Evaluate outcome')
st.caption('Evaluasi memakai bar harian setelah waktu capture. Return 1D/3D/5D/10D serta MFE/MAE dihitung dari harga entry yang direkam.')

if st.button('🔄 Evaluate All Tracked Signals'):
    with st.spinner('Mengambil data terbaru dan mengevaluasi sinyal...'):
        result = evaluate_all(history)
    st.session_state['outcome_eval'] = result
    st.success(f'{len(result)} signal dievaluasi.')

result = st.session_state.get('outcome_eval')
if result is None or not isinstance(result, pd.DataFrame):
    result = evaluate_all(history) if records() else pd.DataFrame()

if not result.empty:
    result = result.replace([np.inf, -np.inf], np.nan)
    completed = result[result['outcome'].isin(['TP1_HIT', 'SL_HIT', 'BOTH_SAME_BAR'])]
    wins = int((completed['outcome'] == 'TP1_HIT').sum())
    losses = int((completed['outcome'] == 'SL_HIT').sum())
    resolved = wins + losses
    accuracy = wins / resolved * 100 if resolved else np.nan
    avg5 = result['return_5d_pct'].dropna().mean() if 'return_5d_pct' in result else np.nan
    avg_mfe = result['mfe_5d_pct'].dropna().mean() if 'mfe_5d_pct' in result else np.nan
    avg_mae = result['mae_5d_pct'].dropna().mean() if 'mae_5d_pct' in result else np.nan

    a,b,c,d,e = st.columns(5)
    a.metric('Tracked', len(result))
    b.metric('Resolved', resolved)
    c.metric('TP1 hit rate', f'{accuracy:.1f}%' if not np.isnan(accuracy) else '—')
    d.metric('Avg return 5D', f'{avg5:+.2f}%' if not np.isnan(avg5) else '—')
    e.metric('Avg MFE 5D', f'{avg_mfe:+.2f}%' if not np.isnan(avg_mfe) else '—')

    st.subheader('Outcome log')
    cols = [c for c in ['ticker','captured_at','entry','final_score','signal','trend','rsi','vol_ratio','mover','ai_pct','outcome','return_1d_pct','return_3d_pct','return_5d_pct','return_10d_pct','mfe_5d_pct','mae_5d_pct'] if c in result.columns]
    display = result[cols].sort_values(['captured_at','final_score'], ascending=[False, False])
    st.dataframe(display, use_container_width=True, hide_index=True)

    st.subheader('Signal quality by score bucket')
    bucket = pd.cut(result['final_score'], bins=[0,55,65,75,85,100], labels=['<55','55–64','65–74','75–84','85+'], include_lowest=True)
    quality = result.assign(score_bucket=bucket).groupby('score_bucket', observed=False).agg(
        Signals=('ticker','count'),
        Avg_5D=('return_5d_pct','mean'),
        MFE_5D=('mfe_5d_pct','mean'),
        MAE_5D=('mae_5d_pct','mean'),
    ).reset_index()
    st.dataframe(quality, use_container_width=True, hide_index=True)

    st.subheader('Next upgrade signal')
    st.info('Setelah data terkumpul, tracker ini bisa dipakai untuk mengkalibrasi bobot Pro Score, Early Mover, volume, dan AI berdasarkan outcome nyata — bukan berdasarkan satu-dua trade.')

    st.download_button('Export Outcome CSV', result.to_csv(index=False), 'swaf_signal_outcomes.csv', 'text/csv')
    if st.button('⚠️ Clear All Tracked Signals'):
        clear_records()
        st.session_state.pop('outcome_eval', None)
        st.rerun()
else:
    st.info('Belum ada signal yang dilacak.')
