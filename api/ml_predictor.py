import numpy as np
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
import warnings
warnings.filterwarnings('ignore')

POSITIONS = ["QB", "RB", "WR", "TE", "K", "DEF"]
POSITION_ENCODING = {pos: i for i, pos in enumerate(POSITIONS)}

def build_training_data(all_players: dict):
    X, y, meta = [], [], []

    for pid, player in all_players.items():
        seasons = player.get("seasons", {})
        season_keys = sorted(seasons.keys())

        if len(season_keys) < 2:
            continue

        position = player.get("position", "WR")
        pos_encoded = POSITION_ENCODING.get(position, 2)

        for i in range(len(season_keys) - 1):
            current_key = season_keys[i]
            next_key = season_keys[i + 1]

            current = seasons[current_key]
            next_season = seasons[next_key]

            gp = current.get("games_played", 0)
            if gp == 0:
                continue

            next_ppg = next_season.get("ppg", 0)
            if next_ppg == 0:
                continue

            age = player.get("age", 25) or 25
            years_exp = player.get("years_experience", 0) or 0
            
            current_year = int(current_key)
            latest_year = 2025
            age_at_season = age - (latest_year - current_year)

            features = [
                current.get("ppg", 0),
                current.get("snap_percentage", 0),
                current.get("games_played", 0) / 17,
                current.get("pts_ppr", 0) / 17,
                current.get("rush_yards", 0) / 17,
                current.get("rush_touchdowns", 0) / 17,
                current.get("rec", 0) / 17,
                current.get("rec_yards", 0) / 17,
                current.get("rec_targets", 0) / 17,
                current.get("rec_touchdowns", 0) / 17,
                current.get("pass_yards", 0) / 17,
                current.get("pass_touchdowns", 0) / 17,
                current.get("pass_interceptions", 0) / 17,
                current.get("fumbles", 0) / 17,
                max(0, age_at_season),
                years_exp,
                pos_encoded,
                i / max(len(season_keys) - 1, 1),  
            ]

            X.append(features)
            y.append(next_ppg)
            meta.append({
                "name": player.get("name"),
                "position": position,
                "season": current_key,
                "predicting": next_key,
            })

    return np.array(X), np.array(y), meta


