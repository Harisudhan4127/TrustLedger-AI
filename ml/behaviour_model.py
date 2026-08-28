"""Behavioural anomaly detection used by Module 8. Uses a simple, explainable
z-score approach by default (works from very little data, which matters for a
hackathon demo with few seeded transactions), with IsolationForest available
as a drop-in upgrade once enough per-agent history exists.
"""

import numpy as np

try:
    from sklearn.ensemble import IsolationForest
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

MIN_SAMPLES_FOR_ISOLATION_FOREST = 10


def zscore_deviation(amount: float, mean: float, std: float) -> float:
    """Returns a 0-100 deviation score from a z-score."""
    std = max(std, 1e-6)  # avoid divide-by-zero for brand-new agents
    z = abs((amount - mean) / std)
    if z <= 1:
        return round(min(30, z * 30), 1)
    elif z <= 3:
        return round(30 + ((z - 1) / 2) * 30, 1)  # 30-60
    else:
        return round(min(100, 60 + (z - 3) * 10), 1)  # 60-100+


def isolation_forest_deviation(history_amounts: list, current_amount: float) -> float:
    """Optional multivariate-style upgrade path. Falls back to None if
    scikit-learn isn't available or there isn't enough history yet."""
    if not SKLEARN_AVAILABLE or len(history_amounts) < MIN_SAMPLES_FOR_ISOLATION_FOREST:
        return None

    X = np.array(history_amounts).reshape(-1, 1)
    model = IsolationForest(contamination=0.1, random_state=42)
    model.fit(X)
    raw_score = model.decision_function([[current_amount]])[0]  # higher = more normal
    # Rescale roughly to 0-100 (lower raw_score -> higher anomaly score)
    anomaly_score = round(max(0, min(100, (0.5 - raw_score) * 200)), 1)
    return anomaly_score


def compute_behaviour_deviation(mean_amount: float, std_amount: float, current_amount: float,
                                 history_amounts: list = None) -> dict:
    z_score_result = zscore_deviation(current_amount, mean_amount, std_amount)

    if_result = None
    if history_amounts:
        if_result = isolation_forest_deviation(history_amounts, current_amount)

    final_score = if_result if if_result is not None else z_score_result
    method = "isolation_forest" if if_result is not None else "z_score"

    return {"behaviour_deviation": final_score, "method": method}
