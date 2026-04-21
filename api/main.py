from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from data import load_all_data
import numpy as np
from predictor import predict
from ml_predictor import get_ml_predictor
import os
import json as jsonlib

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

players_cache = None

def get_players():
    global players_cache

    if players_cache is None:
        training_data = load_all_data(require_team=False) 
        ml = get_ml_predictor(training_data)

        active_players = load_all_data(require_team=True)  
        players_cache = []

        for player_id, player in active_players.items():
            raw_score = predict(player)
            ml_score = ml.predict(player)

            num_seasons = len(player["seasons"])

            age = player.get("age", 25) or 25

            if player.get("position") == "RB":
                last_season = max(player["seasons"].values(), key=lambda s: s.get("games_played", 0))
                is_workhorse = last_season.get("snap_percentage", 0) > 0.7 and last_season.get("ppg", 0) > 18

                if is_workhorse:
                    ml_weight = 0.2
                    rule_weight = 0.9
                elif age <= 24 or num_seasons <= 2:
                    ml_weight = 0.2
                    rule_weight = 0.8
                else:
                    ml_weight = 0.8
                    rule_weight = 0.2
            elif player.get("position") == "WR":
                last_season = sorted(player["seasons"].items())[-1][1]
                prev_seasons = sorted(player["seasons"].items())
                
                if num_seasons <= 2:
                    ml_weight = 0.1
                    rule_weight = 0.9
                elif age <= 24:
                    ml_weight = 0.2
                    rule_weight = 0.8
                else:
                    last_gp = last_season.get("games_played", 17)
                    if last_gp < 12:
                        ml_weight = 0.2
                        rule_weight = 0.8
                    else:
                        ml_weight = 0.5
                        rule_weight = 0.5
            elif player.get("position") == "QB":
                if age <=24 and num_seasons <= 2:
                    ml_weight = 0.9 # way better cuz samples for young qb are very high compared to other positions 
                    rule_weight = 0.1
                else:
                    ml_weight = 0.
                    rule_weight = 1 - ml_weight
            elif player.get("position") in ("K", "DEF"):
                ml_weight = 0.1
                rule_weight = 0.9
            else:
                ml_weight = 0.1
                rule_weight = 0.9

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
            })

        players_cache.sort(key=lambda x: x["projected_points"], reverse=True)

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

    if opponent:
        adjusted = round(base_weekly * opp_mult, 1)
    else:
        adjusted = base_weekly
        opp_mult = 1.0

    return {
        "player_id": player_id,
        "name": player["name"],
        "base_weekly_projection": base_weekly,
        "opponent": opponent,
        "opponent_multiplier": opp_mult,
        "adjusted_projection": adjusted,
    }

@app.get("/api/schedule/{team}")
def get_team_schedule(team: str):
    import json
    path = f"cache/schedule_{team.upper()}.json"
    if not os.path.exists(path):
        return {"error": "Schedule not found"}
    with open(path) as f:
        schedule = json.load(f)
    return schedule


