"""Extract cuaca harian Open-Meteo untuk kabupaten sentra cabai.

Dua langkah:
1. Pilih kabupaten sentra dan cari koordinatnya (Nominatim/OpenStreetMap). Hasil:
   data/interim/sentra_points.csv, satu baris per kabupaten terpilih.
2. Tarik curah hujan dan kelembapan harian per lokasi, 1991-01-01 sampai beberapa hari sebelum
   tanggal extraction, ke data/raw/open_meteo/daily/. Mulai 1991 karena normal cuaca memakai
   1991-2020 (D-19).

Aturan pemilihan (D-24): per grup komoditas, kabupaten diurutkan dari produksi nasional
(rata-rata BDSP 2019-2025) dan diambil sampai kumulatif sekitar 80% produksi nasional. Kabupaten
yang berjarak kurang dari 10 km dari titik berproduksi lebih besar memakai cuaca titik itu
(kolom anchor_id), jadi satu lokasi Open-Meteo bisa melayani beberapa kabupaten dan dua komoditas.
Provinsi tanpa kabupaten terpilih tidak punya data cuaca (not applicable, ditandai di fase transform).

Bobot request Open-Meteo: dengan dua variabel harian, biaya = jumlah hari / 70 call (diukur dari
header X-RateLimit-Cost). Satu lokasi 1991-2026 (13.102 hari) = sekitar 187 call, sedangkan batas
gratis 600/menit, 5.000/jam, 10.000/hari. Script memberi jeda 20 detik antar request, menunggu
reset kalau kena batas per menit atau per jam, dan berhenti kalau batas harian tercapai. Jalankan
ulang keesokan harinya; lokasi yang file-nya sudah valid dilewati.

Jalankan:  python -m pipeline.extract.open_meteo [--only points|weather] [--refresh]
"""
import argparse
import csv
import json
import math
import re
import time
from datetime import date, timedelta

from bs4 import BeautifulSoup

from pipeline.extract.common import (
    EXTRACTION_DATE,
    RAW_DIR,
    new_session,
    request_with_retry,
    save_raw,
    target_path,
)
from pipeline.provinces import BPS_TO_PIHPS

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OUT = RAW_DIR / "open_meteo" / "daily"
POINTS_CSV = RAW_DIR.parent / "interim" / "sentra_points.csv"
GEOCODE_CACHE = RAW_DIR.parent / "interim" / "geocode_cache.json"

START_DATE = "1991-01-01"
END_LAG_DAYS = 5
NATIONAL_COVERAGE = 0.80
MERGE_DISTANCE_KM = 10
GEOCODE_PAUSE = 1.2  # kebijakan Nominatim: maksimal satu request per detik
REQUEST_PAUSE = 20  # satu request 35 tahun = ~187 call, batas 600 call/menit
CALLS_PER_DAY_OF_DATA = 1 / 70  # dua variabel harian, hasil ukur header X-RateLimit-Cost

# berkas BDSP -> (grup komoditas, faktor ke ton). cabai_merah = cabe besar saja (D-28);
# cabe keriting tidak dipakai untuk memilih sentra.
BDSP_FILES = {
    "cabe_besar_produksi": ("cabai_merah", 1.0),
    "cabe_rawit_produksi": ("cabai_rawit", 1.0),
}

# ejaan BDSP yang tidak dikenali OpenStreetMap
NAME_ALIASES = {
    "Kab. Kutai Kertanegara": "Kab. Kutai Kartanegara",
    "Kab. Mamuju Utara/Kab. Pasangkayu": "Kab. Pasangkayu",
    "Kab. Karang Asem": "Kab. Karangasem",  # tanpa alias, Nominatim mencocokkan sebuah sekolah di Sentul, Jawa Barat
}


def parse_number(text):
    return float(text.replace(".", "").replace(",", ".")) if text else 0.0


def read_bdsp_regencies(html_path):
    """Tabel kabupaten BDSP: [(kode_kab, label, produksi rata-rata 2019-2025)]. Kolom pertama (2018) dibuang."""
    soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "lxml")
    rows = []
    for tr in soup.find_all("tr"):
        cells = [cell.get_text(strip=True) for cell in tr.find_all(["th", "td"])]
        if len(cells) < 4 or not re.match(r"^\d{4} - ", cells[1]):
            continue
        yearly = [parse_number(value) for value in cells[3:]]  # 2019-2025
        code, label = cells[1].split(" - ", 1)
        rows.append((code, label, sum(yearly) / len(yearly)))
    return rows


