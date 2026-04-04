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
        if not player.get('full_name'): 
            continue

        players[player_id] = {
            'player_id': player_id,
            'name': player.get['full_name'],
            'position': player.get('position'),
            'team': player.get('team'),
            'age': player.get('age'),
            'experience': player.get('experience', 0),
        }
    return players


            