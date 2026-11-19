"""Produksi cabai: tahunan BDSP per provinsi (34 provinsi PIHPS) dan bulanan nasional dari Buletin.

Disagregasi bulanan per provinsi (Denton) dibatalkan (D-42): core dataset memakai angka tahunan BDSP untuk ke-12
bulan dalam tahunnya (`production_annual_ton`). Hasil hold-out Denton tetap terdokumentasi di
pipeline/validate/holdout_production.py dan transform_report.md.

Definisi (D-28): cabai_merah = cabe besar BDSP saja; cabe keriting disimpan terpisah sebagai cabai_keriting
(referensi, tidak masuk core). Provinsi pemekaran Papua dijumlahkan ke induknya (D-17, D-36).

Output di data/interim/:
  fact_production_annual.parquet            provinsi x tahun x grup, produksi (ton), luas panen (ha), flag
  fact_production_national_monthly.parquet  produksi bulanan nasional, hanya bulan realisasi SPH-BPS
Produksi 2026 tidak di-extrapolate: angka tahunan BDSP 2026 belum ada.
"""
import numpy as np
import pandas as pd

from pipeline.readers import RAW, ROOT, YEARS, load_pihps_provinces, load_province_tables, read_prognosa
from pipeline.rules import YIELD_MAX, YIELD_MIN

OUT = ROOT / "data" / "interim"
GROUP_OF = {"cabe_besar": "cabai_merah", "cabe_rawit": "cabai_rawit", "cabe_keriting": "cabai_keriting"}
BULLETIN_COMMODITY = {"cabai_merah": "besar", "cabai_rawit": "rawit"}  # tabel prognosa "Cabai Besar" dan "Cabai Rawit"
MONTHLY_GROUPS = ["cabai_merah", "cabai_rawit"]


def annual_production():
    frame, _ = load_province_tables()
    frame["commodity_group"] = frame["commodity"].map(GROUP_OF)
    parent = frame.groupby(["province_id", "year", "commodity_group", "indicator"])["value"].sum().unstack("indicator").reset_index()
    parent = parent.rename(columns={"produksi": "production_ton", "luas_panen": "harvested_area_ha"})

    province_ids = sorted(load_pihps_provinces().values())
    grid = pd.MultiIndex.from_product([province_ids, YEARS, list(GROUP_OF.values())], names=["province_id", "year", "commodity_group"])
    parent = parent.set_index(["province_id", "year", "commodity_group"]).reindex(grid).reset_index()

    yield_ton_per_ha = parent["production_ton"] / parent["harvested_area_ha"].replace(0, np.nan)
    parent["is_preliminary"] = parent["year"] == YEARS[-1]
    parent["is_outlier"] = (parent["production_ton"] > 0) & ~yield_ton_per_ha.between(YIELD_MIN, YIELD_MAX)

    flags_path = RAW / "bdsp" / "flags" / "suspect_copy.csv"
    parent["suspect_copy"] = False
    if flags_path.exists():
        flags = pd.read_csv(flags_path)
        flagged = set(zip(flags["province_id"], flags["year"]))
        is_keriting = parent["commodity_group"] == "cabai_keriting"
        parent.loc[is_keriting, "suspect_copy"] = [(p, y) in flagged for p, y in zip(parent.loc[is_keriting, "province_id"], parent.loc[is_keriting, "year"])]
    return parent


def prognosa_tables():
    """{(grup, tahun_edisi): array 12 bulan produksi (ton)} dan {(grup, tahun_edisi): jumlah bulan realisasi}."""
    _, rows, _ = read_prognosa()
    table = pd.DataFrame(rows)
    values, realised = {}, {}
    for (commodity, year), part in table.groupby(["commodity", "edition_year"]):
        group = {"besar": "cabai_merah", "rawit": "cabai_rawit"}[commodity]
        part = part.sort_values("month")
        values[(group, year)] = part["production_ton"].to_numpy(dtype=float)
        realised[(group, year)] = part[part["status"] == "realisasi"]["month"].to_numpy()
    return table, values, realised


def national_monthly(table):
    """Produksi bulanan nasional: hanya bulan realisasi SPH-BPS; proyeksi dan bulan tanpa tabel = missing."""
    rows = []
    for group in MONTHLY_GROUPS:
        commodity = BULLETIN_COMMODITY[group]
        for month in pd.period_range("2018-01", "2026-11", freq="M"):
            part = table[(table["commodity"] == commodity) & (table["edition_year"] == month.year) & (table["month"] == month.month)]
            if len(part) and part["status"].iloc[0] == "realisasi":
                rows.append((month.to_timestamp().date(), group, part["production_ton"].iloc[0], "realisasi", int(part["publication_id"].iloc[0])))
            else:
                rows.append((month.to_timestamp().date(), group, np.nan, "missing", np.nan))
    return pd.DataFrame(rows, columns=["month_start", "commodity_group", "production_ton", "status", "bulletin_publication_id"])


def run():
    annual = annual_production()
    table, _, _ = prognosa_tables()
    national = national_monthly(table)

    OUT.mkdir(parents=True, exist_ok=True)
    annual.to_parquet(OUT / "fact_production_annual.parquet", index=False)
    national.to_parquet(OUT / "fact_production_national_monthly.parquet", index=False)
    stale = OUT / "fact_production_monthly.parquet"  # keluaran Denton lama (D-42)
    if stale.exists():
        stale.unlink()
    print(f"annual {len(annual):,} baris | national realisasi: {(national['status'] == 'realisasi').sum()} bulan")
    return annual, national


if __name__ == "__main__":
    run()
