"""Pemeriksaan struktur dan aturan pada core dataset (data/final). Setiap cek menghasilkan lulus/gagal dan rinciannya.

Yang dicek: key unik dan lengkap, nilai wajar, pasangan flag, imputation hanya di tempat yang diizinkan (D-35, D-43),
setiap sel harga kosong punya alasan, produksi tahunan (D-42), ONI, kalender, dan core_province_year.
"""
import numpy as np
import pandas as pd

from pipeline.readers import ROOT
from pipeline.rules import MAX_FILL_GAP

FINAL = ROOT / "data" / "final"
PRICE_COLUMNS = ["price_retail", "price_wholesale", "price_producer"]
NTT = 19


def check(results, name, passed, detail):
    results.append({"cek": name, "lulus": bool(passed), "rincian": detail})


def runs(mask):
    """[(awal, akhir_eksklusif)] untuk rangkaian True berturut-turut."""
    out, start = [], None
    for i, value in enumerate(list(mask) + [False]):
        if value and start is None:
            start = i
        elif not value and start is not None:
            out.append((start, i))
            start = None
    return out


def classify_nulls(series):
    """Untuk satu seri harga (DataFrame terurut per bulan, periode model): alasan tiap sel kosong."""
    reasons = pd.Series(None, index=series.index, dtype="object")
    value = series["value"].to_numpy()
    observed = ~np.isnan(value) & ~series["is_imputed"].to_numpy(dtype=bool)
    tier = series["tier"].iloc[0]
    empty = np.isnan(value)
    if tier == "excluded":
        reasons[empty] = "tier_excluded"
        return reasons
    positions = np.flatnonzero(observed)
    if positions.size == 0:
        reasons[empty] = "seri_tanpa_observasi"
        return reasons
    for start, end in runs(empty):
        if end <= positions[0]:
            label = "gap_awal_seri"
        elif start > positions[-1]:
            label = "gap_akhir_seri"
        elif end - start > MAX_FILL_GAP:
            label = "gap_tengah_lebih_6_bulan"
        else:
            label = "TIDAK_BERALASAN"
        reasons.iloc[start:end] = label
    return reasons


def price_series(core, column):
    """Seri harga pada jendela imputation Jan 2018 - Okt 2026 (2018 ikut, karena gap awal 2019 bisa dijembatani observasi 2018)."""
    frame = core[~core["is_partial_month"]].copy()
    frame = frame.rename(columns={column: "value", f"{column}_is_imputed": "is_imputed", f"{column}_tier": "tier", f"{column}_impute_method": "impute_method"})
    return frame[["province_id", "commodity_group", "month_start", "in_model_period", "value", "is_imputed", "tier", "impute_method"]].sort_values(["province_id", "commodity_group", "month_start"])


