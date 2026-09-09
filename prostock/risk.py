def position_size(capital, risk_pct, entry, stop, lot_size=100):
    risk_budget=capital*risk_pct/100; per_share=abs(entry-stop)
    shares=int(risk_budget/per_share) if per_share else 0; lots=shares//lot_size; shares=lots*lot_size
    return {"lots":lots,"shares":shares,"investment":shares*entry,"risk_amount":shares*per_share}

def kelly(win_rate, avg_win, avg_loss, fraction=0.25):
    if avg_loss<=0:return 0.0
    b=avg_win/avg_loss; p=win_rate; q=1-p
    return max(0.0,min(0.25,(p*b-q)/b))*fraction
