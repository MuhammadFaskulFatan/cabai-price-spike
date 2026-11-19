"""Hold-out validation untuk metode imputation harga (D-09, D-43).

Cara kerja: dari seri tier main (cabai_merah dan cabai_rawit, tiga tipe harga), sebagian observed value sengaja
di-mask sebagai gap buatan sepanjang 1 sampai 6 bulan, diisi ulang dengan tiap metode, lalu dibandingkan
dengan nilai aslinya (MAPE pada skala harga). Gap buatan selalu diapit observasi di kedua sisi, sama seperti
gap tengah yang sungguhan. Seed tetap supaya hasilnya bisa diulang.

Aturan pemilihan (success criterion): metode dipilih lewat hold-out; kalau kandidat tidak lebih akurat dari
baseline linear (log price), baseline yang dipakai. Hasil 19 Nov 2026: Kalman tidak lebih akurat, jadi semua gap
1-6 bulan memakai linear (D-43).

    python -m pipeline.validate.holdout_imputation [--draws 3] [--seed 42] [--from-results]

--from-results membaca ulang holdout_imputation_results.csv tanpa menghitung ulang (sekitar 15 menit).
"""
import argparse

import numpy as np
import pandas as pd

from pipeline.readers import COMMODITY_LABELS, CORE_START, MODEL_END, PRICE_TYPE_LABELS, ROOT, months
from pipeline.rules import MAX_FILL_GAP, assign_tier, gap_profile
from pipeline.transform.impute_methods import METHODS

REPORTS = ROOT / "pipeline" / "validate" / "reports"
RESULTS = REPORTS / "holdout_imputation_results.csv"
CORE_COMMODITIES = ["cat_7", "cat_8"]
GAP_LENGTHS = list(range(1, MAX_FILL_GAP + 1))
MODEL_MONTHS = months(months()[0], MODEL_END)
BASELINE, CANDIDATE = "linear_log", "kalman"
SHORT_GAP = 2  # batas bucket pelaporan (aturan lama: linear 1-2 bulan, Kalman 3-6 bulan)


def load_observed():
    observed = pd.read_parquet(ROOT / "data" / "interim" / "price_monthly_observed.parquet")
    observed["month"] = pd.PeriodIndex(observed["month"], freq="M")
    return observed


def eligible_series(observed):
    """Seri tier main untuk komoditas inti: {(price_type, commodity, province): Series harga bulanan Jan 2018-Okt 2026}."""
    out = {}
    for key, group in observed[observed["commodity_id"].isin(CORE_COMMODITIES)].groupby(["price_type_id", "commodity_id", "province_id"]):
        series = group.set_index("month")["price_observed"].reindex(MODEL_MONTHS)
        core_valid = series.loc[CORE_START:MODEL_END].notna().to_numpy()
        if assign_tier(core_valid.mean(), gap_profile(core_valid)["longest_interior_gap"]) == "main":
            out[key] = series
    return out


def run_holdout(draws=3, seed=42):
    rng = np.random.default_rng(seed)
    records = []
    for (price_type, commodity, province), series in eligible_series(load_observed()).items():
        values = series.to_numpy()
        size = len(values)
        for length in GAP_LENGTHS:
            starts = [s for s in range(1, size - length) if not np.isnan(values[s - 1 : s + length + 1]).any()]
            if not starts:
                continue
            for start in rng.choice(starts, size=min(draws, len(starts)), replace=False):
                masked = series.copy()
                masked.iloc[start : start + length] = np.nan
                truth = values[start : start + length]
                for name, method in METHODS.items():
                    predicted = method(masked).reindex(series.index).iloc[start : start + length].to_numpy()
                    for offset in range(length):
                        records.append((PRICE_TYPE_LABELS[price_type], COMMODITY_LABELS[commodity], province, length, int(start), offset + 1, name,
                                        abs(predicted[offset] - truth[offset]) / truth[offset]))
    return pd.DataFrame(records, columns=["price_type", "commodity", "province_id", "gap_length", "start", "position_in_gap", "method", "ape"])


