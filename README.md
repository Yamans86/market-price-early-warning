# Humanitarian Market Price Early Warning System

This project is a Python Streamlit MVP for monitoring staple food price stress and supporting humanitarian cash and voucher assistance (CVA) decisions.

The app now uses the Global Market Monitor CSV files provided in `data/` as the default dataset. Because these files contain market indicators and percentage changes rather than nominal food prices, the app builds a derived price index for each country-market-commodity series and trains an alert classifier from the historical GMM trend labels.

## Project Structure

```text
market-price-early-warning/
|-- app.py
|-- run_app.bat
|-- run_app.ps1
|-- requirements.txt
|-- README.md
|-- data/
|   |-- global-market-monitor.csv
|   |-- global-market-monitor_subnational.csv
|   `-- sample_food_prices.csv
|-- src/
|   |-- data_loader.py
|   |-- preprocessing.py
|   |-- indicators.py
|   |-- anomaly_detection.py
|   |-- forecasting.py
|   `-- recommendations.py
`-- notebooks/
    `-- exploratory_analysis.ipynb
```

## Features

- Load national and subnational Global Market Monitor data by default.
- Upload a standard food price CSV or a compatible GMM-format CSV.
- Filter by country, market, commodity, and date range.
- Display a Plotly line chart of observed price index, 6-month rolling mean, and 3-month forecast.
- Calculate monthly percentage change, rolling mean, rolling standard deviation, and z-score.
- Train a `scikit-learn` Random Forest alert classifier from GMM monthly trend labels when dependencies are installed.
- Fall back to transparent threshold-based alerts if `scikit-learn` is unavailable.
- Forecast the next 3 months with `statsmodels` ExponentialSmoothing when installed.
- Generate CVA recommendations based on `Normal`, `Watch`, `Alert`, and `Critical` levels.

## Installation

### One-click Windows launcher

Double-click:

```text
run_app.bat
```

Or run the PowerShell menu:

```powershell
.\run_app.ps1
```

The launcher creates `.venv`, installs dependencies from `requirements.txt`, and starts Streamlit at:

```text
http://localhost:8501
```

### Manual run

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

On macOS or Linux:

```bash
source .venv/bin/activate
```

## Supported Data

Standard uploaded CSV columns:

| Column | Description | Example |
| --- | --- | --- |
| `date` | Observation date | `2025-01-01` |
| `country` | Country name | `Cambodia` |
| `market` | Market name | `Siem Reap` |
| `commodity` | Food item | `Rice` |
| `price` | Numeric price | `3100` |
| `currency` | Currency code or name | `KHR` |
| `unit` | Unit of measure | `kg` |

Global Market Monitor columns used:

| GMM column | App field |
| --- | --- |
| `Date` | `date` |
| `CountryName` | `country` |
| `Admin1` | `market` |
| `MainStapleFood` | `commodity` |
| `MonthlyChangeNSA` / `MonthlyChangeSA` | monthly change and derived price index |
| `PriceTrendMonth` | model training label |
| `CaloricContribution`, `QuarterlyChangeNSA`, `YoYChangeMonth` | model features |

## Methodology

For standard price data, the app calculates indicators from the uploaded price series.

For Global Market Monitor data, the source does not include nominal prices. The app constructs a price index for each country-market-commodity series:

```text
price_index_t = price_index_t-1 * (1 + monthly_change_t / 100)
```

The index starts from 100 and is used for trend visualization, rolling statistics, z-score calculation, and forecasting.

Alert modeling:

- GMM labels are mapped into app alert levels: `Normal` and `Negative` to `Normal`, `Moderate` to `Watch`, `High` to `Alert`, and `Severe` to `Critical`.
- A Random Forest classifier trains on monthly change, rolling statistics, z-score, caloric contribution, quarterly change, and year-on-year change.
- If `scikit-learn` is not installed, the app uses rule-based thresholds.

Forecasting:

- Uses `statsmodels.tsa.holtwinters.ExponentialSmoothing`.
- Uses additive trend and additive seasonality when enough history is available.
- Falls back to a flat forecast for short or difficult series.

## Limitations

- The GMM-derived price index is not a nominal market price and should be interpreted as relative change over time.
- Alert labels inherit the assumptions and quality of the GMM trend classifications.
- Forecasts are short-term statistical estimates, not scenario analysis.
- CVA recommendations are decision-support prompts, not automatic program instructions.
- Operational decisions should triangulate price monitoring with trader capacity, supply chains, household purchasing power, access, protection risks, and cash working group guidance.

## Portfolio Value

This project demonstrates:

- Modular Python application structure.
- Streamlit dashboard development.
- Real humanitarian market monitoring data preparation.
- Time-series indicator engineering.
- Supervised alert classification with `scikit-learn`.
- Forecasting with `statsmodels`.
- Translation of analytics into practical CVA recommendations.
