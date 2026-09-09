from __future__ import annotations
import numpy as np
from .indicators import pattern, trend

def signal(df, ai_probability=0.5):
    a=df.iloc[-1]; b=df.iloc[-2]; score=0
    td=trend(a); score += 30 if td=="BULLISH" else -20 if td=="BEARISH" else 5
    macd_bull=a.MACD>a.Signal_Line; cross=macd_bull and b.MACD<=b.Signal_Line; score += 12 if cross else 4 if macd_bull else -4
    score += 8 if 40<a.RSI<70 else 4 if a.RSI<40 else -10 if a.RSI>75 else 0
    score += 10 if a.Vol_Ratio>1.5 else 4 if a.Vol_Ratio>1.1 else 0
    score += (ai_probability-0.5)*40
    score=float(np.clip(score+40,0,100)); p=pattern(df)
    if score>=80: label,action="STRONG BUY","ENTRY"
    elif score>=65: label,action="BUY","ACCUMULATE"
    elif score>=50: label,action="WATCH","WAIT FOR CONFIRMATION"
    elif score>=35: label,action="HOLD","WAIT"
    else: label,action="AVOID","NO ENTRY"
    return {"score":score,"signal":label,"action":action,"trend":td,"pattern":p,"rsi":float(a.RSI),"vol_ratio":float(a.Vol_Ratio),"ai_probability":float(ai_probability)}

def setup(df, risk_pct=1.0, reward1=1.5, reward2=2.5):
    a=df.iloc[-1]; entry=float(a.Close); stop=max(0.0,entry-float(a.ATR)*1.5); risk=entry-stop
    return {"entry":entry,"stop_loss":stop,"target1":entry+risk*reward1,"target2":entry+risk*reward2,"risk_per_share":risk,"risk_pct":risk_pct}

def early_mover(df):
    a=df.iloc[-1]; prev=df.iloc[-2]; vol=float(a.Vol_Ratio); ret=float(a.Close/prev.Close-1)
    breakout=float(a.Close/a.Resistance-1) if a.Resistance else 0
    score=np.clip(40+ret*500+max(vol-1,0)*15+(10 if a.Close>a.SMA20 else 0)+(10 if a.MACD>a.Signal_Line else 0),0,100)
    label="EARLY MOVER" if score>=75 else "WATCH" if score>=55 else "NORMAL"
    return {"score":float(score),"label":label,"return_pct":ret*100,"volume_ratio":vol,"breakout_pct":breakout*100}
