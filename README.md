# Portfolio Tracker

A local-first portfolio tracker with a FastAPI backend and vanilla JS frontend.

## Setup

### 1. Install dependencies

```bash
cd portfolio-app
pip install -r requirements.txt
```

### 2. Seed the database

Run once with `portfolio_v4.html` as the data source:

```bash
python seed.py ~/Downloads/portfolio_v4.html
```

This populates all 8 tables (tickers, transactions, prices, categories, sectors, brokers, fx_history, config).

### 3. Start the server

```bash
uvicorn main:app --reload
```

Open http://localhost:8000 in your browser.

To use a different port:
```bash
PORT=8080 uvicorn main:app --reload --port 8080
```

## Views

| View | Description |
|------|-------------|
| **Positions** | Category-grouped holdings with P&L, expandable to individual positions |
| **Insights** | Allocation pie chart by category + sector bar chart |
| **Transactions** | Full transaction history with broker/type/date filters |
| **Prices** | Update prices per ticker (stalest first) |
| **Add** | Add new tickers or transactions |

## Notes

- `portfolio.db` is never deleted or truncated by the app.
- FX rate input re-fetches positions on the fly; persisted on blur.
- Cost basis uses historical quarterly FX rates from `fx_history` table.
- Current value always uses the live FX rate from the sidebar input.
