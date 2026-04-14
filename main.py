import os
from datetime import datetime, timezone
from typing import Optional

import jwt as pyjwt
from fastapi import FastAPI, Depends, HTTPException, Query, Request, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session

import models
import schemas
from auth import get_current_user
from database import engine, get_db
from parsers import groww_mf, vested, groww_stocks

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


def get_short_name(ticker_obj) -> str:
    """Return short_name if set, otherwise fall back to name."""
    return ticker_obj.short_name or ticker_obj.name


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
    tickers_map = {t.id: t for t in db.query(models.Ticker).filter_by(user_id=user_id).all()}
    prices_map = {p.ticker_id: p.price for p in db.query(models.Price).filter_by(user_id=user_id).all()}
    fx_rows = db.query(models.FxHistory).all()
    categories_map = {c.id: c for c in db.query(models.Category).filter_by(user_id=user_id).all()}
    sectors_map = {s.id: s for s in db.query(models.Sector).filter_by(user_id=user_id).all()}

    # Group transactions by ticker_id
    txn_by_ticker_id: dict[int, list] = {}
    for t in transactions:
        txn_by_ticker_id.setdefault(t.ticker_id, []).append(t)

    positions = []
    for ticker_id, txns in txn_by_ticker_id.items():
        ticker_obj = tickers_map.get(ticker_id)
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

        current_price = prices_map.get(ticker_id)
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
            "ticker_id": ticker_id,
            "name": get_short_name(ticker_obj),
            "short_name": ticker_obj.short_name,
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
            ticker_id=p["ticker_id"],
            name=p["name"],
            short_name=p["short_name"],
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
            "id": t.id,
            "name": t.name,
            "short_name": t.short_name,
            "currency": t.currency,
            "category_id": t.category_id,
            "sector_id": t.sector_id,
            "category_name": categories[t.category_id].name if t.category_id and t.category_id in categories else None,
            "sector_name": sectors[t.sector_id].name if t.sector_id and t.sector_id in sectors else None,
            "symbol": t.symbol,
        })
    return result


