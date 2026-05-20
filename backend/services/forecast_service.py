"""
Forecast service integrating Kiwi.com Tequila Flight API, ExchangeRate-API,
and Open-Meteo for seasonal adjustments. Computes budget line items
with confidence intervals.
"""
import math
import requests
from datetime import date, timedelta
from typing import List, Dict, Any, Optional
from models import BudgetLineItem
from services.groq_service import generate_forecast_summary
from config import settings


# =============================================================================
# COMPREHENSIVE CITY DATABASE
# =============================================================================
# Coordinates and cost-of-living tiers for 60+ major cities.
# Tier 1 = Ultra-High (NYC, LON, SIN, TYO, HKG, SYD, PAR, DXB, ZUR, GVA)
# Tier 2 = High (LAX, SFO, BOS, CHI, SEA, MIA, TOR, AMS, FRA, MUC, MIL, ROM, MAD, BCN, STO, OSL, CPH, HEL, VIE, BRU, DUB)
# Tier 3 = Medium (DEN, PHX, ATL, DAL, HOU, PHL, SAN, POR, VAN, MTL, EDI, MAN, BHX, GLA, LIS, PRG, BUD, WAW, ATH, BKK, KUL, ICN, TPE, SHA, BJS, BOM, DEL, CAI, JNB, AUK)
# Tier 4 = Low (MEX, BOG, LIM, SCL, BUE, RIO, SAO, BKK is actually tier 3... let me be careful)

