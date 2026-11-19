"""Jarak provinsi ke sentra cabai (D-48 butir 3, D-50).

titik sentra berbobot produksi: per provinsi bertitik sentra dan per komoditas, rata-rata koordinat kabupaten sentra
berbobot produksi rata-rata 2019-2025 (data/interim/sentra_points.csv).
distance_to_sentra_km: jarak great-circle dari ibu kota provinsi ke titik sentra terdekat (termasuk provinsinya sendiri).
is_different_island: pulau ibu kota berbeda dengan pulau titik sentra terdekat. Pulau dipetakan per provinsi (pulau
utama tempat ibu kota berada); semua kabupaten sentra berada di pulau utama provinsinya.

Ibu kota digeocode lewat Nominatim (OpenStreetMap) dengan cache di data/interim/geocode_cache.json.
Output data/interim/province_geography.parquet (provinsi x komoditas).
"""
import json
import time

import numpy as np
import pandas as pd

from pipeline.extract.common import new_session, request_with_retry
from pipeline.readers import ROOT, load_pihps_provinces

INTERIM = ROOT / "data" / "interim"
CACHE = INTERIM / "geocode_cache.json"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

# province_id -> (ibu kota, pulau utama)
CAPITALS = {
    1: ("Banda Aceh", "Sumatera"), 2: ("Medan", "Sumatera"), 3: ("Padang", "Sumatera"), 4: ("Pekanbaru", "Sumatera"),
    5: ("Tanjung Pinang", "Bintan"), 6: ("Jambi", "Sumatera"), 7: ("Bengkulu", "Sumatera"), 8: ("Palembang", "Sumatera"),
    9: ("Pangkal Pinang", "Bangka"), 10: ("Bandar Lampung", "Sumatera"), 11: ("Serang", "Jawa"), 12: ("Bandung", "Jawa"),
    13: ("Jakarta Pusat", "Jawa"), 14: ("Semarang", "Jawa"), 15: ("Yogyakarta", "Jawa"), 16: ("Surabaya", "Jawa"),
    17: ("Denpasar", "Bali"), 18: ("Mataram", "Lombok"), 19: ("Kupang", "Timor"), 20: ("Pontianak", "Kalimantan"),
    21: ("Banjarbaru", "Kalimantan"), 22: ("Palangka Raya", "Kalimantan"), 23: ("Samarinda", "Kalimantan"),
    24: ("Tanjung Selor", "Kalimantan"), 25: ("Gorontalo", "Sulawesi"), 26: ("Makassar", "Sulawesi"), 27: ("Kendari", "Sulawesi"),
    28: ("Palu", "Sulawesi"), 29: ("Manado", "Sulawesi"), 30: ("Mamuju", "Sulawesi"), 31: ("Ambon", "Ambon"),
    32: ("Sofifi", "Halmahera"), 33: ("Jayapura", "Papua"), 34: ("Manokwari", "Papua"),
}
GROUPS = ["cabai_merah", "cabai_rawit"]


def great_circle_km(lat1, lon1, lat2, lon2):
    p1, p2 = np.radians(lat1), np.radians(lat2)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(lon2 - lon1) / 2) ** 2
    return 12742 * np.arcsin(np.sqrt(a))


def geocode_capitals():
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    names = {v: k for k, v in load_pihps_provinces().items()}
    session = new_session()
    session.headers["User-Agent"] = "cabai-price-spike-research/1.0 (academic data project)"
    rows = []
    for province_id, (capital, island) in CAPITALS.items():
        key = f"capital|{capital}|{names[province_id]}"
        if key not in cache:
            found = request_with_retry(session, "GET", NOMINATIM_URL, params={"q": f"{capital}, {names[province_id]}, Indonesia", "format": "jsonv2", "limit": 1, "countrycodes": "id"}).json()
            cache[key] = {"lat": float(found[0]["lat"]), "lon": float(found[0]["lon"]), "match": found[0]["display_name"]} if found else None
            CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
            time.sleep(1.2)
        place = cache[key]
        rows.append({"province_id": province_id, "capital": capital, "island": island, "capital_lat": place["lat"], "capital_lon": place["lon"], "geocode_match": place["match"]})
    return pd.DataFrame(rows)


def sentra_centroids():
    points = pd.read_csv(INTERIM / "sentra_points.csv")
    weight = points["mean_production_ton_2019_2025"]
    points = points.assign(w_lat=points["latitude"] * weight, w_lon=points["longitude"] * weight, w=weight)
    grouped = points.groupby(["commodity_group", "province_id"])[["w_lat", "w_lon", "w"]].sum().reset_index()
    grouped["sentra_lat"] = grouped["w_lat"] / grouped["w"]
    grouped["sentra_lon"] = grouped["w_lon"] / grouped["w"]
    return grouped[["commodity_group", "province_id", "sentra_lat", "sentra_lon"]]


def build():
    capitals = geocode_capitals()
    centroids = sentra_centroids()
    island_of = dict(zip(capitals["province_id"], capitals["island"]))
    rows = []
    for group in GROUPS:
        candidates = centroids[centroids["commodity_group"] == group]
        for _, capital in capitals.iterrows():
            distances = great_circle_km(capital["capital_lat"], capital["capital_lon"], candidates["sentra_lat"].to_numpy(), candidates["sentra_lon"].to_numpy())
            nearest = candidates.iloc[int(np.argmin(distances))]
            rows.append({
                "province_id": capital["province_id"], "commodity_group": group, "capital": capital["capital"],
                "capital_lat": capital["capital_lat"], "capital_lon": capital["capital_lon"],
                "nearest_sentra_province_id": int(nearest["province_id"]),
                "distance_to_sentra_km": float(distances.min()),
                "is_different_island": island_of[capital["province_id"]] != island_of[int(nearest["province_id"])],
            })
    return pd.DataFrame(rows), capitals


def run():
    geography, capitals = build()
    INTERIM.mkdir(parents=True, exist_ok=True)
    geography.to_parquet(INTERIM / "province_geography.parquet", index=False)
    capitals.to_parquet(INTERIM / "province_capitals.parquet", index=False)
    print(f"province_geography: {len(geography)} baris; median jarak {geography['distance_to_sentra_km'].median():.0f} km; beda pulau {int(geography['is_different_island'].sum())}")
    return geography


if __name__ == "__main__":
    run()
