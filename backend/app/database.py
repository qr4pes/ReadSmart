from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base
import os

def get_database_url():
    url = os.getenv(
        "DATABASE_URL",
        "postgresql://analyzer_user:analyzer_pass@localhost:5432/website_analyzer"
    )
    # Railway uses postgres:// but SQLAlchemy needs postgresql://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url

DATABASE_URL = get_database_url()

engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=300)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