def regency_query_name(label):
    label = NAME_ALIASES.get(label, label)
    name = label.replace("Kab. Adm. ", "Kabupaten Administrasi ").replace("Kota Adm. ", "Kota Administrasi ")
    return name.replace("Kab. ", "Kabupaten ")


def collect_regency_production():
    """{grup: {kode_kab: {label, bps_prov, province_id, ton}}} dari semua berkas kabupaten BDSP."""
    production = {}
    for tag, (group, factor) in BDSP_FILES.items():
        for path in sorted((RAW_DIR / "bdsp" / "kabupaten").glob(f"{tag}_prov*.html")):
            bps_code = path.stem.rsplit("prov", 1)[1]
            for code, label, mean_value in read_bdsp_regencies(path):
                entry = production.setdefault(group, {}).setdefault(
                    code,
                    {"label": label, "bps_prov": bps_code, "province_id": BPS_TO_PIHPS[bps_code][0], "ton": 0.0},
                )
                entry["ton"] += mean_value * factor
    return production


def select_regencies(production):
    """Per grup: kabupaten teratas sampai kumulatif NATIONAL_COVERAGE dari produksi nasional."""
    selected = []
    for group, regencies in sorted(production.items()):
        ranked = sorted(regencies.items(), key=lambda item: -item[1]["ton"])
        total = sum(info["ton"] for _, info in ranked)
        covered = 0.0
        for code, info in ranked:
            selected.append((group, code, info))
            covered += info["ton"] / total
            if covered >= NATIONAL_COVERAGE:
                break
    return selected


