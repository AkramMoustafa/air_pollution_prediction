# import requests
# import pandas as pd
# import os
# import time

# # ==============================
# # CONFIG
# # ==============================

# import os

# API_KEY = os.getenv("OPENAQ_API_KEY")

# HEADERS = {"X-API-Key": API_KEY}

# BASE_URL = "https://api.openaq.org/v3/locations"

# HEADERS = {
#     "X-API-Key": API_KEY
# }

# PARAMS = {
#     "limit": 1000,
#     "page": 1
# }

# OUTPUT_FILE = "locations_global.csv"

# # ==============================
# # INIT FILE
# # ==============================
# # Create file with header if it doesn't exist
# if not os.path.exists(OUTPUT_FILE):
#     pd.DataFrame().to_csv(OUTPUT_FILE, index=False)

# total_count = 0

# while True:
#     try:
#         response = requests.get(
#             BASE_URL,
#             headers=HEADERS,
#             params=PARAMS,
#             timeout=15
#         )

#         if response.status_code != 200:
#             print(f"❌ Error {response.status_code}: {response.text}")
#             break

#         data = response.json()
#         results = data.get("results", [])

#         # Stop condition
#         if not results:
#             print("✅ Finished fetching all pages")
#             break

#         # Normalize current batch only
#         df = pd.json_normalize(results)

#         # Append to CSV (NO overwrite)
#         df.to_csv(
#             OUTPUT_FILE,
#             mode="a",
#             header=not os.path.exists(OUTPUT_FILE) or os.path.getsize(OUTPUT_FILE) == 0,
#             index=False
#         )

#         total_count += len(results)

#         print(
#             f"✅ Page {PARAMS['page']} | "
#             f"Fetched: {len(results)} | "
#             f"Total saved: {total_count}"
#         )

#         # Next page
#         PARAMS["page"] += 1

#         # Rate limit safety
#         time.sleep(0.2)

#     except requests.exceptions.RequestException as e:
#         print(f"⚠️ Network error: {e}")
#         print("🔁 Retrying in 5 seconds...")
#         time.sleep(5)

# # ==============================
# # DONE
# # ==============================
# print(f"\n🎉 DONE: Saved {total_count} locations to {OUTPUT_FILE}")