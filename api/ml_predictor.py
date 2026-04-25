import numpy as np
import lightgbm as lgb
from sklearn.model_selection import cross_val_score, KFold
import pickle
import os
import warnings
warnings.filterwarnings('ignore')

POSITIONS = ["QB", "RB", "WR", "TE", "K", "DEF"]
POSITION_ENCODING = {pos: i for i, pos in enumerate(POSITIONS)}
POSITION_PEAK_AGE = {"QB": 29, "RB": 24, "WR": 28, "TE": 28, "K": 33}

MODEL_CACHE = "cache/ml_models.pkl"

FEATURE_NAMES = [
    "ppg", "snap_pct", "games_played", "pts_ppr", "rush_yards", "rush_td",
    "rec", "rec_yards", "rec_targets", "rec_td", "pass_yards", "pass_td",
    "pass_int", "fumbles", "age", "age_sq", "years_past_peak", "years_exp",
    "pos_encoded", "career_stage", "target_spike", "target_share", "rz_target_share"
]


def target_spike_flag(seasons: dict, season_key: str) -> float:
    season_keys = sorted(seasons.keys())
    idx = season_keys.index(season_key)
    if idx == 0:
        return 0.0

    prev = seasons[season_keys[idx - 1]]
    curr = seasons[season_key]

    prev_targets = prev.get("rec_targets", 0)
    curr_targets = curr.get("rec_targets", 0)
    prev_snap = prev.get("snap_percentage", 0)
    curr_snap = curr.get("snap_percentage", 0)

    if prev_targets == 0:
        return 0.0

    target_jump = (curr_targets - prev_targets) / (prev_targets + 1e-6)
    snap_jump = (curr_snap - prev_snap) / (prev_snap + 1e-6) if prev_snap > 0 else 0

    if target_jump > 0.25 and snap_jump < target_jump * 0.5:
        return min(target_jump - snap_jump, 1.0)
    return 0.0


def build_training_data(all_players: dict):
    X, y, meta = [], [], []
    FANTASY_POSITIONS = {'QB', 'RB', 'WR', 'TE', 'K', 'DEF'}

    for pid, player in all_players.items():
        if player.get('position') not in FANTASY_POSITIONS:
            continue

        seasons = player.get("seasons", {})
        season_keys = sorted(seasons.keys())

        if len(season_keys) < 2:
            continue

        position = player.get("position", "WR")
        pos_encoded = POSITION_ENCODING.get(position, 2)
        age = player.get("age", 25) or 25
        years_exp = player.get("years_experience", 0) or 0
        latest_year = 2025

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

            age_at_season = age - (latest_year - int(current_key))

            features = [
                current.get("ppg", 0),
                current.get("snap_percentage", 0),
                gp / 17,
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
                age_at_season,
                age_at_season ** 2,
                max(0, age_at_season - POSITION_PEAK_AGE.get(position, 28)),
                years_exp,
                pos_encoded,
                i / max(len(season_keys) - 1, 1),
                target_spike_flag(seasons, current_key),
                current.get("target_share", 0),
                current.get("rz_target_share", 0),
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
        age ** 2,
        max(0, age - POSITION_PEAK_AGE.get(position, 28)),
        years_exp,
        pos_encoded,
        min(len(season_keys) / 6, 1.0),
        target_spike_flag(seasons, last_key),
        last.get("target_share", 0),
        last.get("rz_target_share", 0),
    ]

    return np.array(features).reshape(1, -1)


class NFLPredictor:
    def __init__(self):
        self.models = {}
        self.trained = False

    def train(self, all_players: dict, evaluate: bool = False):
        X, y, meta = build_training_data(all_players)
        if len(X) == 0:
            print("No training data!")
            return

        pos_col = FEATURE_NAMES.index("pos_encoded")

        for position in POSITIONS:
            pos_encoded = POSITION_ENCODING[position]
            mask = X[:, pos_col] == pos_encoded
            X_pos, y_pos = X[mask], y[mask]

            if len(X_pos) < 10:
                print(f"{position}: not enough data ({len(X_pos)} samples), skipping")
                continue

            model = lgb.LGBMRegressor(
                n_estimators=300,
                learning_rate=0.05,
                num_leaves=15,
                min_child_samples=3,
                subsample=0.8,
                colsample_bytree=0.8,
                reg_alpha=0.1,
                reg_lambda=1.0,
                random_state=42,
                verbose=-1,
            )
            model.fit(X_pos, y_pos)
            self.models[position] = model

            if evaluate and len(X_pos) >= 5:
                cv = min(5, len(X_pos))
                kf = KFold(n_splits=cv, shuffle=True, random_state=42)
                scores = cross_val_score(model, X_pos, y_pos, cv=kf, scoring='r2')
                print(f"{position}: {len(X_pos)} samples | Mean R²: {scores.mean():.3f} (+/- {scores.std():.3f})")
            else:
                print(f"{position}: {len(X_pos)} samples | trained ✅")

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

        ppg_pred = self.models[position].predict(features)[0]

        seasons = player.get("seasons", {})
        season_keys = sorted(seasons.keys())
        last_season = seasons[season_keys[-1]] if season_keys else {}
        last_gp = last_season.get("games_played", 17)
        last_snap = last_season.get("snap_percentage", 0)

        if last_gp < 14 and last_snap > 0.6:
            projected_games = 16
        else:
            projected_games = min(17, max(last_gp, 14))

        return round(max(ppg_pred * projected_games, 0), 1)


def get_ml_predictor(all_players: dict, force_retrain: bool = False, evaluate: bool = False) -> NFLPredictor:
    global _predictor

    if _predictor is not None and not force_retrain:
        return _predictor

    if not force_retrain and os.path.exists(MODEL_CACHE):
        print("Loading ML models from disk...")
        with open(MODEL_CACHE, "rb") as f:
            _predictor = pickle.load(f)
        print("Models loaded from disk")
        return _predictor

    print("Training ML models...")
    _predictor = NFLPredictor()
    _predictor.train(all_players, evaluate=evaluate)

    os.makedirs("cache", exist_ok=True)
    with open(MODEL_CACHE, "wb") as f:
        pickle.dump(_predictor, f)
    print("Models saved to disk")

    return _predictor


_predictor = None