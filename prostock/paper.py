import streamlit as st

def portfolio():
    return st.session_state.setdefault("paper_positions",{})

def buy(ticker,qty,price):
    p=portfolio(); cur=p.get(ticker,{"qty":0,"avg":0}); total=cur["qty"]+qty; cur["avg"]=(cur["qty"]*cur["avg"]+qty*price)/total; cur["qty"]=total; p[ticker]=cur

def sell(ticker,qty):
    p=portfolio();
    if ticker in p:
        p[ticker]["qty"]=max(0,p[ticker]["qty"]-qty)
        if p[ticker]["qty"]==0: del p[ticker]
