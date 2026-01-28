from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base
import os

# Lazy initialization - don't connect until needed
_engine = None
_SessionLocal = None

def get_database_url():
    url = os.getenv("DATABASE_URL", "")
    if not url:
        print("WARNING: DATABASE_URL not set")
        return None
    # Railway uses postgres:// but SQLAlchemy needs postgresql://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url

def get_engine():
    global _engine
    if _engine is None:
        url = get_database_url()
        if url:
            _engine = create_engine(url, pool_pre_ping=True, pool_recycle=300)
    return _engine

def get_session_local():
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        if engine:
            _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return _SessionLocal

def get_db():
    """Dependency for getting database session"""
    SessionLocal = get_session_local()
    if SessionLocal is None:
        raise Exception("Database not configured")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables"""
    engine = get_engine()
    if engine:
        Base.metadata.create_all(bind=engine)
        print("Database tables created")
    else:
        print("Skipping database init - no DATABASE_URL")
