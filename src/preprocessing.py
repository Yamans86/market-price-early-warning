from __future__ import annotations

from datetime import date

import pandas as pd

from src.data_loader import validate_required_columns


def preprocess_price_data(data: pd.DataFrame) -> pd.DataFrame:
    """Clean dates, prices, and text fields before filtering or analysis."""
    validate_required_columns(data)

    if {"Date", "CountryName", "Admin1", "MainStapleFood"}.issubset(data.columns):
        return _preprocess_global_market_monitor(data)

    clean_data = data.copy()
    clean_data["date"] = pd.to_datetime(clean_data["date"], errors="coerce")
    clean_data["price"] = pd.to_numeric(clean_data["price"], errors="coerce")

    # Drop rows that cannot be used in a time-series price analysis.
    clean_data = clean_data.dropna(subset=["date", "price"])
    clean_data = clean_data[clean_data["price"] > 0]

    text_columns = ["country", "market", "commodity", "currency", "unit"]
    for column in text_columns:
        clean_data[column] = clean_data[column].astype(str).str.strip()

    clean_data["date"] = clean_data["date"].dt.to_period("M").dt.to_timestamp()
    clean_data = clean_data.sort_values(["country", "market", "commodity", "date"])
    return clean_data.reset_index(drop=True)


def filter_data(
    data: pd.DataFrame,
    country: str,
    market: str,
    commodity: str,
    start_date: date,
    end_date: date,
) -> pd.DataFrame:
    """Return the selected country-market-commodity time series."""
    start_timestamp = pd.Timestamp(start_date)
    end_timestamp = pd.Timestamp(end_date)

    return data[
        (data["country"] == country)
        & (data["market"] == market)
        & (data["commodity"] == commodity)
        & (data["date"] >= start_timestamp)
        & (data["date"] <= end_timestamp)
    ].copy()


def _preprocess_global_market_monitor(data: pd.DataFrame) -> pd.DataFrame:
    """Convert Global Market Monitor indicator files into the app's analysis schema."""
    clean_data = pd.DataFrame()
    clean_data["date"] = pd.to_datetime(data["Date"], errors="coerce")
    clean_data["country"] = data["CountryName"].astype(str).str.strip()
    clean_data["market"] = data["Admin1"].astype(str).str.strip()
    clean_data["commodity"] = data["MainStapleFood"].astype(str).str.strip()
    clean_data["currency"] = "Index"
    clean_data["unit"] = "price index (base=100)"

    monthly_change = pd.to_numeric(data.get("MonthlyChangeNSA"), errors="coerce")
    monthly_change = monthly_change.fillna(pd.to_numeric(data.get("MonthlyChangeSA"), errors="coerce"))
    clean_data["gmm_monthly_change"] = monthly_change.fillna(0).clip(lower=-95, upper=300)

    clean_data["gmm_price_trend"] = data.get("PriceTrendMonth", "").astype(str).str.strip()
    clean_data["gmm_impact_code"] = data.get("TotImpactMonthlyCode", "").astype(str).str.strip()
    clean_data["caloric_contribution"] = pd.to_numeric(data.get("CaloricContribution"), errors="coerce")
    clean_data["quarterly_change_nsa"] = pd.to_numeric(data.get("QuarterlyChangeNSA"), errors="coerce")
    clean_data["yoy_change_month"] = pd.to_numeric(data.get("YoYChangeMonth"), errors="coerce")
    clean_data["source_dataset"] = data.get("DataLevel", "Global Market Monitor").astype(str).str.strip()

    clean_data = clean_data.dropna(subset=["date"])
    clean_data = clean_data[
        (clean_data["country"] != "")
        & (clean_data["market"] != "")
        & (clean_data["commodity"] != "")
        & (clean_data["gmm_price_trend"].str.upper() != "N/A")
    ]

    clean_data["date"] = clean_data["date"].dt.to_period("M").dt.to_timestamp()
    clean_data = clean_data.sort_values(["country", "market", "commodity", "date"])
    clean_data["price"] = clean_data.groupby(["country", "market", "commodity"], group_keys=False).apply(
        _build_price_index
    )

    return clean_data.reset_index(drop=True)


def _build_price_index(group: pd.DataFrame) -> pd.Series:
    """Construct an index from monthly percentage changes because GMM has no raw price column."""
    monthly_factor = 1 + (group["gmm_monthly_change"].fillna(0) / 100)
    return 100 * monthly_factor.cumprod()
