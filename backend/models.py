"""
Pydantic models for request/response validation and data transfer.
"""
from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class ForecastRequest(BaseModel):
    """Request body for pre-trip budget forecast."""
    destination: str = Field(..., min_length=1, description="City or airport code")
    start_date: date = Field(..., description="Trip start date (YYYY-MM-DD)")
    end_date: date = Field(..., description="Trip end date (YYYY-MM-DD)")
    traveler_level: str = Field(..., pattern="^(junior|mid|senior|executive)$",
                                 description="Employee level affecting per diem")
    origin: str = Field(default="NYC", description="Origin city or airport code")
    currency: str = Field(default="USD", min_length=3, max_length=3)


class BudgetLineItem(BaseModel):
    """A single budget category with estimate and confidence interval."""
    category: str
    estimate: float = Field(..., ge=0)
    low: float = Field(..., ge=0)
    high: float = Field(..., ge=0)
    confidence: float = Field(..., ge=0, le=1)
    notes: str = ""


class ForecastResponse(BaseModel):
    """Response body for pre-trip budget forecast."""
    trip_id: int
    destination: str
    start_date: date
    end_date: date
    traveler_level: str
    total_estimate: float
    total_low: float
    total_high: float
    overall_confidence: float
    line_items: List[BudgetLineItem]
    natural_language_summary: str
    currency: str


class SpendEvent(BaseModel):
    """Incoming card transaction / spend event."""
    trip_id: int
    category: str = Field(..., description="e.g. flight, hotel, meals, ground_transport")
    amount: float = Field(..., ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    description: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    merchant: str = ""


class SpendAlert(BaseModel):
    """Generated alert when spend exceeds thresholds."""
    trip_id: int
    category: str
    budgeted: float
    spent: float
    percent_used: float
    alert_level: str = Field(..., pattern="^(warning|critical)$")
    message: str


class BurnRate(BaseModel):
    """Burn rate metrics for a trip."""
    trip_id: int
    total_budget: float
    total_spent: float
    remaining: float
    days_elapsed: int
    days_total: int
    daily_burn_rate: float
    projected_overspend: Optional[float]


class Anomaly(BaseModel):
    """Flagged anomaly during reconciliation."""
    transaction_id: int
    category: str
    amount: float
    expected_range_low: float
    expected_range_high: float
    severity: str = Field(..., pattern="^(low|medium|high)$")
    explanation: str


class ReconcileResult(BaseModel):
    """Result of post-trip reconciliation."""
    trip_id: int
    total_budgeted: float
    total_spent: float
    variance: float
    anomalies: List[Anomaly]
    natural_language_summary: str


class Trip(BaseModel):
    """Trip record from database."""
    id: int
    destination: str
    start_date: date
    end_date: date
    traveler_level: str
    origin: str
    currency: str
    created_at: datetime


class Transaction(BaseModel):
    """Transaction record from database."""
    id: int
    trip_id: int
    category: str
    amount: float
    currency: str
    description: str
    merchant: str
    timestamp: datetime
