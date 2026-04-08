from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from data import load_all_data
import numpy as np
from predictor import confidence_blend, predict
from ml_predictor import get_ml_predictor

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
        raw = load_all_data()
        ml = get_ml_predictor(raw)
        players_cache = []

        for player_id, player in raw.items():
            if not player.get("team"):
                continue

            raw_score = predict(player)
            ml_score = ml.predict(player)


            num_seasons = len(player["seasons"])

            age = player.get("age", 25) or 25

            if player.get("position") == "RB":
                if age <= 24 or num_seasons <= 2:
                    ml_weight = 0.2  
                    rule_weight = 0.8
                else:
                    ml_weight = 0.8
                    rule_weight = 0.2
            elif player.get("position") == "WR":
                if age <= 24 or num_seasons <= 2:
                    ml_weight = 0.2  
                    rule_weight = 0.8
                else:
                    ml_weight = 0.8
                    rule_weight = 0.2
            elif player.get("position") == "QB":
                if age <=24 or num_seasons <= 2:
                    ml_weight = 0.9 # way better cuz samples for young qb are very high compared to other positions 
                    rule_weight = 0.1
                else:
                    ml_weight = 0.1
                    rule_weight = 1 - ml_weight
            elif player.get("position") in ("K", "DEF", "TE"):
                ml_weight = 0.1
                rule_weight = 0.9
            else:
                ml_weight = 0.3
                rule_weight = 0.7

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

        for position in ["QB", "RB", "WR", "TE", "K", "DEF"]:
            pos_players = [p for p in players_cache if p["position"] == position]

            if not pos_players:
                continue
            top_scores = sorted([p["projected_points"] for p in pos_players], reverse=True)[:20]
            pos_avg = round(np.mean(top_scores), 1)

            for p in pos_players:
                if p["projected_points"] < 60:
                    continue
                if p["age"] and p["age"] <= 24 and p["num_seasons"] <= 2:
                    continue  # don't blend young breakout players
                p["projected_points"] = confidence_blend(
                    p["projected_points"],
                    pos_avg,
                    p["num_seasons"]
                )

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


    