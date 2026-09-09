APP_NAME = "IDX Pro Intelligence"
DEFAULT_TICKERS = ["BBCA.JK","BBRI.JK","BMRI.JK","TLKM.JK","ASII.JK","ICBP.JK","INDF.JK","ANTM.JK","MDKA.JK","GOTO.JK","UNVR.JK","ADRO.JK","ITMG.JK","PTBA.JK","PGAS.JK"]
SECTORS = {
    "Banking": ["BBCA.JK","BBRI.JK","BMRI.JK","BBNI.JK","BRIS.JK","BBTN.JK"],
    "Telecom": ["TLKM.JK","EXCL.JK","ISAT.JK"],
    "Consumer": ["ICBP.JK","INDF.JK","UNVR.JK","MYOR.JK"],
    "Mining": ["ANTM.JK","MDKA.JK","PTBA.JK","ITMG.JK","ADRO.JK"],
    "Industrial": ["ASII.JK","INCO.JK","SMGR.JK"],
    "Energy": ["PGAS.JK","AKRA.JK","MEDC.JK"],
    "Technology": ["GOTO.JK","BUKA.JK"],
}
ALL_TICKERS = sorted(set(DEFAULT_TICKERS + [x for v in SECTORS.values() for x in v]))
