from sqlalchemy import Column, Integer, Text, Float, UniqueConstraint
from database import Base


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (UniqueConstraint("user_id", "name", name="categories_user_name_key"),)
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Text, nullable=True)
    name = Column(Text, nullable=False)
    color = Column(Text, nullable=False)


class Sector(Base):
    __tablename__ = "sectors"
    __table_args__ = (UniqueConstraint("user_id", "name", name="sectors_user_name_key"),)
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Text, nullable=True)
    name = Column(Text, nullable=False)
    color = Column(Text, nullable=False)


class Broker(Base):
    __tablename__ = "brokers"
    __table_args__ = (UniqueConstraint("user_id", "name", name="brokers_user_name_key"),)
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Text, nullable=True)
    name = Column(Text, nullable=False)


class Ticker(Base):
    __tablename__ = "tickers"
    __table_args__ = (UniqueConstraint("user_id", "name", name="tickers_user_name_key"),)
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Text, nullable=True)
    name = Column(Text, nullable=False)
    short_name = Column(Text, nullable=True)
    currency = Column(Text, nullable=False)
    category_id = Column(Integer)
    sector_id = Column(Integer)
    created_at = Column(Text)
    symbol = Column(Text, nullable=True)   # exchange symbol e.g. 'META', 'AAPL'


class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Text, nullable=True)
    date = Column(Text, nullable=False)
    ticker_id = Column(Integer, nullable=False)  # FK to tickers.id
    type = Column(Text, nullable=False)
    units = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    amount = Column(Float, nullable=False)
    broker_id = Column(Integer)
    created_at = Column(Text)


class Price(Base):
    __tablename__ = "prices"
    __table_args__ = (UniqueConstraint("user_id", "ticker_id", name="prices_user_ticker_id_key"),)
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Text, nullable=True)
    ticker_id = Column(Integer, nullable=False)  # FK to tickers.id
    price = Column(Float, nullable=False)
    updated_at = Column(Text)


class FxHistory(Base):
    __tablename__ = "fx_history"
    id = Column(Integer, primary_key=True, autoincrement=True)
    from_ym = Column(Text, nullable=False)   # user_id removed — global table
    rate = Column(Float, nullable=False)


class Config(Base):
    __tablename__ = "config"
    __table_args__ = (UniqueConstraint("user_id", "key", name="config_user_key_key"),)
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Text, nullable=True)
    key = Column(Text, nullable=False)
    value = Column(Text, nullable=False)
    updated_at = Column(Text)


class PriceHistory(Base):
    __tablename__ = "price_history"
    __table_args__ = (UniqueConstraint("symbol", "granularity", "date", name="price_history_symbol_gran_date_key"),)
    id          = Column(Integer, primary_key=True, autoincrement=True)
    symbol      = Column(Text, nullable=False)
    granularity = Column(Text, nullable=False)   # 'monthly'; 'daily' for mfapi later
    date        = Column(Text, nullable=False)   # last trading day of period e.g. '2026-03-31'
    close       = Column(Float, nullable=True)
    high        = Column(Float, nullable=True)
    low         = Column(Float, nullable=True)
    open        = Column(Float, nullable=True)
    source      = Column(Text, nullable=True)    # 'alpha_vantage'
    fetched_at  = Column(Text, nullable=True)
