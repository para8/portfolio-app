from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"].strip()

engine = create_engine(
    DATABASE_URL,
    connect_args={"sslmode": "require", "connect_timeout": 10},
    pool_pre_ping=True,
    pool_size=1,
    max_overflow=0,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
