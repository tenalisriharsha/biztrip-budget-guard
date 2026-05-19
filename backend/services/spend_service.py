"""
Spend tracking service: records transactions, computes burn rate,
generates alerts when categories exceed 80% of budget.
"""
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from database import TransactionDB, BudgetDB, TripDB
from models import SpendEvent, SpendAlert, BurnRate
from services.groq_service import generate_alert_message


def record_spend(db: Session, event: SpendEvent) -> TransactionDB:
    """Persist a spend event to the database."""
    tx = TransactionDB(
        trip_id=event.trip_id,
        category=event.category,
        amount=event.amount,
        currency=event.currency,
        description=event.description,
        merchant=event.merchant,
        timestamp=event.timestamp,
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


def get_spent_by_category(db: Session, trip_id: int) -> Dict[str, float]:
    """Aggregate spent amounts per category for a trip."""
    rows = db.query(TransactionDB).filter(TransactionDB.trip_id == trip_id).all()
    spent: Dict[str, float] = {}
    for r in rows:
        spent[r.category] = spent.get(r.category, 0.0) + r.amount
    return spent


def get_budget_by_category(db: Session, trip_id: int) -> Dict[str, float]:
    """Fetch budgeted estimates per category for a trip."""
    rows = db.query(BudgetDB).filter(BudgetDB.trip_id == trip_id).all()
    return {r.category: r.estimate for r in rows}


def check_alerts(db: Session, trip_id: int) -> List[SpendAlert]:
    """Check all categories for threshold breaches and generate alerts."""
    budgeted = get_budget_by_category(db, trip_id)
    spent = get_spent_by_category(db, trip_id)
    alerts: List[SpendAlert] = []
    for category, budget in budgeted.items():
        s = spent.get(category, 0.0)
        if budget <= 0:
            continue
        percent = (s / budget) * 100
        if percent >= 80:
            level = "critical" if percent >= 100 else "warning"
            msg = generate_alert_message(
                trip_id=trip_id,
                category=category,
                budgeted=budget,
                spent=s,
                percent_used=percent,
            )
            alerts.append(SpendAlert(
                trip_id=trip_id,
                category=category,
                budgeted=budget,
                spent=s,
                percent_used=round(percent, 1),
                alert_level=level,
                message=msg,
            ))
    return alerts


def compute_burn_rate(db: Session, trip_id: int) -> BurnRate:
    """Compute burn rate and projected overspend for a trip."""
    trip = db.query(TripDB).filter(TripDB.id == trip_id).first()
    if not trip:
        raise ValueError(f"Trip {trip_id} not found")

    budgets = db.query(BudgetDB).filter(BudgetDB.trip_id == trip_id).all()
    total_budget = sum(b.estimate for b in budgets)

    txs = db.query(TransactionDB).filter(TransactionDB.trip_id == trip_id).all()
    total_spent = sum(t.amount for t in txs)

    today = date.today()
    days_elapsed = max((today - trip.start_date).days, 0)
    days_total = max((trip.end_date - trip.start_date).days, 1)

    daily_burn = total_spent / max(days_elapsed, 1)
    projected_total = daily_burn * days_total
    projected_overspend = None
    if projected_total > total_budget:
        projected_overspend = round(projected_total - total_budget, 2)

    return BurnRate(
        trip_id=trip_id,
        total_budget=round(total_budget, 2),
        total_spent=round(total_spent, 2),
        remaining=round(total_budget - total_spent, 2),
        days_elapsed=days_elapsed,
        days_total=days_total,
        daily_burn_rate=round(daily_burn, 2),
        projected_overspend=projected_overspend,
    )
