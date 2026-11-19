"""Reconciliation total tahunan: angka produksi dan luas panen di core dataset vs total resmi BDSP.

1. Baris TOTAL nasional di tabel BDSP (raw) = jumlah 34 provinsi di fact_production_annual, per komoditas x indikator x tahun.
2. core_province_year = fact_production_annual untuk cabai_merah (cabe besar) dan cabai_rawit.
3. Papua dan Papua Barat di core = jumlah provinsi induk + pemekaran di BDSP (D-17, D-36).
4. Informasi: realisasi Januari-Maret dari Buletin dibanding total tahunan BDSP (porsi tiga bulan pertama).
"""
import numpy as np
import pandas as pd

from pipeline.readers import COMMODITIES, INDICATORS, RAW, ROOT, TO_BASE_UNIT, YEARS, load_province_tables, read_table, unit_of

INTERIM = ROOT / "data" / "interim"
FINAL = ROOT / "data" / "final"
GROUP_OF = {"cabe_besar": "cabai_merah", "cabe_rawit": "cabai_rawit", "cabe_keriting": "cabai_keriting"}
COLUMN_OF = {"produksi": "production_ton", "luas_panen": "harvested_area_ha"}
TOLERANCE = 0.01  # ton atau ha, untuk perbandingan antar tabel buatan sendiri
# BDSP menampilkan tiap baris provinsi dibulatkan 2 desimal, sedangkan baris TOTAL dihitung dari angka belum dibulatkan:
# selisih wajar paling besar 38 baris x 0,005 = 0,19
ROUNDING_TOLERANCE = 38 * 0.005


def national_totals():
    rows = []
    annual = pd.read_parquet(INTERIM / "fact_production_annual.parquet")
    for commodity in COMMODITIES:
        for indicator in INDICATORS:
            path = RAW / "bdsp" / "provinsi" / f"{commodity}_{indicator}.html"
            official = np.array(read_table(path)["TOTAL"]) * TO_BASE_UNIT[unit_of(path)]
            ours = annual[annual["commodity_group"] == GROUP_OF[commodity]].groupby("year")[COLUMN_OF[indicator]].sum().reindex(YEARS).to_numpy()
            for year, a, b in zip(YEARS, official, ours):
                rows.append({"komoditas": COMMODITIES[commodity], "indikator": INDICATORS[indicator], "tahun": year, "total_bdsp": a, "jumlah_core": b, "selisih": b - a})
    return pd.DataFrame(rows)


def core_year_vs_fact():
    annual = pd.read_parquet(INTERIM / "fact_production_annual.parquet")
    year = pd.read_csv(FINAL / "core_province_year.csv")
    joined = year.merge(annual, on=["province_id", "year", "commodity_group"], suffixes=("_core", "_fact"))
    return float(max((joined["production_ton_core"] - joined["production_ton_fact"]).abs().max(),
                     (joined["harvested_area_ha_core"] - joined["harvested_area_ha_fact"]).abs().max())), len(joined)


def papua_check():
    frame, _ = load_province_tables()
    year = pd.read_csv(FINAL / "core_province_year.csv")
    rows = []
    for parent_id, codes in ((33, ["94", "95", "96", "97"]), (34, ["91", "92"])):
        for commodity, group in (("cabe_besar", "cabai_merah"), ("cabe_rawit", "cabai_rawit")):
            bdsp = frame[(frame["commodity"] == commodity) & (frame["indicator"] == "produksi") & frame["bps_code"].isin(codes)].groupby("year")["value"].sum()
            core = year[(year["province_id"] == parent_id) & (year["commodity_group"] == group)].set_index("year")["production_ton"]
            rows.append({"provinsi_induk": parent_id, "grup": group, "selisih_maks_ton": float((bdsp - core).abs().max())})
    return pd.DataFrame(rows)


def realised_share():
    national = pd.read_parquet(INTERIM / "fact_production_national_monthly.parquet")
    national = national[national["status"] == "realisasi"].copy()
    national["year"] = pd.to_datetime(national["month_start"]).dt.year
    annual = pd.read_parquet(INTERIM / "fact_production_annual.parquet").groupby(["commodity_group", "year"])["production_ton"].sum()
    q1 = national.groupby(["commodity_group", "year"])["production_ton"].sum().reset_index()
    q1["bdsp_tahunan"] = [annual.get((g, y), np.nan) for g, y in zip(q1["commodity_group"], q1["year"])]
    q1["porsi_jan_mar_pct"] = q1["production_ton"] / q1["bdsp_tahunan"] * 100
    return q1.rename(columns={"production_ton": "realisasi_jan_mar_ton"})


def run():
    totals = national_totals()
    max_core_gap, n_joined = core_year_vs_fact()
    papua = papua_check()
    return {
        "totals": totals,
        "totals_pass": bool((totals["selisih"].abs() <= ROUNDING_TOLERANCE).all()),
        "core_year_gap": max_core_gap,
        "core_year_rows": n_joined,
        "papua": papua,
        "papua_pass": bool((papua["selisih_maks_ton"] <= TOLERANCE).all()),
        "realised_share": realised_share(),
    }


if __name__ == "__main__":
    result = run()
    print("total nasional cocok:", result["totals_pass"], "| selisih maks:", result["totals"]["selisih"].abs().max())
    print("core_province_year vs fact:", result["core_year_gap"], "|", result["papua"].to_string(index=False))
    print(result["realised_share"].round(1).to_string(index=False))