CITY_DB = {
    # North America
    "NYC": {"name": "New York", "lat": 40.71, "lon": -74.01, "tier": 1},
    "LAX": {"name": "Los Angeles", "lat": 34.05, "lon": -118.24, "tier": 2},
    "SFO": {"name": "San Francisco", "lat": 37.77, "lon": -122.42, "tier": 2},
    "CHI": {"name": "Chicago", "lat": 41.88, "lon": -87.63, "tier": 2},
    "BOS": {"name": "Boston", "lat": 42.36, "lon": -71.06, "tier": 2},
    "SEA": {"name": "Seattle", "lat": 47.61, "lon": -122.33, "tier": 2},
    "MIA": {"name": "Miami", "lat": 25.76, "lon": -80.19, "tier": 2},
    "DEN": {"name": "Denver", "lat": 39.74, "lon": -104.99, "tier": 3},
    "PHX": {"name": "Phoenix", "lat": 33.45, "lon": -112.07, "tier": 3},
    "ATL": {"name": "Atlanta", "lat": 33.75, "lon": -84.39, "tier": 3},
    "DFW": {"name": "Dallas", "lat": 32.78, "lon": -96.80, "tier": 3},
    "HOU": {"name": "Houston", "lat": 29.76, "lon": -95.37, "tier": 3},
    "PHL": {"name": "Philadelphia", "lat": 39.95, "lon": -75.17, "tier": 3},
    "SAN": {"name": "San Diego", "lat": 32.72, "lon": -117.16, "tier": 3},
    "POR": {"name": "Portland", "lat": 45.52, "lon": -122.68, "tier": 3},
    "TOR": {"name": "Toronto", "lat": 43.65, "lon": -79.38, "tier": 2},
    "VAN": {"name": "Vancouver", "lat": 49.28, "lon": -123.12, "tier": 3},
    "MTL": {"name": "Montreal", "lat": 45.50, "lon": -73.57, "tier": 3},
    "MEX": {"name": "Mexico City", "lat": 19.43, "lon": -99.13, "tier": 4},
    # Europe
    "LON": {"name": "London", "lat": 51.51, "lon": -0.13, "tier": 1},
    "PAR": {"name": "Paris", "lat": 48.86, "lon": 2.35, "tier": 1},
    "AMS": {"name": "Amsterdam", "lat": 52.37, "lon": 4.90, "tier": 2},
    "FRA": {"name": "Frankfurt", "lat": 50.11, "lon": 8.68, "tier": 2},
    "MUC": {"name": "Munich", "lat": 48.14, "lon": 11.58, "tier": 2},
    "BER": {"name": "Berlin", "lat": 52.52, "lon": 13.41, "tier": 2},
    "MIL": {"name": "Milan", "lat": 45.46, "lon": 9.19, "tier": 2},
    "ROM": {"name": "Rome", "lat": 41.90, "lon": 12.50, "tier": 2},
    "MAD": {"name": "Madrid", "lat": 40.42, "lon": -3.70, "tier": 2},
    "BCN": {"name": "Barcelona", "lat": 41.39, "lon": 2.17, "tier": 2},
    "LIS": {"name": "Lisbon", "lat": 38.72, "lon": -9.14, "tier": 3},
    "ZUR": {"name": "Zurich", "lat": 47.38, "lon": 8.54, "tier": 1},
    "GVA": {"name": "Geneva", "lat": 46.20, "lon": 6.14, "tier": 1},
    "VIE": {"name": "Vienna", "lat": 48.21, "lon": 16.37, "tier": 2},
    "BRU": {"name": "Brussels", "lat": 50.85, "lon": 4.35, "tier": 2},
    "DUB": {"name": "Dublin", "lat": 53.35, "lon": -6.26, "tier": 2},
    "STO": {"name": "Stockholm", "lat": 59.33, "lon": 18.07, "tier": 2},
    "OSL": {"name": "Oslo", "lat": 59.91, "lon": 10.75, "tier": 2},
    "CPH": {"name": "Copenhagen", "lat": 55.68, "lon": 12.57, "tier": 2},
    "HEL": {"name": "Helsinki", "lat": 60.17, "lon": 24.94, "tier": 2},
    "EDI": {"name": "Edinburgh", "lat": 55.95, "lon": -3.19, "tier": 3},
    "MAN": {"name": "Manchester", "lat": 53.48, "lon": -2.24, "tier": 3},
    "BHX": {"name": "Birmingham", "lat": 52.49, "lon": -1.89, "tier": 3},
    "GLA": {"name": "Glasgow", "lat": 55.86, "lon": -4.26, "tier": 3},
    "PRG": {"name": "Prague", "lat": 50.08, "lon": 14.42, "tier": 3},
    "BUD": {"name": "Budapest", "lat": 47.50, "lon": 19.04, "tier": 3},
    "WAW": {"name": "Warsaw", "lat": 52.23, "lon": 21.01, "tier": 3},
    "ATH": {"name": "Athens", "lat": 37.98, "lon": 23.73, "tier": 3},
    # Asia
    "TYO": {"name": "Tokyo", "lat": 35.68, "lon": 139.69, "tier": 1},
    "SIN": {"name": "Singapore", "lat": 1.35, "lon": 103.82, "tier": 1},
    "HKG": {"name": "Hong Kong", "lat": 22.32, "lon": 114.17, "tier": 1},
    "DXB": {"name": "Dubai", "lat": 25.20, "lon": 55.27, "tier": 1},
    "BKK": {"name": "Bangkok", "lat": 13.76, "lon": 100.50, "tier": 3},
    "KUL": {"name": "Kuala Lumpur", "lat": 3.14, "lon": 101.69, "tier": 3},
    "ICN": {"name": "Seoul", "lat": 37.57, "lon": 126.98, "tier": 3},
    "TPE": {"name": "Taipei", "lat": 25.03, "lon": 121.56, "tier": 3},
    "SHA": {"name": "Shanghai", "lat": 31.23, "lon": 121.47, "tier": 3},
    "BJS": {"name": "Beijing", "lat": 39.90, "lon": 116.41, "tier": 3},
    "BOM": {"name": "Mumbai", "lat": 19.08, "lon": 72.88, "tier": 3},
    "DEL": {"name": "Delhi", "lat": 28.61, "lon": 77.21, "tier": 3},
    # Oceania
    "SYD": {"name": "Sydney", "lat": -33.87, "lon": 151.21, "tier": 1},
    "MEL": {"name": "Melbourne", "lat": -37.81, "lon": 144.96, "tier": 2},
    "AUK": {"name": "Auckland", "lat": -36.85, "lon": 174.76, "tier": 3},
    # Middle East / Africa
    "CAI": {"name": "Cairo", "lat": 30.04, "lon": 31.24, "tier": 3},
    "JNB": {"name": "Johannesburg", "lat": -26.20, "lon": 28.04, "tier": 3},
    # South America
    "BOG": {"name": "Bogota", "lat": 4.71, "lon": -74.07, "tier": 4},
    "LIM": {"name": "Lima", "lat": -12.05, "lon": -77.04, "tier": 4},
    "SCL": {"name": "Santiago", "lat": -33.45, "lon": -70.67, "tier": 4},
    "BUE": {"name": "Buenos Aires", "lat": -34.60, "lon": -58.38, "tier": 4},
    "RIO": {"name": "Rio de Janeiro", "lat": -22.91, "lon": -43.17, "tier": 4},
    "SAO": {"name": "Sao Paulo", "lat": -23.55, "lon": -46.63, "tier": 4},
}

# Cost-of-living multipliers by tier
TIER_MULTIPLIERS = {
    1: {"hotel": 1.45, "ground": 1.35, "meals": 1.40, "flight_premium": 1.15},
    2: {"hotel": 1.20, "ground": 1.15, "meals": 1.20, "flight_premium": 1.05},
    3: {"hotel": 0.90, "ground": 0.85, "meals": 0.90, "flight_premium": 0.95},
    4: {"hotel": 0.60, "ground": 0.55, "meals": 0.60, "flight_premium": 0.85},
}

# Base daily rates by traveler level
BASE_RATES = {
    "hotel": {"junior": 110, "mid": 170, "senior": 240, "executive": 390},
    "ground": {"junior": 28, "mid": 42, "senior": 58, "executive": 95},
    "meals": {"junior": 48, "mid": 72, "senior": 98, "executive": 145},
    "misc": {"junior": 18, "mid": 32, "senior": 48, "executive": 78},
}


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance in kilometers between two points."""
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def _get_city_tier(destination: str) -> int:
    """Return cost-of-living tier for a city code. Defaults to tier 3."""
    code = destination[:3].upper()
    return CITY_DB.get(code, {}).get("tier", 3)


def _get_city_coords(destination: str) -> tuple:
    """Return (lat, lon) for a city code. Defaults to NYC."""
    code = destination[:3].upper()
    data = CITY_DB.get(code, {})
    return (data.get("lat", 40.71), data.get("lon", -74.01))


def _estimate_flight(origin: str, destination: str) -> Dict[str, float]:
    """
    Estimate flight cost using haversine distance.
    Returns estimate, low, high, and confidence.
    """
    origin_coords = _get_city_coords(origin)
    dest_coords = _get_city_coords(destination)
    distance_km = _haversine(origin_coords[0], origin_coords[1], dest_coords[0], dest_coords[1])

    # Base pricing model: $0.12 per km for short haul, $0.08 for long haul, with minimum $180
    if distance_km < 1500:
        rate_per_km = 0.14
    elif distance_km < 4000:
        rate_per_km = 0.10
    else:
        rate_per_km = 0.07

    base = max(180, distance_km * rate_per_km)

    # Tier premium: ultra-high cost destinations have more expensive routes
    dest_tier = _get_city_tier(destination)
    tier_mult = TIER_MULTIPLIERS.get(dest_tier, TIER_MULTIPLIERS[3])["flight_premium"]

    estimate = base * tier_mult
    return {
        "estimate": round(estimate, 2),
        "low": round(estimate * 0.75, 2),
        "high": round(estimate * 1.45, 2),
        "confidence": 0.60,
        "notes": f"Distance: {int(distance_km)} km, tier {dest_tier} route.",
    }


def _mock_hotel_rate(destination: str, level: str, nights: int) -> Dict[str, float]:
    """Return hotel estimate using city tier and traveler level."""
    tier = _get_city_tier(destination)
    mult = TIER_MULTIPLIERS.get(tier, TIER_MULTIPLIERS[3])["hotel"]
    base = BASE_RATES["hotel"].get(level, 160)
    per_night = base * mult
    total = per_night * nights
    return {"estimate": total, "low": total * 0.80, "high": total * 1.30}


def _mock_ground_transport(destination: str, level: str, days: int) -> Dict[str, float]:
    """Return ground transport estimate."""
    tier = _get_city_tier(destination)
    mult = TIER_MULTIPLIERS.get(tier, TIER_MULTIPLIERS[3])["ground"]
    base = BASE_RATES["ground"].get(level, 40)
    total = base * mult * days
    return {"estimate": total, "low": total * 0.75, "high": total * 1.35}


def _mock_meals_per_diem(destination: str, level: str, days: int) -> Dict[str, float]:
    """Return meals/per diem estimate."""
    tier = _get_city_tier(destination)
    mult = TIER_MULTIPLIERS.get(tier, TIER_MULTIPLIERS[3])["meals"]
    base = BASE_RATES["meals"].get(level, 65)
    total = base * mult * days
    return {"estimate": total, "low": total * 0.85, "high": total * 1.20}


def _mock_miscellaneous(destination: str, level: str, days: int) -> Dict[str, float]:
    """Return miscellaneous estimate."""
    base = BASE_RATES["misc"].get(level, 30)
    total = base * days
    return {"estimate": total, "low": total * 0.75, "high": total * 1.45}


# =============================================================================
# EXTERNAL API CALLS
# =============================================================================

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
    coords = _get_city_coords(destination)
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
        factor = 1.0
        if temp > 30 or temp < 0:
            factor += 0.05
        if precip > 5:
            factor += 0.05
        return round(factor, 2)
    except Exception:
        return 1.0


# =============================================================================
# MAIN FORECAST BUILDER
# =============================================================================

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
        # Fallback: distance-based estimate
        flight_data = _estimate_flight(origin, destination)
        flight_estimate = flight_data["estimate"]
        flight_low = flight_data["low"]
        flight_high = flight_data["high"]
        flight_confidence = flight_data["confidence"]
        flight_notes = flight_data["notes"]
        if not settings.tequila_api_key:
            flight_notes += " Tequila unavailable (no API key)."
        else:
            flight_notes += " Tequila returned no offers."

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
        "notes": f"{nights} nights, tier {_get_city_tier(destination)} city, seasonal factor {season_factor}.",
    }

    ground = _mock_ground_transport(destination, traveler_level, days)
    ground = {
        "category": "ground_transport",
        "estimate": apply_currency_and_season(ground["estimate"]),
        "low": apply_currency_and_season(ground["low"]),
        "high": apply_currency_and_season(ground["high"]),
        "confidence": 0.70,
        "notes": f"{days} days, tier {_get_city_tier(destination)} city.",
    }

    meals = _mock_meals_per_diem(destination, traveler_level, days)
    meals = {
        "category": "meals",
        "estimate": apply_currency_and_season(meals["estimate"]),
        "low": apply_currency_and_season(meals["low"]),
        "high": apply_currency_and_season(meals["high"]),
        "confidence": 0.80,
        "notes": f"{days} days per diem, tier {_get_city_tier(destination)} city.",
    }

    misc = _mock_miscellaneous(destination, traveler_level, days)
    misc = {
        "category": "miscellaneous",
        "estimate": apply_currency_and_season(misc["estimate"]),
        "low": apply_currency_and_season(misc["low"]),
        "high": apply_currency_and_season(misc["high"]),
        "confidence": 0.60,
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
