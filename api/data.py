import json
import os

CACHE_DIR = 'cache'
SEASONS = ['2020', '2021', '2022', '2023', '2024', '2025']
POSITIONS = ['QB', 'RB', 'WR', 'TE', 'K', 'DEF']

def loaded_players() -> dict:
    with open(os.path.join(CACHE_DIR, 'players.json'), 'r') as f:
        raw_data = json.load(f)

    players = {}
    for player_id, player in raw_data.items():
        if player.get('position') not in POSITIONS:
            continue
        if not player.get('team'):
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

def loaded_stats(season:int) -> dict:
    path = os.path.join(CACHE_DIR, f"stats_{season}.json")
    with open(path, 'r') as f:
        raw_data = json.load(f)

    stats = {}
    for player_id, stat in raw_data.items():
        games_played = stat.get('gp', 0) or 0
        if games_played == 0:
            continue
        offensive_snaps = stat.get('off_snp', 0) or 0
        team_snaps = stat.get('tm_off_snp', 1) or 1
        stats[player_id] = {
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
        }
    return stats
         

def load_all_data() -> dict:
    players = loaded_players()
    all_season_stats = {season: loaded_stats(season) for season in SEASONS}
    
    for player_id, player in players.items():
        player['seasons'] = {}
        for season, stats in all_season_stats.items():
            if player_id in stats:
                player['seasons'][season] = stats[player_id]
    
    return {pid: p for pid, p in players.items() if p["seasons"]}
   
   

            