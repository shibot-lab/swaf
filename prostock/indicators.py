from __future__ import annotations
import numpy as np
import pandas as pd

def rsi(close, period=14):
    delta = close.diff(); up = delta.clip(lower=0); down = -delta.clip(upper=0)
    rs = up.ewm(alpha=1/period, adjust=False).mean() / down.ewm(alpha=1/period, adjust=False).mean().replace(0,np.nan)
    return 100 - (100/(1+rs))

def atr(df, period=14):
    tr = pd.concat([df.High-df.Low,(df.High-df.Close.shift()).abs(),(df.Low-df.Close.shift()).abs()],axis=1).max(axis=1)
    return tr.ewm(alpha=1/period, adjust=False).mean()

def macd(close):
    fast=close.ewm(span=12,adjust=False).mean(); slow=close.ewm(span=26,adjust=False).mean(); line=fast-slow; sig=line.ewm(span=9,adjust=False).mean()
    return line,sig,line-sig

def enrich(df):
    x=df.copy(); c=x.Close
    x["RSI"]=rsi(c); x["SMA20"]=c.rolling(20).mean(); x["SMA50"]=c.rolling(50).mean(); x["EMA8"]=c.ewm(span=8,adjust=False).mean(); x["EMA21"]=c.ewm(span=21,adjust=False).mean(); x["ATR"]=atr(x)
    x["Vol_Avg"]=x.Volume.rolling(20).mean(); x["Vol_Ratio"]=x.Volume/x.Vol_Avg.replace(0,np.nan)
    x["Support"]=x.Low.rolling(60).min(); x["Resistance"]=x.High.rolling(60).max()
    ml,ms,mh=macd(c); x["MACD"]=ml; x["Signal_Line"]=ms; x["MACD_Histogram"]=mh
    lo=x.Low.rolling(14).min(); hi=x.High.rolling(14).max(); x["%K"]=100*(c-lo)/(hi-lo).replace(0,np.nan); x["%D"]=x["%K"].rolling(3).mean()
    mid=c.rolling(20).mean(); sd=c.rolling(20).std(); x["BB_Middle"]=mid; x["BB_Upper"]=mid+2*sd; x["BB_Lower"]=mid-2*sd; x["BB_Width"]=(x.BB_Upper-x.BB_Lower)/mid.replace(0,np.nan)
    x["VWAP"]=(x.Close*x.Volume).cumsum()/x.Volume.cumsum().replace(0,np.nan)
    x["OBV"]=(np.sign(c.diff()).fillna(0)*x.Volume).cumsum()
    return x

def pattern(df):
    if len(df)<2:return "Insufficient data"
    a,b=df.iloc[-1],df.iloc[-2]; body=abs(a.Close-a.Open); rng=a.High-a.Low; up=a.High-max(a.Close,a.Open); low=min(a.Close,a.Open)-a.Low
    if rng>0 and low>max(body,1e-9)*2 and up<body:return "Hammer"
    if a.Close>b.Open and a.Open<b.Close and b.Close<b.Open:return "Bullish Engulfing"
    if a.Close<b.Open and a.Open>b.Close and b.Close>b.Open:return "Bearish Engulfing"
    return "Normal"

def trend(row):
    if row.Close>row.SMA50 and row.EMA8>row.EMA21:return "BULLISH"
    if row.Close<row.SMA50 and row.EMA8<row.EMA21:return "BEARISH"
    return "SIDEWAYS"
