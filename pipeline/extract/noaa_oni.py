"""Extract Oceanic Nino Index (ONI) dari NOAA CPC.

Satu file teks apa adanya: kolom SEAS, YR, TOTAL, ANOM.
Pemetaan season ke bulan tengah (DJF -> Januari) dilakukan di fase transform.
Jalankan:  python -m pipeline.extract.noaa_oni [--refresh]
"""
import argparse

from pipeline.extract.common import RAW_DIR, new_session, request_with_retry, save_raw, target_path

URL = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"


def main():
    parser = argparse.ArgumentParser(description="Extract NOAA ONI ke data/raw/noaa_oni")
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()

    path = target_path(RAW_DIR / "noaa_oni" / "oni.ascii.txt", args.refresh)
    if path is None:
        print("oni.ascii.txt sudah ada")
        return
    response = request_with_retry(new_session(), "GET", URL)
    n_rows = len(response.text.strip().splitlines()) - 1  # tanpa baris header
    save_raw(path, response.content, "noaa_oni", {"url": URL}, n_rows=n_rows)
    last = response.text.strip().splitlines()[-1].split()
    print(f"{n_rows} baris; season terakhir: {last[0]} {last[1]}")


if __name__ == "__main__":
    main()
