"""Imputation harga bulanan sesuai data quality rules (D-35).

Per seri (tipe harga x komoditas x provinsi), pada jendela model Jan 2018 - Okt 2026:
  - tier dihitung pada Jan 2019 - Okt 2026: main, descriptive, atau excluded
  - excluded: tidak di-impute
  - gap tengah 1-6 bulan: linear interpolation pada log price (Kalman dibatalkan, D-43)
  - gap tengah > 6 bulan: tetap NULL
  - gap di awal dan di akhir seri: tidak pernah di-impute
November 2026 (bulan parsial) tidak ikut diimputasi; nilai observed-nya dibawa apa adanya dengan flag.

Output data/interim/fact_price_monthly.parquet (semua seri, termasuk varian dan baris nasional province_id 0):
price_idr_per_kg, n_days_observed, is_imputed, impute_method, tier, is_partial_month.
"""
import numpy as np
import pandas as pd

from pipeline.readers import CORE_START, MODEL_END, ROOT, months
from pipeline.rules import MAX_FILL_GAP, assign_tier, gap_profile
from pipeline.transform.impute_methods import linear_log

OUT = ROOT / "data" / "interim"
MODEL_MONTHS = months(months()[0], MODEL_END)


def interior_runs(valid):
    """[(awal, akhir_eksklusif)] untuk tiap gap tengah (di antara observasi pertama dan terakhir)."""
    positions = np.flatnonzero(valid)
    return [(before + 1, after) for before, after in zip(positions[:-1], positions[1:]) if after - before > 1]


def impute_series(observed):
    """observed: Series harga bulanan (PeriodIndex Jan 2018 - Okt 2026, NaN = missing).

    Mengembalikan (price, is_imputed, impute_method, tier)."""
    valid = observed.notna().to_numpy()
    core = observed.loc[CORE_START:MODEL_END].notna().to_numpy()
    tier = assign_tier(core.mean(), gap_profile(core)["longest_interior_gap"])

    price = observed.copy()
    is_imputed = pd.Series(False, index=observed.index)
    method = pd.Series(None, index=observed.index, dtype="object")
    if tier == "excluded" or not valid.any():
        return price, is_imputed, method, tier

    fill_runs = [r for r in interior_runs(valid) if r[1] - r[0] <= MAX_FILL_GAP]
    if fill_runs:
        filled = linear_log(observed).reindex(observed.index)
        for start, end in fill_runs:
            price.iloc[start:end] = filled.iloc[start:end]
            is_imputed.iloc[start:end] = True
            method.iloc[start:end] = "linear_log"
    return price, is_imputed, method, tier


def run():
    observed = pd.read_parquet(OUT / "price_monthly_observed.parquet")
    observed["month"] = pd.PeriodIndex(observed["month"], freq="M")
    frames = []
    for (price_type, commodity, province), group in observed.groupby(["price_type_id", "commodity_id", "province_id"]):
        group = group.set_index("month").sort_index()
        series = group["price_observed"].reindex(MODEL_MONTHS)
        price, is_imputed, method, tier = impute_series(series)
        full = pd.DataFrame(index=group.index)
        full["price_idr_per_kg"] = price.reindex(group.index)
        full["is_imputed"] = is_imputed.reindex(group.index).fillna(False).astype(bool)
        full["impute_method"] = method.reindex(group.index)
        full["tier"] = tier
        full["n_days_observed"] = group["n_days_observed"]
        full["n_weekdays"] = group["n_weekdays"]
        # November 2026 (di luar jendela model): nilai observed dibawa apa adanya
        outside = ~group.index.isin(MODEL_MONTHS)
        full.loc[outside, "price_idr_per_kg"] = group.loc[outside, "price_observed"]
        full["is_partial_month"] = group.index == months()[-1]
        full["price_type_id"], full["commodity_id"], full["province_id"] = price_type, commodity, province
        frames.append(full.reset_index())
    result = pd.concat(frames, ignore_index=True)
    stored = result.assign(month=result["month"].astype(str))
    stored.to_parquet(OUT / "fact_price_monthly.parquet", index=False)

    imputed = result[result["is_imputed"]]
    print(f"fact_price_monthly: {len(result):,} baris; imputed {len(imputed):,} "
          f"(semua linear_log: {bool((imputed['impute_method'] == 'linear_log').all())})")
    return result


if __name__ == "__main__":
    run()
