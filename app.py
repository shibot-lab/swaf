import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import yfinance as yf
from prostock.config import APP_NAME, ALL_TICKERS, SECTORS
from prostock.data import history, info, batch_history
from prostock.indicators import enrich, pattern
from prostock.signals import signal, setup, early_mover
from prostock.risk import position_size, kelly
from prostock.backtest import run, monte_carlo
from prostock.ml import train_predict
from prostock.fundamentals import snapshot, dcf_value
from prostock.timing import analyze as timing_analyze
from prostock.options import chain, greeks
from prostock.alerts import add as add_alert, alerts as get_alerts, check as check_alerts
from prostock.paper import buy as paper_buy, sell as paper_sell, portfolio as paper_portfolio
from prostock.portfolio import analytics as portfolio_analytics
from prostock.universe import metadata as universe_metadata, tickers as universe_tickers

st.set_page_config(page_title=APP_NAME,page_icon="📈",layout="wide")

@st.cache_data(ttl=300, show_spinner=False)
def analyze_ticker(ticker, period="2y"):
    df=history(ticker,period)
    if df.empty:return None
    return enrich(df)

def fmt_rp(v): return f"Rp {v:,.0f}"

def overview(ticker):
    df=analyze_ticker(ticker)
    if df is None or len(df)<60: st.error("Data historis tidak cukup."); return
    ml=train_predict(df); s=signal(df,ml["probability"]); z=setup(df); em=early_mover(df); ts=timing_analyze(df)
    c1,c2,c3,c4,c5=st.columns(5)
    c1.metric("Harga",fmt_rp(df.Close.iloc[-1])); c2.metric("Pro Score",f"{s['score']:.0f}/100"); c3.metric("Signal",s["signal"]); c4.metric("AI Probability",f"{ml['probability']*100:.1f}%"); c5.metric("Early Mover",f"{em['score']:.0f}")
    st.caption(f"Trend {s['trend']} · Pattern {s['pattern']} · RSI {s['rsi']:.1f} · Volume {s['vol_ratio']:.2f}x · Regime {ts['regime']}")
    cols=st.columns(4); cols[0].metric("Entry",fmt_rp(z['entry'])); cols[1].metric("Stop Loss",fmt_rp(z['stop_loss'])); cols[2].metric("Target 1",fmt_rp(z['target1'])); cols[3].metric("Target 2",fmt_rp(z['target2']))
    fig=go.Figure(); fig.add_trace(go.Candlestick(x=df.index,open=df.Open,high=df.High,low=df.Low,close=df.Close,name="Price")); fig.add_trace(go.Scatter(x=df.index,y=df.EMA8,name="EMA8")); fig.add_trace(go.Scatter(x=df.index,y=df.EMA21,name="EMA21")); fig.update_layout(height=520,xaxis_rangeslider_visible=False,title=f"{ticker} · Command Chart"); st.plotly_chart(fig,use_container_width=True)
    a,b,c=st.columns(3)
    a.subheader("Momentum"); a.write(f"MACD: {df.MACD.iloc[-1]:.3f}"); a.write(f"ATR: {df.ATR.iloc[-1]:.3f}"); a.write(f"BB Width: {df.BB_Width.iloc[-1]:.3f}")
    b.subheader("AI / ML"); b.write(f"5-day +2% probability: {ml['probability']*100:.1f}%"); b.write("Feature importance:"); b.dataframe(pd.DataFrame(ml['importance'].items(),columns=['Feature','Importance']),hide_index=True,use_container_width=True)
    c.subheader("Timing"); c.write(f"Gap: {ts['gap_pct']:+.2f}%"); c.write(f"Volume: {ts['volume_ratio']:.2f}x"); c.write(ts['signal'])


