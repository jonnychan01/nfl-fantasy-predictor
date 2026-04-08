# 🏈 NFL Fantasy Predictor
### Not fully finished - still in progress for improvement

A full-stack NFL fantasy football prediction app built with Python and Svelte.

## What it does

Pulls historical NFL player stats from the Sleeper API across multiple seasons (2020–2025) and uses a hybrid prediction model to project fantasy points for the upcoming season. Supports PPR scoring and covers QB, RB, WR, TE, K, and DEF positions.

## Tech Stack

**Backend**
- Python + FastAPI
- Sleeper API (free, no auth required)
- NumPy for data processing and trend calculations
- Scikit-learn (Ridge regression, per-position ML models)

**Frontend**
- Svelte + Vite
- Sortable, filterable and searchable player table
- Position badges and dark theme UI

## Prediction Model

The model uses a hybrid rule-based + machine learning approach:

- Weighted PPG (recent seasons weighted more heavily)
- Injury history penalty with recovery factor
- Role stability scoring via snap percentage
- Softened age decline curves (rule-based floor, not hard penalty)
- Consecutive zero-game season detection (retirement/injury streaks)
- Per-position Ridge regression ML models trained on historical data
- Age and experience-aware ML/rule blending weights (young players trust rule-based more)
- Confidence blending toward position average based on seasons of data
- Separate simpler models for K and DEF

## Getting Started

**Backend**
```bash
cd api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 fetch_and_cache.py  
uvicorn main:app --reload
```

**Frontend**
```bash
cd app
npm install
npm run dev
```

API runs on `http://localhost:8000` and frontend on `http://localhost:5173`.

## Future Implementations
- O-line run blocking grades as a multiplier for RB projections
- Strength of schedule adjustments per player
- Player detail modal on row click showing season-by-season breakdown
- Some sort of graph or chart
- Week by week predictions 