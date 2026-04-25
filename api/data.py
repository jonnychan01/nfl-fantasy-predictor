import json
import os
from concurrent.futures import ThreadPoolExecutor

CACHE_DIR = 'cache'
SEASONS = ['2020', '2021', '2022', '2023', '2024', '2025']
POSITIONS = ['QB', 'RB', 'WR', 'TE', 'K', 'DEF']


def loaded_players(require_team=False) -> dict:
    with open(os.path.join(CACHE_DIR, 'players.json'), 'r') as f:
        raw_data = json.load(f)

    players = {}
    for player_id, player in raw_data.items():
        if player.get('position') not in POSITIONS:
            continue
        if require_team and not player.get('team'):
            continue
        if not player.get('full_name') and player.get('position') != 'DEF':
            continue

        if player.get('position') == 'DEF':
            full_name = f"{player.get('first_name', '')} {player.get('last_name', '')}".strip()
        else:
            full_name = player.get('full_name')
        if not full_name:
            continue

        players[player_id] = {
            'player_id': player_id,
            'name': full_name,
            'position': player.get('position'),
            'team': player.get('team'),
            'age': player.get('age'),
            'years_experience': player.get('years_exp', 0),
        }
    return players


def load_season_file(season: str) -> tuple[dict, dict]:
    """Read a single stats file and return (player_stats, team_stats) in one pass."""
    path = os.path.join(CACHE_DIR, f"stats_{season}.json")
    with open(path, 'r') as f:
        raw = json.load(f)

    player_stats = {}
    team_stats = {}

    for key, stat in raw.items():
        if key.startswith("TEAM_"):
            team = key.replace("TEAM_", "")
            team_stats[team] = {
                "team_rec_tgt": stat.get("rec_tgt", 0),
                "team_rz_tgt": stat.get("rec_rz_tgt", 0),
                "team_pass_att": stat.get("pass_att", 0),
            }
        else:
            games_played = stat.get('gp', 0) or 0
            if games_played == 0:
                continue
            offensive_snaps = stat.get('off_snp', 0) or 0
            team_snaps = stat.get('tm_off_snp', 1) or 1
            player_stats[key] = {
                "pts_ppr": stat.get('pts_ppr', 0) or 0,
                "pts_half_ppr": stat.get('pts_half_ppr', 0) or 0,
                "games_played": games_played,
                "ppg": round((stat.get('pts_ppr', 0) or 0) / games_played, 2),
                "snap_percentage": round(offensive_snaps / team_snaps, 3) if team_snaps > 0 else 0,
                "rush_yards": stat.get('rush_yd', 0) or 0,
                "rush_touchdowns": stat.get('rush_td', 0) or 0,
                "rec": stat.get('rec', 0) or 0,
                "rec_yards": stat.get('rec_yd', 0) or 0,
                "rec_targets": stat.get('rec_tgt', 0) or 0,
                "rec_touchdowns": stat.get('rec_td', 0) or 0,
                "pass_yards": stat.get('pass_yd', 0) or 0,
                "pass_touchdowns": stat.get('pass_td', 0) or 0,
                "pass_interceptions": stat.get('pass_int', 0) or 0,
                "fumbles": stat.get('fum_lost', 0) or 0,
                "rec_rz_tgt": stat.get('rec_rz_tgt', 0) or 0,
            }

    return player_stats, team_stats


def load_all_data(require_team=False) -> dict:
    players = loaded_players(require_team=require_team)

    with ThreadPoolExecutor() as executor:
        results = list(executor.map(load_season_file, SEASONS))

    all_season_stats = {season: r[0] for season, r in zip(SEASONS, results)}
    all_team_stats   = {season: r[1] for season, r in zip(SEASONS, results)}

    for player_id, player in players.items():
        player['seasons'] = {}
        first_season = None
        for season in SEASONS:
            if player_id in all_season_stats[season]:
                first_season = season
                break

        for season in SEASONS:
            stats = all_season_stats[season]
            if player_id in stats:
                team = player.get("team")
                team_data = all_team_stats[season].get(team, {})
                season_data = stats[player_id].copy()

                team_tgt = team_data.get("team_rec_tgt", 0)
                player_tgt = season_data.get("rec_targets", 0)
                season_data["target_share"] = round(player_tgt / team_tgt, 3) if team_tgt > 0 else 0

                team_rz = team_data.get("team_rz_tgt", 0)
                player_rz = season_data.get("rec_rz_tgt", 0)
                season_data["rz_target_share"] = round(player_rz / team_rz, 3) if team_rz > 0 else 0

                player['seasons'][season] = season_data
            elif first_season and season > first_season:
                player['seasons'][season] = {
                    "games_played": 0, "ppg": 0, "snap_percentage": 0,
                    "target_share": 0, "rz_target_share": 0
                }

    return {pid: p for pid, p in players.items() if p["seasons"]}