"""Harga mingguan PIHPS untuk analisis lead-lag: dipetakan ke province_id dan disimpan apa adanya, tanpa imputation (D-12).

Output data/interim/fact_price_weekly.parquet. Label kolom PIHPS tipe laporan 4 adalah tanggal awal minggu.
"""
import pandas as pd

from pipeline.readers import ROOT, load_pihps_grid, load_pihps_provinces
from pipeline.transform.aggregate_monthly import NATIONAL_ID

OUT = ROOT / "data" / "interim"


def run():
    province_ids = load_pihps_provinces()
    weekly = load_pihps_grid("weekly")
    weekly = weekly[(weekly["level"] == 0) | weekly["province"].isin(province_ids)].copy()
    weekly["province_id"] = weekly["province"].map(province_ids).fillna(NATIONAL_ID).astype(int)
    weekly = weekly.rename(columns={"date": "week_start", "price": "price_idr_per_kg"})
    weekly = weekly[["price_type_id", "commodity_id", "province_id", "week_start", "price_idr_per_kg"]].sort_values(
        ["price_type_id", "commodity_id", "province_id", "week_start"]
    )
    OUT.mkdir(parents=True, exist_ok=True)
    weekly.to_parquet(OUT / "fact_price_weekly.parquet", index=False)
    print(f"fact_price_weekly: {len(weekly):,} baris, {int(weekly['price_idr_per_kg'].notna().sum()):,} terisi")
    return weekly


if __name__ == "__main__":
    run()
