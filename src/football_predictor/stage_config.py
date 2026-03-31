from __future__ import annotations

import os
from datetime import date

import numpy as np
import pandas as pd


DEFAULT_STAGE_WINDOWS = {
    "stage1": {
        "start": "2021-05-26",
        "end": "2025-05-26",
    },
    "stage2": {
        "start": "2025-05-27",
        "end": None,
    },
}

DEFAULT_CUTOFF_QUANTILE = 0.07
DEFAULT_STAGE2_STRENGTH_LOWER = 0.05
DEFAULT_STAGE2_STRENGTH_UPPER = 0.95
DEFAULT_MAX_GOAL_LIMIT = 5.99


def resolve_stage_window(stage_name: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    stage_key = stage_name.upper()
    defaults = DEFAULT_STAGE_WINDOWS[stage_name]

    start_value = os.getenv(f"{stage_key}_START_DATE", defaults["start"])
    end_default = defaults["end"] if defaults["end"] is not None else date.today().isoformat()
    end_value = os.getenv(f"{stage_key}_END_DATE", end_default)

    start_date = pd.to_datetime(start_value)
    end_date = pd.to_datetime(end_value)
    return start_date, end_date


def resolve_cutoff_quantile(stage_name: str, default_quantile: float = DEFAULT_CUTOFF_QUANTILE) -> float:
    stage_key = stage_name.upper()
    return float(os.getenv(f"{stage_key}_CUTOFF_QUANTILE", str(default_quantile)))


def add_strength(
    df: pd.DataFrame,
    spi_col: str = "spi",
    lower: float = DEFAULT_STAGE2_STRENGTH_LOWER,
    upper: float = DEFAULT_STAGE2_STRENGTH_UPPER,
) -> pd.DataFrame:
    df = df.copy()
    n = len(df)
    if n <= 1:
        df["strength"] = 0.5
        return df
    ranks = df[spi_col].rank(method="average")
    pct = (ranks - 1) / (n - 1)
    df["strength"] = lower + (upper - lower) * pct
    return df


def estimate_adjustment_factor(metric_max: float, metric_min: float, max_goal_limit: float = DEFAULT_MAX_GOAL_LIMIT) -> float:
    numerator = max_goal_limit
    denominator = (metric_max / metric_min) - 1
    return float(numerator / denominator)


def estimate_dynamism_variable(
    stage_name: str,
    metric_min: float,
    metric_median: float,
    metric_max: float,
    adjustment_factor: float,
) -> float:
    if stage_name == "stage1":
        search_grid = np.arange(0.01, 0.5, 0.01)
    else:
        search_grid = np.arange(0.001, max(metric_min - 0.001, 0.001), 0.001)

    for dynamism_variable in search_grid:
        adjusted_home_goals = (
            adjustment_factor * (metric_median / (metric_min - dynamism_variable))
            - adjustment_factor * ((metric_max + dynamism_variable) / metric_min)
        )
        adjusted_away_goals = (
            adjustment_factor * (metric_min / (metric_min - dynamism_variable))
            - adjustment_factor * ((metric_max + dynamism_variable) / metric_median)
        )
        if adjusted_home_goals > 0 and adjusted_away_goals > 0:
            return float(dynamism_variable)

    raise ValueError(f"Could not estimate dynamism variable for {stage_name}.")


def estimate_stage_metric_parameters(
    stage_name: str,
    metric_series: pd.Series,
    cutoff_quantile: float,
) -> dict:
    metric_series = metric_series.astype(float)
    metric_median = float(metric_series.median())
    metric_min = float(metric_series.min())
    metric_max = float(metric_series.max())
    cutoff_value = float(metric_series.quantile(cutoff_quantile))
    adjustment_factor = estimate_adjustment_factor(metric_max=metric_max, metric_min=metric_min)
    dynamism_variable = estimate_dynamism_variable(
        stage_name=stage_name,
        metric_min=metric_min,
        metric_median=metric_median,
        metric_max=metric_max,
        adjustment_factor=adjustment_factor,
    )
    return {
        "cutoff_quantile": float(cutoff_quantile),
        "cutoff_value": cutoff_value,
        "median": metric_median,
        "minimum": metric_min,
        "maximum": metric_max,
        "adjustment_factor": adjustment_factor,
        "dynamism_variable": dynamism_variable,
    }
