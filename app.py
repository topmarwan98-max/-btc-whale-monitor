import asyncio, json, os
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import websockets

app = FastAPI(title='BTC Whale Monitor')
S = {'price': None, 'buy': 0.0, 'sell': 0.0, 'large_buy': 0, 'large_sell': 0, 'connected': False, 'updated': None, 'error': None}
THRESHOLD = float(os.getenv('LARGE_TRADE_USDT', '100000'))

async def stream():
    url = 'wss://stream.binance.com:9443/ws/btcusdt@trade'
    while True:
        try:
            async with websockets.connect(url, ping_interval=20, ping_timeout=20) as ws:
                S['connected'] = True
                S['error'] = None
                async for raw in ws:
                    d = json.loads(raw)
                    price, qty = float(d['p']), float(d['q'])
                    value = price * qty
                    S['price'] = price
                    if d['m']:
                        S['sell'] += value
                        if value >= THRESHOLD: S['large_sell'] += 1
                    else:
                        S['buy'] += value
                        if value >= THRESHOLD: S['large_buy'] += 1
                    if S['buy'] + S['sell'] > 50000000:
                        S['buy'] *= .5
                        S['sell'] *= .5
                    S['updated'] = datetime.now(timezone.utc).isoformat()
        except Exception as e:
            S['connected'] = False
            S['error'] = str(e)[:160]
            await asyncio.sleep(5)

@app.on_event('startup')
async def start(): asyncio.create_task(stream())

@app.get('/health')
async def health(): return {'ok': True, 'connected': S['connected']}

@app.get('/api/state')
async def state(): return S

@app.get('/', response_class=HTMLResponse)
async def home(): return PAGE

PAGE = '''<!doctype html><html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>BTC Whale Monitor</title><style>body{font-family:system-ui;background:#0b1220;color:#edf2f7;padding:16px;max-width:650px;margin:auto}.card{background:#172338;border:1px solid #30415d;border-radius:14px;padding:16px;margin:12px 0}.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}.big{font-size:27px;font-weight:bold}.muted{color:#a9b8cc}.green{color:#4ade80}.red{color:#fb7185}</style><h2>BTC Whale Monitor</h2><p class="muted">Live Binance BTCUSDT spot trades · monitoring only</p><div class="card"><b id="conn">Connecting…</b><p class="muted">BTCUSDT price</p><div class="big" id="price">—</div></div><div class="grid"><div class="card"><p class="muted">Aggressive buy flow</p><div class="big green" id="buy">—</div></div><div class="card"><p class="muted">Aggressive sell flow</p><div class="big red" id="sell">—</div></div><div class="card"><p class="muted">Large buy trades</p><div class="big" id="lb">0</div></div><div class="card"><p class="muted">Large sell trades</p><div class="big" id="ls">0</div></div></div><div class="card"><b>Flow balance (not probability or signal)</b><p id="balance">Waiting for data</p><p class="muted" id="updated"></p></div><div class="card"><b>Limitations</b><p class="muted">Large trades are threshold-based and do not identify a trader or prove whale activity. This starter has no order-book depth, liquidation feed, open interest, Telegram alerts, or trading execution. It is not a trading recommendation.</p></div><script>async function tick(){try{const d=await (await fetch('/api/state')).json();document.getElementById('conn').textContent=d.connected?'LIVE':'DISCONNECTED';document.getElementById('price').textContent=d.price?'$'+Number(d.price).toLocaleString():'—';document.getElementById('buy').textContent='$'+Math.round(d.buy).toLocaleString();document.getElementById('sell').textContent='$'+Math.round(d.sell).toLocaleString();document.getElementById('lb').textContent=d.large_buy;document.getElementById('ls').textContent=d.large_sell;const t=d.buy+d.sell;document.getElementById('balance').textContent=t?('Buy '+(100*d.buy/t).toFixed(1)+'% · Sell '+(100*d.sell/t).toFixed(1)+'%'):'Waiting for data';document.getElementById('updated').textContent=d.updated||'No trades received yet'}catch(e){document.getElementById('conn').textContent='API ERROR'}}tick();setInterval(tick,2000);</script></html>'''
