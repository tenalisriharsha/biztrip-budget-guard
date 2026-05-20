BizTrip Budget Guard

Project Overview
BizTrip Budget Guard is a full-stack AI-powered corporate travel budget management prototype built for BizTrip AI.
The application helps finance teams and employees forecast trip costs before booking, track real-time spending against budgets during travel, and reconcile expenses after trips with statistical anomaly detection and AI-generated explanations.
Live Demo: https://biztrip-budget-guard-1xjsgh4dg.vercel.app
 
Why This Project Exists
Corporate travel is one of the largest unmanaged cost centers for enterprises. Current tools handle booking and expense reporting separately — no unified system predicts costs before travel, warns during travel, and learns after travel.
Budget Guard closes this loop with three phases:
1.	Pre-Trip Forecast — Predict total trip cost with confidence intervals before anyone books a flight
2.	Real-Time Spend Tracker — Track card transactions against the forecast and alert when categories hit 80% or 100% of budget
3.	Post-Trip Reconciliation — Auto-detect anomalies using Z-score and IQR statistical methods, with AI-powered explanations
 
Key Features
Phase 1: Pre-Trip Forecast
•	Input destination (IATA code), origin, dates, traveler level, and currency
•	Real flight price search via Kiwi.com Tequila API
•	Live currency conversion via ExchangeRate-API
•	Weather-based seasonal pricing adjustments via Open-Meteo
•	Five budget line items: Flight, Hotel, Ground Transport, Meals, Miscellaneous
•	Point estimates with low-high confidence intervals
•	Groq AI (Llama 3.3 70B) generates natural language summaries with actionable advice
•	Mandatory rule-based fallback templates if AI is unavailable
Phase 2: Real-Time Spend Tracker
•	Mock webhook endpoint accepts card transactions
•	Per-category budget tracking with live burn rate calculation
•	Smart alerts at 80% (warning) and 100% (critical) thresholds
•	AI-generated alert messages with human-readable context
•	Daily burn rate and projected overspend calculation
Phase 3: Post-Trip Reconciliation
•	Statistical anomaly detection using Z-score and IQR methods
•	Fallback to strict budget range checks (±20%) for small sample sizes
•	Severity classification: Low / Medium / High
•	AI-generated explanations for every anomaly
•	Visual analytics: Budgeted vs Actual, Variance, Spend Distribution, Burn Rate %, Anomaly Breakdown
 
Tech Stack
Backend
Tool	Purpose
Python 3.12	Programming language
FastAPI	Web framework with auto-generated OpenAPI docs
Uvicorn	ASGI server
Pydantic	Data validation and settings management
SQLAlchemy	ORM for SQLite
SQLite	File-based database (zero setup)
Groq SDK	LLM client (Llama 3.3 70B / Mixtral 8x7B)
Requests / HTTPX	HTTP clients for external APIs
Frontend
Tool	Purpose
React 18	UI library
Vite	Build tool and dev server
React Router DOM	Client-side navigation
Axios	HTTP client
Recharts	Data visualization (bar charts, pie charts, area charts)
External APIs (All Free Tier)
API	Purpose	Free Tier
Groq API	AI summaries & explanations	20 req/min, 1.5M tokens/day
Kiwi.com Tequila API	Real flight price search	Free for non-commercial use
ExchangeRate-API	Live currency conversion	1,500 requests/month
Open-Meteo API	Weather & seasonal adjustments	Unlimited, no API key needed
Deployment
Layer	Platform	Plan
Frontend	Vercel	Free (Hobby)
Backend	Render	Free (Web Service)
Database	SQLite file	Render ephemeral disk
Source Control	GitHub	Free
 
Architecture
User Input (Forecast)
       ↓
FastAPI → forecast_service.py
   ├── Tequila API (flight prices)
   ├── ExchangeRate-API (currency)
   └── Open-Meteo (weather factor)
       ↓
Budget calculation + confidence intervals
       ↓
Groq AI → natural language summary
       ↓
SQLite (trips + budgets table)

User Spend (Webhook)
       ↓
POST /spend → spend_service.py
   ├── Record transaction (SQLite)
   ├── Check thresholds (80% / 100%)
   └── Groq AI → alert message
       ↓
SQLite (transactions table)

Reconcile Request
       ↓
POST /reconcile → reconcile_service.py
   ├── Fetch transactions + budgets
   ├── Z-score + IQR anomaly detection
   └── Groq AI → anomaly explanations
       ↓
