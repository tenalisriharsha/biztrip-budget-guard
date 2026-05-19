"""
SQLite database setup using SQLAlchemy.
Creates tables for trips, budgets, transactions, and anomalies.
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Date, Text
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from datetime import datetime
from config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class TripDB(Base):
    """Trips table."""
    __tablename__ = "trips"
    id = Column(Integer, primary_key=True, index=True)
    destination = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    traveler_level = Column(String, nullable=False)
    origin = Column(String, default="NYC")
    currency = Column(String, default="USD")
    created_at = Column(DateTime, default=datetime.utcnow)


class BudgetDB(Base):
    """Budgets table storing line items per trip."""
    __tablename__ = "budgets"
    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, nullable=False, index=True)
    category = Column(String, nullable=False)
    estimate = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)


class TransactionDB(Base):
    """Transactions table for spend events."""
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, nullable=False, index=True)
    category = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    description = Column(Text, default="")
    merchant = Column(String, default="")
    timestamp = Column(DateTime, default=datetime.utcnow)


class AnomalyDB(Base):
    """Anomalies flagged during reconciliation."""
    __tablename__ = "anomalies"
    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, nullable=False, index=True)
    transaction_id = Column(Integer, nullable=False)
    category = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    expected_range_low = Column(Float, nullable=False)
    expected_range_high = Column(Float, nullable=False)
    severity = Column(String, nullable=False)
    explanation = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db() -> None:
    """Create all tables if they do not exist."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    """Yield a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
