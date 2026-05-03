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

def fetch_historical_adp():
    all_adp = {}
    positions = ["QB", "RB", "WR", "TE", "K", "DEF"]
    years = ["2021", "2022", "2023", "2024", "2025"]

    for year in years:
        print(f"Fetching ADP for {year}...")
        pos_params = "&".join([f"position[]={p}" for p in positions])
        url = f"https://api.sleeper.com/projections/nfl/{year}?season_type=regular&{pos_params}"
        path = os.path.join(CACHE_DIR, f"adp_{year}.json")

        if os.path.exists(path):
            print(f"  [cache hit] adp_{year}.json")
            with open(path) as f:
                year_data = json.load(f)
        else:
            print(f"  [fetching] adp_{year}.json")
            try:
                r = requests.get(url, timeout=30)
                r.raise_for_status()
                year_data = r.json()
                with open(path, "w") as f:
                    json.dump(year_data, f)
                time.sleep(1)
            except Exception as e:
                print(f"  {year} failed: {e}")
                continue

        count = 0
        for entry in year_data:
            pid = entry.get("player_id")
            adp = entry.get("stats", {}).get("adp_ppr")
            pts = entry.get("stats", {}).get("pts_ppr")
            if pid and adp and adp < 400:
                if pid not in all_adp:
                    all_adp[pid] = {}
                all_adp[pid][year] = {
                    "adp": round(adp, 1),
                    "pts_ppr": round(pts, 1) if pts else None,
                }
                count += 1
        print(f"  {year}: {count} players")

    out_path = os.path.join(CACHE_DIR, "historical_adp.json")
    with open(out_path, "w") as f:
        json.dump(all_adp, f)
    print(f"Saved {len(all_adp)} players to historical_adp.json")
    return all_adp

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

    print("Fetching historical ADP...")
    fetch_historical_adp()

    for espn_id, abbr in ESPN_TEAMS.items():
        fetch_team_schedule(espn_id, abbr)
    print("Done!")