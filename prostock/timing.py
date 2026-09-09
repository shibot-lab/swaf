from datetime import datetime
import pandas as pd

def analyze(df):
    if len(df)<20:return {"regime":"UNKNOWN","gap_pct":0,"volume_ratio":0,"signal":"INSUFFICIENT DATA"}
    a=df.iloc[-1]; prev=df.iloc[-2]; gap=(a.Open/prev.Close-1)*100; vr=a.Volume/(df.Volume.tail(20).mean() or 1)
    regime="TREND" if a.EMA8>a.EMA21 else "RISK-OFF" if a.EMA8<a.EMA21 else "RANGE"
    return {"regime":regime,"gap_pct":float(gap),"volume_ratio":float(vr),"signal":"CONFIRMED" if abs(gap)>1 and vr>1.2 else "NORMAL"}
