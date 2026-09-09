import numpy as np, pandas as pd

def analytics(positions):
    if not positions:return {"value":0,"weight":{},"concentration":0}
    df=pd.DataFrame(positions); df["value"]=df.qty*df.price; total=df.value.sum(); weights=(df.set_index("ticker").value/total).to_dict() if total else {}
    concentration=max(weights.values()) if weights else 0
    return {"value":float(total),"weight":weights,"concentration":float(concentration)}
