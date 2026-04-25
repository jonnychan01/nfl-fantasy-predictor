# 🏈 NFL Fantasy Predictor

### Not fully finished - still in progress for improvement

A full-stack NFL fantasy football prediction app built with Python and Svelte.

## What it does

Pulls historical NFL player stats from the Sleeper API across multiple seasons (2020–2025) and uses a hybrid prediction model to project fantasy points for the upcoming season. Supports PPR scoring and covers QB, RB, WR, TE, K, and DEF positions.

## Tech Stack

**Backend**

* Python + FastAPI
* Sleeper API (free, no auth required)
* NumPy for data processing and trend calculations
* LightGBM (per-position gradient boosted ML models)
* Scikit-learn (cross-validation, model evaluation)

**Frontend**

* Svelte + Vite
* Sortable, filterable and searchable player table
* Position badges and dark theme UI

## Prediction Model

The model uses a hybrid rule-based + machine learning approach:

* Weighted PPG (recent seasons weighted more heavily)
* Injury history penalty with recovery factor
* Role stability scoring via snap percentage
* Softened age decline curves (rule-based floor, not hard penalty)
* Consecutive zero-game season detection (retirement/injury streaks)
* Per-position LightGBM models trained on historical season-over-season data
* Age and experience-aware ML/rule blending weights (young players lean rule-based)
* Target spike detection to catch breakout role changes
* Target share and red zone target share as features
* Confidence blending toward position average based on seasons of data
* ML models saved to disk after first run — no retraining on restart

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

The first startup will train and cache the ML models to disk. Subsequent restarts load from cache and are much faster.

**Frontend**

```bash
cd app
npm install
npm run dev
```

API runs on `http://localhost:8000` and frontend on `http://localhost:5173`.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/players` | All players, optional `?position=QB` filter |
| GET | `/api/players/{id}` | Single player |
| GET | `/api/players/{id}/weekly` | Weekly projection, optional `?opponent=SF` |
| GET | `/api/positions` | List of positions |
| GET | `/api/schedule/{team}` | Team schedule |
| POST | `/api/cache/refresh` | Force retrain and rebuild player cache |
| GET | `/api/ml/evaluate` | Run cross-validation and print R² scores |

## Future Implementations

* Opponent multiplier logic in the weekly projection endpoint
* Auto-delete cached ML models when new stats are fetched so predictions never go stale
* Season-by-season stat breakdown in the frontend (data is already in the API response)
* Bust/sleeper tags based on projected points vs ADP
* Injury flag for players who missed 4+ games last season
* Strength of schedule adjustments using the existing schedule cache
* Breakout candidate badges in the UI powered by the existing target spike detection