"""Audit data cuaca Open-Meteo (paket cuaca, D-56).

Yang diperiksa:
- setiap lokasi cuaca (anchor_id di sentra_points.csv) punya file raw yang valid;
- kelengkapan harian 1991-01-01 sampai tanggal akhir file, per variabel (hari kosong);
- nilai yang tidak masuk akal: hujan negatif, kelembapan di luar 0-100, hujan harian > 300 mm (ditandai, tidak diubah);
- kelengkapan per provinsi x bulan (porsi lokasi-hari terisi) untuk 2018-2026, sebagai heatmap tabel;
- file cuaca di raw yang tidak dipakai lagi (misalnya lokasi Sentul yang salah, D-51).

Output: pipeline/audit/reports/weather_audit.md dan weather_locations.csv.
"""
import json

import numpy as np
import pandas as pd

from pipeline.audit.loaders import REPORTS, to_markdown, write_report
from pipeline.extract.common import is_valid
from pipeline.extract.open_meteo import weather_file_name
from pipeline.readers import RAW, ROOT

DAILY = RAW / "open_meteo" / "daily"
EXTREME_RAIN_MM = 300


def load_location(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    frame = pd.DataFrame(data["daily"])
    frame["time"] = pd.to_datetime(frame["time"])
    return frame, data


def run():
    points = pd.read_csv(ROOT / "data" / "interim" / "sentra_points.csv")
    anchors = points.drop_duplicates("anchor_id")
    provinces = pd.read_csv(ROOT / "data" / "final" / "dim_province.csv").set_index("province_id")["province_name"]

    rows, monthly = [], []
    for anchor in anchors.itertuples():
        path = DAILY / weather_file_name(anchor.anchor_latitude, anchor.anchor_longitude)
        valid = is_valid(path)
        row = {"anchor_id": anchor.anchor_id, "kabupaten": anchor.regency_name, "province_id": anchor.province_id, "file": path.name, "valid": valid}
        if valid:
            frame, data = load_location(path)
            rain, humidity = frame["precipitation_sum"], frame["relative_humidity_2m_mean"]
            expected = pd.date_range("1991-01-01", frame["time"].max(), freq="D")
            row.update({
                "awal": frame["time"].min().date(), "akhir": frame["time"].max().date(), "hari": len(frame), "hari_seharusnya": len(expected),
                "hujan_kosong": int(rain.isna().sum()), "kelembapan_kosong": int(humidity.isna().sum()),
                "hujan_negatif": int((rain < 0).sum()), "kelembapan_di_luar_0_100": int(((humidity < 0) | (humidity > 100)).sum()),
                f"hujan_lebih_{EXTREME_RAIN_MM}mm": int((rain > EXTREME_RAIN_MM).sum()), "hujan_harian_maks": float(rain.max()),
                "grid_lat": data["latitude"], "grid_lon": data["longitude"], "elevasi_m": data["elevation"],
                "extraction_date": json.loads(path.with_name(path.name + ".meta.json").read_text(encoding="utf-8"))["extraction_date"],
            })
            recent = frame[frame["time"] >= "2018-01-01"].copy()
            recent["month"] = recent["time"].dt.to_period("M")
            filled = recent.groupby("month")[["precipitation_sum", "relative_humidity_2m_mean"]].count().min(axis=1)
            monthly.append(pd.DataFrame({"anchor_id": anchor.anchor_id, "month": filled.index, "hari_terisi": filled.to_numpy(),
                                         "hari_bulan": [m.days_in_month for m in filled.index]}))
        rows.append(row)
    locations = pd.DataFrame(rows)
    REPORTS.mkdir(parents=True, exist_ok=True)
    locations.to_csv(REPORTS / "weather_locations.csv", index=False)

    used = {weather_file_name(a.anchor_latitude, a.anchor_longitude) for a in anchors.itertuples()}
    unused = sorted(p.name for p in DAILY.glob("*.json") if not p.name.endswith(".meta.json") and p.name not in used)

    # kelengkapan provinsi x bulan: porsi lokasi-hari terisi dari semua lokasi yang melayani provinsi itu
    coverage = pd.concat(monthly) if monthly else pd.DataFrame()
    province_of = points[["anchor_id", "province_id"]].drop_duplicates()
    coverage = coverage.merge(province_of, on="anchor_id")
    by_province = coverage.groupby(["province_id", "month"])[["hari_terisi", "hari_bulan"]].sum()
    by_province["pct"] = by_province["hari_terisi"] / by_province["hari_bulan"] * 100
    by_province = by_province.reset_index()
    by_province["year"] = by_province["month"].dt.year
    year_table = by_province.groupby(["province_id", "year"])["pct"].mean().unstack("year").round(1)
    year_table.index = pd.Index([provinces[i] for i in year_table.index], name="provinsi")

    valid_count = int(locations["valid"].sum())
    ok = locations[locations["valid"]]
    problems = ok[(ok["hujan_kosong"] > 0) | (ok["kelembapan_kosong"] > 0) | (ok["hujan_negatif"] > 0) | (ok["kelembapan_di_luar_0_100"] > 0)]
    lines = ["# Audit cuaca (Open-Meteo)", "",
             f"Lokasi cuaca (anchor) di `sentra_points.csv`: {len(anchors)}; file valid: {valid_count}; belum ada atau tidak valid: {len(anchors) - valid_count}. "
             f"Provinsi bertitik sentra: {points['province_id'].nunique()} (cabai merah {points[points.commodity_group == 'cabai_merah'].province_id.nunique()}, cabai rawit {points[points.commodity_group == 'cabai_rawit'].province_id.nunique()}).", "",
             *([f"Belum ada atau tidak valid: {', '.join(locations.loc[~locations['valid'], 'kabupaten'])}.", ""] if valid_count < len(anchors) else []),
             "## 1. Kelengkapan dan nilai per lokasi", "",
             f"- Rentang data: mulai {ok['awal'].min()}; tanggal akhir {ok['akhir'].min()} s/d {ok['akhir'].max()} (bergantung tanggal extraction; arsip tertinggal sekitar 5 hari).",
             f"- Hari kosong: hujan {int(ok['hujan_kosong'].sum())}, kelembapan {int(ok['kelembapan_kosong'].sum())} dari {int(ok['hari'].sum()):,} lokasi-hari.",
             f"- Hari tidak sesuai rentang (hari < hari seharusnya): {int((ok['hari'] < ok['hari_seharusnya']).sum())} lokasi.",
             f"- Hujan negatif: {int(ok['hujan_negatif'].sum())}; kelembapan di luar 0-100: {int(ok['kelembapan_di_luar_0_100'].sum())}.",
             f"- Hujan harian > {EXTREME_RAIN_MM} mm (ditandai, tidak diubah): {int(ok[f'hujan_lebih_{EXTREME_RAIN_MM}mm'].sum())} lokasi-hari; maksimum {ok['hujan_harian_maks'].max():.1f} mm di {ok.loc[ok['hujan_harian_maks'].idxmax(), 'kabupaten']}. Hujan harian di atas 300 mm jarang tetapi mungkin di Indonesia, jadi tidak dianggap error.",
             f"- Lokasi dengan masalah di atas: {len(problems)}.", "",
             "Rincian per lokasi ada di `weather_locations.csv`.", "",
             "## 2. File raw yang tidak dipakai", "",
             (", ".join(f"`{name}`" for name in unused) + "." if unused else "Tidak ada.") +
             (" Ini lokasi Sentul (-6,49; 106,88) hasil geocoding salah untuk Kab. Karang Asem; tetap di raw, tidak dipakai (D-51)." if "-6.4912_106.8793.json" in unused else ""), "",
             "## 3. Kelengkapan per provinsi x tahun (persen lokasi-hari terisi, 2018-2026)", "",
             "Provinsi tanpa titik sentra tidak muncul (cuaca `not_applicable`, D-25). Tahun 2026 di bawah 100% hanya karena November 2026 baru terisi sampai tanggal akhir file (bulan parsial).", "",
             to_markdown(year_table, index=True, floatfmt="{:.1f}"), ""]
    write_report("weather_audit.md", "\n".join(lines))
    print(f"lokasi valid {valid_count}/{len(anchors)}; file tidak dipakai: {unused}")
    return locations
