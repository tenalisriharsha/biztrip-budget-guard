"""
FastAPI application entry point.
Includes all routes, CORS, startup events, and database integration.
"""
from contextlib import asynccontextmanager
from typing import List
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from config import settings
from database import init_db, get_db
from models import (
    ForecastRequest, ForecastResponse, SpendEvent, SpendAlert,
    BurnRate, ReconcileResult, Trip, Transaction, BudgetLineItem
)
from services.forecast_service import build_forecast
from services.spend_service import record_spend, check_alerts, compute_burn_rate
from services.reconcile_service import reconcile_trip
from database import TripDB, BudgetDB, TransactionDB, AnomalyDB


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/forecast", response_model=ForecastResponse)
def post_forecast(req: ForecastRequest, db: Session = Depends(get_db)):
    """
    Generate a pre-trip budget forecast.
    Stores the trip and budget line items in SQLite.
    """
    try:
        result = build_forecast(
            origin=req.origin,
            destination=req.destination,
            start_date=req.start_date,
            end_date=req.end_date,
            traveler_level=req.traveler_level,
            currency=req.currency,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Forecast error: {exc}")

    trip = TripDB(
        destination=req.destination,
        start_date=req.start_date,
        end_date=req.end_date,
        traveler_level=req.traveler_level,
        origin=req.origin,
        currency=req.currency,
    )
    db.add(trip)
    db.commit()
    db.refresh(trip)

    for item in result["line_items"]:
        db.add(BudgetDB(
            trip_id=trip.id,
            category=item["category"],
            estimate=item["estimate"],
            low=item["low"],
            high=item["high"],
            confidence=item["confidence"],
            notes=item["notes"],
        ))
    db.commit()

    result["trip_id"] = trip.id
    return ForecastResponse(**result)


@app.post("/spend")
def post_spend(event: SpendEvent, db: Session = Depends(get_db)):
    """
    Accept a spend event (mock webhook endpoint).
    Returns the recorded transaction and any alerts.
    """
    tx = record_spend(db, event)
    alerts = check_alerts(db, event.trip_id)
    return {
        "transaction_id": tx.id,
        "trip_id": tx.trip_id,
        "alerts": [a.model_dump() for a in alerts],
    }


@app.get("/trips/{trip_id}/alerts", response_model=List[SpendAlert])
def get_alerts(trip_id: int, db: Session = Depends(get_db)):
    """Fetch current spend alerts for a trip."""
    return check_alerts(db, trip_id)


@app.get("/trips/{trip_id}/burn", response_model=BurnRate)
def get_burn_rate(trip_id: int, db: Session = Depends(get_db)):
    """Fetch burn rate for a trip."""
    try:
        return compute_burn_rate(db, trip_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.post("/reconcile", response_model=ReconcileResult)
def post_reconcile(trip_id: int, db: Session = Depends(get_db)):
    """
    Run post-trip reconciliation for a given trip.
    Detects anomalies and returns a summary.
    """
    trip = db.query(TripDB).filter(TripDB.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    try:
        return reconcile_trip(db, trip_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Reconciliation error: {exc}")


@app.get("/trips", response_model=List[Trip])
def get_trips(db: Session = Depends(get_db)):
    """List all trips."""
    rows = db.query(TripDB).order_by(TripDB.id.desc()).all()
    return [
        Trip(
            id=r.id,
            destination=r.destination,
            start_date=r.start_date,
            end_date=r.end_date,
            traveler_level=r.traveler_level,
            origin=r.origin,
            currency=r.currency,
            created_at=r.created_at,
        )
        for r in rows
    ]


@app.get("/trips/{trip_id}/transactions", response_model=List[Transaction])
def get_transactions(trip_id: int, db: Session = Depends(get_db)):
    """List transactions for a trip."""
    rows = db.query(TransactionDB).filter(TransactionDB.trip_id == trip_id).order_by(TransactionDB.timestamp.desc()).all()
    return [
        Transaction(
            id=r.id,
            trip_id=r.trip_id,
            category=r.category,
            amount=r.amount,
            currency=r.currency,
            description=r.description,
            merchant=r.merchant,
            timestamp=r.timestamp,
        )
        for r in rows
    ]


@app.get("/trips/{trip_id}/budget")
def get_budget(trip_id: int, db: Session = Depends(get_db)):
    """Fetch budget line items for a trip."""
    rows = db.query(BudgetDB).filter(BudgetDB.trip_id == trip_id).all()
    return [
        {
            "category": r.category,
            "estimate": r.estimate,
            "low": r.low,
            "high": r.high,
            "confidence": r.confidence,
            "notes": r.notes,
        }
        for r in rows
    ]


@app.get("/trips/{trip_id}/anomalies")
def get_anomalies(trip_id: int, db: Session = Depends(get_db)):
    """Fetch anomalies for a trip."""
    rows = db.query(AnomalyDB).filter(AnomalyDB.trip_id == trip_id).order_by(AnomalyDB.id.desc()).all()
    return [
        {
            "id": r.id,
            "transaction_id": r.transaction_id,
            "category": r.category,
            "amount": r.amount,
            "expected_range_low": r.expected_range_low,
            "expected_range_high": r.expected_range_high,
            "severity": r.severity,
            "explanation": r.explanation,
        }
        for r in rows
    ]


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=True)
