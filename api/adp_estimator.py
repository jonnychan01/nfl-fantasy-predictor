import numpy as np
import json
import os
import lightgbm as lgb

POSITIONS = ["QB", "RB", "WR", "TE", "K", "DEF"]
POSITION_ENCODING = {pos: i for i, pos in enumerate(POSITIONS)}

POSITIONAL_ADP_ANCHORS = {
    "QB":  [(1,35),  (3,60),  (6,95),  (10,130), (12,160)],
    "RB":  [(1,5),   (4,18),  (8,35),  (15,65),  (24,100), (30,140)],
    "WR":  [(1,8),   (4,20),  (8,38),  (15,65),  (24,100), (36,150)],
    "TE":  [(1,15),  (3,55),  (6,100), (10,140), (12,170)],
    "K":   [(1,150), (6,165), (12,180)],
    "DEF": [(1,148), (6,163), (12,178)],
}

POSITIONAL_SCARCITY = {
    "QB": 0.6, "RB": 1.4, "WR": 1.2,
    "TE": 0.9, "K":  0.2, "DEF": 0.2,
}


def positional_anchor(position: str, pos_rank: int) -> float:
    anchors = POSITIONAL_ADP_ANCHORS.get(position, [(1, 100)])
    if pos_rank <= anchors[0][0]:
        return float(anchors[0][1])
    if pos_rank >= anchors[-1][0]:
        return float(anchors[-1][1])
    for i in range(len(anchors) - 1):
        r1, a1 = anchors[i]
        r2, a2 = anchors[i + 1]
        if r1 <= pos_rank <= r2:
            t = (pos_rank - r1) / (r2 - r1)
            return a1 + t * (a2 - a1)
    return float(anchors[-1][1])


def build_features(pts_ppr: float, position: str, pos_rank: int,
                   overall_rank: int, age: float = 25) -> np.ndarray:
    scarcity = POSITIONAL_SCARCITY.get(position, 1.0)
    anchor = positional_anchor(position, pos_rank)
    return np.array([
        pts_ppr,
        pos_rank,
        overall_rank,
        POSITION_ENCODING.get(position, 2),
        age,
        scarcity,
        anchor,
        pts_ppr * scarcity,       
        pos_rank * scarcity,      
        pts_ppr / (pos_rank + 1), 
    ])

FEATURE_NAMES = [
    "pts_ppr", "pos_rank", "overall_rank", "pos_encoded",
    "age", "scarcity", "anchor", "pts_x_scarcity",
    "rank_x_scarcity", "pts_per_rank",
]


class ADPEstimator:
    def __init__(self):
        self.models = {}
        self.trained = False

    def fit(self, players_cache: list):
        hist_path = "cache/historical_adp.json"
        players_path = "cache/players.json"

        if not os.path.exists(hist_path) or not os.path.exists(players_path):
            print("ADPEstimator: missing historical data, using anchor fallback")
            return

        with open(hist_path) as f:
            hist = json.load(f)
        with open(players_path) as f:
            players_meta = json.load(f)

        year_pos_entries: dict = {}
        for pid, years in hist.items():
            meta = players_meta.get(pid, {})
            pos = meta.get("position") or (meta.get("fantasy_positions") or [None])[0]
            if pos not in POSITIONS:
                continue
            years_exp = meta.get("years_exp", 2) or 2
            age = 22 + years_exp

            for year, d in years.items():
                pts = d.get("pts_ppr")
                adp = d.get("adp")
                if not pts or not adp or adp >= 400:
                    continue
                key = (year, pos)
                if key not in year_pos_entries:
                    year_pos_entries[key] = []
                year_pos_entries[key].append((pid, pts, adp, age))

        X_by_pos = {p: [] for p in POSITIONS}
        y_by_pos = {p: [] for p in POSITIONS}

        for (year, pos), entries in year_pos_entries.items():
            entries.sort(key=lambda x: x[1], reverse=True)
            for pos_rank, (pid, pts, adp, age) in enumerate(entries, 1):
                feats = build_features(pts, pos, pos_rank, pos_rank, age)
                X_by_pos[pos].append(feats)
                y_by_pos[pos].append(adp)

        for pos in POSITIONS:
            X = np.array(X_by_pos[pos])
            y = np.array(y_by_pos[pos])

            if len(X) < 10:
                print(f"ADPEstimator {pos}: only {len(X)} samples, skipping")
                continue

            model = lgb.LGBMRegressor(
                n_estimators=200,
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
            model.fit(X, y, feature_name=FEATURE_NAMES)
            self.models[pos] = model
            print(f"ADPEstimator {pos}: trained on {len(X)} samples ✅")

        self.trained = len(self.models) > 0

    def predict_adp(self, player: dict, pos_rank: int, overall_rank: int) -> float | None:
        position = player.get("position", "WR")
        pts = player.get("projected_points", 0) or 0
        age = player.get("age", 25) or 25
        anchor = positional_anchor(position, pos_rank)

        if not self.trained or position not in self.models:
            scarcity = POSITIONAL_SCARCITY.get(position, 1.0)
            nudge = (overall_rank - pos_rank) * (1 - scarcity) * 0.3
            return round(float(np.clip(anchor + nudge, 1, 220)), 1)

        feats = build_features(pts, position, pos_rank, overall_rank, age).reshape(1, -1)
        raw = self.models[position].predict(feats)[0]

        blended = raw * 0.7 + anchor * 0.3
        return round(float(np.clip(blended, 1, 220)), 1)

    def tag(self, sleeper_adp: float | None, estimated_adp: float | None) -> str | None:
        if sleeper_adp is None or estimated_adp is None:
            return None
        diff = round(sleeper_adp) - round(estimated_adp)
        if diff >= 25:
            return "sleeper"
        if diff <= -25:
            return "bust"
        return None