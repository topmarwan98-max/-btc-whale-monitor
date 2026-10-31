# BTC Whale Monitor

Educational live monitor for Binance public BTCUSDT spot trades.

## Render deployment
Build command: `pip install -r requirements.txt`
Start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
Optional environment variable: `LARGE_TRADE_USDT=100000`.

## Limitations
This starter displays public trade flow and threshold-based large-trade counts only. It does not identify traders, provide verified whale attribution, or include order-book depth, liquidation data, open interest, Telegram alerts, or trading execution. Flow balance is not a probability or trading recommendation. Never put API keys or bot tokens in this repository.
