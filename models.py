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
    __table_args__ = (UniqueConstraint("user_id", "ticker", name="tickers_user_ticker_key"),)
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Text, nullable=True)
    ticker = Column(Text, nullable=False)
    name = Column(Text, nullable=False)
    display_name = Column(Text, nullable=True)
    currency = Column(Text, nullable=False)
    category_id = Column(Integer)
    sector_id = Column(Integer)
    created_at = Column(Text)


class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Text, nullable=True)
    date = Column(Text, nullable=False)
    ticker = Column(Text, nullable=False)  # text only, FK dropped (tickers no longer has text PK)
    type = Column(Text, nullable=False)
    units = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    amount = Column(Float, nullable=False)
    broker_id = Column(Integer)
    created_at = Column(Text)


class Price(Base):
    __tablename__ = "prices"
    __table_args__ = (UniqueConstraint("user_id", "ticker", name="prices_user_ticker_key"),)
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Text, nullable=True)
    ticker = Column(Text, nullable=False)
    price = Column(Float, nullable=False)
    updated_at = Column(Text)


class FxHistory(Base):
    __tablename__ = "fx_history"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Text, nullable=True)
    from_ym = Column(Text, nullable=False)
    rate = Column(Float, nullable=False)


class Config(Base):
    __tablename__ = "config"
    __table_args__ = (UniqueConstraint("user_id", "key", name="config_user_key_key"),)
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Text, nullable=True)
    key = Column(Text, nullable=False)
    value = Column(Text, nullable=False)
    updated_at = Column(Text)
