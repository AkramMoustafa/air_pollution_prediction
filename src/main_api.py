from fastapi import FastAPI
from src.services.data_processer import get_all_sensors_locations, get_sensor_readings_7days_api
from src.services.predictor import predict_one_hour, predict_multi_hour
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
app = FastAPI()

cached_df = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # local dev
        "https://air-pollution-prediction-three.vercel.app"  # production frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

cached_df = None

@app.get("/locations")
def get_locations():
    global cached_df

    if cached_df is None:
        cached_df = get_all_sensors_locations()

    return {
        "count": len(cached_df),
        "data": cached_df.to_dict(orient="records")
    }
@app.get("/sensor-data")
def get_sensor_data(lat: float, lon: float):
    try:
        data = get_sensor_readings_7days_api(lat, lon)

        if not data:
            return {"lat": lat, "lon": lon, "pm25": None}

       

        df = pd.DataFrame(data)

        # ✅ filter ONLY pm25
        df = df[df["parameter"].isin(["pm25", "pm2.5"])]

        # ✅ SAFE datetime parsing
        df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce", utc=True)
        df["value"] = pd.to_numeric(df["value"], errors="coerce")

        # ✅ drop bad rows
        df = df.dropna(subset=["datetime", "value"])

        if df.empty:
            return {"lat": lat, "lon": lon, "pm25": None}

        latest_row = df.sort_values("datetime").iloc[-1]

        return {
            "lat": lat,
            "lon": lon,
            "pm25": float(latest_row["value"]),
            "datetime": str(latest_row["datetime"])
        }

    except Exception as e:
        return {"error": str(e)}
    
# @app.get("/predict")
# def predict_pm25(lat: float, lon: float):
#     try:
#         print("📍 Predict request:", lat, lon)

#         result = predict_one_hour(lat, lon)

#         if result is None:
#             return {
#                 "status": "error",
#                 "message": "Not enough data to make prediction"
#             }

#         return {
#             "status": "success",
#             "lat": lat,
#             "lon": lon,
#             "pm25_prediction": result
#         }

#     except Exception as e:
#         return {
#             "status": "error",
#             "message": str(e)
#         }
    
@app.get("/predict")
def predict_pm25(lat: float, lon: float):
    try:
        print("📍 Predict request:", lat, lon)

        preds = predict_multi_hour(lat, lon)

        if preds is None:
            return {
                "status": "error",
                "message": "Not enough data to make prediction"
            }

        return {
            "status": "success",
            "lat": lat,
            "lon": lon,
            "pm25_1h": preds.get("1h"),
            "pm25_3h": preds.get("3h"),
            "pm25_6h": preds.get("6h"),
            "pm25_12h": preds.get("12h"),
            "forecast": preds
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
    


@app.get("/predict")
def predict_pm25(lat: float, lon: float):
    try:
        print("📍 Predict request:", lat, lon)

        preds = predict_multi_hour(lat, lon)

        if preds is None:
            return {
                "status": "error",
                "message": "Not enough data to make prediction"
            }

        return {
            "status": "success",
            "lat": lat,
            "lon": lon,

            # 🔥 multi-horizon outputs
            "pm25_1h": preds.get("1h"),
            "pm25_3h": preds.get("3h"),
            "pm25_6h": preds.get("6h"),
            "pm25_12h": preds.get("12h"),

            # optional full dict
            "forecast": preds
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }