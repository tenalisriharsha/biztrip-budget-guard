# BizTrip Budget Guard — Testing Guide

Run these `curl` commands in Terminal while the backend is running on `http://localhost:8000`.

---

## 1. Health Check

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"ok"}
```

---

## 2. Generate a Forecast

```bash
curl -X POST http://localhost:8000/forecast \
  -H "Content-Type: application/json" \
  -d '{
    "destination": "LON",
    "origin": "NYC",
    "start_date": "2026-06-01",
    "end_date": "2026-06-05",
    "traveler_level": "mid",
    "currency": "USD"
  }'
```

Expected response includes `trip_id`, `total_estimate`, `line_items`, and `natural_language_summary`.

**Save the `trip_id` value** — you will need it for the next steps.

---

## 3. Record a Spend Transaction

Replace `1` with your actual `trip_id`:

```bash
curl -X POST http://localhost:8000/spend \
  -H "Content-Type: application/json" \
  -d '{
    "trip_id": 1,
    "category": "meals",
    "amount": 85.50,
    "currency": "USD",
    "description": "Team dinner",
    "merchant": "Bistro Central"
  }'
```

Repeat with different categories and amounts to trigger alerts:

```bash
curl -X POST http://localhost:8000/spend \
  -H "Content-Type: application/json" \
  -d '{
    "trip_id": 1,
    "category": "hotel",
    "amount": 950.00,
    "currency": "USD",
    "description": "Four nights",
    "merchant": "Grand Hotel"
  }'
```

---

## 4. Check Alerts

```bash
curl "http://localhost:8000/trips/1/alerts"
```

Returns alerts when any category exceeds 80% of its budget.

---

## 5. Check Burn Rate

```bash
curl "http://localhost:8000/trips/1/burn"
```

Returns total budget, spent, remaining, daily burn rate, and projected overspend.

---

## 6. Run Reconciliation

```bash
curl -X POST "http://localhost:8000/reconcile?trip_id=1"
```

Returns `total_budgeted`, `total_spent`, `variance`, `anomalies`, and `natural_language_summary`.

---

## 7. List All Trips

```bash
curl http://localhost:8000/trips
```

---

## 8. View Transactions for a Trip

```bash
curl "http://localhost:8000/trips/1/transactions"
```

---

## 9. View Budget for a Trip

```bash
curl "http://localhost:8000/trips/1/budget"
```

---

## 10. View Anomalies for a Trip

```bash
curl "http://localhost:8000/trips/1/anomalies"
```

---

## Quick Verification Checklist

- [ ] `POST /forecast` returns a JSON with `trip_id`
- [ ] `POST /spend` returns `transaction_id` and `alerts`
- [ ] `GET /trips/{id}/alerts` shows warnings when >80% spent
- [ ] `POST /reconcile` flags anomalies with Z-score / IQR logic
- [ ] Frontend at `http://localhost:5173` shows charts and data
