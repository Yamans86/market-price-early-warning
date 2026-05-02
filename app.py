from __future__ import annotations

from pathlib import Path

import plotly.graph_objects as go
import pandas as pd
import streamlit as st

from src.anomaly_detection import classify_alerts, train_alert_model
from src.data_loader import load_price_data
from src.forecasting import forecast_next_months
from src.indicators import add_market_indicators
from src.preprocessing import filter_data, preprocess_price_data
from src.recommendations import generate_recommendation


TEMPLATE_PATH = Path(__file__).resolve().parent / "data" / "upload_template.csv"


st.set_page_config(
    page_title="Humanitarian Market Price Early Warning",
    page_icon=":chart_with_upwards_trend:",
    layout="wide",
)


@st.cache_data(show_spinner=False)
def load_and_prepare_data(uploaded_file):
    raw_data = load_price_data(uploaded_file)
    return preprocess_price_data(raw_data)


@st.cache_resource(
    show_spinner=False,
    hash_funcs={
        pd.DataFrame: lambda df: (
            df.shape,
            tuple(df.columns),
            str(df["date"].min()) if "date" in df else "",
            str(df["date"].max()) if "date" in df else "",
        )
    },
)
def train_cached_alert_model(prepared_data):
    return train_alert_model(prepared_data)


@st.cache_data(show_spinner=False)
def load_template_bytes() -> bytes:
    if TEMPLATE_PATH.exists():
        return TEMPLATE_PATH.read_bytes()

    columns = "date,country,market,commodity,price,currency,unit\n"
    example = "2025-01-01,Cambodia,Siem Reap,Rice,3100,KHR,kg\n"
    return (columns + example).encode("utf-8")


def build_price_chart(data, forecast):
    """Create the main observed-price and forecast trend chart."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=data["date"],
            y=data["price"],
            mode="lines+markers",
            name="Observed price",
            line=dict(color="#2563eb", width=3),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=data["date"],
            y=data["rolling_mean_6m"],
            mode="lines",
            name="6-month rolling mean",
            line=dict(color="#475569", width=2, dash="dash"),
        )
    )

    if not forecast.empty:
        forecast_start = data[["date", "price"]].tail(1).rename(columns={"price": "forecast_price"})
        forecast_line = pd.concat([forecast_start, forecast], ignore_index=True)
        fig.add_trace(
            go.Scatter(
                x=forecast_line["date"],
                y=forecast_line["forecast_price"],
                mode="lines+markers",
                name="3-month forecast",
                line=dict(color="#dc2626", width=3, dash="dot"),
            )
        )

    fig.update_layout(
        template="plotly_white",
        height=480,
        margin=dict(l=20, r=20, t=30, b=20),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis_title=None,
        yaxis_title="Price or price index",
    )
    return fig


st.title("Humanitarian Market Price Early Warning System")
st.caption(
    "A Streamlit MVP for monitoring food price volatility and supporting cash programming decisions."
)

with st.sidebar:
    st.header("Upload Data")
    st.download_button(
        label="Download CSV template",
        data=load_template_bytes(),
        file_name="market_price_upload_template.csv",
        mime="text/csv",
        help="Use this template for standard food price uploads.",
    )
    uploaded_file = st.file_uploader(
        "Food price CSV",
        type=["csv"],
        help=(
            "Supports standard columns: date, country, market, commodity, price, currency, unit; "
            "or Global Market Monitor columns."
        ),
    )

try:
    data = load_and_prepare_data(uploaded_file)
except ValueError as error:
    st.error(str(error))
    st.stop()
except Exception as error:
    st.error(f"Could not load the dataset: {error}")
    st.stop()

alert_model = train_cached_alert_model(data)

with st.sidebar:
    st.header("Filters")
    country = st.selectbox("Country", sorted(data["country"].unique()))

    country_data = data[data["country"] == country]
    market = st.selectbox("Market", sorted(country_data["market"].unique()))

    market_data = country_data[country_data["market"] == market]
    commodity = st.selectbox("Commodity", sorted(market_data["commodity"].unique()))

    min_date = data["date"].min().date()
    max_date = data["date"].max().date()
    date_range = st.date_input("Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)

if len(date_range) != 2:
    st.info("Select a start and end date to continue.")
    st.stop()

filtered = filter_data(
    data=data,
    country=country,
    market=market,
    commodity=commodity,
    start_date=date_range[0],
    end_date=date_range[1],
)

if filtered.empty:
    st.warning("No records match the selected filters. Try widening the date range or changing filters.")
    st.stop()

series = add_market_indicators(filtered)
series = classify_alerts(series, model_bundle=alert_model)
forecast = forecast_next_months(series, months=3)
latest = series.sort_values("date").iloc[-1]
recommendation = generate_recommendation(latest["alert_level"])

metric_columns = st.columns(5)
metric_columns[0].metric(
    "Latest price/index",
    f"{latest['currency']} {latest['price']:,.0f}",
    f"{latest['monthly_pct_change']:+.1f}% MoM",
)
metric_columns[1].metric("6-month mean", f"{latest['currency']} {latest['rolling_mean_6m']:,.0f}")
metric_columns[2].metric("Rolling std. dev.", f"{latest['rolling_std_6m']:,.1f}")
metric_columns[3].metric("Z-score", f"{latest['z_score']:+.2f}")
metric_columns[4].metric("Alert level", latest["alert_level"])

left_column, right_column = st.columns([1.8, 1])

with left_column:
    st.subheader("Price Trend and Forecast")
    st.plotly_chart(build_price_chart(series, forecast), use_container_width=True)

with right_column:
    st.subheader("Cash Programming Recommendation")
    st.markdown(f"**Recommended action:** {recommendation['action']}")
    st.write(recommendation["rationale"])
    st.caption(
        f"Alert model: {alert_model.status}"
        + (f" Validation accuracy: {alert_model.accuracy:.1%}." if alert_model.accuracy is not None else "")
        + f" Training rows: {alert_model.training_rows:,}."
    )
    st.markdown("**Suggested checks**")
    for check in recommendation["checks"]:
        st.write(f"- {check}")

st.subheader("Indicator Table")
st.dataframe(
    series[
        [
            "date",
            "country",
            "market",
            "commodity",
            "price",
            "currency",
            "unit",
            "monthly_pct_change",
            "rolling_mean_6m",
            "rolling_std_6m",
            "z_score",
            "alert_level",
        ]
    ].sort_values("date", ascending=False),
    hide_index=True,
    use_container_width=True,
)

with st.expander("Methodology notes"):
    st.write(
        "The app calculates month-on-month price change, 6-month rolling statistics, "
        "and a rolling z-score. For Global Market Monitor files, the price line is a "
        "derived index compounded from reported monthly percentage changes because the "
        "source files do not include nominal prices. When scikit-learn is installed, "
        "the alert classifier is trained from historical GMM trend labels; otherwise "
        "the app uses transparent threshold rules."
    )