def distance_km(lat1, lon1, lat2, lon2):
    """Jarak haversine dalam kilometer."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 12742 * math.asin(math.sqrt(a))


def geocode(session, label, province_name, cache):
    key = f"{label}|{province_name}"
    if key in cache:
        return cache[key]
    result = None
    for query in (f"{regency_query_name(label)}, {province_name}, Indonesia", f"{regency_query_name(label)}, Indonesia"):
        found = request_with_retry(
            session, "GET", NOMINATIM_URL, params={"q": query, "format": "jsonv2", "limit": 1, "countrycodes": "id"}
        ).json()
        time.sleep(GEOCODE_PAUSE)
        if found:
            result = {"lat": float(found[0]["lat"]), "lon": float(found[0]["lon"]), "match": found[0]["display_name"]}
            break
    cache[key] = result
    return result


def assign_anchors(rows):
    """Gabungkan kabupaten yang berjarak < MERGE_DISTANCE_KM; anchor = kabupaten berproduksi terbesar."""
    anchors = []  # (anchor_id, lat, lon)
    for row in sorted(rows, key=lambda r: -r["total_ton"]):
        for anchor_id, lat, lon in anchors:
            if distance_km(row["latitude"], row["longitude"], lat, lon) < MERGE_DISTANCE_KM:
                row["anchor_id"] = anchor_id
                break
        else:
            row["anchor_id"] = row["regency_code"]
            anchors.append((row["anchor_id"], row["latitude"], row["longitude"]))
    anchor_coords = {anchor_id: (lat, lon) for anchor_id, lat, lon in anchors}
    for row in rows:
        row["anchor_latitude"], row["anchor_longitude"] = anchor_coords[row["anchor_id"]]


def calls_per_location():
    days = (EXTRACTION_DATE - timedelta(days=END_LAG_DAYS) - date.fromisoformat(START_DATE)).days + 1
    return days * CALLS_PER_DAY_OF_DATA


def build_points():
    session = new_session()
    session.headers["User-Agent"] = "cabai-price-spike-research/1.0 (academic data project)"
    bdsp_prov = {p["fkode_prop"]: p["nama_prop"] for p in json.loads((RAW_DIR / "bdsp" / "ref" / "getProv.json").read_text(encoding="utf-8"))}
    cache = json.loads(GEOCODE_CACHE.read_text(encoding="utf-8")) if GEOCODE_CACHE.exists() else {}
    GEOCODE_CACHE.parent.mkdir(parents=True, exist_ok=True)

    selected = select_regencies(collect_regency_production())
    totals = {}
    for group, code, info in selected:
        totals[code] = totals.get(code, 0.0) + info["ton"]

    rows, unresolved, suspicious = [], [], []
    for group, code, info in selected:
        place = geocode(session, info["label"], bdsp_prov[info["bps_prov"]], cache)
        GEOCODE_CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
        if place is None:
            unresolved.append(info["label"])
            continue
        province_name = bdsp_prov[info["bps_prov"]]
        if province_name.split(" ")[-1].lower() not in place["match"].lower():
            suspicious.append(f"{info['label']} -> {place['match'][:60]}")
        rows.append(
            {
                "commodity_group": group,
                "province_id": info["province_id"],
                "regency_code": code,
                "regency_name": info["label"],
                "mean_production_ton_2019_2025": round(info["ton"], 1),
                "total_ton": totals[code],
                "latitude": place["lat"],
                "longitude": place["lon"],
                "geocode_match": place["match"],
            }
        )
    assign_anchors(rows)
    rows.sort(key=lambda r: -r["total_ton"])
    fields = ["commodity_group", "province_id", "regency_code", "regency_name", "mean_production_ton_2019_2025",
              "latitude", "longitude", "anchor_id", "anchor_latitude", "anchor_longitude", "geocode_match"]
    with open(POINTS_CSV, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    locations = {row["anchor_id"] for row in rows}
    calls = len(locations) * calls_per_location()
    print(f"{len(rows)} baris kabupaten x komoditas -> {len(locations)} lokasi cuaca; koordinat tidak ketemu: {unresolved or 'tidak ada'}")
    print(f"perkiraan {calls:,.0f} call API (~{calls_per_location():.0f} per lokasi), sekitar {calls / 10000:.1f} hari pada batas 10.000/hari")
    print(f"{len({row['province_id'] for row in rows})} dari 34 provinsi punya titik sentra")
    if suspicious:
        print("PERIKSA geocoding (nama provinsi tidak muncul di hasil):", suspicious)


def weather_file_name(latitude, longitude):
    """Nama file per koordinat anchor; kabupaten yang digabung dan dua komoditas berbagi satu file."""
    return f"{float(latitude):.4f}_{float(longitude):.4f}.json"


def get_archive(session, params):
    """GET arsip Open-Meteo dengan penanganan batas. Mengembalikan None kalau batas harian tercapai."""
    for _ in range(6):
        response = session.get(ARCHIVE_URL, params=params, timeout=120)
        if response.status_code == 200:
            return response
        if response.status_code != 429:
            response.raise_for_status()
        reason = response.json().get("reason", "")
        if "Minutely" in reason:
            time.sleep(65)
        elif "Hourly" in reason:
            print("  batas per jam tercapai; menunggu satu jam")
            time.sleep(3630)
        else:  # batas harian
            return None
    return None


def fetch_weather(refresh):
    with open(POINTS_CSV, newline="", encoding="utf-8") as handle:
        points = list(csv.DictReader(handle))
    session = new_session()
    end_date = (EXTRACTION_DATE - timedelta(days=END_LAG_DAYS)).isoformat()

    # satu anchor satu request, urut dari kabupaten berproduksi terbesar (CSV sudah terurut)
    locations = {}
    for point in points:
        locations.setdefault(point["anchor_id"], (point["anchor_latitude"], point["anchor_longitude"], point["regency_name"]))

    done = 0
    for number, (latitude, longitude, name) in enumerate(locations.values(), start=1):
        path = target_path(OUT / weather_file_name(latitude, longitude), refresh)
        if path is None:
            continue
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": START_DATE,
            "end_date": end_date,
            "daily": "precipitation_sum,relative_humidity_2m_mean",
            "timezone": "Asia/Jakarta",
        }
        response = get_archive(session, params)
        if response is None:
            print(f"berhenti di lokasi {number}/{len(locations)} ({name}): batas harian API tercapai")
            print("jalankan ulang besok; lokasi yang sudah ada dilewati")
            break
        days = len(response.json()["daily"]["time"])
        save_raw(path, response.content, "open_meteo", {"url": ARCHIVE_URL, "params": params, "regency": name}, n_rows=days)
        done += 1
        print(f"[{number}/{len(locations)}] {name}: {days} hari")
        time.sleep(REQUEST_PAUSE)
    remaining = sum(1 for lat, lon, _ in locations.values() if target_path(OUT / weather_file_name(lat, lon)) is not None)
    print(f"selesai: {done} lokasi ditarik, {remaining} belum")


def main():
    parser = argparse.ArgumentParser(description="Extract cuaca Open-Meteo untuk kabupaten sentra")
    parser.add_argument("--only", choices=["points", "weather"])
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    if args.only in (None, "points"):
        build_points()
    if args.only in (None, "weather"):
        fetch_weather(args.refresh)


if __name__ == "__main__":
    main()
