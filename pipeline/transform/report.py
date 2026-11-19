"""Laporan ringkas hasil fase transform: tier, imputation, produksi, dan pemeriksaan core dataset.

Output pipeline/transform/reports/transform_report.md. Dijalankan setelah semua modul transform.
"""
import numpy as np
import pandas as pd

from pipeline.audit.loaders import to_markdown
from pipeline.readers import COMMODITY_LABELS, PRICE_TYPE_LABELS, ROOT
from pipeline.transform.denton import denton_pfd
from pipeline.transform.disaggregate_production import MONTHLY_GROUPS, denton_with_zero_years, national_indicator, prognosa_tables
from pipeline.readers import YEARS

INTERIM = ROOT / "data" / "interim"
FINAL = ROOT / "data" / "final"
REPORTS = ROOT / "pipeline" / "transform" / "reports"


def tier_table(prices):
    series = prices.drop_duplicates(["price_type_id", "commodity_id", "province_id"]).copy()
    series["price_type"] = series["price_type_id"].map(PRICE_TYPE_LABELS)
    series["commodity"] = series["commodity_id"].map(COMMODITY_LABELS)
    table = series.pivot_table(index=["price_type", "commodity"], columns="tier", values="province_id", aggfunc="count", fill_value=0).reset_index()
    for tier in ("main", "descriptive", "excluded"):
        if tier not in table.columns:
            table[tier] = 0
    return table[["price_type", "commodity", "main", "descriptive", "excluded"]]


def imputation_table(prices):
    imputed = prices[prices["is_imputed"]].copy()
    imputed["price_type"] = imputed["price_type_id"].map(PRICE_TYPE_LABELS)
    imputed["commodity"] = imputed["commodity_id"].map(COMMODITY_LABELS)
    pivot = imputed.pivot_table(index=["price_type", "commodity"], columns="impute_method", values="province_id", aggfunc="count", fill_value=0).reset_index()
    for method in ("linear_log", "kalman"):
        if method not in pivot.columns:
            pivot[method] = 0
    pivot["total_imputed"] = pivot["linear_log"] + pivot["kalman"]
    return pivot[["price_type", "commodity", "linear_log", "kalman", "total_imputed"]]


def null_reasons(core):
    """Alasan tiap sel harga kosong pada periode model, supaya tidak ada missing yang tak berpenjelasan."""
    rows = []
    model = core[core["in_model_period"]]
    for column in ("price_retail", "price_wholesale", "price_producer"):
        empty = model[model[column].isna()]
        tier = empty[f"{column}_tier"]
        rows.append({
            "variabel": column,
            "sel_kosong": len(empty),
            "tier_excluded": int((tier == "excluded").sum()),
            "tier_descriptive_atau_main": int((tier != "excluded").sum()),
            "dari_itu_di_NTT": int(((tier != "excluded") & (empty["province_id"] == 19)).sum()),
        })
    return pd.DataFrame(rows)


def negative_denton_count(annual):
    """Berapa seri provinsi x grup yang hasil Denton tanpa batas bawah sempat negatif (lalu diselesaikan dengan batas x >= 0)."""
    _, values, _ = prognosa_tables()
    count = 0
    for group in MONTHLY_GROUPS:
        part = annual[annual["commodity_group"] == group]
        totals = part.groupby("year")["production_ton"].sum()
        indicator = national_indicator(values, group, totals, YEARS)
        for _, rows in part.groupby("province_id"):
            benchmark = rows.set_index("year")["production_ton"].reindex(YEARS).fillna(0).to_numpy()
            positive = benchmark > 0
            if positive.all():
                if (denton_pfd(indicator, benchmark, nonnegative=False) < 0).any():
                    count += 1
    return count


def run():
    prices = pd.read_parquet(INTERIM / "fact_price_monthly.parquet")
    core = pd.read_csv(FINAL / "core_province_month.csv")
    core_year = pd.read_csv(FINAL / "core_province_year.csv")
    annual = pd.read_parquet(INTERIM / "fact_production_annual.parquet")
    monthly_prod = pd.read_parquet(INTERIM / "fact_production_monthly.parquet")

    lines = ["# Laporan Fase 4 (Transform)", "",
             "Sumber angka: `data/interim/` dan `data/final/`. Aturan dan ambang ada di `pipeline/rules.py` (D-35).", "",
             "## 1. Seri per tier (tipe harga x komoditas)", "",
             "Satu seri = satu provinsi (atau baris nasional). Tier dihitung pada Jan 2019 - Okt 2026.", "",
             to_markdown(tier_table(prices)), ""]

    holdout_price = ROOT / "pipeline" / "validate" / "reports" / "holdout_imputation.md"
    if holdout_price.exists():
        text = holdout_price.read_text(encoding="utf-8")
        verdict = text.split("## 1. Apakah aturan gap cocok dengan hasil hold-out?")[1].split("## 2.")[0].strip()
        lines += ["### Hold-out validation metode imputation (D-09)", "", verdict, "", "Rincian di `pipeline/validate/reports/holdout_imputation.md`.", ""]

    lines += ["## 2. Nilai yang di-impute", "", to_markdown(imputation_table(prices)), "",
             f"Total {int(prices['is_imputed'].sum())} nilai dari {int(prices['price_idr_per_kg'].notna().sum()):,} bulan berharga. Gap > 6 bulan, gap awal/akhir, dan seri excluded tidak diisi.", ""]

    lines += ["## 3. Sel harga kosong di core_province_month (periode model Jan 2019 - Okt 2026)", "",
              to_markdown(null_reasons(core)), "",
              "`tier_excluded`: seri di bawah 50% bulan valid (tidak di-impute). Sisanya adalah gap awal atau akhir seri dan gap tengah lebih dari 6 bulan pada seri main atau descriptive.", ""]

    lines += ["## 4. Produksi", "",
              f"- `fact_production_annual`: {len(annual):,} baris (34 provinsi x 8 tahun x 3 grup). `is_preliminary` = 2025; `is_outlier` = {int(annual['is_outlier'].sum())} baris; `suspect_copy` = {int(annual['suspect_copy'].sum())} baris (cabai_keriting).",
              f"- `fact_production_monthly` (Denton, deskriptif): {int(monthly_prod['production_ton_denton'].notna().sum()):,} nilai estimasi, seluruhnya `is_imputed = TRUE`, `impute_method = denton`; 2026 NULL (tanpa ekstrapolasi). "
              f"Total 12 bulan sama dengan angka tahunan BDSP (selisih maksimum {_annual_gap(monthly_prod, annual):.1e} ton).",
              f"- Seri provinsi x grup yang hasil Denton tanpa batas bawah sempat negatif lalu diselesaikan dengan batas x >= 0: {negative_denton_count(annual)}.", ""]
    holdout_path = ROOT / "pipeline" / "validate" / "reports" / "holdout_production.md"
    if holdout_path.exists():
        lines += ["Hold-out MAPE Denton (rincian di `pipeline/validate/reports/holdout_production.md`):", "", holdout_path.read_text(encoding="utf-8").split("Hasil di tingkat nasional (MAPE, persen):")[1].split("Per tahun uji")[0].strip(), ""]

    lines += ["## 5. Core dataset", "",
              f"- `core_province_month.csv`: {len(core):,} baris x {core.shape[1]} kolom; key (provinsi, bulan, grup) unik: {not core.duplicated(['province_id', 'month_start', 'commodity_group']).any()}.",
              f"- `core_province_year.csv`: {len(core_year):,} baris x {core_year.shape[1]} kolom; produksi dan luas panen 2018-2025, 2026 tidak ada.",
              f"- Pasangan flag konsisten (is_imputed TRUE hanya jika impute_method terisi): "
              + str(all(((core[f"{c}_is_imputed"] == True) == core[f"{c}_impute_method"].notna()).all() for c in ("price_retail", "price_wholesale", "price_producer"))) + ".",
              "- Kolom cuaca belum ada; menyusul setelah data Open-Meteo lengkap.", ""]

    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "transform_report.md").write_text("\n".join(lines), encoding="utf-8")
    print("ditulis: pipeline/transform/reports/transform_report.md")


def _annual_gap(monthly, annual):
    estimated = monthly.dropna(subset=["production_ton_denton"]).copy()
    estimated["year"] = pd.to_datetime(estimated["month_start"]).dt.year
    summed = estimated.groupby(["province_id", "commodity_group", "year"])["production_ton_denton"].sum().reset_index()
    joined = summed.merge(annual[["province_id", "commodity_group", "year", "production_ton"]], on=["province_id", "commodity_group", "year"])
    return float((joined["production_ton_denton"] - joined["production_ton"]).abs().max())


if __name__ == "__main__":
    run()
