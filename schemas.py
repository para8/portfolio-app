from pydantic import BaseModel
from typing import Optional, List, Any


class CategoryCreate(BaseModel):
    name: str
    color: str


class CategoryOut(BaseModel):
    id: int
    name: str
    color: str

    class Config:
        from_attributes = True


class SectorCreate(BaseModel):
    name: str
    color: str


class SectorOut(BaseModel):
    id: int
    name: str
    color: str

    class Config:
        from_attributes = True


class BrokerOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class TickerCreate(BaseModel):
    name: str
    short_name: Optional[str] = None
    currency: str
    category_id: int
    sector_id: int


class TickerOut(BaseModel):
    id: int
    name: str
    short_name: Optional[str] = None
    currency: str
    category_id: Optional[int]
    sector_id: Optional[int]
    category_name: Optional[str] = None
    sector_name: Optional[str] = None
    symbol: Optional[str] = None

    class Config:
        from_attributes = True


class TransactionCreate(BaseModel):
    ticker_id: int
    type: str
    units: float
    price: float
    date: str
    broker_id: int


class TransactionOut(BaseModel):
    id: int
    date: str
    ticker_id: int
    ticker_name: Optional[str] = None
    type: str
    units: float
    price: float
    amount: float
    broker_id: Optional[int]
    broker_name: Optional[str] = None
    created_at: Optional[str]

    class Config:
        from_attributes = True


class PriceUpdate(BaseModel):
    price: float


class PriceOut(BaseModel):
    ticker_id: int
    price: float
    updated_at: Optional[str]

    class Config:
        from_attributes = True


class FxHistoryCreate(BaseModel):
    from_ym: str
    rate: float


class FxHistoryOut(BaseModel):
    id: int
    from_ym: str
    rate: float

    class Config:
        from_attributes = True


class ConfigUpdate(BaseModel):
    value: str


class ConfigOut(BaseModel):
    key: str
    value: str
    updated_at: Optional[str]

    class Config:
        from_attributes = True


# Import schemas
class NewTickerAssignment(BaseModel):
    name: str                           # fund name from file (becomes ticker.name)
    short_name: Optional[str] = None
    category_id: int
    sector_id: int


class ImportTransaction(BaseModel):
    fund_name: str                      # scheme name; backend resolves to ticker_id
    date: str
    type: str
    units: float
    price: float
    amount: float


class ImportConfirmPayload(BaseModel):
    broker_id: Optional[int] = None
    currency: str
    new_tickers: List[NewTickerAssignment] = []
    transactions: List[ImportTransaction]  # only checked, non-duplicate rows


# Positions response shapes
class PositionItem(BaseModel):
    ticker_id: int
    name: str
    short_name: Optional[str] = None
    sector: Optional[str]
    held_units: float
    avg_buy_price: float
    current_price: Optional[float]
    currency: str
    invested_inr: float
    value_inr: Optional[float]
    pnl_inr: Optional[float]
    pnl_pct: Optional[float]
    weight_pct: Optional[float]


class CategoryGroup(BaseModel):
    category: str
    color: str
    invested_inr: float
    value_inr: Optional[float]
    pnl_inr: Optional[float]
    pnl_pct: Optional[float]
    weight_pct: Optional[float]
    positions: List[PositionItem]


class PositionSummary(BaseModel):
    total_invested_inr: float
    total_value_inr: Optional[float]
    total_pnl_inr: Optional[float]
    total_pnl_pct: Optional[float]
    usd_exposure_pct: Optional[float]
    priced_count: int
    total_count: int


class PositionsResponse(BaseModel):
    fx_rate: float
    summary: PositionSummary
    by_category: List[CategoryGroup]


# ── Live Prices / Price History ───────────────────────────────────────────────

class TickerSymbolUpdate(BaseModel):
    symbol: str


class PriceHistoryFetchRequest(BaseModel):
    ticker_ids: List[int]


class PriceHistoryFetchResult(BaseModel):
    ticker_id: int
    symbol: str
    status: str          # 'success' | 'rate_limited' | 'invalid_symbol' | 'no_symbol' | 'error'
    rows_stored: int
    latest_close: Optional[float] = None
    latest_date: Optional[str] = None
    error_detail: Optional[str] = None


class PriceHistoryFetchResponse(BaseModel):
    results: List[PriceHistoryFetchResult]


class PriceHistoryLatestResult(BaseModel):
    ticker_id: int
    symbol: str
    latest_close: Optional[float] = None
    latest_date: Optional[str] = None

class PriceHistoryLatestResponse(BaseModel):
    results: List[PriceHistoryLatestResult]


# ── Market Value History Chart ────────────────────────────────────────────────

class MarketValueResponse(BaseModel):
    months: List[str]           # ['YYYY-MM', ...]
    invested: List[float]
    market_value: List[float]
    partial_months: List[bool]  # True where cost basis used for ≥1 holding
    has_any_partial: bool       # drives nudge visibility
