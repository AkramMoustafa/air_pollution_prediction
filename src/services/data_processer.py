import pandas as pd
import os, time, csv, random, json, hashlib, io, gzip, pickle
from concurrent.futures import ThreadPoolExecutor, as_completed
# DATE AND TIME
import requests
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
import os

load_dotenv()

import pandas as pd

df = pd.read_csv("locations_global.csv", header=None)


REQUEST_COUNT = 0
RATE_LIMIT_COUNT = 0
RETRYABLE_ERROR_COUNT = 0
HTTP_ERROR_COUNT = 0
CACHE_HITS = 0

LAT, LON = 34.1808, -118.3490
RADIUS_M = 3_500

CORE_PARAMS = {"pm25", "pm2.5", "pm10"}
INCLUDE_ALL_PARAMS = False

DAYS = 365 * 3
CHUNK_DAYS = 30

LOCATION_LIMIT = 100
MEAS_LIMIT = 1000
MAX_PAGES_LOC = 50
MAX_PAGES_MEAS = 50

# Backfill AWS
USE_AWS_BACKFILL = True
ALLOW_API_FALLBACK = False
AWS_BUCKET = "openaq-data-archive"
AWS_PREFIX = "records/csv.gz"

BASE_SLEEP = 1.00
JITTER = 0.2

K_NEIGHBORS = 3

RANDOM_STATE = 42

CACHE_TTL_HOURS = 24
CACHE_ENABLED = True

SPIKE_THRESHOLD_MAD = 6.0
MAX_GAP_HOURS = 48

RADIUS_M = 1000

# RUN_TAG = f"openaq_global_r{RADIUS_M}_{timestamp}"
# OUT_DIR = RUN_TAG
# os.makedirs(OUT_DIR, exist_ok=True)

# CACHE_PATH = os.path.join(OUT_DIR, "api_cache.json")

BASE_URL = "https://api.openaq.org/v3"

session = requests.Session()

import os
API_KEY = "0cd0fb766d5e0b27831bc8858fa08c333e5c3db92a4afcd2be4801956f782768"

HEADERS = {"X-API-Key": API_KEY}
print(API_KEY)
print(HEADERS)
HORIZON_UNCERTAINTY_SCALE = 0.12
import time
import random

def sleep_time_api(mult=1.0):
    """
    Pauses execution to respect API rate limits, adding jitter to avoid thundering herd problems.

    Args:
        mult (float, optional): Multiplier for the base sleep time. Defaults to 1.0.
    """
    time.sleep((BASE_SLEEP + random.random() * JITTER) * mult)

import os
import json
# Run tag helps show the locations, radius, and time of the data pull
RUN_TAG = f"openaq_{LAT}_{LON}_r{RADIUS_M}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
OUT_DIR = RUN_TAG

CACHE_PATH = os.path.join(OUT_DIR, "api_cache.json")

dt_to = datetime.now(timezone.utc)
dt_from = dt_to - timedelta(days=DAYS)

# ✅ DEFINE IT HERE
if os.path.exists(CACHE_PATH):
    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            RESPONSE_CACHE = json.load(f)
    except Exception:
        RESPONSE_CACHE = {}  # fallback if file is corrupted
else:
    RESPONSE_CACHE = {}

  
def cache_key(endpoint, params):
    """
    Generates a SHA-256 hash to serve as a unique cache key for an API request.

    Args:
        endpoint (str): The API endpoint path.
        params (dict): The query parameters.

    Returns:
        str: A 64-character hexadecimal hash.
    """
    payload = {"endpoint": endpoint, "params": params}
    raw = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

 
def cache_valid(entry):
    """
    Checks whether a given cache entry is still valid based on its age.

    Args:
        entry (dict): The cache entry containing a 'cached_at' timestamp.

    Returns:
        bool: True if the cache is valid, False otherwise.
    """
    if not entry:
        return False
    ts = pd.to_datetime(entry.get("cached_at"), errors="coerce", utc=True)
    if pd.isna(ts):
        return False
    age_h = (pd.Timestamp.now(tz="UTC") - ts).total_seconds() / 3600
    return age_h <= CACHE_TTL_HOURS

def flush_cache():
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(RESPONSE_CACHE, f)

