from __future__ import annotations

import numpy as np
import pandas as pd


def add_market_indicators(data: pd.DataFrame) -> pd.DataFrame:
    """Calculate monthly change, 6-month rolling mean/std, and z-score."""
    if data.empty:
        return data.copy()

    aggregations = {"price": ("price", "mean")}
    optional_columns = [
        "gmm_monthly_change",
        "caloric_contribution",
        "quarterly_change_nsa",
        "yoy_change_month",
    ]
    optional_label_columns = ["gmm_price_trend", "gmm_impact_code", "source_dataset"]
    for column in optional_columns:
        if column in data.columns:
            aggregations[column] = (column, "mean")
    for column in optional_label_columns:
        if column in data.columns:
            aggregations[column] = (column, "first")

    monthly_series = data.groupby(
        ["date", "country", "market", "commodity", "currency", "unit"],
        as_index=False,
    ).agg(**aggregations).sort_values("date")

    if "gmm_monthly_change" in monthly_series.columns:
        monthly_series["monthly_pct_change"] = monthly_series["gmm_monthly_change"]
    else:
        monthly_series["monthly_pct_change"] = monthly_series["price"].pct_change() * 100
    monthly_series["rolling_mean_6m"] = monthly_series["price"].rolling(window=6, min_periods=2).mean()
    monthly_series["rolling_std_6m"] = monthly_series["price"].rolling(window=6, min_periods=3).std(ddof=0)

    monthly_series["z_score"] = (
        (monthly_series["price"] - monthly_series["rolling_mean_6m"]) / monthly_series["rolling_std_6m"]
    )

    # Early rows do not have enough history for stable rolling stats, so use neutral defaults.
    monthly_series["monthly_pct_change"] = monthly_series["monthly_pct_change"].fillna(0)
    monthly_series["rolling_mean_6m"] = monthly_series["rolling_mean_6m"].fillna(monthly_series["price"])
    monthly_series["rolling_std_6m"] = monthly_series["rolling_std_6m"].fillna(0)
    monthly_series["z_score"] = monthly_series["z_score"].replace([np.inf, -np.inf], np.nan).fillna(0)

    return monthly_series
