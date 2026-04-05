import numpy as np

AGE_PEAK = {"QB": 32, "RB": 26, "WR": 28, "TE": 28, "K": 33}
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