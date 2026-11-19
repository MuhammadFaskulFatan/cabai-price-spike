"""Laporan ringkas hasil fase transform: tier, imputation, produksi, dan pemeriksaan core dataset.

Output pipeline/transform/reports/transform_report.md. Dijalankan setelah semua modul transform.
"""
import pandas as pd

from pipeline.audit.loaders import to_markdown
from pipeline.readers import COMMODITY_LABELS, PRICE_TYPE_LABELS, ROOT

INTERIM = ROOT / "data" / "interim"
FINAL = ROOT / "data" / "final"
REPORTS = ROOT / "pipeline" / "transform" / "reports"
VALIDATE_REPORTS = ROOT / "pipeline" / "validate" / "reports"


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
    return imputed.groupby(["price_type", "commodity", "impute_method"]).size().rename("nilai").reset_index()


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


def section(path, start, end=None):
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8").split(start, 1)[1]
    return (text.split(end, 1)[0] if end else text).strip()


def run():
    prices = pd.read_parquet(INTERIM / "fact_price_monthly.parquet")
    core = pd.read_csv(FINAL / "core_province_month.csv")
    core_year = pd.read_csv(FINAL / "core_province_year.csv")
    annual = pd.read_parquet(INTERIM / "fact_production_annual.parquet")

    lines = ["# Laporan Fase 4 (Transform)", "",
             "Sumber angka: `data/interim/` dan `data/final/`. Aturan dan ambang ada di `pipeline/rules.py` (D-35, D-43).", "",
             "## 1. Seri per tier (tipe harga x komoditas)", "",
             "Satu seri = satu provinsi (atau baris nasional). Tier dihitung pada Jan 2019 - Okt 2026.", "",
             to_markdown(tier_table(prices)), "",
             "### Hold-out validation metode imputation (D-09, D-43)", "",
             section(VALIDATE_REPORTS / "holdout_imputation.md", "## 1. Keputusan", "## 2."), "",
             "Rincian di `pipeline/validate/reports/holdout_imputation.md`.", ""]

    lines += ["## 2. Nilai yang di-impute", "", to_markdown(imputation_table(prices)), "",
              f"Total {int(prices['is_imputed'].sum())} nilai dari {int(prices['price_idr_per_kg'].notna().sum()):,} bulan berharga, semuanya linear interpolation pada log price. "
              "Gap > 6 bulan, gap awal/akhir, dan seri excluded tidak diisi. Setiap uji H2/H4 wajib punya sensitivity check tanpa bulan imputasi (D-44).", ""]

    lines += ["## 3. Sel harga kosong di core_province_month (periode model Jan 2019 - Okt 2026)", "",
              to_markdown(null_reasons(core)), "",
              "`tier_excluded`: seri di bawah 50% bulan valid (tidak di-impute). Sisanya adalah gap awal atau akhir seri dan gap tengah lebih dari 6 bulan pada seri main atau descriptive.", ""]

    lines += ["## 4. Produksi", "",
              f"- `fact_production_annual`: {len(annual):,} baris (34 provinsi x 8 tahun x 3 grup). `is_preliminary` = 2025; `is_outlier` = {int(annual['is_outlier'].sum())} baris; `suspect_copy` = {int(annual['suspect_copy'].sum())} baris (cabai_keriting).",
              "- `core_province_month` memakai `production_annual_ton`: angka tahunan BDSP yang sama untuk 12 bulan dalam tahunnya; 2026 NULL. Disagregasi bulanan (Denton) dibatalkan (D-42).", "",
              "### Dokumentasi: hold-out disagregasi bulanan yang membuat Denton dibatalkan (D-42)", "",
              "Realisasi SPH-BPS Januari-Maret 2022-2025 (24 nilai), leave-one-year-out. MAPE nasional (persen):", "",
              section(VALIDATE_REPORTS / "holdout_production.md", "Hasil di tingkat nasional (MAPE, persen):", "Per tahun uji"), "",
              "Pola musiman dari tabel prognosa Buletin tidak membuat tebakan lebih baik dari flat (tahunan / 12). Rincian di `pipeline/validate/reports/holdout_production.md`.", ""]

    flag_ok = all(((core[f"{c}_is_imputed"] == True) == core[f"{c}_impute_method"].notna()).all() for c in ("price_retail", "price_wholesale", "price_producer"))
    lines += ["## 5. Core dataset", "",
              f"- `core_province_month.csv`: {len(core):,} baris x {core.shape[1]} kolom; key (provinsi, bulan, grup) unik: {not core.duplicated(['province_id', 'month_start', 'commodity_group']).any()}.",
              f"- `core_province_year.csv`: {len(core_year):,} baris x {core_year.shape[1]} kolom; produksi dan luas panen 2018-2025, 2026 tidak ada.",
              f"- Pasangan flag konsisten (is_imputed TRUE hanya jika impute_method terisi): {flag_ok}.",
              "- Kolom cuaca belum ada; menyusul setelah data Open-Meteo lengkap.", ""]

    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "transform_report.md").write_text("\n".join(lines), encoding="utf-8")
    print("ditulis: pipeline/transform/reports/transform_report.md")


if __name__ == "__main__":
    run()
