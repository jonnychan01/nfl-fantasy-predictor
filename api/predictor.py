import numpy as np

AGE_PEAK = {"QB": 32, "RB": 24, "WR": 28, "TE": 28, "K": 33}
AGE_DECLINE_RATE = {"QB": 0.025, "RB": 0.055, "WR": 0.035, "TE": 0.03, "K": 0.02}

RECENT_SEASONS = [2023, 2024, 2025]

def age_multiplier(age:int, position:str) -> float:
    if age is None:
        return 1.0
    
    peak_age = AGE_PEAK.get(position, 28)
    decline_rate = AGE_DECLINE_RATE.get(position, 0.035)
    years_past_peak = max(0, age - peak_age)
    return round((1 - decline_rate) ** years_past_peak, 4)

def calc_trend(ppg_values:list) -> float:
    if len(ppg_values) < 2:
        return 0.0
    
    x = np.arange(len(ppg_values))
    coeffs = np.polyfit(x, ppg_values, 1)
    slope = coeffs[0]

    y_hat = np.polyval(coeffs, x)
    ss_res = np.sum((ppg_values - y_hat) ** 2)
    ss_tot = np.sum((ppg_values - np.mean(ppg_values)) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

    return round(slope * r_squared, 4)

def weighted_ppg(seasons:dict) -> float:
    season_keys = sorted(seasons.keys())
    if not season_keys:
        return 0.0
    
    values, weights = [], []
    for key in season_keys:
        ppg = seasons[key].get('ppg', 0)
        games_played = seasons[key].get('games_played', 0)
        if ppg == 0:
            continue

        if key == season_keys[-1]:  
            weight = 3
        elif key in RECENT_SEASONS:
            weight = 2
        else:
            weight = 1

        games_played_weight = min(games_played / 17, 1.0)
        values.append(ppg)
        weights.append(weight * games_played_weight)
    
    if not values:
        return 0.0
    return round(np.average(values, weights=weights), 3)

def role_stability(snap_percentage:dict, position:str) -> float:
    if position in ("K", "DEF"):
        return 1.0
    if not snap_percentage or all(seasons == 0 for seasons in snap_percentage.values()):
        return 0.3
    
    mean = np.mean(list(snap_percentage.values()))
    std = np.std(snap_percentage)

    return round(1 - (std / mean + 1e-6), 3) 

def predict_kicker(player:dict) -> float:
    seasons = player.get('seasons', {})
    if not seasons:
        return 0.0
    
    base_ppg = weighted_ppg(seasons)
    age_mult = age_multiplier(player.get('age'), player.get('position'))
    score = base_ppg * age_mult * 17

    return round(max(score, 0), 1)

def predict_def(player:dict) -> float:
    seasons = player.get('seasons', {})
    if not seasons:
        return 0.0
    
    base_ppg = weighted_ppg(seasons)
    ppg_values = [seasons[k]["ppg"] for k in sorted(seasons.keys())]
    trend = calc_trend(ppg_values)
    score = (base_ppg * 17) + (trend * 17 * 0.5)

    return round(max(score, 0), 1)

def predict_skill(player:dict) -> float:
    """For all non-kicker, non-defense positions"""
    seasons = player.get('seasons', {})
    if not seasons:
        return 0.0
    
    base_ppg = weighted_ppg(seasons)
    baseline = base_ppg * 17

    ppg_values = [seasons[k]["ppg"] for k in sorted(seasons.keys()) if seasons[k].get('ppg', 0) > 0]
    trend = calc_trend(ppg_values)
    trend_adjustment = trend * 17

    snap_percentages = {k: seasons[k].get('snap_percentage', 0) for k in seasons}
    stability = role_stability(snap_percentages, player.get('position'))

    age_mult = age_multiplier(player.get('age'), player.get('position'))

    season_keys = sorted(seasons.keys())
    last_season = season_keys[-1] 
    injury_mult = 1.0

    if last_season.get('games_played', 17) < 10:
        injury_mult = 0.88

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