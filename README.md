# 🏈 NFL Fantasy Predictor
### Not fully finished - still in progress for improvement

A full-stack NFL fantasy football prediction app built with Python and Svelte.

## What it does

Pulls historical NFL player stats from the Sleeper API across multiple seasons (2020–2025) and uses a custom prediction model to project fantasy points for the upcoming season. Supports PPR scoring and covers QB, RB, WR, TE, K, and DEF positions.

## Tech Stack

**Backend**
- Python + FastAPI
- Sleeper API (free, no auth required)
- NumPy for data processing and trend calculations

**Frontend**
- Svelte + Vite
- Sortable, filterable player table
- Position badges and dark theme UI

## Prediction Model

The model uses multiple seasons of data to generate projections:
- Weighted PPG (recent seasons weighted more heavily)
- Position-specific age decline curves
- Role stability scoring via snap percentage
- Injury history penalty
- Separate simpler models for K and DEF

## Getting Started

**Backend**
```bash
cd api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 fetch_and_cache.py  # fetch and cache Sleeper API data
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

- Positional average regression for rookies and injury-returning players
- O-line run blocking grades as a multiplier for RB projections
- QB quality changing WR and TE projections
- Strength of schedule adjustments per player
- Machine learning model (Hopefully) to help with more accurate projections
- Player detail modal on row click showing season-by-season breakdown
- Some sort of graph or chart

## Acknowledgements
Claude was used to help with some code generations, debugging and styling throughout the project
