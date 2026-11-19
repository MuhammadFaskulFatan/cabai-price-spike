"""Hold-out validation disagregasi produksi (D-26): Denton vs dua pembanding sederhana.

Realisasi SPH-BPS Januari-Maret dari tabel prognosa Buletin (2022-2025, 12 bulan per komoditas; 2026 tidak bisa
diuji karena angka tahunan BDSP 2026 belum ada) dipakai sebagai kebenaran. Untuk tiap tahun uji, pola musiman
tahun itu dilepas dari indikator (leave-one-year-out): diganti rata-rata pola tahun edisi lain. Lalu diukur
seberapa dekat Denton dengan benchmark BDSP menebak Januari-Maret tahun itu.

Metode: flat (total tahunan / 12), profile (rata-rata pola x total tahunan), denton (profil + benchmark seluruh tahun).
Evaluasi di tingkat nasional, karena realisasi bulanan hanya ada nasional.

    python -m pipeline.validate.holdout_production
"""
import numpy as np
import pandas as pd

from pipeline.audit.loaders import to_markdown
from pipeline.readers import ROOT, YEARS
from pipeline.transform.denton import denton_pfd
from pipeline.transform.disaggregate_production import MONTHLY_GROUPS, mean_share_profile, national_indicator, prognosa_tables

REPORTS = ROOT / "pipeline" / "validate" / "reports"
TEST_YEARS = [2022, 2023, 2024, 2025]


def run():
    annual = pd.read_parquet(ROOT / "data" / "interim" / "fact_production_annual.parquet")
    national = pd.read_parquet(ROOT / "data" / "interim" / "fact_production_national_monthly.parquet")
    national["month_start"] = pd.to_datetime(national["month_start"])
    _, values, _ = prognosa_tables()

    rows = []
    for group in MONTHLY_GROUPS:
        totals = annual[annual["commodity_group"] == group].groupby("year")["production_ton"].sum()
        for year in TEST_YEARS:
            truth = national[(national["commodity_group"] == group) & (national["month_start"].dt.year == year) & (national["status"] == "realisasi")]
            indicator = national_indicator(values, group, totals, YEARS, exclude_year=year)
            estimate = denton_pfd(indicator, totals.reindex(YEARS).to_numpy())
            profile = mean_share_profile(values, group, exclude_year=year)
            for month, actual in zip(truth["month_start"].dt.month, truth["production_ton"]):
                position = YEARS.index(year) * 12 + month - 1
                predictions = {"flat": totals[year] / 12, "profile": profile[month - 1] * totals[year], "denton": estimate[position]}
                for method, predicted in predictions.items():
                    rows.append((group, year, month, method, actual, predicted, abs(predicted - actual) / actual))
    results = pd.DataFrame(rows, columns=["commodity_group", "year", "month", "method", "actual_ton", "predicted_ton", "ape"])

    summary = results.groupby(["commodity_group", "method"])["ape"].agg(mape="mean", n="size").reset_index()
    summary["mape"] *= 100
    overall = results.groupby("method")["ape"].agg(mape="mean", n="size").reset_index()
    overall["mape"] *= 100
    by_year = results.groupby(["commodity_group", "year", "method"])["ape"].mean().mul(100).unstack("method").reset_index()

    REPORTS.mkdir(parents=True, exist_ok=True)
    results.to_csv(REPORTS / "holdout_production_results.csv", index=False)
    lines = ["# Hold-out validation: disagregasi produksi bulanan (D-26)", "",
             "Kebenaran: realisasi SPH-BPS Januari-Maret dari tabel prognosa Buletin, 2022-2025 (3 bulan x 4 tahun x 2 komoditas = 24 nilai). "
             "Januari-Maret 2026 (3 bulan per komoditas) tidak bisa diuji karena benchmark tahunan BDSP 2026 belum ada. Pola musiman tahun uji dilepas dari indikator (leave-one-year-out).", "",
             "Hasil di tingkat nasional (MAPE, persen):", "", to_markdown(summary.pivot(index="commodity_group", columns="method", values="mape").reset_index(), floatfmt="{:.2f}"), "",
             "Gabungan dua komoditas:", "", to_markdown(overall, floatfmt="{:.2f}"), "",
             "Per tahun uji (MAPE, persen):", "", to_markdown(by_year, floatfmt="{:.2f}"), "",
             "Catatan: realisasi Januari-Maret berasal dari edisi yang sama dengan pola musiman yang dilepas, tetapi pola tahun uji tidak dipakai saat menebak. "
             "Keterbatasan: hanya 3 bulan pertama tiap tahun yang bisa diuji, jadi akurasi untuk bulan lain (misalnya Juli-Desember, yang di tabel prognosa sendiri berasal dari rata-rata tahun sebelumnya) tidak teruji.", ""]
    (REPORTS / "holdout_production.md").write_text("\n".join(lines), encoding="utf-8")
    print(summary.pivot(index="commodity_group", columns="method", values="mape").round(2).to_string())
    print(overall.round(2).to_string(index=False))
    return results


if __name__ == "__main__":
    run()