def _market_snapshot(tickers, period="3mo"):
    data=batch_history(tuple(tickers),period)
    meta=universe_metadata()
    meta=meta.set_index("Ticker") if "Ticker" in meta.columns else pd.DataFrame()
    rows=[]
    for t,df in data.items():
        try:
            if df is None or len(df)<5: continue
            close=df.Close.dropna(); vol=df.Volume.dropna()
            if len(close)<2: continue
            last=float(close.iloc[-1]); prev=float(close.iloc[-2]); chg=(last/prev-1)*100 if prev else np.nan
            avg20=float(vol.tail(20).mean()) if len(vol)>=5 else float(vol.mean())
            vol_ratio=float(vol.iloc[-1]/avg20) if avg20 else np.nan
            value=last*float(vol.iloc[-1])
            row={"Ticker":t,"Price":last,"Change %":chg,"Volume":float(vol.iloc[-1]),"Value Rp":value,"Vol x":vol_ratio}
            if t in meta.index:
                for c in ["NamaEmiten","Sektor","SubSektor","PapanPencatatan"]: row[c]=meta.loc[t,c] if c in meta.columns else None
            rows.append(row)
        except Exception:
            continue
    return pd.DataFrame(rows)


def heatmap_ui():
    st.subheader("🗺️ IDX Market Heatmap")
    st.caption("Pemetaan seluruh universe saham IDX yang berhasil ditarik. Ukuran = aktivitas transaksi; warna = perubahan harga.")
    all_tickers=universe_tickers()
    st.info(f"Universe aktif: {len(all_tickers)} ticker saham IDX. Data diambil bertahap agar tidak membebani Yahoo Finance.")
    c1,c2,c3=st.columns(3)
    period=c1.selectbox("Window data",["1mo","3mo","6mo"],index=1)
    size_mode=c2.selectbox("Ukuran kotak",["Value Rp","Volume","Equal"])
    sector_filter=c3.selectbox("Sektor",["Semua sektor"]+sorted([x for x in universe_metadata()["Sektor"].dropna().unique().tolist() if str(x).strip()]))
    if st.button("Refresh Heatmap",type="primary"):
        st.cache_data.clear()
        st.rerun()
    # Use the scanner snapshot with the selected period for fresh map data.
    snap=_market_snapshot(all_tickers, period)
    if snap.empty:
        st.warning("Belum ada data market yang berhasil diambil."); return
    if sector_filter!="Semua sektor": snap=snap[snap["Sektor"]==sector_filter]
    snap=snap.replace([np.inf,-np.inf],np.nan).dropna(subset=["Change %"])
    if snap.empty: st.warning("Tidak ada data untuk filter ini."); return
    snap["Color"] = snap["Change %"].round(2)
    if size_mode=="Value Rp": snap["Size"]=np.log1p(snap["Value Rp"].clip(lower=1))
    elif size_mode=="Volume": snap["Size"]=np.log1p(snap["Volume"].clip(lower=1))
    else: snap["Size"]=1
    snap["Group"]=snap["Sektor"].fillna("Unknown")
    fig=px.treemap(snap,path=["Group","Ticker"],values="Size",color="Color",color_continuous_scale="RdYlGn",color_continuous_midpoint=0,hover_data={"Price":":,.0f","Change %":":+.2f","Vol x":":.2f","Value Rp":":,.0f","Size":False,"Color":False})
    fig.update_layout(height=720,margin=dict(l=5,r=5,t=30,b=5),coloraxis_colorbar_title="Change %")
    st.plotly_chart(fig,use_container_width=True)
    topg=snap.nlargest(15,"Change %")[['Ticker','Price','Change %','Vol x','Value Rp','Sektor']]
    topl=snap.nsmallest(15,"Change %")[['Ticker','Price','Change %','Vol x','Value Rp','Sektor']]
    a,b=st.columns(2); a.subheader("Top Gainers"); a.dataframe(topg,hide_index=True,use_container_width=True); b.subheader("Top Losers"); b.dataframe(topl,hide_index=True,use_container_width=True)


