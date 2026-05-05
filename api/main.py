from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from data import load_all_data
import numpy as np
from predictor import predict
from ml_predictor import get_ml_predictor
import os
import json
import httpx
from collections import defaultdict
from adp_estimator import ADPEstimator

DEFENSE_RANKINGS = {
    "SF": 17.2, "BAL": 18.1, "BUF": 18.4, "PHI": 18.9, "KC": 19.2,
    "MIN": 19.8, "DET": 20.1, "GB": 20.4, "PIT": 20.7, "LAC": 21.0,
    "HOU": 21.3, "WAS": 21.6, "CLE": 21.9, "SEA": 22.1, "DAL": 22.4,
    "MIA": 22.7, "TB": 23.0, "ATL": 23.2, "LAR": 23.5, "DEN": 23.8,
    "IND": 24.0, "CIN": 24.3, "NYJ": 24.6, "LV": 24.9, "JAX": 25.2,
    "NE": 25.5, "NYG": 25.8, "ARI": 26.1, "CHI": 26.4, "NO": 26.7,
    "CAR": 27.0, "TEN": 27.3
}

LEAGUE_AVG = sum(DEFENSE_RANKINGS.values()) / len(DEFENSE_RANKINGS)

DEPTH_CHART_POSITIONS = ["QB", "RB", "WR", "TE", "K", "DEF"]

players_cache = None
_ml = None
_sleeper_players_cache = None


def fetch_adp_data() -> dict:
    try:
        url = "https://api.sleeper.com/projections/nfl/2025?season_type=regular&position[]=QB&position[]=RB&position[]=WR&position[]=TE&position[]=K&position[]=DEF"
        res = httpx.get(url, timeout=30)
        raw = res.json()
        adp_map = {}
        for entry in raw:
            pid = entry.get("player_id")
            adp = entry.get("stats", {}).get("adp_ppr")
            if pid and adp and adp < 999:
                adp_map[pid] = round(adp, 1)
        return adp_map
    except Exception as e:
        print(f"ADP fetch failed: {e}")
        return {}


def fetch_sleeper_players() -> dict:
    """Fetch and cache the full Sleeper players roster (used for depth charts)."""
    global _sleeper_players_cache
    if _sleeper_players_cache is not None:
        return _sleeper_players_cache

    cache_path = "cache/sleeper_players.json"

    # Use cached file if it exists and is recent enough
    if os.path.exists(cache_path):
        try:
            with open(cache_path) as f:
                _sleeper_players_cache = json.load(f)
            print(f"Loaded Sleeper players from disk cache ({len(_sleeper_players_cache)} players)")
            return _sleeper_players_cache
        except Exception:
            pass

    try:
        print("Fetching Sleeper players database...")
        res = httpx.get("https://api.sleeper.app/v1/players/nfl", timeout=60)
        data = res.json()
        os.makedirs("cache", exist_ok=True)
        with open(cache_path, "w") as f:
            json.dump(data, f)
        _sleeper_players_cache = data
        print(f"Fetched and cached {len(data)} Sleeper players")
        return data
    except Exception as e:
        print(f"Sleeper players fetch failed: {e}")
        return {}


