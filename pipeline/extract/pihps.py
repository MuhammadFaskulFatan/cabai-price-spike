"""Extract harga cabai dari PIHPS Nasional (Bank Indonesia).

Yang ditarik ke data/raw/pihps/:
  daily/    harian per kuartal, tipe harga 1/3/4, dua grup (cat_7, cat_8) dan empat varian
  weekly/   mingguan (label tanggal) per tahun, hanya dua grup, untuk lead-lag
  monthly/  angka bulanan PIHPS (tipe_laporan=3), hanya untuk cross-check (D-18)
  ref/      daftar provinsi, tipe harga, dan komoditas

Request dijalankan berurutan dengan jeda; PIHPS sering timeout kalau diburu.
Jalankan:  python -m pipeline.extract.pihps [--only daily|weekly|monthly|ref] [--refresh]
"""
import argparse
import json
import time
from datetime import date, timedelta

from pipeline.extract.common import (
    EXTRACTION_DATE,
    RAW_DIR,
    new_session,
    request_with_retry,
    save_raw,
    target_path,
)

BASE = "https://www.bi.go.id/hargapangan/WebSite/TabelHarga/"
OUT = RAW_DIR / "pihps"

START_DATE = date(2018, 1, 1)  # 2018 hanya untuk lagged variables
PAUSE_SECONDS = 1.5

# Pasar modern (tipe 2) sengaja tidak ditarik, lihat D-11
PRICE_TYPES = {1: "eceran", 3: "pedagang_besar", 4: "produsen"}

CORE_COMMODITIES = {"cat_7": "cabai_merah", "cat_8": "cabai_rawit"}
VARIANTS = {
    "com_13": "merah_besar",
    "com_14": "merah_keriting",
    "com_16": "rawit_merah",
    "com_15": "rawit_hijau",
}

REPORT_TYPES = {"daily": 1, "weekly": 4, "monthly": 3}


def quarters(first_day, last_day):
    """Pecah rentang jadi potongan per kuartal kalender; potongan terakhir berhenti di last_day."""
    year, quarter = first_day.year, (first_day.month - 1) // 3
    while True:
        q_start = date(year, quarter * 3 + 1, 1)
        if q_start > last_day:
            return
        next_start = date(year + (quarter == 3), (quarter + 1) % 4 * 3 + 1, 1)
        yield q_start, min(next_start - timedelta(days=1), last_day)
        year, quarter = next_start.year, (next_start.month - 1) // 3


def years(first_day, last_day):
    for year in range(first_day.year, last_day.year + 1):
        yield date(year, 1, 1), min(date(year, 12, 31), last_day)


def build_jobs(only):
    jobs = []
    if only in (None, "daily"):
        commodities = {**CORE_COMMODITIES, **VARIANTS}
        for q_start, q_end in quarters(START_DATE, EXTRACTION_DATE):
            for price_type in PRICE_TYPES:
                for comcat in commodities:
                    jobs.append(("daily", price_type, comcat, q_start, q_end))
    if only in (None, "weekly"):
        for y_start, y_end in years(START_DATE, EXTRACTION_DATE):
            for price_type in PRICE_TYPES:
                for comcat in CORE_COMMODITIES:
                    jobs.append(("weekly", price_type, comcat, y_start, y_end))
    if only in (None, "monthly"):
        for price_type in PRICE_TYPES:
            for comcat in CORE_COMMODITIES:
                jobs.append(("monthly", price_type, comcat, START_DATE, EXTRACTION_DATE))
    return jobs


def extract_reference(session, refresh):
    for endpoint in ("GetRefProvince", "GetRefPriceType", "GetRefCommodityAndCategory"):
        path = target_path(OUT / "ref" / f"{endpoint}.json", refresh)
        if path is None:
            continue
        response = request_with_retry(session, "GET", BASE + endpoint)
        n_rows = len(response.json()["data"])
        save_raw(path, response.content, "pihps", {"url": BASE + endpoint}, n_rows=n_rows)
        print(f"ref {endpoint}: {n_rows} baris")
        time.sleep(PAUSE_SECONDS)


def extract_grid(session, job, refresh):
    report, price_type, comcat, start, end = job
    params = {
        "price_type_id": price_type,
        "comcat_id": comcat,
        "province_id": "",
        "regency_id": "",
        "showKota": "false",
        "showPasar": "false",
        "tipe_laporan": REPORT_TYPES[report],
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
    }
    name = f"pt{price_type}_{comcat}_{start:%Y%m%d}_{end:%Y%m%d}.json"
    path = target_path(OUT / report / name, refresh)
    if path is None:
        return False

    response = request_with_retry(session, "GET", BASE + "GetGridDataKomoditas", params=params)
    rows = response.json()["data"]  # validasi bahwa responsnya JSON dengan kunci "data"
    save_raw(path, response.content, "pihps", {"url": BASE + "GetGridDataKomoditas", "params": params}, n_rows=len(rows))
    if not rows:
        print(f"  peringatan: respons kosong untuk {name}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Extract PIHPS ke data/raw/pihps")
    parser.add_argument("--only", choices=["daily", "weekly", "monthly", "ref"])
    parser.add_argument("--refresh", action="store_true", help="tarik ulang; file lama tidak ditimpa")
    args = parser.parse_args()

    session = new_session()
    if args.only in (None, "ref"):
        extract_reference(session, args.refresh)
    if args.only == "ref":
        return

    jobs = build_jobs(args.only)
    print(f"{len(jobs)} request terjadwal (tanggal extraction {EXTRACTION_DATE})")
    done = skipped = 0
    for number, job in enumerate(jobs, start=1):
        if extract_grid(session, job, args.refresh):
            done += 1
            print(f"[{number}/{len(jobs)}] {job[0]} tipe {job[1]} {job[2]} {job[3]} s/d {job[4]}")
            time.sleep(PAUSE_SECONDS)
        else:
            skipped += 1
    print(f"selesai: {done} ditarik, {skipped} sudah ada")


if __name__ == "__main__":
    main()
