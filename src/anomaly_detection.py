from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


FEATURE_COLUMNS = [
    "monthly_pct_change",
    "rolling_mean_6m",
    "rolling_std_6m",
    "z_score",
    "caloric_contribution",
    "quarterly_change_nsa",
    "yoy_change_month",
]

LABEL_MAP = {
    "Normal": "Normal",
    "Negative": "Normal",
    "Moderate": "Watch",
    "High": "Alert",
    "Severe": "Critical",
}


@dataclass
class AlertModelBundle:
    model: object | None
    features: list[str]
    training_rows: int
    accuracy: float | None
    status: str


def classify_alerts(data: pd.DataFrame, model_bundle: AlertModelBundle | None = None) -> pd.DataFrame:
    """Classify each month as Normal, Watch, Alert, or Critical."""
    classified = data.copy()
    if classified.empty:
        classified["alert_level"] = []
        return classified

    model_predictions = predict_alert_levels(classified, model_bundle)
    if model_predictions is not None:
        classified["alert_level"] = model_predictions
        classified["rule_alert_level"] = classified.apply(_classify_row, axis=1)
    else:
        classified["alert_level"] = classified.apply(_classify_row, axis=1)
    return classified


def train_alert_model(data: pd.DataFrame) -> AlertModelBundle:
    """Train a supervised alert classifier from Global Market Monitor labels."""
    training_data = _build_training_frame(data)
    if training_data.empty:
        return AlertModelBundle(None, FEATURE_COLUMNS, 0, None, "No labeled GMM rows available.")

    try:
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.metrics import accuracy_score
        from sklearn.model_selection import train_test_split
    except ImportError:
        return AlertModelBundle(
            None,
            FEATURE_COLUMNS,
            len(training_data),
            None,
            "scikit-learn is not installed; using threshold-based alerts.",
        )

    x = training_data[FEATURE_COLUMNS]
    y = training_data["training_alert_level"]

    if y.nunique() < 2 or len(training_data) < 50:
        return AlertModelBundle(None, FEATURE_COLUMNS, len(training_data), None, "Not enough label variety to train.")

    stratify = y if y.value_counts().min() >= 2 else None
    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=0.2,
        random_state=42,
        stratify=stratify,
    )
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        min_samples_leaf=5,
        random_state=42,
        class_weight="balanced",
        n_jobs=-1,
    )
    model.fit(x_train, y_train)
    accuracy = float(accuracy_score(y_test, model.predict(x_test)))
    return AlertModelBundle(model, FEATURE_COLUMNS, len(training_data), accuracy, "Trained on GMM labels.")


def predict_alert_levels(data: pd.DataFrame, bundle: AlertModelBundle | None) -> list[str] | None:
    """Predict alert levels if a trained model is available."""
    if bundle is None or bundle.model is None:
        return None

    features = _ensure_feature_columns(data, bundle.features)
    return list(bundle.model.predict(features))


def _classify_row(row: pd.Series) -> str:
    monthly_change = float(row["monthly_pct_change"])
    z_score = float(row["z_score"])

    if z_score >= 2.5 or monthly_change >= 25:
        return "Critical"
    if z_score >= 1.75 or monthly_change >= 15:
        return "Alert"
    if z_score >= 1.0 or monthly_change >= 8:
        return "Watch"
    return "Normal"


def _build_training_frame(data: pd.DataFrame) -> pd.DataFrame:
    label_column = "gmm_price_trend"
    if label_column not in data.columns:
        return pd.DataFrame()

    training_data = _add_training_features(data.copy())
    training_data["training_alert_level"] = (
        training_data[label_column].astype(str).str.strip().map(LABEL_MAP)
    )
    training_data = training_data.dropna(subset=["training_alert_level"])
    return _ensure_feature_columns(training_data, FEATURE_COLUMNS).assign(
        training_alert_level=training_data["training_alert_level"].values
    )


def _add_training_features(data: pd.DataFrame) -> pd.DataFrame:
    """Ensure model features exist even when training starts from preprocessed data."""
    group_columns = ["country", "market", "commodity"]
    data = data.sort_values([*group_columns, "date"])

    if "monthly_pct_change" not in data.columns:
        if "gmm_monthly_change" in data.columns:
            data["monthly_pct_change"] = pd.to_numeric(data["gmm_monthly_change"], errors="coerce")
        else:
            data["monthly_pct_change"] = data.groupby(group_columns)["price"].pct_change() * 100

    if "rolling_mean_6m" not in data.columns:
        data["rolling_mean_6m"] = data.groupby(group_columns)["price"].transform(
            lambda series: series.rolling(window=6, min_periods=2).mean()
        )

    if "rolling_std_6m" not in data.columns:
        data["rolling_std_6m"] = data.groupby(group_columns)["price"].transform(
            lambda series: series.rolling(window=6, min_periods=3).std(ddof=0)
        )

    if "z_score" not in data.columns:
        data["z_score"] = (data["price"] - data["rolling_mean_6m"]) / data["rolling_std_6m"]

    return data


def _ensure_feature_columns(data: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    frame = pd.DataFrame(index=data.index)
    for feature in features:
        if feature in data.columns:
            frame[feature] = pd.to_numeric(data[feature], errors="coerce")
        else:
            frame[feature] = 0.0
    return frame.fillna(0.0)