SQLite (anomalies table)
 
Folder Structure
biztrip-budget-guard/
├── backend/
│   ├── main.py                 # FastAPI app entry point, all routes, CORS
│   ├── config.py               # Settings from .env
│   ├── models.py               # Pydantic request/response models
│   ├── database.py             # SQLAlchemy SQLite setup
│   ├── requirements.txt        # Python dependencies
│   ├── .env.example            # Environment variable template
│   ├── Procfile                # Render process definition
│   ├── render.yaml             # Render infrastructure config
│   └── services/
│       ├── forecast_service.py # Flight + currency + weather + budget logic
│       ├── spend_service.py    # Transaction recording, alerts, burn rate
│       ├── reconcile_service.py# Anomaly detection (Z-score, IQR)
│       └── groq_service.py     # LLM client with mandatory fallbacks
├── frontend/
│   ├── index.html              # Root HTML
│   ├── package.json            # Node dependencies
│   ├── vite.config.js          # Vite config + proxy
│   ├── vercel.json             # Vercel build config
│   └── src/
│       ├── main.jsx            # React entry point
│       ├── App.jsx             # Main layout + routing
│       ├── components/
│       │   ├── ForecastForm.jsx      # Pre-trip input form
│       │   ├── BudgetDashboard.jsx   # Charts: budget, burn rate, confidence
│       │   ├── SpendTracker.jsx      # Real-time spend feed + alerts
│       │   ├── ReconcileView.jsx     # Post-trip reconciliation trigger
│       │   ├── PostTripDashboard.jsx # Budget vs actual analytics
│       │   └── AlertBanner.jsx       # Reusable alert component
│       ├── services/
│       │   └── api.js                # Axios client, all backend calls
│       └── data/
│           └── mockData.js           # Fallback rates by city & level
├── runtime.txt                 # Render Python version specifier
├── .gitignore                  # Git exclusions
├── SETUP.md                    # Local setup guide
├── TESTING.md                  # curl testing guide
└── DEPLOYMENT.md               # Render + Vercel deployment guide
 
Database Schema (SQLite)
trips
Column	Type	Purpose
id	Integer (PK)	Trip identifier
destination	String	IATA code or city name
origin	String	Departure city
start_date	Date	Trip start
end_date	Date	Trip end
traveler_level	String	IC / Manager / Executive
currency	String	Target currency code
created_at	DateTime	Record timestamp
budgets
Column	Type	Purpose
id	Integer (PK)	Budget line item ID
trip_id	Integer (FK)	Associated trip
category	String	flight / hotel / ground_transport / meals / miscellaneous
estimate	Float	Point estimate
low	Float	Confidence interval lower bound
high	Float	Confidence interval upper bound
confidence	Float	0.0 – 1.0
notes	String	Context
created_at	DateTime	Record timestamp
transactions
Column	Type	Purpose
id	Integer (PK)	Transaction ID
trip_id	Integer (FK)	Associated trip
category	String	Budget category
amount	Float	Spend amount
currency	String	Transaction currency
description	String	Merchant or note
merchant	String	Vendor name
timestamp	DateTime	Transaction time
anomalies
Column	Type	Purpose
id	Integer (PK)	Anomaly ID
trip_id	Integer (FK)	Associated trip
transaction_id	Integer (FK)	Source transaction
category	String	Budget category
amount	Float	Actual spend
expected_range_low	Float	Lower statistical bound
expected_range_high	Float	Upper statistical bound
severity	String	Low / Medium / High
explanation	String	AI or template explanation
created_at	DateTime	Record timestamp
 
API Endpoints
Method	Endpoint	Description
GET	/health	Health check
POST	/forecast	Generate pre-trip budget
POST	/spend	Record transaction + check alerts
GET	/trips	List all trips
GET	/trips/{id}/budget	Get budget line items
GET	/trips/{id}/transactions	Get transactions
GET	/trips/{id}/alerts	Get active alerts
GET	/trips/{id}/burn	Get burn rate metrics
GET	/trips/{id}/anomalies	Get flagged anomalies
POST	/reconcile	Run post-trip reconciliation
All endpoints include Pydantic validation, try/except error handling, and CORS enabled for the frontend origin.
 
