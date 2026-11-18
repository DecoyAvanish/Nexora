# Nexora

Nexora is a personal paper-trading dashboard with Firebase authentication, live market data, portfolio tracking, and an LSTM-based next-session price forecast.

## Architecture

- `src/` — React client and Firebase user experience
- `backend/` — Flask API for market search, quotes, history, and predictions
- `model_weights.pth` and `scaler.pkl` — trained prediction artifacts
- `backend/tests/` — isolated API tests using provider fakes

The browser never receives a market-provider secret. It talks to the Flask API, which validates inputs and returns explicit errors when upstream data is unavailable. Nexora does not fabricate market prices.

## Local setup

Requirements: Node.js 18+, npm, and Python 3.9+.

```bash
cp .env.example .env
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
npm install
```

The default configuration uses Yahoo Finance without an API key.

Start the backend:

```bash
.venv/bin/python -m backend.app
```

In a second terminal, start the client:

```bash
npm start
```

Open [http://localhost:3000](http://localhost:3000). The API listens on [http://localhost:5001](http://localhost:5001).

## API

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Readiness and model-artifact status |
| `GET` | `/api/search?q=apple` | Search equities and ETFs |
| `GET` | `/api/quote/AAPL` | Latest validated quote |
| `GET` | `/api/history/AAPL?period=6mo` | Historical price and volume series |
| `GET` | `/api/predict/AAPL` | Historical series plus LSTM forecast |
| `GET` | `/api/news/AAPL?company=Apple%20Inc` | Recent company news from GDELT |
| `GET` | `/api/sentiment/AAPL?company=Apple%20Inc` | FinBERT sentiment for recent real headlines |
| `GET` | `/api/score/AAPL?company=Apple%20Inc` | Explainable 1–10 score and green/red signal |

Errors use a consistent shape:

```json
{
  "error": {
    "code": "invalid_symbol",
    "message": "Enter a valid stock symbol."
  }
}
```

## Tests

```bash
.venv/bin/python -m pytest backend/tests -q
CI=true npm test -- --watchAll=false
```

## Cross-sectional model training

The live score works immediately from technical factors and real FinBERT news sentiment. For a true market-relative decile model, prepare a point-in-time CSV or Parquet dataset with `date`, `ticker`, `fwd_ret_63d`, `bench_ret_63d`, and numeric feature columns, then run:

```bash
.venv/bin/python -m backend.training.cross_sectional data/features.parquet
```

The trainer ranks every feature cross-sectionally by date, applies a 63-trading-day embargo, runs walk-forward LightGBM folds, and exports the model, out-of-sample scores, AUC, information coefficient, and top-versus-bottom-decile return spread. Do not train it on restated or survivorship-biased data.

## Security notes

- Keep `.env` and Firebase service credentials out of Git.
- Firebase's browser configuration identifies the project; Firestore Security Rules must still restrict each user to their own document.
- Predictions are experimental and are not financial advice.
