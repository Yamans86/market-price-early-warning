from __future__ import annotations

import pandas as pd


def forecast_next_months(data: pd.DataFrame, months: int = 3) -> pd.DataFrame:
    """Forecast prices using statsmodels ExponentialSmoothing."""
    if data.empty:
        return pd.DataFrame(columns=["date", "forecast_price"])

    series = data.sort_values("date").set_index("date")["price"].astype(float)
    future_dates = pd.date_range(series.index.max() + pd.offsets.MonthBegin(1), periods=months, freq="MS")

    if len(series) < 6:
        # ExponentialSmoothing needs enough history; fall back to a flat forecast for short series.
        return pd.DataFrame({"date": future_dates, "forecast_price": [float(series.iloc[-1])] * months})

    try:
        from statsmodels.tsa.holtwinters import ExponentialSmoothing

        seasonal_periods = 12 if len(series) >= 24 else None
        model = ExponentialSmoothing(
            series,
            trend="add",
            seasonal="add" if seasonal_periods else None,
            seasonal_periods=seasonal_periods,
            initialization_method="estimated",
        )
        fitted_model = model.fit(optimized=True)
        forecast_values = fitted_model.forecast(months)
    except (ImportError, Exception):
        # Keep the app usable if statsmodels is not installed or the model cannot converge.
        forecast_values = pd.Series([float(series.iloc[-1])] * months, index=future_dates)

    return pd.DataFrame(
        {
            "date": future_dates,
            "forecast_price": [max(float(value), 0.0) for value in forecast_values],
        }
    )
