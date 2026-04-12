import numpy as np

RECENT_SEASONS = ["2023", "2024", "2025"]
AGE_PEAK = {"QB": 29, "RB": 24, "WR": 28, "TE": 28, "K": 33}
AGE_DECLINE_RATE = {"QB": 0.025, "RB": 0.06, "WR": 0.035, "TE": 0.03, "K": 0.02}

def age_multiplier(age: int, position: str) -> float:
    if age is None:
        return 1.0
    
    peak_age = AGE_PEAK.get(position, 28)
    decline_rate = AGE_DECLINE_RATE.get(position, 0.035)
    years_past_peak = max(0, age - peak_age)
    raw = (1 - decline_rate) ** years_past_peak

    return round(0.5 + 0.5 * raw, 4)


def improvement_multiplier(seasons: dict) -> float:
    season_keys = sorted(seasons.keys())
    ppg_values = [seasons[k].get("ppg", 0) for k in season_keys if seasons[k].get("ppg", 0) > 0]

    if len(ppg_values) < 2:
        return 1.0
    
    improvements = sum(1 for i in range(1, len(ppg_values)) if ppg_values[i] > ppg_values[i-1])
    improvement_rate = improvements / (len(ppg_values) - 1)

    if improvement_rate == 1.0:
        return 1.10
    elif improvement_rate >= 0.67:
        return 1.05
    
    return 1.0


def is_opportunity_spike(seasons: dict, current_key: str) -> bool:
    season_keys = sorted(seasons.keys())
    idx = season_keys.index(current_key)

    if idx == 0:
        return False
    
    prev = seasons[season_keys[idx - 1]]
    curr = seasons[current_key]
    prev_targets = prev.get("rec_targets", 0)
    curr_targets = curr.get("rec_targets", 0)
    prev_snap = prev.get("snap_percentage", 0)
    curr_snap = curr.get("snap_percentage", 0)

    if prev_targets == 0:
        return False
    
    target_jump = (curr_targets - prev_targets) / (prev_targets + 1e-6)
    snap_jump = (curr_snap - prev_snap) / (prev_snap + 1e-6) if prev_snap > 0 else 0

    return target_jump > 0.25 and snap_jump < (target_jump * 0.5)


def calc_trend(ppg_values: list, seasons: dict = None) -> float:
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
    raw_trend = round(slope * r_squared, 4)

    if seasons:
        season_keys = sorted(seasons.keys())
        if is_opportunity_spike(seasons, season_keys[-1]):
            raw_trend *= 0.25

    return raw_trend


def consecutive_zero_seasons(seasons: dict) -> int:
    season_keys = sorted(seasons.keys(), reverse=True)
    count = 0

    for key in season_keys:
        if seasons[key].get("games_played", 0) == 0:
            count += 1
        else:
            break

    return count


def injury_severity(season_data: dict) -> float:
    games_played = season_data.get("games_played", 0)
    snap_pct = season_data.get("snap_percentage", 0)
    games_severity = max(0, (17 - games_played) / 17)
    snap_severity = max(0, (0.4 - snap_pct) / 0.4) if snap_pct < 0.4 else 0.0

    return round(min(games_severity * 0.7 + snap_severity * 0.3, 1.0), 3)


def recovery_factor(seasons: dict, season_key: str) -> float:
    season_keys = sorted(seasons.keys())
    idx = season_keys.index(season_key)

    if idx == 0 or idx >= len(season_keys) - 1:
        return 0.85
    
    pre = seasons[season_keys[idx - 1]]
    post = seasons[season_keys[idx + 1]]
    pre_ppg = pre.get("ppg", 0)

    if pre_ppg == 0:
        return 0.85
    
    ppg_recovery = min(post.get("ppg", 0) / pre_ppg, 1.0)
    snap_recovery = min(post.get("snap_percentage", 0) / pre.get("snap_percentage", 1), 1.0) if pre.get("snap_percentage", 0) > 0 else 1.0
    combined = ppg_recovery * 0.6 + snap_recovery * 0.4

    if combined >= 0.85:
        return 1.0
    elif combined >= 0.60:
        return 0.75
    
    return 0.55


def infer_projected_snap(seasons: dict) -> float:
    for key in sorted(seasons.keys(), reverse=True):
        season = seasons[key]
        if injury_severity(season) < 0.3:
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
    role_confidence = min(infer_projected_snap(seasons) / 0.8, 1.0)

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
            weight *= (1 - severity * 0.7) * recovery_factor(seasons, key)
        values.append(ppg)
        weights.append(weight * min(games_played / 17, 1.0))

    if not values:
        return 0.0
    
    return round(np.average(values, weights=weights), 3)


def role_stability(snap_percentages: dict, position: str) -> float:
    if position in ("K", "DEF"):
        return 1.0
    
    if not snap_percentages or all(v == 0 for v in snap_percentages.values()):
        return 0.3
    
    values = list(snap_percentages.values())

    return round(1 - (np.std(values) / (np.mean(values) + 1e-6)), 3)


def predict_kicker(player: dict) -> float:
    seasons = player.get("seasons", {})

    if not seasons:
        return 0.0
    
    return round(max(weighted_ppg(seasons) * 17 * age_multiplier(player.get("age"), player.get("position")), 0), 1)


def predict_def(player: dict) -> float:
    seasons = player.get("seasons", {})

    if not seasons:
        return 0.0
    base_ppg = weighted_ppg(seasons)

    ppg_values = [seasons[k]["ppg"] for k in sorted(seasons.keys())]
    trend = calc_trend(ppg_values, seasons=seasons)

    return round(max((base_ppg * 17) + (trend * 17 * 0.5), 0), 1)


def predict_skill(player: dict) -> float:
    seasons = player.get("seasons", {})

    if not seasons:
        return 0.0

    zero_streak = consecutive_zero_seasons(seasons)
    if zero_streak >= 2:
        return 0.0

    base_ppg = weighted_ppg(seasons)
    ppg_values = [seasons[k]["ppg"] for k in sorted(seasons.keys()) if seasons[k].get("ppg", 0) > 0]
    trend = calc_trend(ppg_values, seasons=seasons)

    snap_percentages = {k: seasons[k].get("snap_percentage", 0) for k in seasons}
    stability = role_stability(snap_percentages, player.get("position"))
    injury_mult = last_season_injury_mult(seasons)
    age_mult = age_multiplier(player.get("age"), player.get("position"))
    improvement_mult = improvement_multiplier(seasons)

    if zero_streak == 1:
        injury_mult *= 0.6

    score = (base_ppg * 17 + trend * 17) * stability * injury_mult * age_mult * improvement_mult
    return round(max(score, 0), 1)


def predict(player: dict) -> float:
    position = player.get("position")

    if position == "K":
        return predict_kicker(player)
    elif position == "DEF":
        return predict_def(player)
    
    return predict_skill(player)