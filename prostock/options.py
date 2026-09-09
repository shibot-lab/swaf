from __future__ import annotations
from math import log,sqrt,exp,erf

def norm_cdf(x): return 0.5*(1+erf(x/sqrt(2)))
def greeks(S,K,T,r,sigma,call=True):
    if min(S,K,T,sigma)<=0:return {}
    d1=(log(S/K)+(r+sigma*sigma/2)*T)/(sigma*sqrt(T)); d2=d1-sigma*sqrt(T); pdf=exp(-d1*d1/2)/sqrt(2*3.1415926535)
    delta=norm_cdf(d1) if call else norm_cdf(d1)-1; gamma=pdf/(S*sigma*sqrt(T)); theta=-(S*pdf*sigma/(2*sqrt(T)) + (r*K*exp(-r*T)*norm_cdf(d2 if call else -d2)))*(1/365); vega=S*pdf*sqrt(T)/100
    return {"delta":delta,"gamma":gamma,"theta":theta,"vega":vega}

def chain(ticker_obj):
    try:
        expiries=ticker_obj.options
        if not expiries:return None,[]
        exp0=expiries[0]; calls=ticker_obj.option_chain(exp0).calls; puts=ticker_obj.option_chain(exp0).puts
        return exp0, [calls,puts]
    except Exception:return None,[]