def build_players_cache():
    global players_cache, _ml

    training_data = load_all_data(require_team=False)
    _ml = get_ml_predictor(training_data, force_retrain=True)

    active_players = load_all_data(require_team=True)
    adp_data = fetch_adp_data()
    players_cache = []

    for player_id, player in active_players.items():
        raw_score = predict(player)
        ml_score = _ml.predict(player)

        num_seasons = len(player["seasons"])
        age = player.get("age", 25) or 25
        position = player.get("position")

        if position == "RB":
            last_season = max(player["seasons"].values(), key=lambda s: s.get("games_played", 0))
            is_workhorse = last_season.get("snap_percentage", 0) > 0.7 and last_season.get("ppg", 0) > 18
            if is_workhorse:
                ml_weight, rule_weight = 0.2, 0.9
            elif age <= 24 or num_seasons <= 2:
                ml_weight, rule_weight = 0.2, 0.8
            else:
                ml_weight, rule_weight = 0.8, 0.2

        elif position == "WR":
            last_season = sorted(player["seasons"].items())[-1][1]
            last_gp = last_season.get("games_played", 17)
            last_ppg = last_season.get("ppg", 0)
            if num_seasons <= 2:
                ml_weight, rule_weight = 0.1, 0.9
            elif age <= 24:
                ml_weight, rule_weight = 0.2, 0.8
            elif last_gp < 12:
                ml_weight, rule_weight = 0.2, 0.8
            elif last_ppg > 12 and last_season.get("target_share", 0) > 0.15:
                ml_weight, rule_weight = 0.25, 0.75
            else:
                ml_weight, rule_weight = 0.5, 0.5

        elif position == "QB":
            if age <= 24 and num_seasons <= 2:
                ml_weight, rule_weight = 0.9, 0.1
            else:
                ml_weight, rule_weight = 0.3, 0.7

        elif position in ("K", "DEF"):
            ml_weight, rule_weight = 0.0, 1.0

        else:
            ml_weight, rule_weight = 0.1, 0.9

        combined = round((raw_score * rule_weight) + (ml_score * ml_weight), 1)

        players_cache.append({
            "player_id": player_id,
            "name": player["name"],
            "position": player["position"],
            "team": player["team"],
            "age": player["age"],
            "years_experience": player["years_experience"],
            "projected_points": combined,
            "num_seasons": num_seasons,
            "seasons": player["seasons"],
            "adp": adp_data.get(player_id),
        })

    players_cache.sort(key=lambda x: x["projected_points"], reverse=True)

    pos_rank = defaultdict(int)

    for i, p in enumerate(players_cache):
        p["projected_rank"] = i + 1
        pos_rank[p["position"]] += 1
        p["projected_pos_rank"] = pos_rank[p["position"]]

    estimator = ADPEstimator()
    estimator.fit(players_cache)

    for p in players_cache:
        estimated = estimator.predict_adp(p, p["projected_pos_rank"], p["projected_rank"])
        p["estimated_adp"] = estimated
        adp = p.get("adp")
        p["tag"] = estimator.tag(adp, estimated)
        p["adp_diff"] = round(round(adp) - round(estimated)) if adp and estimated else None

    print(f"Cache built — {len(players_cache)} players loaded")


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Building player cache at startup...")
    build_players_cache()
    yield
    print("Server shutting down")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_players():
    return players_cache


@app.get("/api/players")
def get_all_players(position: str = None):
    players = get_players()
    if position and position != "ALL":
        players = [p for p in players if p["position"] == position.upper()]
    return players


@app.get("/api/players/{player_id}")
def get_player(player_id: str):
    players = get_players()
    for player in players:
        if player["player_id"] == player_id:
            return player
    return {"error": "Player not found"}


@app.get("/api/positions")
def get_positions():
    return ["ALL", "QB", "RB", "WR", "TE", "K", "DEF"]


@app.get("/api/players/{player_id}/weekly")
def get_weekly_projection(player_id: str, opponent: str = None):
    players = get_players()
    player = next((p for p in players if p["player_id"] == player_id), None)

    if not player:
        return {"error": "Player not found"}

    base_weekly = round(player["projected_points"] / 17, 1)
    opp_mult = 1.0
    opp_rating = None

    if opponent:
        opponent = opponent.upper()
        if opponent not in DEFENSE_RANKINGS:
            return {"error": f"Unknown opponent: {opponent}"}
        opp_rating = DEFENSE_RANKINGS[opponent]
        opp_mult = round(opp_rating / LEAGUE_AVG, 4)

    adjusted = round(base_weekly * opp_mult, 1)

    return {
        "player_id": player_id,
        "name": player["name"],
        "position": player["position"],
        "team": player["team"],
        "base_weekly_projection": base_weekly,
        "opponent": opponent,
        "opponent_defense_rating": opp_rating,
        "league_avg_defense_rating": round(LEAGUE_AVG, 2),
        "opponent_multiplier": opp_mult,
        "adjusted_projection": adjusted,
        "matchup_quality": (
            "favorable" if opp_mult >= 1.05
            else "unfavorable" if opp_mult <= 0.95
            else "neutral"
        )
    }