def run_checks():
    core = pd.read_csv(FINAL / "core_province_month.csv")
    year = pd.read_csv(FINAL / "core_province_year.csv")
    dim_month = pd.read_csv(FINAL / "dim_month.csv")
    dim_holiday = pd.read_csv(FINAL / "dim_holiday.csv")
    results = []

    # --- struktur ---
    check(results, "core_province_month: key unik", not core.duplicated(["province_id", "month_start", "commodity_group"]).any(), f"{len(core):,} baris")
    check(results, "core_province_month: lengkap 34 provinsi x 107 bulan x 2 grup", len(core) == 34 * 107 * 2 and core["province_id"].nunique() == 34, f"{core['province_id'].nunique()} provinsi, {core['month_start'].nunique()} bulan")
    check(results, "core_province_month: rentang Jan 2018 - Nov 2026", core["month_start"].min() == "2018-01-01" and core["month_start"].max() == "2026-11-01", f"{core['month_start'].min()} s/d {core['month_start'].max()}")

    # --- nilai wajar ---
    for column in PRICE_COLUMNS:
        values = core[column].dropna()
        check(results, f"{column}: semua harga positif dan < Rp500.000/kg", bool(((values > 0) & (values < 500_000)).all()), f"min {values.min():,.0f}, max {values.max():,.0f}")

    # --- flag dan aturan imputation ---
    for column in PRICE_COLUMNS:
        flag, method = core[f"{column}_is_imputed"] == True, core[f"{column}_impute_method"]
        check(results, f"{column}: is_imputed TRUE tepat ketika impute_method terisi", bool((flag == method.notna()).all()), f"{int(flag.sum())} nilai imputed")
        check(results, f"{column}: impute_method hanya linear_log (D-43)", set(method.dropna().unique()) <= {"linear_log"}, str(sorted(method.dropna().unique())))
        check(results, f"{column}: tidak ada imputation di seri excluded", not (flag & (core[f"{column}_tier"] == "excluded")).any(), "")
        check(results, f"{column}: tidak ada imputation di luar periode model (2018 boleh, Nov 2026 tidak)", not (flag & core["is_partial_month"]).any(), "")
        check(results, f"{column}: nilai imputed tidak pernah kosong", not (flag & core[column].isna()).any(), "")

        series = price_series(core, column)
        too_long, edges, unexplained = 0, 0, 0
        reason_counts = {}
        for _, group in series.groupby(["province_id", "commodity_group"]):
            for start, end in runs(group["is_imputed"].to_numpy(dtype=bool)):
                if end - start > MAX_FILL_GAP:
                    too_long += 1
            observed = group["value"].notna().to_numpy() & ~group["is_imputed"].to_numpy(dtype=bool)
            positions = np.flatnonzero(observed)
            imputed = np.flatnonzero(group["is_imputed"].to_numpy(dtype=bool))
            if imputed.size and positions.size and (imputed.min() < positions.min() or imputed.max() > positions.max()):
                edges += 1
            group = group.reset_index(drop=True)
            reasons = classify_nulls(group)[group["in_model_period"].to_numpy()]  # hanya sel kosong di periode model yang dihitung
            for reason, count in reasons.value_counts().items():
                reason_counts[reason] = reason_counts.get(reason, 0) + int(count)
        check(results, f"{column}: tidak ada rangkaian imputed lebih dari {MAX_FILL_GAP} bulan", too_long == 0, f"{too_long} rangkaian")
        check(results, f"{column}: tidak ada imputation di awal atau akhir seri", edges == 0, f"{edges} seri")
        check(results, f"{column}: setiap sel kosong di periode model punya alasan", reason_counts.get("TIDAK_BERALASAN", 0) == 0,
              "; ".join(f"{k} {v}" for k, v in sorted(reason_counts.items())) or "tidak ada sel kosong")

    ntt_after = core[(core["province_id"] == NTT) & (core["month_start"] >= "2024-01-01") & core["in_model_period"]]
    check(results, "NTT harga produsen sejak 2024 tetap kosong (tanpa ekstrapolasi) dan ditandai keluar analisis", ntt_after["price_producer"].isna().all() and not core[core["province_id"] == NTT]["in_producer_price_analysis"].any(),
          f"{ntt_after['price_producer'].notna().sum()} sel terisi")

    # --- produksi tahunan (D-42) ---
    core["year"] = core["month_start"].str[:4].astype(int)
    per_year = core.groupby(["province_id", "commodity_group", "year"])["production_annual_ton"].nunique(dropna=False)
    check(results, "production_annual_ton sama untuk 12 bulan dalam tahunnya", bool((per_year == 1).all()), "")
    check(results, "production_annual_ton kosong untuk 2026 dan terisi untuk 2018-2025", core[core["year"] == 2026]["production_annual_ton"].isna().all() and core[core["year"] < 2026]["production_annual_ton"].notna().all(), "")
    check(results, "production_annual_preliminary hanya 2025", set(core[core["production_annual_preliminary"] == True]["year"].unique()) == {2025}, "")
    check(results, "tidak ada kolom produksi bulanan Denton", not any("denton" in c for c in core.columns), "")

    # --- ONI dan kalender ---
    oni_missing = sorted(core[core["oni_anomaly"].isna()]["month_start"].unique())
    check(results, "ONI kosong hanya Okt-Nov 2026", oni_missing == ["2026-10-01", "2026-11-01"], ", ".join(oni_missing))
    phase_ok = core.dropna(subset=["oni_anomaly"]).apply(
        lambda r: r["enso_phase"] == ("el_nino" if r["oni_anomaly"] >= 0.5 else "la_nina" if r["oni_anomaly"] <= -0.5 else "neutral"), axis=1)
    check(results, "enso_phase konsisten dengan ambang +-0,5", bool(phase_ok.all()), "")
    idul = dim_holiday[(dim_holiday["holiday"] == "idulfitri") & ~dim_holiday["is_cuti_bersama"]].groupby(dim_holiday["date"].str[:4])["date"].min().str[:7]
    zero_months = set(dim_month[dim_month["months_to_idulfitri"] == 0]["month_start"].str[:7])
    check(results, "months_to_idulfitri = 0 tepat di bulan 1 Syawal", zero_months == set(idul), f"{len(zero_months)} bulan")
    in_range = dim_holiday[~dim_holiday["is_cuti_bersama"] & (dim_holiday["date"] < "2026-12-01")]  # dim_month berakhir Nov 2026
    recount = in_range.groupby(in_range["date"].str[:7]).size()
    from_dim = dim_month.set_index(dim_month["month_start"].str[:7])["n_holiday_days"]
    check(results, "n_holiday_days = jumlah libur nasional di dim_holiday", bool((from_dim.reindex(recount.index) == recount).all() and from_dim.sum() == recount.sum()), f"{int(recount.sum())} hari")
    check(results, "dim_holiday: source_level hanya official/secondary", set(dim_holiday["source_level"]) <= {"official", "secondary"}, dim_holiday["source_level"].value_counts().to_dict().__str__())
    check(results, "periode model = Jan 2019 - Okt 2026", dim_month[dim_month["in_model_period"]]["month_start"].agg(["min", "max"]).tolist() == ["2019-01-01", "2026-10-01"], "")

    # --- core_province_year ---
    check(results, "core_province_year: key unik dan lengkap 34 x 8 tahun x 2 grup", len(year) == 34 * 8 * 2 and not year.duplicated(["province_id", "year", "commodity_group"]).any(), f"{len(year)} baris")
    check(results, "core_province_year: producer_price_n_months di 0-12", bool(year["producer_price_n_months"].between(0, 12).all()), "")
    check(results, "core_province_year: is_preliminary hanya 2025", set(year[year["is_preliminary"]]["year"]) == {2025}, "")
    productivity = year["production_ton"] / year["harvested_area_ha"].replace(0, np.nan)
    expected_outlier = (year["production_ton"] > 0) & ~productivity.between(1, 30)
    check(results, "core_province_year: is_outlier sesuai aturan 1-30 ton/ha", bool((expected_outlier == year["is_outlier"]).all()), f"{int(year['is_outlier'].sum())} baris outlier")
    joined = core[core["year"] < 2026].drop_duplicates(["province_id", "commodity_group", "year"]).merge(year, on=["province_id", "commodity_group", "year"])
    check(results, "production_annual_ton di core bulanan = production_ton di core tahunan", bool(np.allclose(joined["production_annual_ton"], joined["production_ton"])), f"{len(joined)} provinsi-tahun")

    return pd.DataFrame(results)


if __name__ == "__main__":
    print(run_checks().to_string(index=False))
