import streamlit as st

def alerts(): return st.session_state.setdefault("alerts",[])
def add(ticker,kind,value): alerts().append({"ticker":ticker,"kind":kind,"value":float(value)})
def check(ticker,price,rsi,vol_ratio):
    hits=[]
    for a in alerts():
        if a["ticker"]!=ticker:continue
        if a["kind"]=="price_above" and price>=a["value"]:hits.append(a)
        if a["kind"]=="price_below" and price<=a["value"]:hits.append(a)
        if a["kind"]=="rsi_above" and rsi>=a["value"]:hits.append(a)
        if a["kind"]=="volume" and vol_ratio>=a["value"]:hits.append(a)
    return hits
