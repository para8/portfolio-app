import os
from datetime import datetime, timezone
from typing import Optional

import jwt as pyjwt
from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session

import models
import schemas
from auth import get_current_user
from database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Portfolio Tracker")

# ── Static files ──────────────────────────────────────────────────────────────
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(_BASE_DIR, "frontend")), name="static")


@app.get("/")
def root():
    return FileResponse(os.path.join(_BASE_DIR, "frontend", "index.html"))


@app.get("/api/v1/health")
def health():
    return {"status": "ok"}


@app.get("/api/v1/me")
def me(request: Request, db: Session = Depends(get_db)):
    """Temporary debug endpoint — JWT decode + DB row count."""
    from auth import _jwks_client
    auth = request.headers.get("Authorization", "")
    token = auth.removeprefix("Bearer ").strip()
    if not token:
        return {"error": "no token", "sub": None, "txn_count": None}
    try:
        signing_key = _jwks_client().get_signing_key_from_jwt(token)
        payload = pyjwt.decode(token, signing_key.key, algorithms=["ES256"], audience="authenticated")
        uid = payload.get("sub")
        count = db.query(models.Transaction).filter_by(user_id=uid).count()
        return {"verified": True, "sub": uid, "txn_count": count}
    except Exception as e:
        try:
            unverified = pyjwt.decode(token, options={"verify_signature": False})
            uid_unverified = unverified.get("sub")
        except Exception:
            uid_unverified = None
        return {"verified": False, "error": str(e), "sub_unverified": uid_unverified}


@app.get("/api/v1/auth-config")
def auth_config():
    """Public endpoint — returns Supabase public config for the frontend."""
    return JSONResponse({
        "supabase_url": os.environ["SUPABASE_URL"].strip(),
        "supabase_anon_key": os.environ["SUPABASE_ANON_KEY"].strip(),
    })


# ── Helpers ───────────────────────────────────────────────────────────────────

def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def get_display_name(ticker_obj) -> str:
    """Return display_name if set, otherwise fall back to name."""
    return ticker_obj.display_name or ticker_obj.name


def historical_fx(date_str: str, fx_rows: list) -> float:
    """Return the applicable USD→INR rate for a transaction date."""
    ym = date_str[:7]
    for row in sorted(fx_rows, key=lambda r: r.from_ym, reverse=True):
        if ym >= row.from_ym:
            return row.rate
    return 74.0


# ── Positions ─────────────────────────────────────────────────────────────────

