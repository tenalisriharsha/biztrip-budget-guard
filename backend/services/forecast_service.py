"""
Forecast service integrating Kiwi.com Tequila Flight API, ExchangeRate-API,
and Open-Meteo for seasonal adjustments. Computes budget line items
with confidence intervals.
"""
import os
import requests
from datetime import date, timedelta
from typing import List, Dict, Any, Optional
from models import BudgetLineItem
from services.groq_service import generate_forecast_summary
from config import settings


def _search_tequila_flights(origin: str, destination: str, departure_date: date,
                            return_date: date) -> List[Dict[str, Any]]:
    """Search flight offers via Kiwi.com Tequila API (free tier)."""
    if not settings.tequila_api_key:
        return []
    try:
        resp = requests.get(
            "https://api.tequila.kiwi.com/v2/search",
            headers={"apikey": settings.tequila_api_key},
            params={
                "fly_from": origin[:3].upper(),
                "fly_to": destination[:3].upper(),
                "date_from": departure_date.strftime("%d/%m/%Y"),
                "date_to": departure_date.strftime("%d/%m/%Y"),
                "return_from": return_date.strftime("%d/%m/%Y"),
                "return_to": return_date.strftime("%d/%m/%Y"),
                "adults": 1,
                "curr": "USD",
                "limit": 5,
            },
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json().get("data", [])
    except Exception:
        return []


def _get_exchange_rate(base: str, target: str) -> Optional[float]:
    """Fetch exchange rate from ExchangeRate-API free tier."""
    if not settings.exchange_rate_api_key:
        return None
    try:
        url = f"https://v6.exchangerate-api.com/v6/{settings.exchange_rate_api_key}/latest/{base.upper()}"
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        rates = data.get("conversion_rates", {})
        return rates.get(target.upper())
    except Exception:
        return None


def _get_weather_season_factor(destination: str, trip_date: date) -> float:
    """
    Fetch seasonal weather data from Open-Meteo and return a pricing factor.
    Returns 1.0 on failure. Higher values mean higher expected prices.
    """
    # Approximate lat/lon for major cities (fallback)
    city_coords = {
        "NYC": (40.71, -74.01), "LON": (51.51, -0.13), "PAR": (48.86, 2.35),
        "TYO": (35.68, 139.69), "SIN": (1.35, 103.82), "DXB": (25.20, 55.27),
        "LAX": (34.05, -118.24), "BER": (52.52, 13.41), "SYD": (-33.87, 151.21),
        "HKG": (22.32, 114.17),
    }
    coords = city_coords.get(destination[:3].upper(), (40.71, -74.01))
    try:
        resp = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": coords[0],
                "longitude": coords[1],
                "start_date": trip_date.isoformat(),
                "end_date": (trip_date + timedelta(days=1)).isoformat(),
                "daily": "temperature_2m_max,precipitation_sum",
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        daily = data.get("daily", {})
        temps = daily.get("temperature_2m_max", [])
        precips = daily.get("precipitation_sum", [])
        temp = temps[0] if temps else 20
        precip = precips[0] if precips else 0
        # Simple heuristic: very hot/cold or rainy days can increase costs (taxis, etc)
        factor = 1.0
        if temp > 30 or temp < 0:
            factor += 0.05
        if precip > 5:
            factor += 0.05
        return round(factor, 2)
    except Exception:
        return 1.0


def _mock_hotel_rate(destination: str, level: str, nights: int) -> Dict[str, float]:
    """Return hotel estimate using mock data logic when no API is available."""
    base_rates = {
        "junior": 120, "mid": 180, "senior": 250, "executive": 400
    }
    city_multipliers = {
        "NYC": 1.5, "LON": 1.4, "PAR": 1.3, "TYO": 1.2, "SIN": 1.3,
        "DXB": 1.1, "LAX": 1.3, "BER": 1.1, "SYD": 1.2, "HKG": 1.3,
    }
    mult = city_multipliers.get(destination[:3].upper(), 1.0)
    base = base_rates.get(level, 150)
    per_night = base * mult
    total = per_night * nights
    return {"estimate": total, "low": total * 0.85, "high": total * 1.25}


def _mock_ground_transport(destination: str, level: str, days: int) -> Dict[str, float]:
    """Return ground transport estimate."""
    daily = {"junior": 30, "mid": 45, "senior": 60, "executive": 100}
    city_mult = {"NYC": 1.4, "LON": 1.3, "PAR": 1.2, "TYO": 1.5, "SIN": 1.1,
                 "DXB": 1.0, "LAX": 1.2, "BER": 1.1, "SYD": 1.2, "HKG": 1.2}
    mult = city_mult.get(destination[:3].upper(), 1.0)
    d = daily.get(level, 40)
    total = d * mult * days
    return {"estimate": total, "low": total * 0.8, "high": total * 1.3}


def _mock_meals_per_diem(destination: str, level: str, days: int) -> Dict[str, float]:
    """Return meals/per diem estimate."""
    daily = {"junior": 50, "mid": 75, "senior": 100, "executive": 150}
    city_mult = {"NYC": 1.5, "LON": 1.4, "PAR": 1.4, "TYO": 1.3, "SIN": 1.4,
                 "DXB": 1.2, "LAX": 1.4, "BER": 1.2, "SYD": 1.3, "HKG": 1.4}
    mult = city_mult.get(destination[:3].upper(), 1.0)
    d = daily.get(level, 60)
    total = d * mult * days
    return {"estimate": total, "low": total * 0.9, "high": total * 1.15}


def _mock_miscellaneous(destination: str, level: str, days: int) -> Dict[str, float]:
    """Return miscellaneous estimate."""
    daily = {"junior": 20, "mid": 35, "senior": 50, "executive": 80}
    mult = 1.0
    d = daily.get(level, 30)
    total = d * mult * days
    return {"estimate": total, "low": total * 0.8, "high": total * 1.4}


def build_forecast(origin: str, destination: str, start_date: date,
                   end_date: date, traveler_level: str,
                   currency: str) -> Dict[str, Any]:
    """
    Build a full forecast with real API calls and local fallbacks.
    Returns a dict compatible with ForecastResponse creation.
    """
    nights = max((end_date - start_date).days, 1)
    days = nights + 1

    # --- Flight ---
    flight_estimate = 0.0
    flight_low = 0.0
    flight_high = 0.0
    flight_confidence = 0.5
    flight_notes = "Using mock estimate."
    offers = _search_tequila_flights(origin, destination, start_date, end_date)
    if offers:
        prices = []
        for offer in offers:
            try:
                p = float(offer["price"])
                prices.append(p)
            except Exception:
                continue
        if prices:
            prices.sort()
            flight_estimate = prices[len(prices) // 2]  # median
            flight_low = prices[0]
            flight_high = prices[-1]
            flight_confidence = 0.85
            flight_notes = "Based on real Tequila (Kiwi.com) flight offers."
        else:
            flight_notes = "Tequila returned no prices; using fallback."
    if flight_estimate == 0.0:
        # Fallback flight estimate
        base_flight = 300.0
        dist_mult = {"LON": 1.2, "PAR": 1.1, "TYO": 1.8, "SIN": 1.9, "DXB": 1.7,
                     "LAX": 1.3, "BER": 1.2, "SYD": 2.0, "HKG": 1.8}
        mult = dist_mult.get(destination[:3].upper(), 1.0)
        flight_estimate = base_flight * mult
        flight_low = flight_estimate * 0.8
        flight_high = flight_estimate * 1.4
        flight_confidence = 0.55
        if not settings.tequila_api_key:
            flight_notes = "Tequila unavailable (no API key). Mock estimate used."
        else:
            flight_notes = "Tequila returned no offers for this route. Mock estimate used."

    # --- Currency conversion ---
    rate = 1.0
    if currency.upper() != "USD":
        fetched_rate = _get_exchange_rate("USD", currency)
        if fetched_rate:
            rate = fetched_rate
        else:
            rate = 1.0  # fallback to USD if API fails

    # --- Weather factor ---
    season_factor = _get_weather_season_factor(destination, start_date)

    def apply_currency_and_season(val: float) -> float:
        return round(val * rate * season_factor, 2)

    flight = {
        "category": "flight",
        "estimate": apply_currency_and_season(flight_estimate),
        "low": apply_currency_and_season(flight_low),
        "high": apply_currency_and_season(flight_high),
        "confidence": flight_confidence,
        "notes": flight_notes,
    }

    hotel = _mock_hotel_rate(destination, traveler_level, nights)
    hotel = {
        "category": "hotel",
        "estimate": apply_currency_and_season(hotel["estimate"]),
        "low": apply_currency_and_season(hotel["low"]),
        "high": apply_currency_and_season(hotel["high"]),
        "confidence": 0.75,
        "notes": f"{nights} nights, seasonal factor {season_factor}.",
    }

    ground = _mock_ground_transport(destination, traveler_level, days)
    ground = {
        "category": "ground_transport",
        "estimate": apply_currency_and_season(ground["estimate"]),
        "low": apply_currency_and_season(ground["low"]),
        "high": apply_currency_and_season(ground["high"]),
        "confidence": 0.7,
        "notes": f"{days} days.",
    }

    meals = _mock_meals_per_diem(destination, traveler_level, days)
    meals = {
        "category": "meals",
        "estimate": apply_currency_and_season(meals["estimate"]),
        "low": apply_currency_and_season(meals["low"]),
        "high": apply_currency_and_season(meals["high"]),
        "confidence": 0.8,
        "notes": f"{days} days per diem.",
    }

    misc = _mock_miscellaneous(destination, traveler_level, days)
    misc = {
        "category": "miscellaneous",
        "estimate": apply_currency_and_season(misc["estimate"]),
        "low": apply_currency_and_season(misc["low"]),
        "high": apply_currency_and_season(misc["high"]),
        "confidence": 0.6,
        "notes": "Buffer for unexpected expenses.",
    }

    line_items = [flight, hotel, ground, meals, misc]

    total_estimate = sum(i["estimate"] for i in line_items)
    total_low = sum(i["low"] for i in line_items)
    total_high = sum(i["high"] for i in line_items)
    overall_confidence = round(sum(i["confidence"] for i in line_items) / len(line_items), 2)

    summary = generate_forecast_summary(
        destination=destination,
        total_estimate=total_estimate,
        currency=currency,
        confidence=overall_confidence,
        line_items=line_items,
    )

    return {
        "destination": destination,
        "start_date": start_date,
        "end_date": end_date,
        "traveler_level": traveler_level,
        "total_estimate": total_estimate,
        "total_low": total_low,
        "total_high": total_high,
        "overall_confidence": overall_confidence,
        "line_items": line_items,
        "natural_language_summary": summary,
        "currency": currency,
    }
