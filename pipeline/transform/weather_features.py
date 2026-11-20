"""Cuaca bulanan per provinsi x komoditas dari titik sentra Open-Meteo (D-19, D-24, D-25, D-57).

Langkah:
1. Per lokasi (anchor): hujan bulanan = jumlah harian, kelembapan = rata-rata harian. Bulan yang tidak lengkap harinya
   dibiarkan kosong.
2. Per provinsi x komoditas: rata-rata berbobot produksi dari kabupaten sentra di provinsi itu (bobot =
   produksi rata-rata 2019-2025; tiap kabupaten memakai cuaca anchor-nya). Seri 1991 sampai sekarang.
3. Normal = rata-rata bulan kalender 1991-2020 (WMO climate normal) dari seri provinsi tersebut.
   rain_anomaly_mm = hujan - normal; rain_anomaly = anomali terstandar (dibagi simpangan baku 1991-2020 bulan kalender
   yang sama), sehingga 1 = satu SD lebih basah dari normal.
4. Provinsi x komoditas tanpa titik sentra: weather_status = not_applicable, nilai NULL (bukan missing, tidak di-impute).
   November 2026 (bulan parsial, arsip tertinggal beberapa hari): weather_status = partial_month, nilai NULL.

Output data/interim/fact_weather_monthly.parquet (2018-01 sampai 2026-11) dan weather_monthly_full.parquet (1991-2026,
untuk analisis yang butuh seri panjang).
"""
import json

import numpy as np
import pandas as pd

from pipeline.extract.open_meteo import weather_file_name
from pipeline.readers import FIRST_MONTH, LAST_MONTH, RAW, ROOT, load_pihps_provinces, months

INTERIM = ROOT / "data" / "interim"
DAILY = RAW / "open_meteo" / "daily"
NORMAL_START, NORMAL_END = pd.Period("1991-01", "M"), pd.Period("2020-12", "M")
GROUPS = ["cabai_merah", "cabai_rawit"]


def anchor_monthly(latitude, longitude):
    path = DAILY / weather_file_name(latitude, longitude)
    data = json.loads(path.read_text(encoding="utf-8"))
    extract_date = json.loads(path.with_name(path.name + ".meta.json").read_text(encoding="utf-8"))["extraction_date"]
    daily = pd.DataFrame(data["daily"])
    daily["month"] = pd.PeriodIndex(daily["time"], freq="M")
    grouped = daily.groupby("month").agg(
        rain=("precipitation_sum", lambda s: s.sum() if s.notna().all() else np.nan),
        humidity=("relative_humidity_2m_mean", "mean"),
        days=("time", "size"),
    )
    complete = grouped["days"] == [m.days_in_month for m in grouped.index]
    grouped.loc[~complete, ["rain", "humidity"]] = np.nan
    return grouped[["rain", "humidity"]], extract_date


def province_series(points):
    """Seri bulanan berbobot produksi per provinsi x komoditas, 1991 sampai bulan terakhir."""
    cache, extract_dates, rows = {}, {}, []
    for (province, group), part in points.groupby(["province_id", "commodity_group"]):
        weights, frames = [], []
        for item in part.itertuples():
            key = (item.anchor_latitude, item.anchor_longitude)
            if key not in cache:
                cache[key], extract_dates[key] = anchor_monthly(*key)
            frames.append(cache[key])
            weights.append(item.mean_production_ton_2019_2025)
        weights = np.array(weights) / np.sum(weights)
        rain = sum(w * f["rain"] for w, f in zip(weights, frames))
        humidity = sum(w * f["humidity"] for w, f in zip(weights, frames))
        frame = pd.DataFrame({"rain_total_mm": rain, "rel_humidity_mean": humidity})
        frame["province_id"], frame["commodity_group"] = province, group
        frame["n_points"] = len(part)
        frame["source_extract_date"] = max(extract_dates[(i.anchor_latitude, i.anchor_longitude)] for i in part.itertuples())
        rows.append(frame.rename_axis("month").reset_index())
    return pd.concat(rows, ignore_index=True)


def add_anomalies(series):
    series = series.copy()
    series["moy"] = series["month"].dt.month
    base = series[(series["month"] >= NORMAL_START) & (series["month"] <= NORMAL_END)]
    normals = base.groupby(["province_id", "commodity_group", "moy"])["rain_total_mm"].agg(rain_normal_mm="mean", rain_sd_mm="std").reset_index()
    series = series.merge(normals, on=["province_id", "commodity_group", "moy"], how="left")
    series["rain_anomaly_mm"] = series["rain_total_mm"] - series["rain_normal_mm"]
    series["rain_anomaly"] = series["rain_anomaly_mm"] / series["rain_sd_mm"]
    return series.drop(columns="moy")


def core_grid(series):
    """34 provinsi x 2 grup x Jan 2018 - Nov 2026, dengan weather_status."""
    grid = pd.MultiIndex.from_product([sorted(load_pihps_provinces().values()), GROUPS, months(FIRST_MONTH, LAST_MONTH)],
                                      names=["province_id", "commodity_group", "month"]).to_frame(index=False)
    merged = grid.merge(series, on=["province_id", "commodity_group", "month"], how="left")
    has_points = merged["n_points"].notna()
    merged["weather_status"] = np.where(has_points, "observed", "not_applicable")
    partial = has_points & (merged["month"] == LAST_MONTH)
    merged.loc[partial, "weather_status"] = "partial_month"
    value_columns = ["rain_total_mm", "rain_normal_mm", "rain_sd_mm", "rain_anomaly_mm", "rain_anomaly", "rel_humidity_mean"]
    merged.loc[partial, value_columns] = np.nan
    merged["n_points"] = merged["n_points"].fillna(0).astype(int)
    return merged


def run():
    points = pd.read_csv(INTERIM / "sentra_points.csv")
    series = add_anomalies(province_series(points))
    fact = core_grid(series)
    INTERIM.mkdir(parents=True, exist_ok=True)
    series.assign(month=series["month"].astype(str)).to_parquet(INTERIM / "weather_monthly_full.parquet", index=False)
    fact.assign(month=fact["month"].astype(str)).to_parquet(INTERIM / "fact_weather_monthly.parquet", index=False)
    observed = fact[fact["weather_status"] == "observed"]
    print(f"fact_weather_monthly: {len(fact):,} baris; observed {len(observed):,} (kosong {int(observed['rain_total_mm'].isna().sum())}); "
          f"status {fact['weather_status'].value_counts().to_dict()}")
    return fact


if __name__ == "__main__":
    run()
