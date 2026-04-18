from fastapi import FastAPI
from src.services.data_processer import get_all_sensors_locations
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

cached_df = None


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # your frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def load_data():
    global cached_df
    cached_df = get_all_sensors_locations()

@app.get("/locations")
def get_locations():
    if cached_df is None:
        return {"error": "Data not loaded"}

    return {
        "count": len(cached_df),
        "data": cached_df.to_dict(orient="records")
    }