from __future__ import annotations

def snapshot(info):
    keys=["trailingPE","priceToBook","priceToSalesTrailing12Months","returnOnEquity","debtToEquity","dividendYield","marketCap","profitMargins","revenueGrowth"]
    return {k:info.get(k) for k in keys}

def dcf_value(info, years=5, growth=None, discount=0.12, terminal_growth=0.03):
    fcf=info.get("freeCashflow") or info.get("operatingCashflow")
    shares=info.get("sharesOutstanding"); debt=info.get("totalDebt") or 0; cash=info.get("totalCash") or 0
    if not fcf or not shares:return None
    g=growth if growth is not None else max(-0.05,min(0.15,info.get("revenueGrowth") or 0.05))
    pv=sum(fcf*((1+g)**t)/((1+discount)**t) for t in range(1,years+1)); tv=fcf*((1+g)**years)*(1+terminal_growth)/(discount-terminal_growth); enterprise=pv+tv/(1+discount)**years
    return (enterprise+cash-debt)/shares
