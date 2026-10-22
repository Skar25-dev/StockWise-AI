import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "stockwise.db"


def get_database_url(environ=os.environ) -> str:
    """Usa DATABASE_URL si existe (p. ej. postgresql://...); si no, SQLite local."""
    return environ.get("DATABASE_URL") or f"sqlite:///{DB_PATH}"


SQLALCHEMY_DATABASE_URL = get_database_url()

_connect_args = (
    {"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}
)
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
