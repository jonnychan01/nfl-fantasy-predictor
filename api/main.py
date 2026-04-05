from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from data import load_all_data
from predictor import predict

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
        players_cache = []
        raw = load_all_data()

        for player_id, player in raw.items():
            players_cache.append({
                "player_id": player_id,
                "name": player["name"],
                "position": player["position"],
                "team": player["team"],
                "age": player["age"],
                "years_experience": player["years_experience"],
                "projected_points": predict(player),
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


    