@app.get("/api/players/{player_id}/schedule-projections")
def get_schedule_projections(player_id: str):
    players = get_players()
    player = next((p for p in players if p["player_id"] == player_id), None)

    if not player:
        return {"error": "Player not found"}

    team = player["team"]
    schedule_path = f"cache/schedule_{team.upper()}.json"
    if not os.path.exists(schedule_path):
        return {"error": "Schedule not found", "team": team}

    with open(schedule_path) as f:
        schedule = json.load(f)

    base = player["projected_points"] / 17
    raw_mults = [DEFENSE_RANKINGS.get(w["opponent"], LEAGUE_AVG) for w in schedule]
    schedule_avg = sum(raw_mults) / len(raw_mults)
    multipliers = [m / schedule_avg for m in raw_mults]

    weeks = []
    for week, mult in zip(schedule, multipliers):
        projected = round(base * mult, 1)
        weeks.append({
            "week": week["week"],
            "opponent": week["opponent"],
            "home": week.get("home", True),
            "defense_rating": DEFENSE_RANKINGS.get(week["opponent"], LEAGUE_AVG),
            "multiplier": round(mult, 4),
            "projected": projected,
        })

    sorted_weeks = sorted(weeks, key=lambda w: w["projected"], reverse=True)

    return {
        "player_id": player_id,
        "name": player["name"],
        "weeks": weeks,
        "best_matchups": sorted_weeks[:3],
        "worst_matchups": sorted_weeks[-3:][::-1],
    }


@app.get("/api/schedule/{team}")
def get_team_schedule(team: str):
    path = f"cache/schedule_{team.upper()}.json"
    if not os.path.exists(path):
        return {"error": "Schedule not found"}
    with open(path) as f:
        schedule = json.load(f)
    return schedule


@app.get("/api/players/{player_id}/adp-history")
def get_adp_history(player_id: str):
    players = get_players()
    player = next((p for p in players if p["player_id"] == player_id), None)

    if not player:
        return {"error": "Player not found"}

    hist_path = "cache/historical_adp.json"
    historical = []

    if os.path.exists(hist_path):
        try:
            with open(hist_path) as f:
                hist = json.load(f)
            player_hist = hist.get(player_id, {})
            for year in sorted(player_hist.keys()):
                entry = player_hist[year]
                adp = entry.get("adp")
                if adp and adp < 400:
                    historical.append({"year": int(year), "adp": round(adp, 1)})
        except Exception as e:
            print(f"ADP history read failed: {e}")

    return {
        "player_id": player_id,
        "name": player["name"],
        "historical": historical,
        "current_adp": player.get("adp"),
        "estimated_adp": player.get("estimated_adp"),
    }


@app.get("/api/players/{player_id}/depth-chart")
def get_depth_chart(player_id: str):
    players = get_players()
    player = next((p for p in players if p["player_id"] == player_id), None)

    if not player:
        return {"error": "Player not found"}

    team = player["team"]
    sleeper_players = fetch_sleeper_players()

    if not sleeper_players:
        return {"error": "Could not load player data"}

    # Collect all players on this team with depth chart info
    depth_by_pos: dict = {pos: [] for pos in DEPTH_CHART_POSITIONS}

    for pid, pdata in sleeper_players.items():
        if pdata.get("team") != team:
            continue
        if pdata.get("status") == "Inactive":
            continue

        pos = pdata.get("position")
        if pos not in DEPTH_CHART_POSITIONS:
            continue

        depth_order = pdata.get("depth_chart_order")
        if depth_order is None:
            continue

        depth_by_pos[pos].append({
            "player_id": pid,
            "name": f"{pdata.get('first_name', '')} {pdata.get('last_name', '')}".strip(),
            "depth_order": depth_order,
            "is_current_player": pid == player_id,
            "jersey_number": pdata.get("number"),
            "status": pdata.get("injury_status") or pdata.get("status") or "Active",
        })

    # Sort each position group by depth order
    result = {}
    for pos in DEPTH_CHART_POSITIONS:
        group = sorted(depth_by_pos[pos], key=lambda x: x["depth_order"])
        if group:
            result[pos] = group

    return {
        "player_id": player_id,
        "team": team,
        "depth_chart": result,
    }


@app.post("/api/cache/refresh")
def refresh_cache():
    global players_cache, _ml
    players_cache = None
    _ml = None
    build_players_cache()
    return {"status": "cache refreshed", "players": len(players_cache)}