"""SQLAlchemy 引擎 & 会话工厂"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import get_settings

settings = get_settings()

_engine = create_engine(
    settings.database_url,
    echo=False,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def get_db() -> Session:
    """FastAPI 依赖注入：每个请求一个 session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_engine():
    return _engine
