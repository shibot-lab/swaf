# IDX Pro Intelligence

A self-contained Streamlit trading research terminal rebuilt from the capabilities exposed by the original `app.py` — without `stock_data.py`, `shared_analysis.py`, `enhanced_analyzer.py`, `market_timing.py`, `telegram_bot.py`, or `config.py` dependencies.

## Highlights

- IDX scanner with technical score, momentum, volume anomaly, trend and pattern detection
- Early-mover / breakout / accumulation profiles
- Entry, stop-loss, TP1/TP2 and risk-based position sizing
- Strategy backtesting with equity curve, trade log, Profit Factor, Sharpe and drawdown
- Monte Carlo outcome distribution
- ML signal predictor with probability, feature importance and regime awareness
- Fundamental snapshot + DCF valuation
- Options chain / Greeks when the Yahoo Finance instrument exposes options
- Smart watchlist and local alert engine
- Paper trading simulator with persistent session state
- Market timing / pre-post session diagnostics
- Portfolio risk dashboard
- Single-stock "Command Center" report
- **Signal Outcome Tracker** to record scanner candidates and measure 1D/3D/5D/10D returns, MFE/MAE, TP1/SL outcomes and score-bucket quality

## Run

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

The app is research software, not financial advice. Market data availability and Yahoo Finance coverage can change.

## Development direction

SWAF is being developed as a feedback-driven research terminal: **market discovery → candidate capture → outcome tracking → signal calibration → adaptive ranking**. The Outcome Tracker stores local observations under `.swaf_data/` (ignored by Git) so experimental results are not committed into the repository.
