# TradeSignal Backend

FastAPI backend implementing the full pipeline: market data ingestion → long-term
& short-term signal engines → AI analysis → Firestore storage → subscription-gated
delivery to the Next.js frontend.

## Instruments (fixed, per product decision)
- **Forex** (Twelve Data): XAU/USD, EUR/USD
- **Crypto** (CoinGecko): BTCUSDT, SOLUSDT
- **Indian Stocks** (Angel One SmartAPI): ITC, WIPRO, HDFCBANK — full BUY/SELL signals
- **Index** (Angel One SmartAPI): NIFTY50 — **trend/direction only**, no entry/SL/TP

## Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in real API keys and secrets
```

Place your Firebase service account JSON at `app/firebase/service_account.json`
(path configurable via `FIREBASE_CREDENTIALS_PATH`).

## Run
```bash
uvicorn app.main:app --reload --port 8000
```
API docs available at `http://localhost:8000/docs`.

## Pipeline flow
1. **Scheduler** (`app/market/scheduler.py`) polls market data every minute,
   runs the long-term engine hourly, and the short-term engine every 15 minutes.
2. **Market Data Service** fetches → validates → cleans → caches data from all
   three sources before handing it to engines.
3. **Long-Term Engine**: Daily Trend → EMA50 → EMA200 → RSI14 → Trend Decision
   → 1H Entry confirmation → ATR-based Risk → BUY/SELL/NO_TRADE → Confidence.
4. **Short-Term Engine**: 4H Trend (EMA5/10/20/30 stack) → 1H RSI Confirmation
   → 15M Entry → ATR-based Risk:Reward → BUY/SELL/NO_TRADE → Confidence.
5. **AI Analysis Engine**: reads ONLY engine output (never raw market data),
   calls the Anthropic API, and produces professional analysis + trade/risk
   summaries.
6. **Storage**: live signal (overwritten) + append-only history in Firestore.
7. **Payment**: Razorpay order creation → client payment → webhook verification
   (source of truth) → subscription activation → Firestore update → dashboard
   unlock.

## Known data limitations to revisit
- CoinGecko free tier has no true 15-minute candles; the crypto service uses
  the finest available granularity (30-min via `days=1`) as an approximation.
- Twelve Data free tier is rate-limited (8 req/min, 800/day) — with 2 forex
  pairs × 4 timeframes, monitor usage as instruments/timeframes are added.
- Angel One requires a daily TOTP-based re-login; the session is cached and
  refreshed automatically but depends on a valid TOTP secret being configured.