@app.get("/api/v1/positions", response_model=schemas.PositionsResponse)
def get_positions(
    fx_rate: Optional[float] = Query(None),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    # Determine effective FX rate
    if fx_rate is None:
        cfg = db.query(models.Config).filter_by(user_id=user_id, key="fx_rate_usd_inr").first()
        fx_rate = float(cfg.value) if cfg else 86.0

    transactions = db.query(models.Transaction).filter_by(user_id=user_id).all()
    tickers_map = {t.ticker: t for t in db.query(models.Ticker).filter_by(user_id=user_id).all()}
    prices_map = {p.ticker: p.price for p in db.query(models.Price).filter_by(user_id=user_id).all()}
    fx_rows = db.query(models.FxHistory).filter_by(user_id=user_id).all()
    categories_map = {c.id: c for c in db.query(models.Category).filter_by(user_id=user_id).all()}
    sectors_map = {s.id: s for s in db.query(models.Sector).filter_by(user_id=user_id).all()}

    # Group transactions by ticker
    txn_by_ticker: dict[str, list] = {}
    for t in transactions:
        txn_by_ticker.setdefault(t.ticker, []).append(t)

    positions = []
    for ticker, txns in txn_by_ticker.items():
        ticker_obj = tickers_map.get(ticker)
        if not ticker_obj:
            continue
        currency = ticker_obj.currency

        buys = [t for t in txns if t.type == "Buy"]
        sells = [t for t in txns if t.type == "Sell"]

        buy_units = sum(t.units for t in buys)
        sell_units = sum(t.units for t in sells)
        held_units = buy_units - sell_units

        if held_units < 0.001:
            continue

        # Cost basis in INR
        if currency == "USD":
            total_cost_inr = sum(t.units * t.price * historical_fx(t.date, fx_rows) for t in buys)
            sell_cost_inr = sum(t.units * t.price * historical_fx(t.date, fx_rows) for t in sells)
            invested_inr = total_cost_inr - sell_cost_inr
        else:
            total_cost = sum(t.units * t.price for t in buys)
            sell_cost = sum(t.units * t.price for t in sells)
            invested_inr = total_cost - sell_cost

        # Avg buy price in native currency
        total_cost_native = sum(t.units * t.price for t in buys)
        avg_buy_price = total_cost_native / buy_units if buy_units > 0 else 0

        current_price = prices_map.get(ticker)
        if current_price is not None:
            value_inr = held_units * current_price * (fx_rate if currency == "USD" else 1)
            pnl_inr = value_inr - invested_inr
            pnl_pct = (pnl_inr / invested_inr * 100) if invested_inr > 0 else None
        else:
            value_inr = None
            pnl_inr = None
            pnl_pct = None

        sector_name = None
        if ticker_obj.sector_id and ticker_obj.sector_id in sectors_map:
            sector_name = sectors_map[ticker_obj.sector_id].name

        positions.append({
            "ticker": ticker,
            "name": get_display_name(ticker_obj),
            "display_name": ticker_obj.display_name,
            "currency": currency,
            "category_id": ticker_obj.category_id,
            "sector": sector_name,
            "held_units": held_units,
            "avg_buy_price": avg_buy_price,
            "current_price": current_price,
            "invested_inr": invested_inr,
            "value_inr": value_inr,
            "pnl_inr": pnl_inr,
            "pnl_pct": pnl_pct,
        })

    # Total portfolio value for weight calculation
    total_value = sum(p["value_inr"] for p in positions if p["value_inr"] is not None)

    for p in positions:
        if p["value_inr"] is not None and total_value > 0:
            p["weight_pct"] = p["value_inr"] / total_value * 100
        else:
            p["weight_pct"] = None

    # Summary
    priced = [p for p in positions if p["value_inr"] is not None]
    total_invested = sum(p["invested_inr"] for p in positions)
    total_value_inr = sum(p["value_inr"] for p in priced) if priced else None
    priced_invested = sum(p["invested_inr"] for p in priced)
    total_pnl = (total_value_inr - priced_invested) if total_value_inr is not None else None
    total_pnl_pct = (total_pnl / priced_invested * 100) if (total_pnl is not None and priced_invested > 0) else None

    usd_positions = [p for p in positions if p["currency"] == "USD"]
    usd_val = sum(p["value_inr"] if p["value_inr"] is not None else p["invested_inr"] for p in usd_positions)
    total_known = sum(p["value_inr"] if p["value_inr"] is not None else p["invested_inr"] for p in positions)
    usd_exposure_pct = (usd_val / total_known * 100) if total_known > 0 else None

    summary = schemas.PositionSummary(
        total_invested_inr=total_invested,
        total_value_inr=total_value_inr,
        total_pnl_inr=total_pnl,
        total_pnl_pct=total_pnl_pct,
        usd_exposure_pct=usd_exposure_pct,
        priced_count=len(priced),
        total_count=len(positions),
    )

    # Group by category
    cat_groups: dict[int, dict] = {}
    for p in positions:
        cat_id = p["category_id"]
        cat_obj = categories_map.get(cat_id) if cat_id else None
        cat_name = cat_obj.name if cat_obj else "Uncategorized"
        cat_color = cat_obj.color if cat_obj else "#888888"

        if cat_id not in cat_groups:
            cat_groups[cat_id] = {
                "category": cat_name,
                "color": cat_color,
                "invested_inr": 0,
                "value_known": 0,
                "invested_known": 0,
                "has_prices": False,
                "positions": [],
            }
        g = cat_groups[cat_id]
        g["invested_inr"] += p["invested_inr"]
        if p["value_inr"] is not None:
            g["value_known"] += p["value_inr"]
            g["invested_known"] += p["invested_inr"]
            g["has_prices"] = True
        g["positions"].append(schemas.PositionItem(
            ticker=p["ticker"],
            name=p["name"],
            display_name=p["display_name"],
            sector=p["sector"],
            held_units=p["held_units"],
            avg_buy_price=p["avg_buy_price"],
            current_price=p["current_price"],
            currency=p["currency"],
            invested_inr=p["invested_inr"],
            value_inr=p["value_inr"],
            pnl_inr=p["pnl_inr"],
            pnl_pct=p["pnl_pct"],
            weight_pct=p["weight_pct"],
        ))

    by_category = []
    for g in cat_groups.values():
        val = g["value_known"] if g["has_prices"] else None
        pnl = (val - g["invested_known"]) if val is not None else None
        pnl_pct = (pnl / g["invested_known"] * 100) if (pnl is not None and g["invested_known"] > 0) else None
        weight = (val / total_value * 100) if (val is not None and total_value > 0) else None
        by_category.append(schemas.CategoryGroup(
            category=g["category"],
            color=g["color"],
            invested_inr=g["invested_inr"],
            value_inr=val,
            pnl_inr=pnl,
            pnl_pct=pnl_pct,
            weight_pct=weight,
            positions=sorted(g["positions"], key=lambda x: x.value_inr or x.invested_inr, reverse=True),
        ))

    by_category.sort(key=lambda x: x.value_inr or x.invested_inr, reverse=True)

    return schemas.PositionsResponse(
        fx_rate=fx_rate,
        summary=summary,
        by_category=by_category,
    )


# ── Tickers ───────────────────────────────────────────────────────────────────

@app.get("/api/v1/tickers")
def get_tickers(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    tickers = db.query(models.Ticker).filter_by(user_id=user_id).all()
    categories = {c.id: c for c in db.query(models.Category).filter_by(user_id=user_id).all()}
    sectors = {s.id: s for s in db.query(models.Sector).filter_by(user_id=user_id).all()}
    result = []
    for t in tickers:
        result.append({
            "ticker": t.ticker,
            "name": t.name,
            "display_name": t.display_name,
            "currency": t.currency,
            "category_id": t.category_id,
            "sector_id": t.sector_id,
            "category_name": categories[t.category_id].name if t.category_id and t.category_id in categories else None,
            "sector_name": sectors[t.sector_id].name if t.sector_id and t.sector_id in sectors else None,
        })
    return result


@app.post("/api/v1/tickers", status_code=201)
def create_ticker(
    payload: schemas.TickerCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    existing = db.query(models.Ticker).filter_by(user_id=user_id, ticker=payload.ticker).first()
    if existing:
        raise HTTPException(status_code=409, detail="Ticker already exists")
    t = models.Ticker(
        user_id=user_id,
        ticker=payload.ticker,
        name=payload.name,
        display_name=payload.display_name or None,
        currency=payload.currency,
        category_id=payload.category_id,
        sector_id=payload.sector_id,
        created_at=now_iso(),
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return {"ticker": t.ticker, "name": t.name, "display_name": t.display_name,
            "currency": t.currency, "category_id": t.category_id, "sector_id": t.sector_id}


# ── Transactions ──────────────────────────────────────────────────────────────

@app.get("/api/v1/transactions")
def get_transactions(
    ticker: Optional[str] = None,
    broker_id: Optional[int] = None,
    type: Optional[str] = None,
    days: Optional[int] = None,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    q = db.query(models.Transaction).filter_by(user_id=user_id)
    if ticker:
        q = q.filter(models.Transaction.ticker == ticker)
    if broker_id:
        q = q.filter(models.Transaction.broker_id == broker_id)
    if type:
        q = q.filter(models.Transaction.type == type)
    if days:
        from datetime import date, timedelta
        cutoff = (date.today() - timedelta(days=days)).isoformat()
        q = q.filter(models.Transaction.date >= cutoff)

    txns = q.order_by(models.Transaction.date.desc()).all()
    brokers = {b.id: b.name for b in db.query(models.Broker).filter_by(user_id=user_id).all()}
    result = []
    for t in txns:
        result.append({
            "id": t.id,
            "date": t.date,
            "ticker": t.ticker,
            "type": t.type,
            "units": t.units,
            "price": t.price,
            "amount": t.amount,
            "broker_id": t.broker_id,
            "broker_name": brokers.get(t.broker_id) if t.broker_id else None,
            "created_at": t.created_at,
        })
    return result


@app.post("/api/v1/transactions", status_code=201)
def create_transaction(
    payload: schemas.TransactionCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    ticker_obj = db.query(models.Ticker).filter_by(user_id=user_id, ticker=payload.ticker).first()
    if not ticker_obj:
        raise HTTPException(status_code=404, detail="Ticker not found")
    t = models.Transaction(
        user_id=user_id,
        date=payload.date,
        ticker=payload.ticker,
        type=payload.type,
        units=payload.units,
        price=payload.price,
        amount=payload.units * payload.price,
        broker_id=payload.broker_id,
        created_at=now_iso(),
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return {"id": t.id, "date": t.date, "ticker": t.ticker, "type": t.type,
            "units": t.units, "price": t.price, "amount": t.amount, "broker_id": t.broker_id}


@app.delete("/api/v1/transactions/{txn_id}", status_code=204)
def delete_transaction(
    txn_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    t = db.query(models.Transaction).filter_by(id=txn_id, user_id=user_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Transaction not found")
    db.delete(t)
    db.commit()


# ── Prices ────────────────────────────────────────────────────────────────────

@app.get("/api/v1/prices")
def get_prices(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    prices = db.query(models.Price).filter_by(user_id=user_id).all()
    return {p.ticker: p.price for p in prices}


@app.put("/api/v1/prices/{ticker}")
def update_price(
    ticker: str,
    payload: schemas.PriceUpdate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    p = db.query(models.Price).filter_by(user_id=user_id, ticker=ticker).first()
    if p:
        p.price = payload.price
        p.updated_at = now_iso()
    else:
        p = models.Price(user_id=user_id, ticker=ticker, price=payload.price, updated_at=now_iso())
        db.add(p)
    db.commit()
    return {"ticker": ticker, "price": payload.price, "updated_at": p.updated_at}


@app.get("/api/v1/prices/detail")
def get_prices_detail(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    prices = db.query(models.Price).filter_by(user_id=user_id).all()
    return [{"ticker": p.ticker, "price": p.price, "updated_at": p.updated_at} for p in prices]


# ── Categories ────────────────────────────────────────────────────────────────

@app.get("/api/v1/categories")
def get_categories(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    return db.query(models.Category).filter_by(user_id=user_id).all()


@app.post("/api/v1/categories", status_code=201)
def create_category(
    payload: schemas.CategoryCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    c = models.Category(user_id=user_id, name=payload.name, color=payload.color)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


# ── Sectors ───────────────────────────────────────────────────────────────────

@app.get("/api/v1/sectors")
def get_sectors(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    return db.query(models.Sector).filter_by(user_id=user_id).all()


@app.post("/api/v1/sectors", status_code=201)
def create_sector(
    payload: schemas.SectorCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    s = models.Sector(user_id=user_id, name=payload.name, color=payload.color)
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


# ── Brokers ───────────────────────────────────────────────────────────────────

@app.get("/api/v1/brokers")
def get_brokers(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    return db.query(models.Broker).filter_by(user_id=user_id).all()


# ── FX History ────────────────────────────────────────────────────────────────

@app.get("/api/v1/fx-history")
def get_fx_history(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    return db.query(models.FxHistory).filter_by(user_id=user_id).order_by(models.FxHistory.from_ym.desc()).all()


@app.post("/api/v1/fx-history", status_code=201)
def create_fx_history(
    payload: schemas.FxHistoryCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    row = models.FxHistory(user_id=user_id, from_ym=payload.from_ym, rate=payload.rate)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


# ── Config ────────────────────────────────────────────────────────────────────

@app.get("/api/v1/config/{key}")
def get_config(
    key: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    c = db.query(models.Config).filter_by(user_id=user_id, key=key).first()
    if not c:
        raise HTTPException(status_code=404, detail="Config key not found")
    return {"key": c.key, "value": c.value, "updated_at": c.updated_at}


@app.put("/api/v1/config/{key}")
def set_config(
    key: str,
    payload: schemas.ConfigUpdate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    c = db.query(models.Config).filter_by(user_id=user_id, key=key).first()
    if c:
        c.value = payload.value
        c.updated_at = now_iso()
    else:
        c = models.Config(user_id=user_id, key=key, value=payload.value, updated_at=now_iso())
        db.add(c)
    db.commit()
    return {"key": c.key, "value": c.value, "updated_at": c.updated_at}
