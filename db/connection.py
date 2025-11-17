"""
Database connection helpers for Explorer Scraper.
"""

import os
from typing import Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from contextlib import contextmanager


# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://localhost/explorer_scraper"
)

# Create engine
engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,  # Simple for now, can optimize later
    echo=False,  # Set to True for SQL debugging
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db_session():
    """
    Context manager for database sessions.
    
    Usage:
        with get_db_session() as db:
            result = db.execute(text("SELECT * FROM deals LIMIT 1"))
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def test_connection() -> bool:
    """Test database connection."""
    try:
        with get_db_session() as db:
            result = db.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False


def get_origin_count() -> int:
    """Get count of origins in database."""
    with get_db_session() as db:
        result = db.execute(text("SELECT COUNT(*) FROM origins"))
        return result.scalar()


def get_deal_count() -> int:
    """Get count of deals in database."""
    with get_db_session() as db:
        result = db.execute(text("SELECT COUNT(*) FROM deals"))
        return result.scalar()


def get_db_stats() -> dict:
    """Get database statistics."""
    with get_db_session() as db:
        stats = {}
        
        # Origins
        result = db.execute(text("SELECT COUNT(*) FROM origins"))
        stats['origins'] = result.scalar()
        
        # Deals
        result = db.execute(text("SELECT COUNT(*) FROM deals"))
        stats['deals'] = result.scalar()
        
        # Used deals
        result = db.execute(text("SELECT COUNT(*) FROM used_deals WHERE expires_at > CURRENT_TIMESTAMP"))
        stats['active_used_deals'] = result.scalar()
        
        # Featured deals
        result = db.execute(text("SELECT COUNT(*) FROM deals WHERE is_featured_candidate = TRUE"))
        stats['featured_deals'] = result.scalar()
        
        return stats


if __name__ == "__main__":
    print("Testing database connection...")
    if test_connection():
        print("✅ Connection successful!")
        print("\n📊 Database stats:")
        stats = get_db_stats()
        for key, value in stats.items():
            print(f"  • {key}: {value}")
    else:
        print("❌ Connection failed!")