AI / LLM Integration (Groq)
Every AI feature has a mandatory rule-based fallback — the demo works even if Groq is down.
AI Function	What Groq Does	Fallback (if rate-limited/error)
generate_forecast_summary	Writes 2–3 sentence trip summary with advice	Template: “Your trip to X is estimated at $Y with Z% confidence…”
generate_alert_message	Writes concise spending alert	Template: “WARNING: Trip X category is at Y% of budget…”
generate_anomaly_explanation	Explains possible causes of anomaly	Template: “The X charge exceeds expected range. Possible causes: upgraded service…”
Rate limit handling: - Primary model: llama-3.3-70b-versatile - Fallback model: mixtral-8x7b-32768 - If both fail → returns local template immediately
 
Resilience & Fallbacks
The app is designed to work 100% even without API keys:
Service	Limit	Fallback Behavior
Render Free	Sleeps after 15 min inactivity	First request takes ~30s to wake
Render Free	512 MB RAM	SQLite only, no heavy processing
Vercel Free	100 GB/month bandwidth	More than enough for demo
Groq Free	20 req/min	Rule-based templates
ExchangeRate-API	1,500 req/month	Fallback to USD (rate = 1.0)
Tequila API	Free non-commercial	Distance-based mock flight estimates
Open-Meteo	Unlimited	Seasonal factor = 1.0 (no adjustment)
 
How to Run Locally
Prerequisites
•	macOS (tested on MacBook Air M2, 8GB RAM)
•	Python 3.12+
•	Node.js 18+
Backend Setup
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Add your free API keys to .env
uvicorn main:app --reload --port 8000
Frontend Setup
cd frontend
npm install
npm run dev
Open http://localhost:5173 in your browser.
 
Testing
Use the curl commands in TESTING.md to verify every endpoint:
# Health check
curl http://localhost:8000/health

# Create forecast
curl -X POST http://localhost:8000/forecast   -H "Content-Type: application/json"   -d '{
    "origin": "NYC",
    "destination": "LAX",
    "start_date": "2026-06-01",
    "end_date": "2026-06-05",
    "traveler_level": "manager",
    "currency": "USD"
  }'
 
Deployment
Backend → Render
1.	Push code to GitHub
2.	Create new Web Service on Render
3.	Connect GitHub repo
4.	Set environment variables from .env.example
5.	Deploy
Frontend → Vercel
1.	Push frontend/ to GitHub
2.	Import project on Vercel
3.	Set Framework Preset to Vite
4.	Set Root Directory to frontend
5.	Add environment variable VITE_API_URL pointing to Render backend
6.	Deploy
See DEPLOYMENT.md for full details.
 
Key Design Decisions
Decision	Rationale
SQLite over PostgreSQL	Zero setup, file-based, perfect for prototype and free deployment
Mock data with real API fallbacks	App works 100% even without API keys or when services are down
Every external call has try/except	No crashes if APIs fail
Rule-based fallbacks for every AI function	Demo-ready even if Groq is rate-limited
Monorepo structure	Backend and frontend in one GitHub repo for simplicity
CORS wide open	Simplifies cross-origin during prototyping
 
What Happens When Budget Is Overspent
Stage	Detection	Action	User Sees
Real-time	Transaction pushes category ≥80%	AI alert generated	Red warning banner in Spend Tracker
Real-time	Transaction pushes category ≥100%	Critical alert generated	Critical alert with AI explanation
Burn Rate	Projected total > budget	projected_overspend calculated	Red banner in Dashboard
Reconciliation	Transaction outside statistical bounds	Anomaly flagged	Anomaly list + AI explanation in Post-Trip Dashboard
 
Future Roadmap
•	☐ Integration with corporate card APIs (Stripe Issuing, Brex)
•	☐ Multi-currency real-time conversion with caching
•	☐ Policy engine integration (travel policy enforcement)
•	☐ Slack/Teams bot for instant alerts
•	☐ Manager approval workflows for high-budget trips
•	☐ Historical learning — per-company, per-traveler cost baselines
•	☐ Integration with BizTrip AI’s multi-agent orchestration layer
 
About the Builder
Built by Sri Harsha Chakravarthy Tenali — backend engineer with 3+ years designing scalable microservices, event-driven workflows, and AI integrations for fintech and enterprise platforms.
Contact: tenalisriharsha@gmail.com
LinkedIn: linkedin.com/in/tenalisriharsha
GitHub: github.com/tenalisriharsha
 
License
Open source for demonstration purposes. Built entirely with free-tier tools and open-source libraries.
 
Built for BizTrip AI — travel with intelligent budget management.
