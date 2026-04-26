import pandas as pd
import numpy as np
from src.services.data_processer import get_sensor_readings_7days_api

# =========================
# FEATURE ENGINEERING
# =========================
import requests

def fetch_weather(lat, lon, start_date, end_date):
    url = "https://archive-api.open-meteo.com/v1/archive"

    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,wind_direction_10m,surface_pressure",
        "timezone": "UTC"
    }

    r = requests.get(url, params=params, timeout=30)

    if r.status_code != 200:
        return pd.DataFrame()

    data = r.json().get("hourly", {})

    if "time" not in data:
        return pd.DataFrame()

    weather_df = pd.DataFrame({
        "datetime": pd.to_datetime(data["time"], utc=True),
        "temp_c": data.get("temperature_2m"),
        "humidity_pct": data.get("relative_humidity_2m"),
        "precip_mm": data.get("precipitation"),
        "wind_speed_ms": data.get("wind_speed_10m"),
        "wind_dir_deg": data.get("wind_direction_10m"),
        "surface_pressure_hpa": data.get("surface_pressure"),
    })

    return weather_df


def debug_df(df, name):
    print(f"\n===== {name} =====")
    print("Shape:", df.shape)
    print("Columns:", df.columns.tolist())
    print("\nHead:")
    print(df.head(5))
    print("\nTail:")
    print(df.tail(5))
    print("\nNaN count:")
    print(df.isna().sum())

def build_features(data):
    df = pd.DataFrame(data)

    if df.empty:
        return None

    pd.set_option("display.max_rows", 200)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", None)


    # debug_df(df, "RAW DATA")

    # --- CLEAN ---
    df["datetime"] = pd.to_datetime(df["datetime"], utc=True, errors="coerce")
    df = df.set_index("datetime")
    df = df.resample("1H").mean()
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    df = df[df["parameter"].isin(["pm25", "pm2.5"])]
    df = df.dropna(subset=["datetime", "value"])

    if df.empty:
        return None

    # debug_df(df, "AFTER CLEAN")

    sensor_counts = (
        df.groupby("datetime")["sensor_id"]
        .nunique()
        .reset_index(name="sensor_count")
    )

    # --- AGGREGATE ---
    df = (
        df.groupby("datetime")["value"]
        .mean()
        .reset_index()
    )
    

    # --- MERGE SENSOR COUNT ---
    df = df.merge(sensor_counts, on="datetime", how="left")

    df = df.sort_values("datetime")

    df = df.set_index("datetime")              # 🔥 FIX
    df["value"] = df["value"].interpolate(method="time")
    df = df.reset_index()                      
    # --- INTERPOLATE ---


    # debug_df(df, "AFTER INTERPOLATION")


    lat = data[0]["lat"]
    lon = data[0]["lon"]

    start_date = df["datetime"].min().strftime("%Y-%m-%d")
    end_date = df["datetime"].max().strftime("%Y-%m-%d")

    weather_df = fetch_weather(lat, lon, start_date, end_date)

    if not weather_df.empty:
        df = df.merge(weather_df, on="datetime", how="left")

        weather_cols = [
            "temp_c",
            "humidity_pct",
            "precip_mm",
            "wind_speed_ms",
            "wind_dir_deg",
            "surface_pressure_hpa",
        ]

        df[weather_cols] = df[weather_cols].ffill().bfill()
    else:
        print("⚠️ Weather data missing")

    if len(df) < 30:
        return None

    # --- FEATURES ---
    df["lag_1h"] = df["value"].shift(1)
    df["lag_6h"] = df["value"].shift(6)
    df["lag_12h"] = df["value"].shift(12)
    df["lag_24h"] = df["value"].shift(24)

    df["roll_mean_3h"] = df["value"].shift(1).rolling(3).mean()
    df["roll_mean_6h"] = df["value"].shift(1).rolling(6).mean()
    df["roll_mean_24h"] = df["value"].shift(1).rolling(24).mean()
    df["roll_mean_7d"] = df["value"].shift(1).rolling(168, min_periods=24).mean()    

    df["roll_std_3h"] = df["value"].shift(1).rolling(3).std()
    df["roll_std_6h"] = df["value"].shift(1).rolling(6).std()
    df["roll_std_24h"] = df["value"].shift(1).rolling(24).std()

    # --- TIME FEATURES ---
    df["hour"] = df["datetime"].dt.hour
    df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)

    df["month"] = df["datetime"].dt.month
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)

    df["day_of_week"] = df["datetime"].dt.dayofweek.astype("int8")

    df["dow_sin"] = np.sin(2 * np.pi * df["day_of_week"] / 7).astype("float32")
    df["dow_cos"] = np.cos(2 * np.pi * df["day_of_week"] / 7).astype("float32")

    df["is_weekend"] = (df["day_of_week"] >= 5).astype("int8")
    
    df["day_of_year"] = df["datetime"].dt.dayofyear


    
    df["sensor_health_mean"] = 100
    df["sensor_health_min"] = 100

    print("\n===== BEFORE DROPNA =====")
    print("Rows:", len(df))
    print(df.isna().sum().sort_values(ascending=False).head(10))

    # --- FINAL CLEAN ---
    df_final = df.dropna(subset=[
        "lag_1h", "lag_6h", "lag_12h", "lag_24h",
        "roll_mean_3h", "roll_mean_6h", "roll_mean_24h", "roll_mean_7d",
        "roll_std_3h", "roll_std_6h", "roll_std_24h"
    ])

    # debug_df(df_final, "FINAL DATA")

    # --- SAVE DEBUG FILES ---
    df.to_csv("debug_after_features.csv", index=False)
    df_final.to_csv("debug_final.csv", index=False)

    if df_final.empty:
        return None

    return df_final.iloc[-1:]
