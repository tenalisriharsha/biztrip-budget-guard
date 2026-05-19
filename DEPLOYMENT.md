# BizTrip Budget Guard — Deployment Notes

Deploy the backend to **Render** free tier and the frontend to **Vercel** free tier.

---

## Backend Deployment (Render Free Tier)

### 1. Prepare Render Config

Create `backend/render.yaml` in your repo:

```yaml
services:
  - type: web
    name: biztrip-budget-guard-api
    runtime: python
    plan: free
    buildCommand: "pip install -r requirements.txt"
    startCommand: "uvicorn main:app --host 0.0.0.0 --port $PORT"
    envVars:
      - key: DATABASE_URL
        value: sqlite:///./biztrip.db
      - key: GROQ_API_KEY
        sync: false
      - key: AMADEUS_API_KEY
        sync: false
      - key: AMADEUS_API_SECRET
        sync: false
      - key: EXCHANGE_RATE_API_KEY
        sync: false
```

Create `backend/Procfile`:

```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

### 2. Push to GitHub

```bash
cd ~/Desktop/biztrip-budget-guard
git init
git add .
git commit -m "Initial commit"
```

Create a free GitHub repo and push:

```bash
git remote add origin https://github.com/YOUR_USERNAME/biztrip-budget-guard.git
git branch -M main
git push -u origin main
```

### 3. Deploy on Render

1. Go to https://dashboard.render.com
2. Click **New +** → **Web Service**
3. Connect your GitHub repo
4. Use these settings:
   - **Name**: `biztrip-budget-guard-api`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free
5. Add environment variables from your `.env` file in the Render dashboard
6. Click **Deploy**

Your backend will be available at `https://biztrip-budget-guard-api.onrender.com` (or similar).

> **Note:** Render free tier spins down after 15 minutes of inactivity. First request may take ~30 seconds to wake up.

---

## Frontend Deployment (Vercel Free Tier)

### 1. Add Environment Variable for Production API

Create `frontend/.env.production`:

```env
VITE_API_URL=https://biztrip-budget-guard-api.onrender.com
```

### 2. Push Frontend Code

If you pushed the whole repo to GitHub, the frontend folder is already there.

### 3. Deploy on Vercel

1. Go to https://vercel.com
2. Click **Add New Project**
3. Import your GitHub repo
4. In project settings:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
5. Add environment variable:
   - `VITE_API_URL` = your Render backend URL
6. Click **Deploy**

Your frontend will be available at a Vercel URL like `https://biztrip-budget-guard.vercel.app`.

---

## Post-Deployment Verification

1. Visit your Vercel frontend URL
2. Open browser DevTools → Network tab
3. Generate a forecast and confirm requests hit your Render backend
4. Check Render logs if anything fails

---

## Important Free Tier Limits

| Service | Limit |
|---------|-------|
| Render Web Service | 512 MB RAM, sleeps after 15 min inactivity |
| Vercel | 100 GB bandwidth/month, 10s serverless function timeout |
| Groq Free | 20 requests/minute, 1,500,000 tokens/day |
| Amadeus Test | 2,000 API calls/month |
| ExchangeRate-API | 1,500 requests/month |
| Open-Meteo | Unlimited, no key required |

The app is built to fall back to local logic if any API limit is reached.
