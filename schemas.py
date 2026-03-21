from pydantic import BaseModel
from typing import Optional, List


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
    ticker: str
    name: str
    currency: str
    category_id: int
    sector_id: int


class TickerOut(BaseModel):
    ticker: str
    name: str
    currency: str
    category_id: Optional[int]
    sector_id: Optional[int]
    category_name: Optional[str] = None
    sector_name: Optional[str] = None

    class Config:
        from_attributes = True


class TransactionCreate(BaseModel):
    ticker: str
    type: str
    units: float
    price: float
    date: str
    broker_id: int


class TransactionOut(BaseModel):
    id: int
    date: str
    ticker: str
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
    ticker: str
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


# Positions response shapes
class PositionItem(BaseModel):
    ticker: str
    name: str
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
