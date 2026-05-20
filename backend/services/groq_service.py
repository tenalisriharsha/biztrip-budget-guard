"""
Groq API client with mandatory rule-based fallback for every function.
Handles rate limits, network errors, and missing API keys gracefully.
"""
import os
import random
from typing import Optional
from groq import Groq, RateLimitError, APIError
from config import settings


# Initialize Groq client if key is present
_client: Optional[Groq] = None
if settings.groq_api_key:
    _client = Groq(api_key=settings.groq_api_key)


def _fallback_summary(destination: str, destination_name: str, total_estimate: float, currency: str,
                      confidence: float, items: list) -> str:
    """Rule-based fallback forecast summary."""
    level = "high" if confidence >= 0.8 else "moderate" if confidence >= 0.6 else "low"
    place = destination_name if destination_name else destination
    return (
        f"Your trip to {place} is estimated at {total_estimate:.2f} {currency} "
        f"with {level} confidence ({confidence:.0%}). "
        f"Key categories: {', '.join([i['category'] for i in items[:3]])}. "
        f"Book flights early for better rates."
    )


def _fallback_alert_message(trip_id: int, category: str, percent_used: float) -> str:
    """Rule-based fallback alert message."""
    if percent_used >= 100:
        return (
            f"CRITICAL: Trip {trip_id} {category} budget is exceeded ({percent_used:.1f}% used). "
            f"Freeze non-essential spending immediately."
        )
    return (
        f"WARNING: Trip {trip_id} {category} is at {percent_used:.1f}% of budget. "
        f"Review upcoming expenses to stay on track."
    )


def _fallback_anomaly_explanation(category: str, amount: float,
                                   low: float, high: float) -> str:
    """Rule-based fallback anomaly explanation."""
    if amount > high:
        return (
            f"The {category} charge of {amount:.2f} exceeds the expected range "
            f"({low:.2f} - {high:.2f}). Possible causes: upgraded service, surge pricing, "
            f"or duplicate charge."
        )
    return (
        f"The {category} charge of {amount:.2f} is below the expected range "
        f"({low:.2f} - {high:.2f}). Possible causes: refund applied, partial charge, "
        f"or missing add-ons."
    )


def generate_forecast_summary(destination: str, destination_name: str, total_estimate: float, currency: str,
                               confidence: float, line_items: list) -> str:
    """Generate natural language forecast summary via Groq with fallback."""
    if not _client or not settings.enable_groq:
        return _fallback_summary(destination, destination_name, total_estimate, currency, confidence, line_items)

    place = destination_name if destination_name else destination
    prompt = (
        "You are a corporate travel budget assistant. Summarize this trip forecast briefly:\n"
        f"Destination: {place} ({destination})\n"
        f"Total Estimate: {total_estimate:.2f} {currency}\n"
        f"Confidence: {confidence:.0%}\n"
        f"Categories:\n"
    )
    for item in line_items:
        prompt += (
            f"- {item['category']}: {item['estimate']:.2f} "
            f"(range {item['low']:.2f} - {item['high']:.2f})\n"
        )
    prompt += "Provide 2-3 sentences of actionable advice."

    try:
        response = _client.chat.completions.create(
            model=settings.groq_model,
            messages=[
                {"role": "system", "content": "You are a helpful corporate travel assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=256
        )
        return response.choices[0].message.content.strip()
    except RateLimitError:
        # Try fallback model once
        try:
            response = _client.chat.completions.create(
                model=settings.groq_fallback_model,
                messages=[
                    {"role": "system", "content": "You are a helpful corporate travel assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=256
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return _fallback_summary(destination, destination_name, total_estimate, currency, confidence, line_items)
    except APIError:
        return _fallback_summary(destination, destination_name, total_estimate, currency, confidence, line_items)
    except Exception:
        return _fallback_summary(destination, destination_name, total_estimate, currency, confidence, line_items)


def generate_alert_message(trip_id: int, category: str, budgeted: float,
                            spent: float, percent_used: float) -> str:
    """Generate natural language alert via Groq with fallback."""
    if not _client or not settings.enable_groq:
        return _fallback_alert_message(trip_id, category, percent_used)

    prompt = (
        "You are a corporate travel budget assistant. Write a concise spending alert:\n"
        f"Trip ID: {trip_id}\n"
        f"Category: {category}\n"
        f"Budgeted: {budgeted:.2f}\n"
        f"Spent: {spent:.2f}\n"
        f"Percent Used: {percent_used:.1f}%\n"
        f"Keep it under 2 sentences."
    )

    try:
        response = _client.chat.completions.create(
            model=settings.groq_model,
            messages=[
                {"role": "system", "content": "You are a helpful corporate travel assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=128
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return _fallback_alert_message(trip_id, category, percent_used)


def generate_anomaly_explanation(category: str, amount: float,
                                  expected_low: float, expected_high: float,
                                  severity: str) -> str:
    """Generate natural language anomaly explanation via Groq with fallback."""
    if not _client or not settings.enable_groq:
        return _fallback_anomaly_explanation(category, amount, expected_low, expected_high)

    prompt = (
        "You are a corporate travel budget assistant. Explain this anomaly briefly:\n"
        f"Category: {category}\n"
        f"Amount: {amount:.2f}\n"
        f"Expected Range: {expected_low:.2f} - {expected_high:.2f}\n"
        f"Severity: {severity}\n"
        f"Suggest 1-2 possible causes in one sentence."
    )

    try:
        response = _client.chat.completions.create(
            model=settings.groq_model,
            messages=[
                {"role": "system", "content": "You are a helpful corporate travel assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=128
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return _fallback_anomaly_explanation(category, amount, expected_low, expected_high)