# =========================
# MODEL LOADING
# =========================
import pickle
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.join(BASE_DIR, "..", "lgb_model.pkl")
MODEL_PATH = os.path.abspath(MODEL_PATH)
print("🔥 NEW VERSION OF PREDICTOR LOADED")
# with open(MODEL_PATH, "rb") as f:
#     model = pickle.load(f)


FEATURES = [
    "lag_1h", "lag_6h", "lag_12h", "lag_24h",
    "hour_sin", "hour_cos",
    "month_sin", "month_cos",
    "dow_sin", "dow_cos",
    "is_weekend", "day_of_year",

    "roll_mean_3h", "roll_mean_6h", "roll_mean_24h", "roll_mean_7d",
    "roll_std_3h", "roll_std_6h", "roll_std_24h",

    "sensor_count", "sensor_health_mean", "sensor_health_min",

    "temp_c",
    "humidity_pct",
    "precip_mm",
    "wind_speed_ms",
    "wind_dir_deg",
    "surface_pressure_hpa",
]


# =========================
# PREDICTION
# =========================
def predict(df):
    if df is None:
        return None

    return float(model.predict(df[FEATURES])[0])


# =========================
# TEST PIPELINE
# =========================
def predict_one_hour(lat, lon):
    # print("📡 Fetching data...")
    data = get_sensor_readings_7days_api(lat, lon)

    if not data:
        print("❌ No data returned")
        return

    # print("📊 Building features...")
    features_df = build_features(data)

    if features_df is None:
        print("❌ Not enough data to build features")
        return

    print("🤖 Predicting...")
    try:
        result = predict(features_df)
        print("✅ Prediction:", result)
        return result
    except Exception as e:
        print("❌ Prediction failed:", e)


# lat, lon = 39.82055407605199, -104.9397126865905

# test_prediction(lat, lon)


def predict_multi_hour(lat, lon, steps=[1, 3, 6, 12]):
    data = get_sensor_readings_7days_api(lat, lon)

    if not data:
        return None

    df = build_features(data)

    if df is None:
        return None

    preds = {}
    current_df = df.copy()

    max_step = max(steps)

    for step in range(1, max_step + 1):
        y_pred = predict(current_df)

        # store only requested steps
        if step in steps:
            preds[f"{step}h"] = float(y_pred)

        # 🔥 simulate next timestep
        current_df["lag_24h"] = current_df["lag_12h"]
        current_df["lag_12h"] = current_df["lag_6h"]
        current_df["lag_6h"] = current_df["lag_1h"]
        current_df["lag_1h"] = y_pred

        # update rolling features (approximation)
        current_df["roll_mean_3h"] = (current_df["roll_mean_3h"] * 2 + y_pred) / 3
        current_df["roll_mean_6h"] = (current_df["roll_mean_6h"] * 5 + y_pred) / 6

    return preds


