import requests
import os
import json
import time

CACHE_DIR = 'cache'
SEASONS = ['2020', '2021', '2022', '2023', '2024', '2025']
ESPN_TEAMS = {
    "1": "ATL", "2": "BUF", "3": "CHI", "4": "CIN", "5": "CLE",
    "6": "DAL", "7": "DEN", "8": "DET", "9": "GB", "10": "TEN",
    "11": "IND", "12": "KC", "13": "LV", "14": "LAR", "15": "MIA",
    "16": "MIN", "17": "NE", "18": "NO", "19": "NYG", "20": "NYJ",
    "21": "PHI", "22": "ARI", "23": "PIT", "24": "LAC", "25": "SF",
    "26": "SEA", "27": "TB", "28": "WAS", "29": "CAR", "30": "JAX",
    "33": "BAL", "34": "HOU"
}

ABBR_MAP = {"WSH": "WAS", "LA": "LAR"}

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


def fetch_team_schedule(espn_id: str, team_abbr: str):
    path = os.path.join(CACHE_DIR, f"schedule_{team_abbr}.json")
    if os.path.exists(path):
        print(f"  [cache hit] schedule_{team_abbr}.json")
        return

    print(f"  [fetching] schedule for {team_abbr}")
    r = requests.get(
        f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{espn_id}/schedule?season=2025",
        timeout=30
    )
    r.raise_for_status()
    data = r.json()

    schedule = []
    for event in data.get("events", []):
        try:
            if event.get("seasonType", {}).get("type") != 2:
                continue
            week = event["week"]["number"]
            competitors = event["competitions"][0]["competitors"]
            home = next(c for c in competitors if c["homeAway"] == "home")
            away = next(c for c in competitors if c["homeAway"] == "away")
            home_abbr = home["team"]["abbreviation"]
            away_abbr = away["team"]["abbreviation"]

            is_home = home_abbr == team_abbr
            opponent = away_abbr if is_home else home_abbr
            opponent = ABBR_MAP.get(opponent, opponent)

            schedule.append({
                "week": week,
                "opponent": opponent,
                "home": is_home,
            })
        except (KeyError, StopIteration):
            continue

    with open(path, "w") as f:
        json.dump(schedule, f)
    time.sleep(0.3)

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

    for espn_id, abbr in ESPN_TEAMS.items():
        fetch_team_schedule(espn_id, abbr)
    print("Done!")