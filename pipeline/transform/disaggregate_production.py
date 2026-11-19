"""Produksi cabai: tahunan BDSP per provinsi (34 provinsi PIHPS), bulanan nasional dari Buletin, dan
disagregasi bulanan per provinsi dengan Denton (D-26).

Definisi (D-28): cabai_merah = cabe besar BDSP saja; cabe keriting disimpan terpisah sebagai cabai_keriting
(referensi, tidak masuk core). Provinsi pemekaran Papua dijumlahkan ke induknya (D-17, D-36).

Output di data/interim/:
  fact_production_annual.parquet            provinsi x tahun x grup, produksi (ton), luas panen (ha), flag
  fact_production_national_monthly.parquet  produksi bulanan nasional, hanya bulan realisasi SPH-BPS
  fact_production_monthly.parquet           estimasi Denton per provinsi x bulan (deskriptif saja, flag estimated)
Produksi 2026 tidak di-extrapolate: angka tahunan BDSP 2026 belum ada.
"""
import numpy as np
import pandas as pd

from pipeline.readers import RAW, ROOT, YEARS, load_pihps_provinces, load_province_tables, read_prognosa
from pipeline.rules import YIELD_MAX, YIELD_MIN
from pipeline.transform.denton import denton_pfd

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


def mean_share_profile(values, group, exclude_year=None):
    """Rata-rata pola musiman (porsi tiap bulan terhadap total tahun) dari edisi yang ada, tanpa exclude_year."""
    shares = [v / v.sum() for (g, y), v in values.items() if g == group and y != exclude_year]
    return np.mean(shares, axis=0)


def national_indicator(values, group, national_totals, years, exclude_year=None):
    """Indikator bulanan nasional 2018-2025: tabel prognosa kalau ada, selain itu pola rata-rata x total tahunan BDSP."""
    profile = mean_share_profile(values, group, exclude_year)
    pieces = []
    for year in years:
        if (group, year) in values and year != exclude_year:
            pieces.append(values[(group, year)])
        else:
            pieces.append(profile * national_totals[year])
    return np.concatenate(pieces)


def denton_with_zero_years(indicator, annual):
    """Denton per segmen tahun berurutan yang benchmark-nya positif; tahun dengan benchmark 0 diisi 0."""
    result = np.zeros_like(indicator, dtype=float)
    positive = annual > 0
    start = None
    for year in range(len(annual) + 1):
        if year < len(annual) and positive[year]:
            start = year if start is None else start
        elif start is not None:
            sl = slice(start * 12, year * 12)
            result[sl] = denton_pfd(indicator[sl], annual[start:year])
            start = None
    return result


def monthly_production(annual, values):
    years = YEARS
    rows = []
    for group in MONTHLY_GROUPS:
        part = annual[annual["commodity_group"] == group]
        totals = part.groupby("year")["production_ton"].sum()
        indicator = national_indicator(values, group, totals, years)
        for province_id, province_rows in part.groupby("province_id"):
            benchmark = province_rows.set_index("year")["production_ton"].reindex(years).fillna(0).to_numpy()
            estimate = denton_with_zero_years(indicator, benchmark)
            for index, month in enumerate(pd.period_range(f"{years[0]}-01", f"{years[-1]}-12", freq="M")):
                rows.append((province_id, month.to_timestamp().date(), group, estimate[index], month.year == years[-1]))
    frame = pd.DataFrame(rows, columns=["province_id", "month_start", "commodity_group", "production_ton_denton", "is_preliminary_year"])
    frame["is_imputed"] = True
    frame["impute_method"] = "denton"
    # 2026: angka tahunan belum ada, tidak di-extrapolate (baris tetap ada dengan nilai NULL)
    extra = pd.DataFrame(
        [(p, m.to_timestamp().date(), g, np.nan, False, True, "denton")
         for g in MONTHLY_GROUPS for p in sorted(load_pihps_provinces().values()) for m in pd.period_range("2026-01", "2026-11", freq="M")],
        columns=frame.columns,
    )
    return pd.concat([frame, extra], ignore_index=True)


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
    table, values, _ = prognosa_tables()
    monthly = monthly_production(annual, values)
    national = national_monthly(table)

    OUT.mkdir(parents=True, exist_ok=True)
    annual.to_parquet(OUT / "fact_production_annual.parquet", index=False)
    monthly.to_parquet(OUT / "fact_production_monthly.parquet", index=False)
    national.to_parquet(OUT / "fact_production_national_monthly.parquet", index=False)

    estimated = monthly.dropna(subset=["production_ton_denton"])
    print(f"annual {len(annual):,} baris | monthly {len(monthly):,} baris ({len(estimated):,} berisi nilai, "
          f"negatif: {(estimated['production_ton_denton'] < 0).sum()}) | national realisasi: {(national['status'] == 'realisasi').sum()} bulan")
    return annual, monthly, national


if __name__ == "__main__":
    run()
