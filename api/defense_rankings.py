DEFENSE_RANKINGS = {
    "SF":  17.2,
    "BAL": 18.1,
    "BUF": 18.4,
    "PHI": 18.9,
    "KC":  19.2,
    "MIN": 19.8,
    "DET": 20.1,
    "GB":  20.4,
    "PIT": 20.7,
    "LAC": 21.0,
    "HOU": 21.3,
    "WAS": 21.6,
    "CLE": 21.9,
    "SEA": 22.1,
    "DAL": 22.4,
    "MIA": 22.7,
    "TB":  23.0,
    "ATL": 23.2,
    "LAR": 23.5,
    "DEN": 23.8,
    "IND": 24.0,
    "CIN": 24.3,
    "NYJ": 24.6,
    "LV":  24.9,
    "JAX": 25.2,
    "NE":  25.5,
    "NYG": 25.8,
    "ARI": 26.1,
    "CHI": 26.4,
    "NO":  26.7,
    "CAR": 27.0,
    "TEN": 27.3,
}

LEAGUE_AVG = sum(DEFENSE_RANKINGS.values()) / len(DEFENSE_RANKINGS)

def opponent_multiplier(opponent_team: str) -> float:
    pts_allowed = DEFENSE_RANKINGS.get(opponent_team, LEAGUE_AVG)

    return round(pts_allowed / LEAGUE_AVG, 3)