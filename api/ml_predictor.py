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


def build_prediction_features(player: dict) -> np.ndarray:
    seasons = player.get("seasons", {})
    season_keys = sorted(seasons.keys())

    if not season_keys:
        return None

    last_key = season_keys[-1]
    last = seasons[last_key]

    position = player.get("position", "WR")
    pos_encoded = POSITION_ENCODING.get(position, 2)
    age = player.get("age", 25) or 25
    years_exp = player.get("years_experience", 0) or 0
    career_prog = min(len(season_keys) / 6, 1.0)

    features = [
        last.get("ppg", 0),
        last.get("snap_percentage", 0),
        last.get("games_played", 0) / 17,
        last.get("pts_ppr", 0) / 17,
        last.get("rush_yards", 0) / 17,
        last.get("rush_touchdowns", 0) / 17,
        last.get("rec", 0) / 17,
        last.get("rec_yards", 0) / 17,
        last.get("rec_targets", 0) / 17,
        last.get("rec_touchdowns", 0) / 17,
        last.get("pass_yards", 0) / 17,
        last.get("pass_touchdowns", 0) / 17,
        last.get("pass_interceptions", 0) / 17,
        last.get("fumbles", 0) / 17,
        age,
        years_exp,
        pos_encoded,
        career_prog,
    ]

    return np.array(features).reshape(1, -1)


class NFLPredictor:
    def __init__(self):
        self.models = {}   
        self.scalers = {}  
        self.trained = False

    def train(self, all_players: dict):
        X, y, meta = build_training_data(all_players)
        if len(X) == 0:
            print("No training data!")
            return

        for position in POSITIONS:
            pos_encoded = POSITION_ENCODING[position]
            mask = X[:, 16] == pos_encoded
            X_pos = X[mask]
            y_pos = y[mask]

            if len(X_pos) < 10:
                print(f"{position}: not enough data ({len(X_pos)} samples), skipping")
                continue

            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X_pos)
            model = Ridge(alpha=1.0)
            model.fit(X_scaled, y_pos)

            self.scalers[position] = scaler
            self.models[position] = model

            if len(X_pos) >= 5:
                cv = min(5, len(X_pos))
                scores = cross_val_score(model, X_scaled, y_pos, cv=cv, scoring='r2')
                print(f"{position}: {len(X_pos)} samples | Mean R²: {scores.mean():.3f} (+/- {scores.std():.3f})")

        self.trained = True

    def predict(self, player: dict) -> float:
        if not self.trained:
            return 0.0

        position = player.get("position", "WR")
        if position not in self.models:
            return 0.0

        features = build_prediction_features(player)
        if features is None:
            return 0.0

        features_scaled = self.scalers[position].transform(features)
        ppg_pred = self.models[position].predict(features_scaled)[0]

        seasons = player.get("seasons", {})
        season_keys = sorted(seasons.keys())
        last_gp = seasons[season_keys[-1]].get("games_played", 17) if season_keys else 17
        projected_games = min(17, max(last_gp, 14))

        return round(max(ppg_pred * projected_games, 0), 1)


_predictor = None

def get_ml_predictor(all_players: dict) -> NFLPredictor:
    global _predictor
    if _predictor is None:
        _predictor = NFLPredictor()
        _predictor.train(all_players)
    return _predictor