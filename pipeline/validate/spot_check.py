"""Spot-check angka acak di core dataset terhadap sumbernya (seed tetap, bisa diulang).

1. Harga: 30 sel harga observed (bukan imputed) dihitung ulang langsung dari file raw harian dengan kode terpisah
   dari transform; 10 di antaranya juga ditarik ulang dari PIHPS live untuk mendeteksi revisi sumber.
2. Produksi: 10 provinsi-tahun di core_province_year dihitung ulang dari HTML raw BDSP; tabel provinsi BDSP untuk
   cabe besar dan cabe rawit ditarik ulang live (request yang sama dengan metadata raw).
3. ONI: 5 bulan acak dibanding file ONI live dari NOAA.
Hasil live tidak disimpan ke data/raw (raw tetap snapshot tanggal extraction).
"""
import json
import time
from datetime import date

import numpy as np
import pandas as pd
from bs4 import BeautifulSoup

from pipeline.extract.common import new_session, request_with_retry
from pipeline.provinces import BPS_TO_PIHPS
from pipeline.readers import RAW, ROOT, load_pihps_provinces

FINAL = ROOT / "data" / "final"
SEED = 2026
PRICE_TYPE_OF = {"price_retail": 1, "price_wholesale": 3, "price_producer": 4}
COMMODITY_OF = {"cabai_merah": "cat_7", "cabai_rawit": "cat_8"}
PIHPS_GRID = "https://www.bi.go.id/hargapangan/WebSite/TabelHarga/GetGridDataKomoditas"
ONI_URL = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"
SEASONS = ["DJF", "JFM", "FMA", "MAM", "AMJ", "MJJ", "JJA", "JAS", "ASO", "SON", "OND", "NDJ"]


def to_rupiah(text):
    return None if text in (None, "-", "") else float(text.replace(",", ""))


def month_mean_from_rows(rows, province_name, month_start):
    """Rata-rata harian satu provinsi pada satu bulan, dibaca langsung dari baris respons PIHPS."""
    row = next(r for r in rows if r["name"] == province_name)
    prefix = month_start.strftime("/%m/%Y")
    values = [to_rupiah(v) for k, v in row.items() if k.endswith(prefix) and len(k) == 10]
    values = [v for v in values if v is not None]
    return (float(np.mean(values)) if values else None), len(values)