def scanner():
    st.subheader("⚡ Pro Scanner — Full IDX Candidate Discovery")
    meta=universe_metadata(); all_tickers=meta["Ticker"].tolist()
    st.caption("Mode default menyapu seluruh universe saham IDX, bukan hanya blue chips. Pipeline: broad technical scan → ranking → AI hanya untuk kandidat teratas.")
    c1,c2,c3,c4=st.columns(4)
    scope=c1.selectbox("Universe",["FULL IDX","Pilih sektor","Custom"])
    period=c2.selectbox("History",["3mo","6mo","1y"],index=1)
    top_ai=c3.number_input("AI re-score top N",10,200,50,10)
    min_score=c4.slider("Minimum Pro Score",0,100,55,5)
    if scope=="Pilih sektor":
        sectors=[x for x in meta["Sektor"].dropna().unique().tolist() if str(x).strip()]
        chosen=st.multiselect("Sektor",sorted(sectors),default=sorted(sectors))
        tickers=meta[meta["Sektor"].isin(chosen)]["Ticker"].tolist()
    elif scope=="Custom":
        tickers=st.multiselect("Ticker custom",all_tickers,default=all_tickers[:20])
    else:
        tickers=all_tickers
    st.write(f"**{len(tickers):,} ticker** akan diproses.")
    if st.button("🚀 Scan Full Universe",type="primary"):
        data=batch_history(tuple(tickers),period); rows=[]
        progress=st.progress(0.0); total=max(len(data),1)
        for i,(t,df) in enumerate(data.items(),1):
            try:
                x=enrich(df).dropna()
                if len(x)<60: continue
                s=signal(x,0.5); em=early_mover(x)
                rows.append({"Ticker":t,"Price":float(x.Close.iloc[-1]),"Score":s['score'],"Signal":s['signal'],"Trend":s['trend'],"Pattern":s['pattern'],"RSI":float(x.RSI.iloc[-1]),"Vol x":float(x.Vol_Ratio.iloc[-1]),"Mover":em['score']})
            except Exception: pass
            progress.progress(min(i/total,1.0))
        if rows:
            broad=pd.DataFrame(rows).sort_values(['Score','Mover'],ascending=False)
            candidates=broad[broad.Score>=min_score].head(int(top_ai)).copy()
            for idx,row in candidates.iterrows():
                try:
                    x=enrich(data[row.Ticker]).dropna(); ml=train_predict(x); broad.loc[idx,"AI %"]=ml['probability']*100; broad.loc[idx,"Final Score"]=0.75*broad.loc[idx,"Score"]+0.25*ml['probability']*100
                except Exception: broad.loc[idx,"AI %"]=np.nan; broad.loc[idx,"Final Score"]=broad.loc[idx,"Score"]
            broad["Final Score"]=broad["Final Score"].fillna(broad["Score"])
            broad=broad.sort_values(["Final Score","Score","Mover"],ascending=False).reset_index(drop=True)
            # Persist the completed scan in the Streamlit session. Streamlit reruns the
            # script whenever the user changes a sidebar tab/widget, so rendering the
            # result only inside the button block would otherwise make it disappear.
            st.session_state["scanner_result"] = broad
            st.session_state["scanner_stats"] = {
                "data_count": len(data),
                "technical_count": len(broad),
                "scope": scope,
                "period": period,
                "universe_count": len(tickers),
            }
            st.session_state["scanner_completed"] = True
            st.success(f"Scan selesai: {len(data):,} ticker punya data, {len(broad):,} lolos analisis teknikal.")
        else:
            st.session_state.pop("scanner_result", None)
            st.session_state.pop("scanner_stats", None)
            st.session_state["scanner_completed"] = False
            st.warning("Tidak ada data yang berhasil di-scan.")

    # IMPORTANT: keep the last completed scan visible after navigation.
    # Sidebar changes cause a Streamlit rerun, but session_state survives reruns.
    if st.session_state.get("scanner_completed") and "scanner_result" in st.session_state:
        broad=st.session_state["scanner_result"]
        stats=st.session_state.get("scanner_stats", {})
        st.divider()
        st.subheader("📌 Hasil Scan Tersimpan")
        st.caption(
            f"Universe: {stats.get('universe_count', len(tickers)):,} ticker · "
            f"History: {stats.get('period', period)} · "
            f"Data tersedia: {stats.get('data_count', len(broad)):,} · "
            f"Kandidat teknikal: {stats.get('technical_count', len(broad)):,}. "
            "Hasil tetap tersimpan selama sesi aplikasi."
        )
        st.dataframe(broad,use_container_width=True,hide_index=True)
        st.download_button(
            "Export CSV",
            broad.to_csv(index=False),
            "idx_full_scanner.csv",
            "text/csv",
            key="scanner_export_csv",
        )


def backtest_ui():
    ticker=st.selectbox("Ticker",ALL_TICKERS); strategy=st.selectbox("Strategy",["ma_crossover","rsi_reversal"]); capital=st.number_input("Initial Capital",1_000_000,1_000_000_000,10_000_000,1_000_000); period=st.selectbox("Period",["1y","2y","3y","5y"])
    if st.button("Run Backtest",type="primary"):
        df=history(ticker,period); r=run(df,strategy,capital)
        a,b,c,d=st.columns(4); a.metric("Return",f"{r['total_return']:+.2f}%"); b.metric("Win Rate",f"{r['win_rate']:.1f}%"); c.metric("Max DD",f"{r['max_drawdown']:.1f}%"); d.metric("Sharpe",f"{r['sharpe']:.2f}")
        e,f=st.columns(2); e.metric("Profit Factor",f"{r['profit_factor']:.2f}"); f.metric("Trades",len(r['trades']))
        if r['equity']:
            fig=go.Figure(go.Scatter(x=df.index[-len(r['equity']):],y=r['equity'],mode='lines',name='Equity')); fig.update_layout(height=400,title='Equity Curve'); st.plotly_chart(fig,use_container_width=True)
        st.dataframe(pd.DataFrame(r['trades']),use_container_width=True)
        if r['trades']:
            returns=[t['return_pct']/100 for t in r['trades']]; mc=monte_carlo(returns); st.subheader("Monte Carlo"); st.write({k:round(v,2) for k,v in mc.items()})

def risk_ui():
    ticker=st.selectbox("Ticker",ALL_TICKERS); capital=st.number_input("Capital",1_000_000,1_000_000_000,10_000_000,1_000_000); risk_pct=st.slider("Risk / trade (%)",0.25,5.0,1.0,0.25)
    df=analyze_ticker(ticker)
    if df is not None and len(df)>60:
        z=setup(df,risk_pct); p=position_size(capital,risk_pct,z['entry'],z['stop_loss']); st.json({"setup":z,"position":p}); st.info(f"Risk budget {fmt_rp(capital*risk_pct/100)} · Max {p['lots']} lot ({p['shares']} shares)")

def fundamentals_ui():
    ticker=st.selectbox("Ticker",ALL_TICKERS); inf=info(ticker); snap=snapshot(inf); st.dataframe(pd.DataFrame([snap]).T.rename(columns={0:'Value'}),use_container_width=True)
    fair=dcf_value(inf); price=inf.get('currentPrice') or inf.get('regularMarketPrice')
    if fair and price: st.metric("DCF Fair Value",fmt_rp(fair),delta=f"{(fair/price-1)*100:+.1f}%")
    else: st.caption("DCF memerlukan free cash flow dan share count yang tersedia dari provider.")

def options_ui():
    ticker=st.selectbox("Ticker",ALL_TICKERS); obj=yf.Ticker(ticker); expiry,parts=chain(obj)
    if not expiry: st.warning("Option chain tidak tersedia untuk instrumen ini."); return
    st.success(f"Nearest expiry: {expiry}"); calls,puts=parts; st.write("Calls"); st.dataframe(calls.head(30),use_container_width=True); st.write("Puts"); st.dataframe(puts.head(30),use_container_width=True)

