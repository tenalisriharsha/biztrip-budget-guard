"""
Reconciliation service: matches transactions to budget categories,
detects anomalies using statistical thresholds (Z-score and IQR),
and generates human-readable explanations with fallback templates.
"""
import statistics
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from database import TransactionDB, BudgetDB, AnomalyDB
from models import Anomaly, ReconcileResult
from services.groq_service import generate_anomaly_explanation


def _compute_z_score(value: float, data: List[float]) -> float:
    """Compute Z-score for a value against a dataset."""
    if len(data) < 2:
        return 0.0
    mean = statistics.mean(data)
    stdev = statistics.stdev(data)
    if stdev == 0:
        return 0.0
    return (value - mean) / stdev


def _compute_iqr_bounds(data: List[float]) -> tuple:
    """Compute 1.5*IQR lower and upper bounds."""
    if len(data) < 4:
        return (min(data) * 0.5, max(data) * 2.0) if data else (0, 0)
    sorted_data = sorted(data)
    n = len(sorted_data)
    q1 = sorted_data[n // 4] if n >= 4 else sorted_data[0]
    q3 = sorted_data[(3 * n) // 4] if n >= 4 else sorted_data[-1]
    iqr = q3 - q1
    low = q1 - 1.5 * iqr
    high = q3 + 1.5 * iqr
    return (low, high)


def detect_anomalies(db: Session, trip_id: int) -> List[Anomaly]:
    """
    Detect anomalies for a trip using Z-score and IQR.
    Compares each transaction against the budget range and historical variance.
    For small sample sizes, uses the budget range directly with tighter tolerance.
    """
    budgets = db.query(BudgetDB).filter(BudgetDB.trip_id == trip_id).all()
    budget_map = {b.category: b for b in budgets}
    txs = db.query(TransactionDB).filter(TransactionDB.trip_id == trip_id).all()

    # Group historical amounts by category for IQR computation
    category_amounts: Dict[str, List[float]] = {}
    for tx in txs:
        category_amounts.setdefault(tx.category, []).append(tx.amount)

    anomalies: List[Anomaly] = []
    for tx in txs:
        cat = tx.category
        b = budget_map.get(cat)
        if not b:
            continue

        amounts = category_amounts.get(cat, [])
        n = len(amounts)

        if n >= 4:
            # Enough data: use IQR bounds blended with budget range
            low, high = _compute_iqr_bounds(amounts)
            low = min(low, b.low)
            high = max(high, b.high)
        elif n >= 2:
            # Small sample: use budget range with moderate tolerance
            low = b.low * 0.7
            high = b.high * 1.3
        else:
            # Single transaction: strict budget range check
            low = b.low * 0.8
            high = b.high * 1.2

        z = _compute_z_score(tx.amount, amounts)
        is_anomaly = tx.amount < low or tx.amount > high
        if is_anomaly and n >= 2:
            # Reinforce with Z-score when we have enough data
            is_anomaly = abs(z) > 1.5

        if is_anomaly:
            severity = "high" if abs(z) > 3 or tx.amount > high * 1.5 else "medium" if abs(z) > 2 or tx.amount > high * 1.2 else "low"
            explanation = generate_anomaly_explanation(
                category=cat,
                amount=tx.amount,
                expected_low=low,
                expected_high=high,
                severity=severity,
            )
            anomalies.append(Anomaly(
                transaction_id=tx.id,
                category=cat,
                amount=tx.amount,
                expected_range_low=round(low, 2),
                expected_range_high=round(high, 2),
                severity=severity,
                explanation=explanation,
            ))

    return anomalies


def reconcile_trip(db: Session, trip_id: int) -> ReconcileResult:
    """Run full reconciliation for a trip and persist anomalies."""
    budgets = db.query(BudgetDB).filter(BudgetDB.trip_id == trip_id).all()
    txs = db.query(TransactionDB).filter(TransactionDB.trip_id == trip_id).all()

    total_budgeted = sum(b.estimate for b in budgets)
    total_spent = sum(t.amount for t in txs)
    variance = total_spent - total_budgeted

    anomalies = detect_anomalies(db, trip_id)

    # Persist anomalies
    for a in anomalies:
        db.add(AnomalyDB(
            trip_id=trip_id,
            transaction_id=a.transaction_id,
            category=a.category,
            amount=a.amount,
            expected_range_low=a.expected_range_low,
            expected_range_high=a.expected_range_high,
            severity=a.severity,
            explanation=a.explanation,
        ))
    db.commit()

    summary = (
        f"Trip {trip_id} reconciliation complete. "
        f"Budgeted: {total_budgeted:.2f}, Spent: {total_spent:.2f}, "
        f"Variance: {variance:.2f}. "
        f"{len(anomalies)} anomaly(ies) flagged."
    )

    return ReconcileResult(
        trip_id=trip_id,
        total_budgeted=round(total_budgeted, 2),
        total_spent=round(total_spent, 2),
        variance=round(variance, 2),
        anomalies=anomalies,
        natural_language_summary=summary,
    )