def get_json(endpoint, params=None, retries=6):
    """
    Fetches JSON data from the OpenAQ API with caching, retries, and rate-limit handling.

    Args:
        endpoint (str): The API endpoint path (e.g., '/locations').
        params (dict, optional): Query parameters for the request.
        retries (int, optional): Maximum number of request attempts. Defaults to 6.

    Returns:
        dict: The JSON payload returned by the API.

    Raises:
        requests.exceptions.HTTPError: If a non-retryable HTTP error occurs (e.g., 401, 404).
        RuntimeError: If all retry attempts fail.

    Side Effects:
        - Modifies global tracking counters (REQUEST_COUNT, RATE_LIMIT_COUNT, etc.).
        - Reads from and writes to the global RESPONSE_CACHE.
        - May pause execution (sleep) if rate limits or server errors are encountered.
    """
    global REQUEST_COUNT, RATE_LIMIT_COUNT, RETRYABLE_ERROR_COUNT, HTTP_ERROR_COUNT, CACHE_HITS

    url = f"{BASE_URL}{endpoint}"
    params = params or {}

    ck = cache_key(endpoint, params)
    if CACHE_ENABLED:
        entry = RESPONSE_CACHE.get(ck)
        if cache_valid(entry):
            CACHE_HITS += 1
            return entry["payload"]

    backoff = 1.0

    for attempt in range(retries):
        try:
            REQUEST_COUNT += 1
            r = session.get(url, headers=HEADERS, params=params, timeout=60)
            print(f"[API GET] Status {r.status_code} | Endpoint: {endpoint} | Attempt: {attempt+1}/{retries}")

            remaining = r.headers.get("x-ratelimit-remaining")
            reset_ts = r.headers.get("x-ratelimit-reset")
            if remaining is not None or reset_ts is not None:
                print(f"[API LIMITS] Calls remaining: {remaining} | Resets at epoch: {reset_ts}")

            if r.status_code == 429:
                RATE_LIMIT_COUNT += 1
                RETRYABLE_ERROR_COUNT += 1
                if reset_ts:
                    wait_s = max(1, int(reset_ts) - int(time.time()) + 1)
                    print(f"[API WARNING] Rate limit (429) hit. Pausing execution for {wait_s} seconds.")
                    time.sleep(wait_s)
                else:
                    print(f"[API WARNING] Rate limit (429) hit without reset header. Backing off for {backoff:.2f}s.")
                    sleep_time_api(mult=backoff)
                    backoff *= 2
                continue

            if r.status_code in (408, 500, 502, 503, 504):
                RETRYABLE_ERROR_COUNT += 1
                print(f"[API ERROR] Retryable server error ({r.status_code}). Backing off for {backoff:.2f}s.")
                sleep_time_api(mult=backoff)
                backoff *= 2
                continue

            if r.status_code in (401, 403, 404, 422):
                HTTP_ERROR_COUNT += 1
                print(f"[API FATAL] Client error ({r.status_code}) on {endpoint}. Check API key and parameters.")
                r.raise_for_status()

            r.raise_for_status()
            payload = r.json()
            if CACHE_ENABLED:
                RESPONSE_CACHE[ck] = {
                    "cached_at": pd.Timestamp.now(tz="UTC").isoformat(),
                    "payload": payload
                }
                if len(RESPONSE_CACHE) % 25 == 0:
                    flush_cache()

            return payload

        except requests.exceptions.RequestException as e:
            print(f"[API EXCEPTION] Request failed for {endpoint}: {repr(e)}")
            if attempt == retries - 1:
                print(f"[API FATAL] Max retries reached for {endpoint}.")
                raise
            RETRYABLE_ERROR_COUNT += 1
            sleep_time_api(mult=backoff)
            backoff *= 2

    raise RuntimeError(f"Failed to fetch data from {endpoint} after {retries} attempts.")

def iteration_chunks(start_dt, end_dt, chunk_days=30):
    """
    Yields chunked datetime ranges between a start and end date.

    Args:
        start_dt (datetime): The start of the overall range.
        end_dt (datetime): The end of the overall range.
        chunk_days (int, optional): The maximum duration of each chunk in days. Defaults to 30.

    Yields:
        tuple: A pair of datetime objects representing the start and end of the chunk.
    """
    cur = start_dt
    while cur < end_dt:
        next_dt = min(cur + timedelta(days=chunk_days), end_dt)
        yield cur, next_dt
        cur = next_dt

       
def iso(dt):
    """
    Converts a datetime object to an ISO 8601 formatted string.

    Args:
        dt (datetime): The datetime object to convert.

    Returns:
        str: The ISO-formatted string.
    """
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def paginate(endpoint, params, limit=1000, max_pages=50):
    """
    Retrieves all pages of results from an OpenAQ API endpoint.

    Args:
        endpoint (str): The API endpoint path.
        params (dict): Base query parameters.
        limit (int, optional): Number of records per page. Defaults to 1000.
        max_pages (int, optional): Safety limit to prevent infinite loops. Defaults to 50.

    Returns:
        list: A combined list of all result dictionaries retrieved across pages.
    """
    out = []
    last_meta_found = None

    for page in range(1, max_pages + 1):
        p = dict(params)
        p["limit"] = limit
        p["page"] = page

        data = get_json(endpoint, p)
        results = data.get("results", [])
        meta = data.get("meta", {}) or {}
        last_meta_found = meta.get("found")

        if last_meta_found is not None:
            try:
                last_meta_found = int(last_meta_found)
            except:
                last_meta_found = None

        print(f"[PAGINATE INFO] Endpoint: {endpoint} | Page: {page} | Records retrieved: {len(results)}")

        if not results:
            break

        out.extend(results)

        if len(results) < limit:
            break

        sleep_time_api()

    if last_meta_found is not None and len(out) < last_meta_found:
        print(f"[PAGINATE WARNING] Endpoint {endpoint} returned {len(out)} records, but metadata indicates {last_meta_found} total.")

    print(f"[PAGINATE SUCCESS] Endpoint {endpoint} completed. Total records compiled: {len(out)}")
    return out

