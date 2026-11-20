"""Lampiran H1 (eksploratif, D-59): adakah sinyal cuaca untuk cabai merah yang tidak tertangkap uji H1?

E1. Anomali kelembapan (rh_anomaly, logit kelembapan relatif, z-score per lokasi x bulan kalender 1991-2020,
    berbobot produksi) lag 1-4 + kuadrat terhadap harga produsen dan pedagang besar. Spesifikasi panel sama
    dengan H1. Dasar: antraknosa di pohon sebab-akibat (lembap -> penyakit -> pasokan turun).
E2. Indeks cuaca nasional berbobot produksi sentra cabai merah (hujan dan kelembapan) terhadap log harga
    pedagang besar nasional, time series bulanan Jan 2019 - Okt 2026, lag 1-4, FE bulan kalender + trend + ONI,
    SE HAC (maxlags 6).

Kriteria sinyal konsisten (D-59, ditetapkan sebelum uji): variabel masuk H4 merah kalau
    (i)  panel pedagang besar: uji gabungan lag 1-4 p < 0,05, tetap p < 0,05 tanpa bulan ekstrem, dan arah efek
         kumulatif sama dengan harga produsen; atau
    (ii) indeks nasional: uji gabungan lag 1-4 p < 0,05 dengan arah efek kumulatif sama seperti panel pedagang besar.
Hasil ini bukan bagian keputusan H1.

    python -m analysis.h1_exploratory_merah
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm

from analysis.h1_weather import ALPHA, MAIN_LAGS, combination, fit, joint_test, per_lag, prepare, summarise
from analysis.style import ROOT, TABLES, load_core, national_prices, setup

GROUP = "cabai_merah"
HAC_LAGS = 6
VARIABLES = {"rain_anomaly": "hujan", "rh_anomaly": "kelembapan"}
OUTCOMES = {"log_producer": ("harga produsen", "price_producer_tier"), "log_wholesale": ("harga pedagang besar", "price_wholesale_tier")}


def panel_tests(data):
    rows, lag_tables = [], []
    not_extreme = ~data["extreme_in_lags"]
    for variable, variable_label in VARIABLES.items():
        for outcome, (outcome_label, tier_column) in OUTCOMES.items():
            for spec, kwargs in (("utama", {}), ("tanpa bulan ekstrem", {"mask": not_extreme}), ("linear", {"quadratic": False})):
                fitted, sample, _ = fit(data, GROUP, variable=variable, outcome=outcome, tier_column=tier_column, **kwargs)
                quadratic = kwargs.get("quadratic", True)
                out = summarise(fitted, sample, variable, MAIN_LAGS, quadratic)
                rows.append({"variabel": variable_label, "outcome": outcome_label, "spesifikasi": spec, **out})
                lag_tables.append(per_lag(fitted, variable, MAIN_LAGS, quadratic).assign(variabel=variable_label, outcome=outcome_label, spesifikasi=spec))
    return pd.DataFrame(rows), pd.concat(lag_tables, ignore_index=True)


def national_index():
    """Rata-rata berbobot produksi sentra cabai merah dari anomali provinsi (setara rata-rata berbobot per lokasi)."""
    points = pd.read_csv(ROOT / "data" / "interim" / "sentra_points.csv")
    weights = points[points["commodity_group"] == GROUP].groupby("province_id")["mean_production_ton_2019_2025"].sum()
    core = load_core()
    weather = core[(core["commodity_group"] == GROUP) & (core["weather_status"] == "observed")].copy()
    weather["weight"] = weather["province_id"].map(weights)
    index = weather.groupby("month").apply(lambda m: pd.Series({name: np.average(m[name], weights=m["weight"]) for name in VARIABLES}), include_groups=False)
    oni = core.drop_duplicates("month").set_index("month")["oni_anomaly"]
    return index.join(oni)


def national_tests():
    index = national_index()
    prices = national_prices()
    wholesale = prices[(prices["price_type"] == "pedagang_besar") & (prices["commodity"] == GROUP)].set_index("month")["price_idr_per_kg"]
    frame = index.join(np.log(wholesale).rename("log_wholesale"), how="left")
    for name in VARIABLES:
        for k in MAIN_LAGS:
            frame[f"{name}_l{k}"] = frame[name].shift(k)
    frame = frame[(frame.index >= pd.Period("2019-01", "M")) & (frame.index <= pd.Period("2026-10", "M"))].copy()
    frame["trend"] = np.arange(len(frame)) / 12
    months = pd.get_dummies(frame.index.month, prefix="m", drop_first=True, dtype=float).set_index(frame.index)
    rows = []
    for label, names in (("hujan", ["rain_anomaly"]), ("kelembapan", ["rh_anomaly"]), ("hujan + kelembapan", list(VARIABLES))):
        terms = [f"{n}_l{k}" for n in names for k in MAIN_LAGS]
        sample = frame.dropna(subset=["log_wholesale", "oni_anomaly", *terms])
        X = sm.add_constant(pd.concat([sample[terms + ["trend", "oni_anomaly"]], months.loc[sample.index]], axis=1))
        fitted = sm.OLS(sample["log_wholesale"], X).fit(cov_type="HAC", cov_kwds={"maxlags": HAC_LAGS})
        for name in names:
            lagged = [f"{name}_l{k}" for k in MAIN_LAGS]
            chi2, p = joint_test(fitted, lagged)
            effect, low, high, p_cum = combination(fitted, {n: 1.0 for n in lagged})
            best = max(MAIN_LAGS, key=lambda k: abs(fitted.tvalues[f"{name}_l{k}"]))
            rows.append({"model": label, "variabel": VARIABLES[name], "n": len(sample), "sd_indeks": frame[name].std(), "uji_gabungan_p": p,
                         "efek_+1_kumulatif_pct": effect, "ci_bawah": low, "ci_atas": high, "p_kumulatif": p_cum,
                         "lag_terkuat": best, "p_lag_terkuat": fitted.pvalues[f"{name}_l{best}"]})
    return pd.DataFrame(rows), index


def verdict(panel, national):
    rows = []
    for label in VARIABLES.values():
        pick = lambda outcome, spec: panel[(panel["variabel"] == label) & (panel["outcome"] == outcome) & (panel["spesifikasi"] == spec)].iloc[0]
        wholesale, wholesale_b = pick("harga pedagang besar", "utama"), pick("harga pedagang besar", "tanpa bulan ekstrem")
        sign_wholesale = np.sign(pick("harga pedagang besar", "linear")["efek_+1.0_pct"])
        sign_producer = np.sign(pick("harga produsen", "linear")["efek_+1.0_pct"])
        criterion_i = bool(wholesale["semua_lag_p"] < ALPHA and wholesale_b["semua_lag_p"] < ALPHA and sign_wholesale == sign_producer)
        single = national[(national["model"] == label)].iloc[0]
        criterion_ii = bool(single["uji_gabungan_p"] < ALPHA and np.sign(single["efek_+1_kumulatif_pct"]) == sign_wholesale)
        rows.append({"variabel": label, "panel_pedagang_besar_p": wholesale["semua_lag_p"], "panel_tanpa_ekstrem_p": wholesale_b["semua_lag_p"],
                     "arah_pedagang_besar": int(sign_wholesale), "arah_produsen": int(sign_producer), "kriteria_i": criterion_i,
                     "nasional_p": single["uji_gabungan_p"], "arah_nasional": int(np.sign(single["efek_+1_kumulatif_pct"])), "kriteria_ii": criterion_ii,
                     "masuk_h4": criterion_i or criterion_ii})
    return pd.DataFrame(rows)


def run():
    setup()
    data, _ = prepare()
    panel, lags = panel_tests(data)
    national, index = national_tests()
    decision = verdict(panel, national)
    panel.to_csv(TABLES / "h1x_merah_panel.csv", index=False)
    lags.to_csv(TABLES / "h1x_merah_panel_lags.csv", index=False)
    national.to_csv(TABLES / "h1x_merah_national.csv", index=False)
    index.assign(month=index.index.astype(str)).to_csv(TABLES / "h1x_merah_national_index.csv", index=False)
    decision.to_csv(TABLES / "h1x_merah_verdict.csv", index=False)
    pd.set_option("display.width", 250)
    columns = ["variabel", "outcome", "spesifikasi", "n", "semua_lag_p", "kuadrat_p", "efek_-1.5_pct", "p_-1.5", "efek_+1.5_pct", "p_+1.5", "efek_-1.0_pct", "efek_+1.0_pct", "p_+1.0"]
    print(panel[columns].round(3).to_string(index=False))
    print(lags[lags["spesifikasi"] != "tanpa bulan ekstrem"][["variabel", "outcome", "spesifikasi", "lag", "chi2_lag", "p_lag", "efek_-1.5_pct", "efek_+1.5_pct"]].round(3).to_string(index=False))
    print(national.round(3).to_string(index=False))
    print(decision.round(3).to_string(index=False))


if __name__ == "__main__":
    run()
