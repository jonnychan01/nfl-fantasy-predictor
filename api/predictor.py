import numpy as np

AGE_PEAK = {"QB": 32, "RB": 25, "WR": 28, "TE": 28, "K": 33}
AGE_DECLINE_RATE = {"QB": 0.025, "RB": 0.03, "WR": 0.035, "TE": 0.03, "K": 0.02}
RECENT_SEASONS = ["2023", "2024", "2025"]


def age_multiplier(age: int, position: str) -> float:
    if age is None:
        return 1.0
    
    peak_age = AGE_PEAK.get(position, 28)
    decline_rate = AGE_DECLINE_RATE.get(position, 0.035)
    years_past_peak = max(0, age - peak_age)

    return round((1 - decline_rate) ** years_past_peak, 4)


def calc_trend(ppg_values: list) -> float:
    if len(ppg_values) < 2:
        return 0.0
    
    ppg_array = np.array(ppg_values)
    x = np.arange(len(ppg_array))

    coeffs = np.polyfit(x, ppg_array, 1)
    slope = coeffs[0]

    y_hat = np.polyval(coeffs, x)
    ss_res = np.sum((ppg_array - y_hat) ** 2)
    ss_tot = np.sum((ppg_array - np.mean(ppg_array)) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

    return round(slope * r_squared, 4)

def injury_severity(season_data:dict) -> float:

    games_played = season_data.get("games_played", 0)
    snap_pct = season_data.get("snap_percentage", 0)

    games_severity = max(0, (17 - games_played) / 17)

    snap_severity = max(0, (0.4 - snap_pct) / 0.4) if snap_pct < 0.4 else 0.0

    return round(min(games_severity * 0.7 + snap_severity * 0.3, 1.0), 3)

def recovery_factor(seasons: dict, season_key: str) -> float:
    season_keys= sorted(seasons.keys())
    idx = season_keys.index(season_key)

    if idx == 0 or idx >= len(season_keys) - 1:
        return 0.85
    
    pre_injury = seasons[season_keys[idx - 1]]
    post_injury = seasons[season_keys[idx + 1]]
 
    pre_ppg = pre_injury.get("ppg", 0)
    post_ppg = post_injury.get("ppg", 0)
    pre_snap = pre_injury.get("snap_percentage", 0)
    post_snap = post_injury.get("snap_percentage", 0)
 
    if pre_ppg == 0:
        return 0.85
 
    ppg_recovery = min(post_ppg / pre_ppg, 1.0)
    snap_recovery = min(post_snap / pre_snap, 1.0) if pre_snap > 0 else 1.0
 
    combined = ppg_recovery * 0.6 + snap_recovery * 0.4
 
    if combined >= 0.85:
        return 1.0   
    elif combined >= 0.60:
        return 0.75  
    else:
        return 0.55  #
    


def infer_projected_snap(seasons: dict) -> float:
    season_keys = sorted(seasons.keys(), reverse=True)
 
    for key in season_keys:
        season = seasons[key]
        severity = injury_severity(season)
        if severity < 0.3:  # Reasonably healthy season
            return season.get("snap_percentage", 0)
 
    all_snaps = [s.get("snap_percentage", 0) for s in seasons.values() if s.get("snap_percentage", 0) > 0]
    return round(np.mean(all_snaps), 3) if all_snaps else 0.3
 
 
def last_season_injury_mult(seasons: dict) -> float:
    season_keys = sorted(seasons.keys())
    last = seasons[season_keys[-1]]
 
    severity = injury_severity(last)
    if severity == 0:
        return 1.0
 
    base_mult = round(1.0 - (severity * 0.28), 3)
 
    projected_snap = infer_projected_snap(seasons)
    role_confidence = min(projected_snap / 0.8, 1.0)
 
    return round(base_mult + (1.0 - base_mult) * role_confidence, 3)


def weighted_ppg(seasons: dict) -> float:
    season_keys = sorted(seasons.keys())
    if not season_keys:
        return 0.0
 
    values, weights = [], []
    for key in season_keys:
        season = seasons[key]
        ppg = season.get("ppg", 0)
        games_played = season.get("games_played", 0)
 
        if ppg == 0:
            continue
 
        severity = injury_severity(season)
 
        if key == season_keys[-1]:
            weight = 3
        elif key in RECENT_SEASONS:
            weight = 2
        else:
            weight = 1
 
        if severity > 0:
            rf = recovery_factor(seasons, key)
            weight *= (1 - severity * 0.7) * rf
 
        games_played_weight = min(games_played / 17, 1.0)
        values.append(ppg)
        weights.append(weight * games_played_weight)
 
    if not values:
        return 0.0
 
    return round(np.average(values, weights=weights), 3)
 


def role_stability(snap_percentages: dict, position: str) -> float:
    if position in ("K", "DEF"):
        return 1.0
    
    if not snap_percentages or all(v == 0 for v in snap_percentages.values()):
        return 0.3
    
    values = list(snap_percentages.values())
    mean = np.mean(values)
    std = np.std(values)

    return round(1 - (std / (mean + 1e-6)), 3)


def predict_kicker(player: dict) -> float:
    seasons = player.get("seasons", {})
    if not seasons:
        return 0.0
    
    base_ppg = weighted_ppg(seasons)
    age_mult = age_multiplier(player.get("age"), player.get("position"))
    score = base_ppg * 17 * age_mult

    return round(max(score, 0), 1)


def predict_def(player: dict) -> float:
    seasons = player.get("seasons", {})
    if not seasons:
        return 0.0
    
    base_ppg = weighted_ppg(seasons)
    ppg_values = [seasons[k]["ppg"] for k in sorted(seasons.keys())]
    trend = calc_trend(ppg_values)
    score = (base_ppg * 17) + (trend * 17 * 0.5)

    return round(max(score, 0), 1)


def predict_skill(player: dict) -> float:
    seasons = player.get("seasons", {})
    if not seasons:
        return 0.0
 
    base_ppg = weighted_ppg(seasons)
    baseline = base_ppg * 17
 
    ppg_values = [seasons[k]["ppg"] for k in sorted(seasons.keys()) if seasons[k].get("ppg", 0) > 0]
    trend = calc_trend(ppg_values)
    trend_adjustment = trend * 17
 
    snap_percentages = {k: seasons[k].get("snap_percentage", 0) for k in seasons}
    stability = role_stability(snap_percentages, player.get("position"))
 
    age_mult = age_multiplier(player.get("age"), player.get("position"))
    injury_mult = last_season_injury_mult(seasons)
 
    score = (baseline + trend_adjustment) * stability * age_mult * injury_mult
    return round(max(score, 0), 1)


def predict(player: dict) -> float:
    position = player.get("position")
    if position == "K":
        return predict_kicker(player)
    elif position == "DEF":
        return predict_def(player)
    else:
        return predict_skill(player)