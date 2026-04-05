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

    