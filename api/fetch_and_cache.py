import requests
import os
import json
import time

CACHE_DIR = 'cache'
SEASONS = ['2020', '2021', '2022', '2023', '2024', '2025']

os.makedirs(CACHE_DIR, exist_ok=True)

def fetch_and_cache_data(url, filename):
    path = os.path.join(CACHE_DIR, filename)

    if os.path.exists(path):
        print(f" [CACHE HIT] {filename}")
        return
    print(f" [FETCHING] {filename} from {url}")
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    with open(path, 'w') as f:
        json.dump(r.json(), f)
    time.sleep(1)  # API rate limit

if __name__ == "__main__":
    # Fetch all NFL players
    print("Fetching player list...")
    fetch_and_cache_data(
        "https://api.sleeper.app/v1/players/nfl",
        "players.json"
    )

    # Season stats
    for season in SEASONS:
        print(f"Fetching season stats for {season}...")
        fetch_and_cache_data(
            f"https://api.sleeper.app/v1/stats/nfl/regular/{season}",
            f"stats_{season}.json"
        )
