import numpy as np
from sklearn.linear_model import Ridge
from collections import defaultdict

POSITIONS = ["QB", "RB", "WR", "TE", "K", "DEF"]
POSITION_ENCODING = {pos: i for i, pos in enumerate(POSITIONS)}

POSITIONAL_SCARCITY = {
    "QB":  {"starters": 12, "elite_cutoff": 3,  "scarcity": 0.6},
    "RB":  {"starters": 30, "elite_cutoff": 6,  "scarcity": 1.4},
    "WR":  {"starters": 36, "elite_cutoff": 8,  "scarcity": 1.2},
    "TE":  {"starters": 12, "elite_cutoff": 3,  "scarcity": 0.9},
    "K":   {"starters": 12, "elite_cutoff": 12, "scarcity": 0.2},
    "DEF": {"starters": 12, "elite_cutoff": 12, "scarcity": 0.2},
}

POSITIONAL_ADP_ANCHORS = {
    "QB":  [(1,35),  (3,60),  (6,95),  (10,130), (12,160)],
    "RB":  [(1,5),   (4,18),  (8,35),  (15,65),  (24,100), (30,140)],
    "WR":  [(1,8),   (4,20),  (8,38),  (15,65),  (24,100), (36,150)],
    "TE":  [(1,15),  (3,55),  (6,100), (10,140), (12,170)],
    "K":   [(1,150), (6,165), (12,180)],
    "DEF": [(1,148), (6,163), (12,178)],
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


def build_features(player: dict, pos_rank: int, overall_rank: int) -> np.ndarray:
    position = player.get("position", "WR")
    age = player.get("age", 25) or 25
    years_exp = player.get("years_experience", 0) or 0
    projected = player.get("projected_points", 0) or 0
    scarcity = POSITIONAL_SCARCITY.get(position, {}).get("scarcity", 1.0)
    anchor = positional_anchor(position, pos_rank)

    seasons = player.get("seasons", {})
    season_keys = sorted(seasons.keys())
    last = seasons[season_keys[-1]] if season_keys else {}
    snap_pct = last.get("snap_percentage", 0) or 0
    target_share = last.get("target_share", 0) or 0
    games_played = last.get("games_played", 17) or 17
    injury_flag = 1.0 if games_played < 12 else 0.0

    return np.array([
        projected,
        pos_rank,
        overall_rank,
        POSITION_ENCODING.get(position, 2),
        age,
        years_exp,
        scarcity,
        anchor,                          
        snap_pct,
        target_share,
        injury_flag,
        projected * scarcity,            
        pos_rank * scarcity,             
    ])


class ADPEstimator:
    def __init__(self):
        self.model = Ridge(alpha=10.0)
        self.trained = False
        self._pos_ranks: dict = {}

    def fit(self, players_cache: list):
        X, y = [], []

        for p in players_cache:
            adp = p.get("adp")
            if adp is None or adp >= 999:
                continue
            pos_rank = p.get("projected_pos_rank", 1)
            overall_rank = p.get("projected_rank", 1)
            feats = build_features(p, pos_rank, overall_rank)
            X.append(feats)
            y.append(adp)

        if len(X) < 10:
            print(f"ADPEstimator: only {len(X)} training samples — skipping fit")
            return

        self.model.fit(np.array(X), np.array(y))
        self.trained = True
        print(f"ADPEstimator: trained on {len(X)} players ✅")

    def predict_adp(self, player: dict, pos_rank: int, overall_rank: int) -> float | None:
        if not self.trained:
            return None
        feats = build_features(player, pos_rank, overall_rank).reshape(1, -1)
        raw = self.model.predict(feats)[0]
        return round(float(np.clip(raw, 1, 220)), 1)

    def tag(self, sleeper_adp: float | None, estimated_adp: float | None) -> str | None:
        if sleeper_adp is None or estimated_adp is None:
            return None
        diff = round(sleeper_adp) - round(estimated_adp)
        if diff >= 25:
            return "sleeper"
        if diff <= -25:
            return "bust"
        return None