import os

def get_all_sensors_locations(csv_path="locations_global.csv"):
   
    

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_PATH = os.path.join(BASE_DIR, "locations_global.csv")

    df = pd.read_csv(DATA_PATH, header=None)

    all_rows = []

    for _, row in df.iterrows():

        possible_pairs = [(18, 19), (20, 21)]
        lat, lon = None, None

        for lat_idx, lon_idx in possible_pairs:
            lat_candidate = pd.to_numeric(row[lat_idx], errors="coerce")
            lon_candidate = pd.to_numeric(row[lon_idx], errors="coerce")

            if (
                pd.notna(lat_candidate) and pd.notna(lon_candidate)
                and -90 <= lat_candidate <= 90
                and -180 <= lon_candidate <= 180
            ):
                lat, lon = lat_candidate, lon_candidate
                break

        if lat is None or lon is None:
            continue

        all_rows.append({
            "lat": lat,
            "lon": lon
        })

    return pd.DataFrame(all_rows)

def get_sensor_readings(lat, lon, radius=1000):
    """
    Given latitude and longitude, return nearby sensor readings
    """

    # Step 1: find nearby locations
    locations = paginate(
        "/locations",
        params={"coordinates": f"{lat},{lon}", "radius": radius},
        limit=10,
        max_pages=1
    )

    if not locations:
        return []

    results = []

    for loc in locations:
        loc_id = loc.get("id")
        loc_name = loc.get("name")

        # Step 2: get latest readings
        latest = get_json(f"/locations/{loc_id}/latest")

        for r in latest.get("results", []):
            dt = r.get("datetime", {})

            results.append({
                "location_id": loc_id,
                "location_name": loc_name,
                "sensor_id": r.get("sensor", {}).get("id"),
                "parameter": r.get("parameter"),
                "value": r.get("value"),
                "datetime_utc": dt.get("utc"),
            })

    return results

def get_sensor_readings(lat, lon, radius=1000):

    # Step 1: find nearby locations
    locations = paginate(
        "/locations",
        params={"coordinates": f"{lat},{lon}", "radius": radius},
        limit=10,
        max_pages=1
    )

    if not locations:
        return []

    results = []

    for loc in locations:
        loc_id = loc.get("id")
        loc_name = loc.get("name")

        # Step 2: get latest readings
        latest = get_json(f"/locations/{loc_id}/latest")

        for r in latest.get("results", []):
            dt = r.get("datetime", {})

            results.append({
                "location_id": loc_id,
                "location_name": loc_name,
                "sensor_id": r.get("sensor", {}).get("id"),
                "parameter": r.get("parameter"),
                "value": r.get("value"),
                "datetime_utc": dt.get("utc"),
            })

    return results

# lat = -33.673752071375
# lon = -70.953064737434

# data = get_sensor_readings(lat, lon)

# print("RESULT COUNT:", len(data))
# print("SAMPLE:", data[:3])

import csv
import os
def get_sensor_readings_7days_api(lat, lon, radius=1000):
    from datetime import datetime, timedelta

    results = []

    # STEP 1: find nearby locations
    locations = paginate(
        "/locations",
        params={"coordinates": f"{lat},{lon}", "radius": radius},
        limit=5,
        max_pages=1
    )

    if not locations:
        return []
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    seven_days_ago = now - timedelta(days=7)

    date_from = seven_days_ago.strftime("%Y-%m-%dT%H:%M:%SZ")
    date_to = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    # STEP 2: loop locations → sensors → measurements
    for loc in locations:
        loc_id = loc.get("id")
        loc_name = loc.get("name")

        sensors = paginate(
            f"/locations/{loc_id}/sensors",
            params={},
            limit=10,
            max_pages=1
        )

        for s in sensors:
            sensor_id = s.get("id")

            if not sensor_id:
                continue

            measurements = paginate(
                f"/sensors/{sensor_id}/measurements",
                params={
                    "date_from": date_from,
                    "date_to": date_to
                },
                limit=500,
                max_pages=2
            )

            for m in measurements:
                param = m.get("parameter", {}).get("name", "").lower()

                # filter only pm25 / pm10
                if param not in {"pm25", "pm2.5", "pm10"}:
                    continue

                results.append({
                    "location_id": loc_id,
                    "location_name": loc_name,
                    "sensor_id": sensor_id,
                    "parameter": param,
                    "value": m.get("value"),
                    "datetime": m.get("datetime", {}).get("utc"),
                    "lat": lat,
                    "lon": lon
                })

    return results

lat = -33.673752071375
lon = -70.953064737434

data = get_sensor_readings_7days_api(lat, lon)

print("FINAL RESULT COUNT:")

if data:
    print("SAMPLE:")
    for row in data[:5]:
        print(row)