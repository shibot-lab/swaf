from __future__ import annotations
import numpy as np, pandas as pd
from .indicators import enrich

def run(df, strategy="ma_crossover", initial_capital=10_000_000):
    x=enrich(df).dropna().copy(); cash=float(initial_capital); shares=0; entry=0; trades=[]; equity=[]
    for i,row in x.iterrows():
        buy=sell=False
        if strategy=="ma_crossover": buy=row.EMA8>row.EMA21 and row.MACD>row.Signal_Line; sell=row.EMA8<row.EMA21
        elif strategy=="rsi_reversal": buy=row.RSI<35; sell=row.RSI>65
        elif strategy=="breakout": buy=row.Close>row.Resistance.shift(1) if hasattr(row.Resistance,'shift') else False
        if shares==0 and buy:
            qty=int(cash//(row.Close*100))*100
            if qty>0: shares=qty; entry=row.Close; cash-=qty*row.Close; entry_date=i
        elif shares>0 and sell:
            cash+=shares*row.Close; trades.append({"entry":entry_date,"exit":i,"entry_price":entry,"exit_price":row.Close,"return_pct":(row.Close/entry-1)*100}); shares=0
        equity.append(cash+shares*row.Close)
    if shares:
        cash+=shares*x.iloc[-1].Close; trades.append({"entry":entry_date,"exit":x.index[-1],"entry_price":entry,"exit_price":x.iloc[-1].Close,"return_pct":(x.iloc[-1].Close/entry-1)*100}); shares=0
        equity[-1]=cash
    eq=np.array(equity); rets=pd.Series(eq).pct_change().dropna(); wins=[t["return_pct"] for t in trades if t["return_pct"]>0]; losses=[t["return_pct"] for t in trades if t["return_pct"]<=0]
    peak=np.maximum.accumulate(eq); dd=(eq/peak-1)*100
    pf=(sum(wins)/abs(sum(losses))) if losses and sum(losses)!=0 else float("inf") if wins else 0
    sharpe=(rets.mean()/rets.std()*np.sqrt(252)) if rets.std()>0 else 0
    return {"total_return":(eq[-1]/initial_capital-1)*100 if len(eq) else 0,"win_rate":100*len(wins)/len(trades) if trades else 0,"max_drawdown":float(dd.min()) if len(dd) else 0,"profit_factor":float(pf),"sharpe":float(sharpe),"trades":trades,"equity":equity}

def monte_carlo(returns, simulations=1000):
    r=np.asarray(returns,dtype=float); r=r[np.isfinite(r)]
    if len(r)==0:return {"mean_return":0,"std_return":0,"p5":0,"p95":0,"prob_profit":0}
    finals=[]
    for _ in range(simulations): finals.append((np.random.choice(r,len(r),replace=True)+1).prod()-1)
    f=np.asarray(finals)*100
    return {"mean_return":float(f.mean()),"std_return":float(f.std()),"p5":float(np.percentile(f,5)),"p95":float(np.percentile(f,95)),"prob_profit":float((f>0).mean()*100)}