def summarize(results):
    results = results.assign(bucket=np.where(results["gap_length"] <= SHORT_GAP, f"1-{SHORT_GAP} bulan", f"{SHORT_GAP + 1}-{MAX_FILL_GAP} bulan"))
    by_length = results.groupby(["gap_length", "method"])["ape"].mean().rename("mape").reset_index()
    by_bucket = results.groupby(["bucket", "method"])["ape"].mean().rename("mape").reset_index()
    overall = results.groupby("method")["ape"].mean().rename("mape").reset_index().assign(bucket=f"1-{MAX_FILL_GAP} bulan")
    by_type = results.groupby(["bucket", "price_type", "method"])["ape"].mean().rename("mape").reset_index()
    key = ["price_type", "commodity", "province_id", "gap_length", "start", "position_in_gap"]
    wide = results.pivot_table(index=key + ["bucket"], columns="method", values="ape").reset_index()
    wide["kalman_better"] = wide[CANDIDATE] < wide[BASELINE]
    paired = wide.groupby("bucket")["kalman_better"].agg(kalman_lebih_baik="mean", n="size").reset_index()
    return by_length, pd.concat([by_bucket, overall], ignore_index=True), by_type, paired


def decide(by_bucket):
    rows = []
    for bucket, part in by_bucket.groupby("bucket", sort=False):
        mape = part.set_index("method")["mape"]
        chosen = CANDIDATE if mape[CANDIDATE] < mape[BASELINE] else BASELINE
        rows.append({"bucket": bucket, "mape_linear_pct": mape[BASELINE] * 100, "mape_kalman_pct": mape[CANDIDATE] * 100,
                     "mape_locf_pct": mape["locf"] * 100, "kalman_lebih_akurat": mape[CANDIDATE] < mape[BASELINE], "metode_dipakai": chosen})
    return pd.DataFrame(rows)


def run(draws=3, seed=42, from_results=False):
    from pipeline.audit.loaders import to_markdown  # hanya untuk menulis laporan

    REPORTS.mkdir(parents=True, exist_ok=True)
    if from_results and RESULTS.exists():
        results = pd.read_csv(RESULTS)
    else:
        results = run_holdout(draws, seed)
        results.to_csv(RESULTS, index=False)
    by_length, by_bucket, by_type, paired = summarize(results)
    decision = decide(by_bucket)

    def pct(frame):
        return frame.assign(mape=frame["mape"] * 100)

    lines = ["# Hold-out validation: metode imputation harga (D-09, D-43)", "",
             f"Seri tier main cabai_merah dan cabai_rawit, tipe harga eceran, pedagang besar, produsen (baris provinsi dan nasional). Gap buatan 1-{MAX_FILL_GAP} bulan, "
             f"{results[['price_type','commodity','province_id']].drop_duplicates().shape[0]} seri, sampai {draws} posisi acak per panjang gap (seed {seed}), "
             f"{results[['price_type','commodity','province_id','gap_length','start']].drop_duplicates().shape[0]:,} gap buatan, "
             f"{len(results) // results['method'].nunique():,} nilai diprediksi per metode. Metrik: MAPE pada skala harga (Rp/kg). `locf` (nilai terakhir diteruskan) hanya pembanding.", "",
             "## 1. Keputusan", "",
             "Success criterion: metode imputasi dipilih lewat hold-out; jika tidak lebih akurat dari baseline linear, baseline yang dipakai. "
             f"Kandidat `{CANDIDATE}` tidak lebih akurat di bucket mana pun, jadi semua gap 1-{MAX_FILL_GAP} bulan memakai `{BASELINE}` (D-43).", "",
             to_markdown(decision, floatfmt="{:.2f}"), "",
             "## 2. MAPE per panjang gap (persen)", "", to_markdown(pct(by_length).pivot(index="gap_length", columns="method", values="mape").reset_index().astype({"gap_length": str}), floatfmt="{:.2f}"), "",
             "## 3. MAPE per bucket dan tipe harga (persen)", "", to_markdown(pct(by_type).pivot_table(index=["bucket", "price_type"], columns="method", values="mape").reset_index(), floatfmt="{:.2f}"), "",
             "## 4. Kalman vs linear pada gap yang sama (berpasangan)", "",
             "Porsi nilai prediksi yang lebih akurat dengan Kalman daripada dengan linear (persen):", "",
             to_markdown(paired.assign(kalman_lebih_baik=paired["kalman_lebih_baik"] * 100), floatfmt="{:.1f}"), "",
             "MAPE 15-27% mencerminkan gejolak harga cabai: satu bulan saja bisa bergeser puluhan persen, sehingga setiap uji H2/H4 wajib punya sensitivity check yang mengecualikan bulan imputasi (D-44).", ""]
    (REPORTS / "holdout_imputation.md").write_text("\n".join(lines), encoding="utf-8")
    print(decision.round(2).to_string(index=False))
    return decision


def main():
    parser = argparse.ArgumentParser(description="Hold-out validation metode imputation")
    parser.add_argument("--draws", type=int, default=3)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--from-results", action="store_true")
    args = parser.parse_args()
    run(args.draws, args.seed, args.from_results)


if __name__ == "__main__":
    main()