@app.post("/api/v1/tickers", status_code=201)
def create_ticker(
    payload: schemas.TickerCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    existing = db.query(models.Ticker).filter_by(user_id=user_id, name=payload.name).first()
    if existing:
        raise HTTPException(status_code=409, detail="Ticker already exists")
    t = models.Ticker(
        user_id=user_id,
        name=payload.name,
        short_name=payload.short_name or None,
        currency=payload.currency,
        category_id=payload.category_id,
        sector_id=payload.sector_id,
        created_at=now_iso(),
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return {"id": t.id, "name": t.name, "short_name": t.short_name,
            "currency": t.currency, "category_id": t.category_id, "sector_id": t.sector_id}


# ── Import ────────────────────────────────────────────────────────────────────

@app.post("/api/v1/import/parse")
async def import_parse(
    file: UploadFile = File(...),
    currency: str = Form(...),
    source: str = Form("groww_mf"),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    file_bytes = await file.read()
    try:
        if source == 'vested':
            rows = vested.parse(file_bytes)
        elif source == 'groww_stocks':
            rows = groww_stocks.parse(file_bytes)
        else:
            rows = groww_mf.parse(file_bytes)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse file: {e}")

    # Build name→ticker lookup for this user
    tickers = db.query(models.Ticker).filter_by(user_id=user_id).all()
    tickers_by_name = {t.name.lower(): t for t in tickers}

    result_txns = []
    unresolved_set = []

    for row in rows:
        name_lower = row['name'].lower()
        ticker_obj = tickers_by_name.get(name_lower)
        ticker_id = ticker_obj.id if ticker_obj else None

        if ticker_obj:
            # Dedup: match on ticker_id + date + type + amount
            existing = db.query(models.Transaction).filter_by(
                user_id=user_id,
                ticker_id=ticker_id,
                date=row['date'],
                type=row['type'],
            ).filter(models.Transaction.amount == row['amount']).first()
            status = "duplicate" if existing else "new"
        else:
            status = "new"
            if row['name'] not in unresolved_set:
                unresolved_set.append(row['name'])

        result_txns.append({
            "name": row['name'],
            "date": row['date'],
            "type": row['type'],
            "units": row['units'],
            "price": row['price'],
            "amount": row['amount'],
            "currency": currency,
            "ticker_id": ticker_id,
            "status": status,
        })

    return {"transactions": result_txns, "unresolved_funds": unresolved_set}


@app.post("/api/v1/import/confirm")
def import_confirm(
    payload: schemas.ImportConfirmPayload,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    # Step 1: create new tickers (DB unique constraint on (user_id, name) handles dedup)
    for nt in payload.new_tickers:
        t = models.Ticker(
            user_id=user_id,
            name=nt.name,
            short_name=nt.short_name or None,
            currency=payload.currency,
            category_id=nt.category_id,
            sector_id=nt.sector_id,
            created_at=now_iso(),
        )
        db.add(t)
    db.commit()

    # Rebuild name lookup (includes newly created tickers)
    tickers_by_name = {t.name.lower(): t for t in db.query(models.Ticker).filter_by(user_id=user_id).all()}

    # Step 2: insert transactions (re-dedup)
    imported = 0
    skipped = 0
    for txn in payload.transactions:
        # Resolve ticker_id from fund name
        ticker_obj = tickers_by_name.get(txn.fund_name.lower())
        if not ticker_obj:
            skipped += 1
            continue
        ticker_id = ticker_obj.id
        # Dedup check
        existing = db.query(models.Transaction).filter_by(
            user_id=user_id,
            ticker_id=ticker_id,
            date=txn.date,
            type=txn.type,
        ).filter(models.Transaction.amount == txn.amount).first()
        if existing:
            skipped += 1
            continue
        t = models.Transaction(
            user_id=user_id,
            date=txn.date,
            ticker_id=ticker_id,
            type=txn.type,
            units=txn.units,
            price=txn.price,
            amount=txn.amount,
            broker_id=payload.broker_id,
            created_at=now_iso(),
        )
        db.add(t)
        imported += 1

    db.commit()
    return {"imported": imported, "skipped": skipped}


# ── Transactions ──────────────────────────────────────────────────────────────

@app.get("/api/v1/transactions")
def get_transactions(
    ticker_id: Optional[int] = None,
    broker_id: Optional[int] = None,
    type: Optional[str] = None,
    days: Optional[int] = None,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    q = db.query(models.Transaction).filter_by(user_id=user_id)
    if ticker_id:
        q = q.filter(models.Transaction.ticker_id == ticker_id)
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
    tickers_map = {t.id: t for t in db.query(models.Ticker).filter_by(user_id=user_id).all()}
    fx_rows = db.query(models.FxHistory).all()
    result = []
    for t in txns:
        ticker_obj = tickers_map.get(t.ticker_id)
        if ticker_obj and ticker_obj.currency == "USD":
            amount_inr = round(t.amount * historical_fx(t.date, fx_rows))
        else:
            amount_inr = round(t.amount)
        result.append({
            "id": t.id,
            "date": t.date,
            "ticker_id": t.ticker_id,
            "ticker_name": get_short_name(ticker_obj) if ticker_obj else None,
            "type": t.type,
            "units": t.units,
            "price": t.price,
            "amount": t.amount,
            "broker_id": t.broker_id,
            "broker_name": brokers.get(t.broker_id) if t.broker_id else None,
            "created_at": t.created_at,
            "amount_inr": amount_inr,
        })
    return result


@app.post("/api/v1/transactions", status_code=201)
def create_transaction(
    payload: schemas.TransactionCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    ticker_obj = db.query(models.Ticker).filter_by(user_id=user_id, id=payload.ticker_id).first()
    if not ticker_obj:
        raise HTTPException(status_code=404, detail="Ticker not found")
    t = models.Transaction(
        user_id=user_id,
        date=payload.date,
        ticker_id=payload.ticker_id,
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
    return {"id": t.id, "date": t.date, "ticker_id": t.ticker_id, "type": t.type,
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
    return {str(p.ticker_id): p.price for p in prices}


@app.put("/api/v1/prices/{ticker_id}")
def update_price(
    ticker_id: int,
    payload: schemas.PriceUpdate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    p = db.query(models.Price).filter_by(user_id=user_id, ticker_id=ticker_id).first()
    if p:
        p.price = payload.price
        p.updated_at = now_iso()
    else:
        p = models.Price(user_id=user_id, ticker_id=ticker_id, price=payload.price, updated_at=now_iso())
        db.add(p)
    db.commit()
    return {"ticker_id": ticker_id, "price": payload.price, "updated_at": p.updated_at}


@app.get("/api/v1/prices/detail")
def get_prices_detail(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    prices = db.query(models.Price).filter_by(user_id=user_id).all()
    return [{"ticker_id": p.ticker_id, "price": p.price, "updated_at": p.updated_at} for p in prices]


# ── Categories ────────────────────────────────────────────────────────────────

@app.get("/api/v1/categories")
def get_categories(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    return db.query(models.Category).filter_by(user_id=user_id).all()


@app.post("/api/v1/categories", status_code=201, response_model=schemas.CategoryOut)
def create_category(
    payload: schemas.CategoryCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    # #region agent log
    import json, time as _time
    _log_path = "/Users/param/claudecode-portfoliotracker-v2/.cursor/debug.log"
    def _dbg(msg, data, hyp="?"):
        entry = json.dumps({"timestamp": int(_time.time()*1000), "hypothesisId": hyp, "location": "main.py:create_category", "message": msg, "data": data})
        open(_log_path, "a").write(entry + "\n")
    _dbg("create_category called", {"user_id": str(user_id), "name": payload.name, "color": payload.color}, "A/C/D")
    # #endregion
    try:
        c = models.Category(user_id=user_id, name=payload.name, color=payload.color)
        db.add(c)
        db.commit()
        db.refresh(c)
        # #region agent log
        _dbg("create_category success", {"id": c.id, "name": c.name}, "A/C/D")
        # #endregion
        return c
    except Exception as _e:
        db.rollback()
        # #region agent log
        import traceback as _tb
        _dbg("create_category EXCEPTION", {"type": type(_e).__name__, "msg": str(_e), "traceback": _tb.format_exc()}, "A/B/C/D")
        # #endregion
        raise


# ── Sectors ───────────────────────────────────────────────────────────────────

@app.get("/api/v1/sectors")
def get_sectors(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    return db.query(models.Sector).filter_by(user_id=user_id).all()


@app.post("/api/v1/sectors", status_code=201, response_model=schemas.SectorOut)
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


# ── Insights: Quarterly Invested ──────────────────────────────────────────────

@app.get("/api/v1/insights/quarterly-invested")
def quarterly_invested(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    from datetime import date as date_type

    transactions = (
        db.query(models.Transaction)
        .filter_by(user_id=user_id)
        .order_by(models.Transaction.date)
        .all()
    )
    if not transactions:
        return {"quarters": [], "categories": []}

    tickers_map = {t.id: t for t in db.query(models.Ticker).filter_by(user_id=user_id).all()}
    categories_map = {c.id: c for c in db.query(models.Category).filter_by(user_id=user_id).all()}
    fx_rows = db.query(models.FxHistory).all()

    def to_yq(d):
        return d.year, (d.month - 1) // 3 + 1

    def next_yq(y, q):
        return (y + 1, 1) if q == 4 else (y, q + 1)

    def quarter_end(y, q):
        last_month = q * 3
        last_day = {3: 31, 6: 30, 9: 30, 12: 31}[last_month]
        return date_type(y, last_month, last_day)

    first_date = date_type.fromisoformat(transactions[0].date)
    today = date_type.today()

    # Build ordered list of all quarters from first transaction to current
    quarters = []
    y, q = to_yq(first_date)
    cy, cq = to_yq(today)
    while (y, q) <= (cy, cq):
        quarters.append((y, q))
        y, q = next_yq(y, q)

    quarter_labels = [f"{y}-Q{q}" for y, q in quarters]
    quarter_end_dates = [quarter_end(y, q) for y, q in quarters]

    # Compute per-transaction INR amount (signed: buy +, sell -)
    txn_data = []
    for t in transactions:
        ticker = tickers_map.get(t.ticker_id)
        if not ticker:
            continue
        amount = t.units * t.price
        if ticker.currency == "USD":
            amount *= historical_fx(t.date, fx_rows)
        if t.type == "Sell":
            amount = -amount
        txn_data.append({
            "date": date_type.fromisoformat(t.date),
            "cat_id": ticker.category_id,
            "amount_inr": amount,
        })

    txn_data.sort(key=lambda x: x["date"])

    all_cat_ids = list({t["cat_id"] for t in txn_data})
    cumulative = {cat_id: 0.0 for cat_id in all_cat_ids}
    txn_idx = 0
    n = len(txn_data)

    snapshots = []
    for qend in quarter_end_dates:
        while txn_idx < n and txn_data[txn_idx]["date"] <= qend:
            td = txn_data[txn_idx]
            cumulative[td["cat_id"]] = cumulative.get(td["cat_id"], 0.0) + td["amount_inr"]
            txn_idx += 1
        snapshots.append({cat_id: max(0.0, val) for cat_id, val in cumulative.items()})

    result_categories = []
    for cat_id in all_cat_ids:
        cat_obj = categories_map.get(cat_id)
        result_categories.append({
            "name": cat_obj.name if cat_obj else "Uncategorized",
            "color": cat_obj.color if cat_obj else "#888888",
            "values": [snap.get(cat_id, 0.0) for snap in snapshots],
        })

    result_categories.sort(
        key=lambda c: c["values"][-1] if c["values"] else 0,
        reverse=True,
    )

    return {"quarters": quarter_labels, "categories": result_categories}


# ── Live Prices: update ticker symbol ────────────────────────────────────────

@app.put("/api/v1/tickers/{ticker_id}/symbol")
def update_ticker_symbol(
    ticker_id: int,
    payload: schemas.TickerSymbolUpdate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    t = db.query(models.Ticker).filter_by(id=ticker_id, user_id=user_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Ticker not found")
    t.symbol = payload.symbol.upper().strip()
    db.commit()
    return {"ticker_id": ticker_id, "symbol": t.symbol}


# ── MF: search schemes via mfapi.in ──────────────────────────────────────────

@app.get("/api/v1/mf/search")
def search_mf_schemes(
    q: str = Query(..., min_length=2),
    _user_id: str = Depends(get_current_user),
):
    import httpx
    try:
        resp = httpx.get(
            f"https://api.mfapi.in/mf/search",
            params={"q": q},
            timeout=10,
        )
        return resp.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"mfapi search failed: {e}")


# ── Live Prices: get latest stored price per ticker ──────────────────────────

@app.get("/api/v1/price-history/latest", response_model=schemas.PriceHistoryLatestResponse)
def get_latest_prices(
    ticker_ids: str = Query(...),   # comma-separated ints
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    ids = [int(i) for i in ticker_ids.split(",") if i.strip()]
    results = []
    for ticker_id in ids:
        ticker = db.query(models.Ticker).filter_by(id=ticker_id, user_id=user_id).first()
        if not ticker or not ticker.symbol:
            continue
        symbol = ticker.symbol.upper()
        row = (
            db.query(models.PriceHistory)
            .filter_by(symbol=symbol)
            .order_by(models.PriceHistory.date.desc())
            .first()
        )
        if row:
            results.append(schemas.PriceHistoryLatestResult(
                ticker_id=ticker_id, symbol=symbol,
                latest_close=row.close, latest_date=row.date,
            ))
    return schemas.PriceHistoryLatestResponse(results=results)


# ── Live Prices: fetch price history from Alpha Vantage ──────────────────────

@app.post("/api/v1/price-history/fetch", response_model=schemas.PriceHistoryFetchResponse)
def fetch_price_history(
    payload: schemas.PriceHistoryFetchRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    import httpx

    # 1. Get AV API key from user config
    cfg = db.query(models.Config).filter_by(user_id=user_id, key="av_api_key").first()
    if not cfg:
        raise HTTPException(status_code=400, detail="Alpha Vantage API key not configured")

    api_key = cfg.value.strip()
    results = []

    for ticker_id in payload.ticker_ids:
        # 2. Verify ownership and get symbol
        ticker = db.query(models.Ticker).filter_by(id=ticker_id, user_id=user_id).first()
        if not ticker:
            results.append(schemas.PriceHistoryFetchResult(
                ticker_id=ticker_id, symbol="", status="error",
                rows_stored=0, error_detail="Ticker not found"
            ))
            continue
        if not ticker.symbol:
            results.append(schemas.PriceHistoryFetchResult(
                ticker_id=ticker_id, symbol="", status="no_symbol", rows_stored=0
            ))
            continue

        symbol = ticker.symbol.upper()

        # 3. Call Alpha Vantage (sequential)
        try:
            url = (
                f"https://www.alphavantage.co/query"
                f"?function=TIME_SERIES_MONTHLY&symbol={symbol}&apikey={api_key}"
            )
            response = httpx.get(url, timeout=15)
            data = response.json()
        except Exception as e:
            results.append(schemas.PriceHistoryFetchResult(
                ticker_id=ticker_id, symbol=symbol, status="error",
                rows_stored=0, error_detail=str(e)
            ))
            continue

        # 4. Detect AV error responses (all arrive as HTTP 200)
        if "Note" in data or "Information" in data:
            results.append(schemas.PriceHistoryFetchResult(
                ticker_id=ticker_id, symbol=symbol, status="rate_limited", rows_stored=0
            ))
            break  # quota exhausted — stop processing remaining tickers

        if "Error Message" in data:
            results.append(schemas.PriceHistoryFetchResult(
                ticker_id=ticker_id, symbol=symbol, status="invalid_symbol", rows_stored=0
            ))
            continue

        # 5. Parse and upsert monthly rows
        monthly = data.get("Monthly Time Series", {})
        rows_stored = 0
        latest_close = None
        latest_date = None

        for date_str, values in monthly.items():
            close = float(values["4. close"])
            high  = float(values["2. high"])
            low   = float(values["3. low"])
            open_ = float(values["1. open"])

            existing = db.query(models.PriceHistory).filter_by(
                symbol=symbol, granularity="monthly", date=date_str
            ).first()
            if existing:
                existing.close = close
                existing.high = high
                existing.low = low
                existing.open = open_
                existing.fetched_at = now_iso()
            else:
                row = models.PriceHistory(
                    symbol=symbol, granularity="monthly", date=date_str,
                    close=close, high=high, low=low, open=open_,
                    source="alpha_vantage", fetched_at=now_iso()
                )
                db.add(row)

            rows_stored += 1
            if latest_date is None or date_str > latest_date:
                latest_date = date_str
                latest_close = close

        db.commit()
        results.append(schemas.PriceHistoryFetchResult(
            ticker_id=ticker_id, symbol=symbol, status="success",
            rows_stored=rows_stored, latest_close=latest_close, latest_date=latest_date
        ))

    return schemas.PriceHistoryFetchResponse(results=results)


# ── Live Prices: fetch NAV history from mfapi.in ─────────────────────────────

@app.post("/api/v1/price-history/fetch-mf", response_model=schemas.PriceHistoryFetchResponse)
def fetch_mf_price_history(
    payload: schemas.PriceHistoryFetchRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    import httpx
    from datetime import date as date_type, timedelta

    today = date_type.today()
    start = today - timedelta(days=365 * 2)
    end_str   = today.strftime("%d-%m-%Y")
    start_str = start.strftime("%d-%m-%Y")

    results = []

    for ticker_id in payload.ticker_ids:
        # 1. Verify ownership and get scheme code
        ticker = db.query(models.Ticker).filter_by(id=ticker_id, user_id=user_id).first()
        if not ticker:
            results.append(schemas.PriceHistoryFetchResult(
                ticker_id=ticker_id, symbol="", status="error",
                rows_stored=0, error_detail="Ticker not found"
            ))
            continue
        if not ticker.symbol:
            results.append(schemas.PriceHistoryFetchResult(
                ticker_id=ticker_id, symbol="", status="no_symbol", rows_stored=0
            ))
            continue

        scheme_code = ticker.symbol.strip()

        # 2. Call mfapi.in with 2-year date range
        try:
            url = f"https://api.mfapi.in/mf/{scheme_code}"
            response = httpx.get(url, params={"startDate": start_str, "endDate": end_str}, timeout=15)
            data = response.json()
        except Exception as e:
            results.append(schemas.PriceHistoryFetchResult(
                ticker_id=ticker_id, symbol=scheme_code, status="error",
                rows_stored=0, error_detail=str(e)
            ))
            continue

        # 3. Validate response
        if data.get("status") != "SUCCESS" or not data.get("data"):
            results.append(schemas.PriceHistoryFetchResult(
                ticker_id=ticker_id, symbol=scheme_code, status="invalid_symbol", rows_stored=0
            ))
            continue

        # 4. Upsert daily NAV records
        rows_stored  = 0
        latest_close = None
        latest_date  = None

        for entry in data["data"]:
            # Convert DD-MM-YYYY → YYYY-MM-DD
            raw_date = entry["date"]          # e.g. "13-04-2026"
            parts = raw_date.split("-")
            date_str = f"{parts[2]}-{parts[1]}-{parts[0]}"   # "2026-04-13"
            nav = float(entry["nav"])

            existing = db.query(models.PriceHistory).filter_by(
                symbol=scheme_code, granularity="daily", date=date_str
            ).first()
            if existing:
                existing.close     = nav
                existing.fetched_at = now_iso()
            else:
                row = models.PriceHistory(
                    symbol=scheme_code, granularity="daily", date=date_str,
                    close=nav, source="mfapi", fetched_at=now_iso()
                )
                db.add(row)

            rows_stored += 1
            if latest_date is None or date_str > latest_date:
                latest_date  = date_str
                latest_close = nav

        db.commit()
        results.append(schemas.PriceHistoryFetchResult(
            ticker_id=ticker_id, symbol=scheme_code, status="success",
            rows_stored=rows_stored, latest_close=latest_close, latest_date=latest_date
        ))

    return schemas.PriceHistoryFetchResponse(results=results)


# ── Insights: Market Value History ───────────────────────────────────────────

@app.get("/api/v1/insights/market-value-history", response_model=schemas.MarketValueResponse)
def market_value_history(
    category_ids: Optional[str] = Query(None),      # comma-separated ints
    sector_ids: Optional[str] = Query(None),
    ticker_ids_filter: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    from datetime import date as date_type
    from calendar import monthrange

    transactions = (
        db.query(models.Transaction)
        .filter_by(user_id=user_id)
        .order_by(models.Transaction.date)
        .all()
    )
    if not transactions:
        return schemas.MarketValueResponse(
            months=[], invested=[], market_value=[],
            partial_months=[], has_any_partial=False
        )

    tickers_map = {t.id: t for t in db.query(models.Ticker).filter_by(user_id=user_id).all()}
    fx_rows = db.query(models.FxHistory).all()

    # Parse optional filter params
    cat_filter  = {int(x) for x in category_ids.split(",") if x}    if category_ids      else None
    sec_filter  = {int(x) for x in sector_ids.split(",") if x}      if sector_ids        else None
    tkr_filter  = {int(x) for x in ticker_ids_filter.split(",") if x} if ticker_ids_filter else None

    def ticker_in_filter(ticker) -> bool:
        if tkr_filter is not None and ticker.id not in tkr_filter:
            return False
        if cat_filter is not None and ticker.category_id not in cat_filter:
            return False
        if sec_filter is not None and ticker.sector_id not in sec_filter:
            return False
        return True

    # Build price lookup: {symbol: {ym: close}}  (ym = 'YYYY-MM')
    # Ordered ASC so the latest date in each month wins (handles both monthly AV
    # records and daily mfapi records stored with granularity="daily").
    all_symbols = list({t.symbol for t in tickers_map.values() if t.symbol})
    price_lookup: dict[str, dict[str, float]] = {}
    if all_symbols:
        for ph in db.query(models.PriceHistory).filter(
            models.PriceHistory.symbol.in_(all_symbols),
            models.PriceHistory.granularity.in_(["monthly", "daily"]),
        ).order_by(models.PriceHistory.date.asc()).all():
            ym = ph.date[:7]
            price_lookup.setdefault(ph.symbol, {})[ym] = ph.close

    # Build monthly timeline from first transaction → today
    first_date = date_type.fromisoformat(transactions[0].date)
    today = date_type.today()

    def month_end(y: int, m: int) -> date_type:
        return date_type(y, m, monthrange(y, m)[1])

    def next_ym(y: int, m: int):
        return (y + 1, 1) if m == 12 else (y, m + 1)

    months: list[str] = []
    month_ends: list[date_type] = []
    y, m = first_date.year, first_date.month
    while (y, m) <= (today.year, today.month):
        months.append(f"{y:04d}-{m:02d}")
        month_ends.append(month_end(y, m))
        y, m = next_ym(y, m)

    # Replay transactions month by month (mirrors quarterly_invested pattern)
    txn_sorted = sorted(transactions, key=lambda t: t.date)
    txn_idx = 0
    n = len(txn_sorted)
    holdings: dict[int, dict] = {}  # ticker_id -> {units, cost_inr}

    invested_series: list[float] = []
    market_value_series: list[float] = []
    partial_months: list[bool] = []

    for mend, ym in zip(month_ends, months):
        mend_str = mend.isoformat()

        # Advance transactions up to this month-end
        while txn_idx < n and txn_sorted[txn_idx].date <= mend_str:
            t = txn_sorted[txn_idx]
            ticker = tickers_map.get(t.ticker_id)
            if ticker:
                if t.ticker_id not in holdings:
                    holdings[t.ticker_id] = {"units": 0.0, "cost_inr": 0.0}
                h = holdings[t.ticker_id]
                fx = historical_fx(t.date, fx_rows) if ticker.currency == "USD" else 1.0
                if t.type == "Buy":
                    h["units"] += t.units
                    h["cost_inr"] += t.units * t.price * fx
                else:  # Sell — reduce proportionally
                    if h["units"] > 0:
                        avg_cost = h["cost_inr"] / h["units"]
                        h["units"] = max(0.0, h["units"] - t.units)
                        h["cost_inr"] = max(0.0, h["cost_inr"] - t.units * avg_cost)
            txn_idx += 1

        total_invested = 0.0
        total_market = 0.0
        is_partial = False

        for ticker_id, h in holdings.items():
            if h["units"] < 0.001:
                continue
            ticker = tickers_map.get(ticker_id)
            if not ticker or not ticker_in_filter(ticker):
                continue

            cost_inr = h["cost_inr"]
            total_invested += cost_inr

            # Use price history if available, else fall back to cost basis
            sym = ticker.symbol
            if sym and sym in price_lookup and ym in price_lookup[sym]:
                close = price_lookup[sym][ym]
                fx = historical_fx(mend_str, fx_rows) if ticker.currency == "USD" else 1.0
                total_market += h["units"] * close * fx
            else:
                total_market += cost_inr
                is_partial = True

        invested_series.append(round(total_invested))
        market_value_series.append(round(total_market))
        partial_months.append(is_partial)

    return schemas.MarketValueResponse(
        months=months,
        invested=invested_series,
        market_value=market_value_series,
        partial_months=partial_months,
        has_any_partial=any(partial_months),
    )
