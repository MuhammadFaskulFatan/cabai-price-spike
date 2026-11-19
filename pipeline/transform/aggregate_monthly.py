"""Harga harian PIHPS menjadi harga bulanan (rata-rata hari kerja terisi, minimal 10 hari).

Output data/interim/price_monthly_observed.parquet: satu baris per tipe harga x komoditas x provinsi x bulan,
termasuk seri yang tidak muncul di respons (nol hari). province_id 0 = baris nasional ("Semua Provinsi").
Baris provinsi yang namanya tidak ada di referensi 34 provinsi ("Dum", D-34) dibuang.
"""
import pandas as pd

from pipeline.readers import (
    COMMODITY_LABELS,
    PRICE_TYPE_LABELS,
    ROOT,
    load_pihps_grid,
    load_pihps_provinces,
    months,
    weekdays_per_month,
)
from pipeline.rules import MIN_VALID_DAYS

OUT = ROOT / "data" / "interim"
NATIONAL_ID = 0


def build_monthly_observed():
    province_ids = load_pihps_provinces()
    daily = load_pihps_grid("daily")
    daily = daily[(daily["level"] == 0) | daily["province"].isin(province_ids)].copy()
    daily["province_id"] = daily["province"].map(province_ids).fillna(NATIONAL_ID).astype(int)
    daily["month"] = pd.PeriodIndex(pd.to_datetime(daily["date"]), freq="M")

    grouped = daily.groupby(["price_type_id", "commodity_id", "province_id", "month"])["price"].agg(n_days_observed="count", price_mean="mean")
    full_index = pd.MultiIndex.from_product(
        [sorted(PRICE_TYPE_LABELS), list(COMMODITY_LABELS), [NATIONAL_ID] + sorted(province_ids.values()), months()],
        names=["price_type_id", "commodity_id", "province_id", "month"],
    )
    monthly = grouped.reindex(full_index).reset_index()
    monthly["n_days_observed"] = monthly["n_days_observed"].fillna(0).astype(int)
    monthly["n_weekdays"] = monthly["month"].map(weekdays_per_month()).astype(int)
    monthly["price_observed"] = monthly["price_mean"].where(monthly["n_days_observed"] >= MIN_VALID_DAYS)
    return monthly.drop(columns="price_mean")


def run():
    monthly = build_monthly_observed()
    OUT.mkdir(parents=True, exist_ok=True)
    stored = monthly.assign(month=monthly["month"].astype(str))
    stored.to_parquet(OUT / "price_monthly_observed.parquet", index=False)
    valid = int(monthly["price_observed"].notna().sum())
    print(f"price_monthly_observed: {len(monthly):,} baris, {valid:,} bulan valid (>= {MIN_VALID_DAYS} hari kerja)")
    return monthly


if __name__ == "__main__":
    run()
