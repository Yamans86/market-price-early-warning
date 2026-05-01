from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DEFAULT_DATA_PATH = DATA_DIR / "global-market-monitor_subnational.csv"
NATIONAL_GMM_PATH = DATA_DIR / "global-market-monitor.csv"
SAMPLE_DATA_PATH = DATA_DIR / "sample_food_prices.csv"
REQUIRED_COLUMNS = {"date", "country", "market", "commodity", "price", "currency", "unit"}
GMM_COLUMNS = {
    "Date",
    "CountryName",
    "Admin1",
    "MainStapleFood",
    "MonthlyChangeNSA",
    "PriceTrendMonth",
    "TotImpactMonthlyCode",
}


def load_price_data(uploaded_file=None) -> pd.DataFrame:
    """Load uploaded data, project GMM data, sample data, or generated synthetic data."""
    if uploaded_file is not None:
        return pd.read_csv(uploaded_file)

    if DEFAULT_DATA_PATH.exists():
        frames = [pd.read_csv(DEFAULT_DATA_PATH)]
        if NATIONAL_GMM_PATH.exists():
            frames.append(pd.read_csv(NATIONAL_GMM_PATH))
        return pd.concat(frames, ignore_index=True)

    if SAMPLE_DATA_PATH.exists():
        return pd.read_csv(SAMPLE_DATA_PATH)

    return generate_synthetic_cambodia_data()


def validate_required_columns(data: pd.DataFrame) -> None:
    """Raise a clear error if the dataset is missing required columns."""
    if REQUIRED_COLUMNS.issubset(data.columns) or GMM_COLUMNS.issubset(data.columns):
        return

    missing_columns = REQUIRED_COLUMNS - set(data.columns)
    missing_gmm_columns = GMM_COLUMNS - set(data.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        missing_gmm = ", ".join(sorted(missing_gmm_columns))
        required = ", ".join(sorted(REQUIRED_COLUMNS))
        raise ValueError(
            f"Missing required column(s): {missing}. Required columns are: {required}. "
            f"For Global Market Monitor files, missing: {missing_gmm}."
        )


def generate_synthetic_cambodia_data() -> pd.DataFrame:
    """Generate deterministic sample food price data for portfolio demos."""
    rng = np.random.default_rng(42)
    dates = pd.date_range("2021-01-01", "2025-12-01", freq="MS")
    markets = ["Phnom Penh", "Battambang", "Siem Reap", "Kampong Cham"]
    commodities = [
        ("Rice", "kg", 2700),
        ("Vegetable oil", "liter", 6200),
        ("Eggs", "10 pieces", 6500),
        ("Fish", "kg", 15000),
    ]

    rows = []
    for market in markets:
        market_factor = 1 + rng.normal(0, 0.05)
        for commodity, unit, base_price in commodities:
            for index, date in enumerate(dates):
                seasonal_factor = 1 + 0.04 * np.sin((index % 12) / 12 * 2 * np.pi)
                trend_factor = 1 + index * 0.003
                shock_factor = _shock_factor(date, commodity, market)
                noise = rng.normal(0, base_price * 0.02)
                price = base_price * market_factor * seasonal_factor * trend_factor * shock_factor + noise

                rows.append(
                    {
                        "date": date,
                        "country": "Cambodia",
                        "market": market,
                        "commodity": commodity,
                        "price": round(max(price, 100), 0),
                        "currency": "KHR",
                        "unit": unit,
                    }
                )

    return pd.DataFrame(rows)


def _shock_factor(date: pd.Timestamp, commodity: str, market: str) -> float:
    """Add a few plausible synthetic shocks so the dashboard has meaningful alerts."""
    if pd.Timestamp("2022-06-01") <= date <= pd.Timestamp("2022-10-01") and commodity == "Vegetable oil":
        return 1.16
    if pd.Timestamp("2023-09-01") <= date <= pd.Timestamp("2024-01-01") and commodity == "Rice":
        return 1.18
    if pd.Timestamp("2025-05-01") <= date <= pd.Timestamp("2025-08-01") and market == "Siem Reap":
        return 1.14
    return 1.0