def alerts_ui():
    ticker=st.selectbox("Ticker",ALL_TICKERS); kind=st.selectbox("Alert",["price_above","price_below","rsi_above","volume"]); value=st.number_input("Threshold",value=100.0)
    if st.button("Add Alert"): add_alert(ticker,kind,value); st.success("Alert ditambahkan.")
    st.dataframe(pd.DataFrame(get_alerts()),use_container_width=True)
    df=analyze_ticker(ticker)
    if df is not None:
        hits=check_alerts(ticker,float(df.Close.iloc[-1]),float(df.RSI.iloc[-1]),float(df.Vol_Ratio.iloc[-1]));
        if hits: st.warning(f"{len(hits)} alert aktif untuk {ticker}.")

def paper_ui():
    ticker=st.selectbox("Ticker",ALL_TICKERS); df=analyze_ticker(ticker); price=float(df.Close.iloc[-1]) if df is not None else 0
    qty=st.number_input("Shares",100,1_000_000,100,100); c1,c2=st.columns(2)
    if c1.button("BUY"): paper_buy(ticker,qty,price); st.success("Paper order BUY dicatat.")
    if c2.button("SELL"): paper_sell(ticker,qty); st.success("Paper order SELL dicatat.")
    p=paper_portfolio(); rows=[{"ticker":t,"qty":v['qty'],"avg":v['avg']} for t,v in p.items()]; st.dataframe(pd.DataFrame(rows),use_container_width=True)

def portfolio_ui():
    st.info("Masukkan posisi paper trading untuk melihat konsentrasi portofolio.")
    p=paper_portfolio(); rows=[]
    for t,v in p.items():
        df=analyze_ticker(t); px=float(df.Close.iloc[-1]) if df is not None else v['avg']; rows.append({"ticker":t,"qty":v['qty'],"price":px})
    a=portfolio_analytics(rows); st.metric("Portfolio Value",fmt_rp(a['value'])); st.write("Weights",a['weight']); st.metric("Largest Weight",f"{a['concentration']*100:.1f}%")

def timing_ui():
    ticker=st.selectbox("Ticker",ALL_TICKERS); df=analyze_ticker(ticker); 
    if df is not None: st.json(timing_analyze(df))

st.sidebar.title("IDX PRO")
mode=st.sidebar.radio("Command Center",["Dashboard","Market Heatmap","Pro Scanner","Backtesting Lab","Risk & Position Sizing","Fundamental + DCF","Options Intelligence","Watchlist & Alerts","Paper Trading","Portfolio Risk","Market Timing"])
try:
    ucount=len(universe_tickers())
    st.sidebar.caption(f"Universe IDX: {ucount:,} saham")
except Exception:
    st.sidebar.caption("Universe IDX: fallback")
st.sidebar.caption("Self-contained rebuild · research only")

if mode=="Dashboard":
    st.title("📈 IDX Pro Intelligence"); ticker=st.sidebar.selectbox("Focus Ticker",ALL_TICKERS,index=0); overview(ticker)
elif mode=="Market Heatmap": st.title("🗺️ Market Heatmap"); heatmap_ui()
elif mode=="Pro Scanner": st.title("⚡ Pro Scanner"); scanner()
elif mode=="Backtesting Lab": st.title("🧪 Backtesting Lab"); backtest_ui()
elif mode=="Risk & Position Sizing": st.title("🛡️ Risk Engine"); risk_ui()
elif mode=="Fundamental + DCF": st.title("💎 Valuation Desk"); fundamentals_ui()
elif mode=="Options Intelligence": st.title("📐 Options Intelligence"); options_ui()
elif mode=="Watchlist & Alerts": st.title("🔔 Smart Alerts"); alerts_ui()
elif mode=="Paper Trading": st.title("🎮 Paper Trading Simulator"); paper_ui()
elif mode=="Portfolio Risk": st.title("🧭 Portfolio Risk"); portfolio_ui()
elif mode=="Market Timing": st.title("⏱️ Market Timing"); timing_ui()