def raw_daily_file(price_type, commodity, month_start):
    quarter_start = date(month_start.year, (month_start.month - 1) // 3 * 3 + 1, 1)
    matches = sorted((RAW / "pihps" / "daily").glob(f"pt{price_type}_{commodity}_{quarter_start:%Y%m%d}_*.json"))
    return [m for m in matches if not m.name.endswith(".meta.json")][0]


def sample_prices(core, n=30):
    cells = []
    model = core[core["in_model_period"]]
    for column in PRICE_TYPE_OF:
        part = model[model[column].notna() & (model[f"{column}_is_imputed"] != True)]
        cells.append(part[["province_id", "commodity_group", "month_start", column]].rename(columns={column: "core_value"}).assign(variable=column))
    pool = pd.concat(cells, ignore_index=True)
    return pool.sample(n=n, random_state=SEED).reset_index(drop=True)


def check_prices(core, live_count=10):
    names = {v: k for k, v in load_pihps_provinces().items()}
    sample = sample_prices(core)
    session = new_session()
    rows = []
    for index, cell in sample.iterrows():
        month_start = pd.Timestamp(cell["month_start"]).date()
        price_type, commodity = PRICE_TYPE_OF[cell["variable"]], COMMODITY_OF[cell["commodity_group"]]
        raw_rows = json.loads(raw_daily_file(price_type, commodity, month_start).read_text(encoding="utf-8"))["data"]
        raw_value, raw_days = month_mean_from_rows(raw_rows, names[cell["province_id"]], month_start)
        live_value = live_days = None
        if index < live_count:
            month_end = (pd.Timestamp(month_start) + pd.offsets.MonthEnd(0)).date()
            params = {"price_type_id": price_type, "comcat_id": commodity, "province_id": "", "regency_id": "", "showKota": "false",
                      "showPasar": "false", "tipe_laporan": 1, "start_date": month_start.isoformat(), "end_date": month_end.isoformat()}
            live_rows = request_with_retry(session, "GET", PIHPS_GRID, params=params).json()["data"]
            live_value, live_days = month_mean_from_rows(live_rows, names[cell["province_id"]], month_start)
            time.sleep(1.5)
        rows.append({"variabel": cell["variable"], "grup": cell["commodity_group"], "province_id": cell["province_id"], "bulan": str(month_start)[:7],
                     "core": cell["core_value"], "raw": raw_value, "hari_raw": raw_days, "live": live_value, "hari_live": live_days})
    result = pd.DataFrame(rows)
    result["raw_cocok"] = (result["core"] - result["raw"]).abs() < 0.01
    result["live_selisih_pct"] = (result["live"] - result["core"]).abs() / result["core"] * 100
    return result


def bdsp_parent_values(html, factor=1.0):
    soup = BeautifulSoup(html, "lxml")
    out = {}
    for tr in soup.find_all("tr"):
        cells = [c.get_text(strip=True) for c in tr.find_all(["th", "td"])]
        if len(cells) >= 10 and " - " in cells[1] and cells[1][:2].isdigit():
            parent = BPS_TO_PIHPS[cells[1].split(" - ")[0]][0]
            for year, value in zip(range(2018, 2026), cells[2:10]):
                out[(parent, year)] = out.get((parent, year), 0.0) + float(value.replace(".", "").replace(",", ".")) * factor
    return out


def check_production(n=10):
    year = pd.read_csv(FINAL / "core_province_year.csv")
    sample = year[year["year"] <= 2025].sample(n=n, random_state=SEED)
    session = new_session()
    session.get("https://bdsp2.pertanian.go.id/bdsp/id/lokasi", timeout=60)
    rows = []
    for group, commodity in (("cabai_merah", "cabe_besar"), ("cabai_rawit", "cabe_rawit")):
        path = RAW / "bdsp" / "provinsi" / f"{commodity}_produksi.html"
        raw = bdsp_parent_values(path.read_text(encoding="utf-8"))
        request = json.loads(path.with_name(path.name + ".meta.json").read_text(encoding="utf-8"))["request"]
        live_html = request_with_retry(session, "POST", request["url"], data=request["body"], timeout=180).text
        live = bdsp_parent_values(live_html)
        for _, cell in sample[sample["commodity_group"] == group].iterrows():
            key = (cell["province_id"], cell["year"])
            rows.append({"grup": group, "province_id": cell["province_id"], "tahun": cell["year"], "core": cell["production_ton"], "raw": raw.get(key), "live": live.get(key)})
        time.sleep(1)
    result = pd.DataFrame(rows)
    result["raw_cocok"] = (result["core"] - result["raw"]).abs() < 0.01
    result["live_cocok"] = (result["core"] - result["live"]).abs() < 0.01
    return result


def check_oni(n=5):
    core = pd.read_csv(FINAL / "core_province_month.csv").dropna(subset=["oni_anomaly"]).drop_duplicates("month_start")
    sample = core.sample(n=n, random_state=SEED)
    text = request_with_retry(new_session(), "GET", ONI_URL).text
    live = {}
    for line in text.strip().splitlines()[1:]:
        season, year, _, anomaly = line.split()
        live[(int(year), SEASONS.index(season) + 1)] = float(anomaly)
    rows = []
    for _, cell in sample.iterrows():
        month = pd.Timestamp(cell["month_start"])
        rows.append({"bulan": cell["month_start"][:7], "core": cell["oni_anomaly"], "live": live.get((month.year, month.month))})
    result = pd.DataFrame(rows)
    result["cocok"] = (result["core"] - result["live"]).abs() < 1e-9
    return result


def run():
    core = pd.read_csv(FINAL / "core_province_month.csv")
    return {"prices": check_prices(core), "production": check_production(), "oni": check_oni()}


if __name__ == "__main__":
    out = run()
    for name, frame in out.items():
        print(f"== {name}")
        print(frame.round(2).to_string(index=False))
