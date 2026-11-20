"""Cuaca bulanan per provinsi x komoditas dari titik sentra Open-Meteo (D-19, D-24, D-25, D-57, D-58).

Langkah:
1. Per lokasi (anchor): hujan bulanan = jumlah harian, kelembapan = rata-rata harian, plus hujan harian maksimum.
   Bulan yang tidak lengkap harinya dibiarkan kosong.
2. Anomali per lokasi x bulan kalender terhadap baseline 1991-2020 (D-58): z-score dari akar kuadrat hujan bulanan.
   Akar kuadrat membuat sebaran hujan bulanan mendekati normal; tanpa itu bulan kemarau dengan normal hampir nol
   menghasilkan z yang meledak (Situbondo Agustus 2022: 18 mm = +14,7 SD). z-score biasa (tanpa akar) ikut disimpan
   untuk sensitivity. Lokasi-bulan ditandai ekstrem kalau |z| >= 3 atau ada hari dengan hujan > 300 mm.
3. Per provinsi x komoditas: rata-rata berbobot produksi kabupaten sentra (bobot = produksi rata-rata 2019-2025;
   tiap kabupaten memakai cuaca anchor-nya), untuk hujan, kelembapan, dan anomali. rain_is_extreme = TRUE kalau ada
   titik penyumbang yang ditandai ekstrem.
4. rain_anomaly_mm = hujan provinsi dikurangi rata-rata bulan kalender 1991-2020 dari seri provinsi yang sama (D-57).
5. Provinsi x komoditas tanpa titik sentra: weather_status = not_applicable, nilai NULL (bukan missing, tidak di-impute).
   November 2026 (bulan parsial, arsip tertinggal beberapa hari): weather_status = partial_month, nilai NULL.

Output data/interim/fact_weather_monthly.parquet (2018-01 sampai 2026-11), weather_monthly_full.parquet (seri provinsi
1991-2026) dan weather_site_monthly.parquet (seri per lokasi, dipakai audit bulan ekstrem).
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
EXTREME_Z = 3
EXTREME_DAILY_MM = 300
VALUE_COLUMNS = ["rain_total_mm", "rain_normal_mm", "rain_anomaly_mm", "rain_anomaly", "rain_anomaly_plain_z", "rel_humidity_mean"]


def anchor_monthly(latitude, longitude):
    path = DAILY / weather_file_name(latitude, longitude)
    data = json.loads(path.read_text(encoding="utf-8"))
    extract_date = json.loads(path.with_name(path.name + ".meta.json").read_text(encoding="utf-8"))["extraction_date"]
    daily = pd.DataFrame(data["daily"])
    daily["month"] = pd.PeriodIndex(daily["time"], freq="M")
    grouped = daily.groupby("month").agg(
        rain=("precipitation_sum", lambda s: s.sum() if s.notna().all() else np.nan),
        rain_daily_max=("precipitation_sum", "max"),
        humidity=("relative_humidity_2m_mean", "mean"),
        days=("time", "size"),
    )
    complete = grouped["days"] == [m.days_in_month for m in grouped.index]
    grouped.loc[~complete, ["rain", "rain_daily_max", "humidity"]] = np.nan
    return grouped[["rain", "rain_daily_max", "humidity"]], extract_date


def standardise(values, moy, in_base):
    """z-score per bulan kalender terhadap periode baseline."""
    base = values[in_base].groupby(moy[in_base]).agg(["mean", "std"])
    return (values - moy.map(base["mean"])) / moy.map(base["std"])


def site_series(points):
    """Seri bulanan per lokasi cuaca dengan anomali dan flag ekstrem (D-58)."""
    frames, extract_dates = [], {}
    for anchor in points.drop_duplicates("anchor_id").itertuples():
        monthly, extract_dates[anchor.anchor_id] = anchor_monthly(anchor.anchor_latitude, anchor.anchor_longitude)
        monthly = monthly.rename_axis("month").reset_index()
        moy = monthly["month"].dt.month
        in_base = (monthly["month"] >= NORMAL_START) & (monthly["month"] <= NORMAL_END)
        monthly["rain_z"] = standardise(np.sqrt(monthly["rain"]), moy, in_base)
        monthly["rain_z_plain"] = standardise(monthly["rain"], moy, in_base)
        monthly["is_extreme"] = (monthly["rain_z"].abs() >= EXTREME_Z) | (monthly["rain_daily_max"] > EXTREME_DAILY_MM)
        monthly["anchor_id"], monthly["regency_name"] = anchor.anchor_id, anchor.regency_name
        frames.append(monthly)
    sites = pd.concat(frames, ignore_index=True)
    sites["extraction_date"] = sites["anchor_id"].map(extract_dates)
    return sites


def province_series(points, sites):
    """Rata-rata berbobot produksi per provinsi x komoditas, 1991 sampai bulan terakhir."""
    links = points[["province_id", "commodity_group", "anchor_id", "mean_production_ton_2019_2025"]]
    merged = links.merge(sites, on="anchor_id")
    merged["weight"] = merged["mean_production_ton_2019_2025"] / merged.groupby(["province_id", "commodity_group", "month"])["mean_production_ton_2019_2025"].transform("sum")
    weighted = merged[["rain", "humidity", "rain_z", "rain_z_plain"]].mul(merged["weight"], axis=0)
    # NaN di salah satu titik membuat nilai provinsi NaN (min_count = jumlah titik)
    merged = pd.concat([merged[["province_id", "commodity_group", "month", "is_extreme", "extraction_date"]], weighted], axis=1)
    keys = ["province_id", "commodity_group", "month"]
    n_points = merged.groupby(keys).size().rename("n_points")
    sums = merged.groupby(keys)[["rain", "humidity", "rain_z", "rain_z_plain"]].sum(min_count=1)
    complete = merged.groupby(keys)[["rain", "humidity", "rain_z", "rain_z_plain"]].count().eq(n_points, axis=0)
    sums = sums.where(complete)
    series = sums.rename(columns={"rain": "rain_total_mm", "humidity": "rel_humidity_mean", "rain_z": "rain_anomaly", "rain_z_plain": "rain_anomaly_plain_z"})
    series["rain_is_extreme"] = merged.groupby(keys)["is_extreme"].any()
    series["n_points"] = n_points
    series["source_extract_date"] = merged.groupby(keys)["extraction_date"].max()
    return series.reset_index()


def add_anomaly_mm(series):
    series = series.copy()
    series["moy"] = series["month"].dt.month
    base = series[(series["month"] >= NORMAL_START) & (series["month"] <= NORMAL_END)]
    normals = base.groupby(["province_id", "commodity_group", "moy"])["rain_total_mm"].mean().rename("rain_normal_mm").reset_index()
    series = series.merge(normals, on=["province_id", "commodity_group", "moy"], how="left")
    series["rain_anomaly_mm"] = series["rain_total_mm"] - series["rain_normal_mm"]
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
    merged.loc[partial, VALUE_COLUMNS] = np.nan
    merged["rain_is_extreme"] = merged["rain_is_extreme"].astype("boolean")
    merged.loc[merged["weather_status"] != "observed", "rain_is_extreme"] = pd.NA
    merged["n_points"] = merged["n_points"].fillna(0).astype(int)
    return merged


def run():
    points = pd.read_csv(INTERIM / "sentra_points.csv")
    sites = site_series(points)
    series = add_anomaly_mm(province_series(points, sites))
    fact = core_grid(series)
    INTERIM.mkdir(parents=True, exist_ok=True)
    sites.assign(month=sites["month"].astype(str)).to_parquet(INTERIM / "weather_site_monthly.parquet", index=False)
    series.assign(month=series["month"].astype(str)).to_parquet(INTERIM / "weather_monthly_full.parquet", index=False)
    fact.assign(month=fact["month"].astype(str)).to_parquet(INTERIM / "fact_weather_monthly.parquet", index=False)
    observed = fact[fact["weather_status"] == "observed"]
    print(f"fact_weather_monthly: {len(fact):,} baris; observed {len(observed):,} (kosong {int(observed['rain_total_mm'].isna().sum())}); "
          f"ekstrem {int(observed['rain_is_extreme'].sum())}; status {fact['weather_status'].value_counts().to_dict()}")
    return fact


if __name__ == "__main__":
    run()
