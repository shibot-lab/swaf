from __future__ import annotations
import numpy as np, pandas as pd
from sklearn.ensemble import RandomForestClassifier

def train_predict(df):
    x=df.copy(); x["ret1"]=x.Close.pct_change(); x["ret5"]=x.Close.pct_change(5); x["vol_z"]=(x.Vol_Ratio-1); x["rsi_dist"]=(x.RSI-50)/50; x["trend_gap"]=(x.EMA8/x.EMA21-1); x["macd_gap"]=x.MACD-x.Signal_Line
    features=["ret1","ret5","vol_z","rsi_dist","trend_gap","macd_gap"]
    x["target"]=(x.Close.shift(-5)/x.Close-1>0.02).astype(int); z=x.dropna()
    if len(z)<120:return {"probability":0.5,"importance":{},"model":None}
    train=z.iloc[:-20]; live=z.iloc[-1:]; model=RandomForestClassifier(n_estimators=300,max_depth=7,min_samples_leaf=4,class_weight="balanced",random_state=42); model.fit(train[features],train.target)
    prob=float(model.predict_proba(live[features])[0,1]); imp=dict(sorted(zip(features,model.feature_importances_),key=lambda q:q[1],reverse=True))
    return {"probability":prob,"importance":imp,"model":model}
