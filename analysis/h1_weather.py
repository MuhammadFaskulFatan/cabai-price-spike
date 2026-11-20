"""H1: apakah hujan ekstrem di sentra (terlalu kering atau terlalu basah) menaikkan harga produsen, dan berapa lag-nya?

Rencana: docs/05_analysis_plan.md bagian 7 (D-48), ketentuan tambahan D-58. Panel provinsi bertitik sentra x bulan:
    log(harga produsen) = sum_k [b_k * anomali_{t-k} + c_k * anomali_{t-k}^2], k = 1..4
                          + FE provinsi + FE month-of-year + trend + ONI + e            (spesifikasi utama)
anomali = rain_anomaly (rata-rata berbobot produksi dari z-score per lokasi, akar kuadrat hujan, baseline 1991-2020).
SE Driscoll-Kraay (maxlags 6): anomali hujan berkorelasi antarprovinsi di bulan yang sama dan residual harga
berkorelasi antarbulan.

Pola U didukung kalau: uji gabungan 4 suku kuadrat p < 0,05, jumlah koefisien kuadrat positif, dan efek kumulatif
lag 1-4 positif di anomali -1,5 dan +1,5. Klaim U hanya kalau bertahan di sensitivity (a) winsorize dan (b) tanpa
bulan ekstrem (D-58). Jalur produksi diuji di grain tahunan (produksi bulanan tidak ada, D-42).

    python -m analysis.h1_weather
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

from analysis.style import ACCENT, FIGURES, GROUP_COLOR, GROUP_LABEL, INK_2, MUTED, SURFACE, TABLES, FINAL, load_core, plt, setup

ALPHA = 0.05
MAIN_LAGS = (1, 2, 3, 4)
DK_LAGS = 6
EXTREME_POINTS = (-1.5, -1.0, 1.0, 1.5)
U_POINT = 1.5


def add_lags(core, columns, lags):
    core = core.sort_values(["province_id", "commodity_group", "month"]).copy()
    grouped = core.groupby(["province_id", "commodity_group"])
    for column in columns:
        for k in lags:
            core[f"{column}_l{k}"] = grouped[column].shift(k)
    return core


def prepare():
    core = load_core()
    core = core[core["weather_status"].isin(["observed", "partial_month"])].copy()
    core["rain_is_extreme"] = core["rain_is_extreme"].fillna(False).astype(bool)
    # winsorize (a): batas persentil 1/99 dari seluruh bulan observed 2018 - Okt 2026, per komoditas
    observed = core[core["weather_status"] == "observed"]
    bounds = observed.groupby("commodity_group")["rain_anomaly"].quantile([0.01, 0.99]).unstack()
    core["rain_anomaly_wins"] = core["rain_anomaly"].clip(core["commodity_group"].map(bounds[0.01]), core["commodity_group"].map(bounds[0.99]))
    for label, lower, upper in (("dry", -np.inf, -1.0), ("wet", 1.0, np.inf)):
        core[f"rain_{label}"] = core["rain_anomaly"].between(lower, upper, inclusive="neither").astype(float).where(core["rain_anomaly"].notna())
    core = add_lags(core, ["rain_anomaly", "rain_anomaly_wins", "rain_anomaly_plain_z", "rain_dry", "rain_wet", "rain_is_extreme", "rh_anomaly"], range(0, 7))
    data = core[core["in_model_period"]].copy()
    data["log_producer"] = np.log(data["price_producer"])
    data["log_wholesale"] = np.log(data["price_wholesale"])
    data["trend"] = (data["month"] - pd.Period("2019-01", "M")).apply(lambda d: d.n) / 12
    data["moy"] = data["month"].dt.month
    data["time"] = (data["month"] - pd.Period("2019-01", "M")).apply(lambda d: d.n)
    data["extreme_in_lags"] = data[[f"rain_is_extreme_l{k}" for k in MAIN_LAGS]].fillna(False).astype(bool).any(axis=1)
    return data, bounds


def design(sample, variable, lags, quadratic, fe, controls):
    terms = []
    for k in lags:
        name = f"{variable}_l{k}"
        terms.append(name)
        if quadratic:
            sample[f"{name}_sq"] = sample[name] ** 2
            terms.append(f"{name}_sq")
    blocks = [sample[terms + list(controls)], pd.get_dummies(sample["province_id"], prefix="p", drop_first=True, dtype=float)]
    if fe == "moy":
        blocks.append(pd.get_dummies(sample["moy"], prefix="m", drop_first=True, dtype=float))
    else:
        blocks.append(pd.get_dummies(sample["month"].astype(str), prefix="ym", drop_first=True, dtype=float))
    return sm.add_constant(pd.concat(blocks, axis=1)), terms


def fit(data, group, variable="rain_anomaly", lags=MAIN_LAGS, quadratic=True, fe="moy", controls=("trend", "oni_anomaly"),
        outcome="log_producer", tier_column="price_producer_tier", tiers=("main",), mask=None):
    sample = data[(data["commodity_group"] == group) & data[tier_column].isin(tiers)]
    if outcome == "log_producer":
        sample = sample[sample["in_producer_price_analysis"]]
    if mask is not None:
        sample = sample[mask.loc[sample.index]]
    needed = [outcome] + [f"{variable}_l{k}" for k in lags] + list(controls)
    sample = sample.dropna(subset=needed).copy()
    X, terms = design(sample, variable, lags, quadratic, fe, controls)
    fitted = sm.OLS(sample[outcome], X).fit(cov_type="hac-groupsum", cov_kwds={"time": sample["time"].to_numpy(), "maxlags": DK_LAGS})
    return fitted, sample, terms


def combination(fitted, weights):
    """Kombinasi linear koefisien -> (efek %, CI bawah %, CI atas %, p)."""
    names = list(weights)
    vector = np.array([weights[n] for n in names])
    estimate = float(vector @ fitted.params[names].to_numpy())
    se = float(np.sqrt(vector @ fitted.cov_params().loc[names, names].to_numpy() @ vector))
    z = stats.norm.ppf(1 - ALPHA / 2)
    p = 2 * (1 - stats.norm.cdf(abs(estimate / se))) if se > 0 else np.nan
    pct = lambda x: (np.exp(x) - 1) * 100
    return pct(estimate), pct(estimate - z * se), pct(estimate + z * se), p


def joint_test(fitted, names):
    """Uji Wald gabungan (chi2) untuk koefisien = 0."""
    restriction = np.zeros((len(names), len(fitted.params)))
    for i, name in enumerate(names):
        restriction[i, list(fitted.params.index).index(name)] = 1
    result = fitted.wald_test(restriction, scalar=True)
    return float(result.statistic), float(result.pvalue)


def cumulative_effect(fitted, variable, lags, value, quadratic=True):
    weights = {f"{variable}_l{k}": value for k in lags}
    if quadratic:
        weights.update({f"{variable}_l{k}_sq": value ** 2 for k in lags})
    return combination(fitted, weights)


def summarise(fitted, sample, variable, lags, quadratic=True):
    out = {"n": len(sample), "provinsi": sample["province_id"].nunique(), "periode": f"{sample['month'].min()} s/d {sample['month'].max()}"}
    all_terms = [f"{variable}_l{k}" for k in lags] + ([f"{variable}_l{k}_sq" for k in lags] if quadratic else [])
    out["semua_lag_chi2"], out["semua_lag_p"] = joint_test(fitted, all_terms)
    if quadratic:
        squares = [f"{variable}_l{k}_sq" for k in lags if k in MAIN_LAGS]
        out["kuadrat_chi2"], out["kuadrat_p"] = joint_test(fitted, squares)
        out["jumlah_kuadrat"] = float(fitted.params[squares].sum())
    for value in EXTREME_POINTS:
        effect, low, high, p = cumulative_effect(fitted, variable, [k for k in lags if k in MAIN_LAGS], value, quadratic)
        key = f"{value:+.1f}"
        out[f"efek_{key}_pct"], out[f"ci_bawah_{key}"], out[f"ci_atas_{key}"], out[f"p_{key}"] = effect, low, high, p
    if "oni_anomaly" in fitted.params:
        effect, low, high, p = combination(fitted, {"oni_anomaly": 1.0})
        out["oni_efek_pct"], out["oni_p"] = effect, p
    if quadratic:
        out["pola_u"] = bool(out["kuadrat_p"] < ALPHA and out["jumlah_kuadrat"] > 0 and out[f"efek_{-U_POINT:+.1f}_pct"] > 0 and out[f"efek_{U_POINT:+.1f}_pct"] > 0)
    return out


def per_lag(fitted, variable, lags, quadratic=True):
    rows = []
    for k in lags:
        name = f"{variable}_l{k}"
        square = f"{name}_sq"
        chi2, p = joint_test(fitted, [name, square] if quadratic else [name])
        row = {"lag": k, "chi2_lag": chi2, "p_lag": p, "b_linear": fitted.params[name],
               "c_kuadrat": fitted.params[square] if quadratic else np.nan, "p_kuadrat": fitted.pvalues[square] if quadratic else np.nan}
        for value in (-U_POINT, U_POINT):
            effect, low, high, p_value = combination(fitted, {name: value, square: value ** 2} if quadratic else {name: value})
            key = f"{value:+.1f}"
            row[f"efek_{key}_pct"], row[f"ci_bawah_{key}"], row[f"ci_atas_{key}"] = effect, low, high
        rows.append(row)
    return pd.DataFrame(rows)


def specifications(data):
    """(label, kwargs untuk fit). Empat sensitivity wajib D-58 di urutan pertama, lalu sensitivity dari rencana."""
    not_extreme = ~data["extreme_in_lags"]
    not_imputed = data["price_producer_is_imputed"] != True
    return {
        "utama": {},
        "(a) winsorize 1/99": {"variable": "rain_anomaly_wins"},
        "(b) tanpa bulan ekstrem di lag 1-4": {"mask": not_extreme},
        "(c) tanpa bulan imputasi (D-44)": {"mask": not_imputed},
        "(d) FE tahun-bulan (D-48)": {"fe": "ym", "controls": ()},
        "(a)+(b)": {"variable": "rain_anomaly_wins", "mask": not_extreme},
        "z-score biasa (tanpa akar)": {"variable": "rain_anomaly_plain_z"},
        "tanpa ONI": {"controls": ("trend",)},
        "lag 0-6": {"lags": tuple(range(0, 7))},
        "outcome harga pedagang besar": {"outcome": "log_wholesale", "tier_column": "price_wholesale_tier"},
        "linear saja (tanpa kuadrat)": {"quadratic": False},
    }


def run_specs(data):
    rows, lag_tables, fits = [], [], {}
    for group in GROUP_LABEL:
        for label, kwargs in specifications(data).items():
            fitted, sample, _ = fit(data, group, **kwargs)
            variable, lags, quadratic = kwargs.get("variable", "rain_anomaly"), kwargs.get("lags", MAIN_LAGS), kwargs.get("quadratic", True)
            rows.append({"grup": group, "spesifikasi": label, **summarise(fitted, sample, variable, lags, quadratic)})
            lags_frame = per_lag(fitted, variable, lags, quadratic).assign(grup=group, spesifikasi=label)
            lag_tables.append(lags_frame)
            fits[(group, label)] = (fitted, variable)
    return pd.DataFrame(rows), pd.concat(lag_tables, ignore_index=True), fits


def categories(data):
    """Sensitivity dari rencana: dummy kering (< -1) dan basah (> +1) lag 1-4 menggantikan kuadrat."""
    rows = []
    for group in GROUP_LABEL:
        sample = data[(data["commodity_group"] == group) & (data["price_producer_tier"] == "main") & data["in_producer_price_analysis"]]
        terms = [f"rain_{label}_l{k}" for label in ("dry", "wet") for k in MAIN_LAGS]
        sample = sample.dropna(subset=["log_producer", "oni_anomaly", *terms]).copy()
        X = sm.add_constant(pd.concat([sample[terms + ["trend", "oni_anomaly"]],
                                       pd.get_dummies(sample["province_id"], prefix="p", drop_first=True, dtype=float),
                                       pd.get_dummies(sample["moy"], prefix="m", drop_first=True, dtype=float)], axis=1))
        fitted = sm.OLS(sample["log_producer"], X).fit(cov_type="hac-groupsum", cov_kwds={"time": sample["time"].to_numpy(), "maxlags": DK_LAGS})
        for label, name in (("kering", "dry"), ("basah", "wet")):
            names = [f"rain_{name}_l{k}" for k in MAIN_LAGS]
            effect, low, high, p = combination(fitted, {n: 1.0 for n in names})
            chi2, joint_p = joint_test(fitted, names)
            share = sample[f"rain_{name}_l1"].mean() * 100
            rows.append({"grup": group, "kategori": label, "porsi_bulan_pct": share, "efek_kumulatif_pct": effect, "ci_bawah": low, "ci_atas": high,
                         "p_kumulatif": p, "p_gabungan": joint_p, "n": len(sample)})
    return pd.DataFrame(rows)


def leave_one_out(data):
    """Pemeriksaan pendukung: spesifikasi linear diulang dengan membuang satu tahun atau satu provinsi."""
    rows = []
    for group in GROUP_LABEL:
        for kind, column in (("tahun", data["month"].dt.year), ("provinsi", data["province_id"])):
            for value in sorted(column[data["commodity_group"] == group].unique()):
                fitted, sample, _ = fit(data, group, quadratic=False, mask=column != value)
                effect, low, high, p = cumulative_effect(fitted, "rain_anomaly", MAIN_LAGS, -1.0, quadratic=False)
                chi2, p_lag3 = joint_test(fitted, ["rain_anomaly_l3"])
                rows.append({"grup": group, "dibuang": kind, "nilai": value, "n": len(sample), "efek_kering_1sd_pct": effect, "p_kumulatif": p,
                             "b_lag3": fitted.params["rain_anomaly_l3"], "p_lag3": p_lag3})
    return pd.DataFrame(rows)


def annual_production(data_points):
    """Jalur produksi, grain tahunan: dlog produksi pada rata-rata anomali tahunan dan rata-rata kuadratnya, FE tahun."""
    core = load_core()
    core = core[core["weather_status"] == "observed"].copy()
    core["year"] = core["month"].dt.year
    core["anom_sq"] = core["rain_anomaly"] ** 2
    yearly = core[core["year"] <= 2025].groupby(["province_id", "commodity_group", "year"]).agg(
        anomali=("rain_anomaly", "mean"), anomali_kuadrat=("anom_sq", "mean"), bulan_ekstrem=("rain_is_extreme", "sum")).reset_index()
    production = pd.read_csv(FINAL / "core_province_year.csv")
    production = production.sort_values(["province_id", "commodity_group", "year"])
    production["dlog_produksi"] = production.groupby(["province_id", "commodity_group"])["production_ton"].transform(lambda s: np.log(s.where(s > 0)).diff())
    merged = yearly.merge(production[["province_id", "commodity_group", "year", "dlog_produksi", "is_outlier"]], on=["province_id", "commodity_group", "year"]).dropna(subset=["dlog_produksi"])
    rows = []
    for group in GROUP_LABEL:
        for label, subset in (("utama 2019-2025", merged), ("tanpa 2025 (preliminary)", merged[merged["year"] <= 2024]), ("tanpa outlier produktivitas", merged[~merged["is_outlier"].astype(bool)])):
            part = subset[subset["commodity_group"] == group]
            X = sm.add_constant(pd.concat([part[["anomali", "anomali_kuadrat"]], pd.get_dummies(part["year"], prefix="y", drop_first=True, dtype=float)], axis=1))
            fitted = sm.OLS(part["dlog_produksi"], X).fit(cov_type="cluster", cov_kwds={"groups": part["province_id"]})
            row = {"grup": group, "spesifikasi": label, "n": len(part), "provinsi": part["province_id"].nunique()}
            for name in ("anomali", "anomali_kuadrat"):
                row[f"{name}_koef"], row[f"{name}_p"] = fitted.params[name], fitted.pvalues[name]
            # efek tahun dengan rata-rata anomali +-1 vs 0 (kuadrat ikut naik 1)
            for value in (-1.0, 1.0):
                effect, low, high, p = combination(fitted, {"anomali": value, "anomali_kuadrat": value ** 2})
                row[f"efek_{value:+.0f}_pct"], row[f"p_{value:+.0f}"] = effect, p
            rows.append(row)
    return pd.DataFrame(rows)


def curve(fitted, variable, values):
    rows = []
    for value in values:
        effect, low, high, _ = cumulative_effect(fitted, variable, MAIN_LAGS, value)
        rows.append({"anomali": value, "efek": effect, "bawah": low, "atas": high})
    return pd.DataFrame(rows)


def chart_curves(fits, data, path):
    values = np.round(np.arange(-2.5, 2.51, 0.1), 2)
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.9), sharey=True)
    for ax, group in zip(axes, GROUP_LABEL):
        fitted, variable = fits[(group, "utama")]
        main = curve(fitted, variable, values)
        ax.fill_between(main["anomali"], main["bawah"], main["atas"], color=GROUP_COLOR[group], alpha=0.15, linewidth=0)
        ax.plot(main["anomali"], main["efek"], color=GROUP_COLOR[group], linewidth=2, label="utama (95% CI)")
        for label, style in (("(a) winsorize 1/99", (0, (4, 2))), ("(b) tanpa bulan ekstrem di lag 1-4", (0, (1, 1.5)))):
            alt_fit, alt_variable = fits[(group, label)]
            alt = curve(alt_fit, alt_variable, values)
            ax.plot(alt["anomali"], alt["efek"], color=INK_2, linewidth=1.1, linestyle=style, label=label)
        observed = data[(data["commodity_group"] == group)]["rain_anomaly_l1"].dropna()
        low, high = observed.quantile([0.05, 0.95])
        ax.axvspan(-2.5, low, color=MUTED, alpha=0.18, linewidth=0)
        ax.axvspan(high, 2.5, color=MUTED, alpha=0.18, linewidth=0)
        ax.axhline(0, color=INK_2, linewidth=0.8)
        ax.set_title(GROUP_LABEL[group], loc="left", fontsize=9, color=INK_2)
        ax.set_xlabel("anomali hujan di sentra, sama di lag 1-4 (z)")
    axes[0].set_ylabel("harga produsen vs anomali 0 (%)")
    axes[0].legend(loc="upper left", fontsize=7.5)
    fig.suptitle("H1: efek kumulatif anomali hujan lag 1-4 terhadap harga produsen", x=0.01, ha="left", fontweight="bold", fontsize=10)
    fig.text(0.01, 0.905, "Area abu-abu = di luar persentil 5-95 data; FE provinsi, FE bulan kalender, trend, ONI; SE Driscoll-Kraay",
             fontsize=7.5, color=INK_2, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    fig.savefig(path, dpi=150)
    plt.close(fig)


def chart_lags(lag_table, path):
    main = lag_table[lag_table["spesifikasi"] == "utama"]
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.6), sharey=True)
    for ax, (value, title) in zip(axes, ((-U_POINT, "Sangat kering (anomali -1,5)"), (U_POINT, "Sangat basah (anomali +1,5)"))):
        key = f"{value:+.1f}"
        for offset, group in zip((-0.1, 0.1), GROUP_LABEL):
            part = main[main["grup"] == group]
            ax.errorbar(part["lag"] + offset, part[f"efek_{key}_pct"], yerr=[part[f"efek_{key}_pct"] - part[f"ci_bawah_{key}"], part[f"ci_atas_{key}"] - part[f"efek_{key}_pct"]],
                        fmt="o", color=GROUP_COLOR[group], elinewidth=1.2, capsize=0, markersize=6, markeredgecolor=SURFACE, label=GROUP_LABEL[group])
        ax.axhline(0, color=INK_2, linewidth=0.8)
        ax.set_xticks(list(MAIN_LAGS), [f"lag {k}" for k in MAIN_LAGS])
        ax.set_title(title, loc="left", fontsize=9, color=INK_2)
    axes[0].set_ylabel("harga produsen vs anomali 0 (%)")
    axes[0].legend(loc="upper left", fontsize=8)
    fig.suptitle("H1: efek per lag (lag lain ditahan nol), spesifikasi utama", x=0.01, ha="left", fontweight="bold", fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(path, dpi=150)
    plt.close(fig)


def run():
    setup()
    data, bounds = prepare()
    results, lag_table, fits = run_specs(data)
    cats = categories(data)
    production = annual_production(data)
    loo = leave_one_out(data)
    loo.to_csv(TABLES / "h1_leave_one_out.csv", index=False)
    chart_curves(fits, data, FIGURES / "h1_rain_effect_curve.png")
    chart_lags(lag_table, FIGURES / "h1_lag_profile.png")
    results.to_csv(TABLES / "h1_results.csv", index=False)
    lag_table.to_csv(TABLES / "h1_lag_effects.csv", index=False)
    cats.to_csv(TABLES / "h1_categories.csv", index=False)
    production.to_csv(TABLES / "h1_production_annual.csv", index=False)
    bounds.to_csv(TABLES / "h1_winsor_bounds.csv")
    extreme = data[(data["price_producer_tier"] == "main")].groupby("commodity_group")["extreme_in_lags"].agg(["sum", "size"])
    print(extreme)
    print(bounds)
    pd.set_option("display.width", 250)
    columns = ["grup", "spesifikasi", "n", "provinsi", "semua_lag_p", "kuadrat_p", "jumlah_kuadrat", "efek_-1.5_pct", "p_-1.5", "efek_+1.5_pct", "p_+1.5", "efek_-1.0_pct", "efek_+1.0_pct", "pola_u"]
    print(results[columns].round(3).to_string(index=False))
    print(lag_table[lag_table["spesifikasi"].isin(["utama", "(a) winsorize 1/99", "(b) tanpa bulan ekstrem di lag 1-4", "(d) FE tahun-bulan (D-48)", "outcome harga pedagang besar", "lag 0-6", "linear saja (tanpa kuadrat)"])]
          [["grup", "spesifikasi", "lag", "chi2_lag", "p_lag", "c_kuadrat", "p_kuadrat", "efek_-1.5_pct", "efek_+1.5_pct"]].round(3).to_string(index=False))
    print(cats.round(3).to_string(index=False))
    print(production.round(3).to_string(index=False))
    print(loo.groupby(["grup", "dibuang"]).agg(efek_min=("efek_kering_1sd_pct", "min"), efek_maks=("efek_kering_1sd_pct", "max"), p_maks=("p_kumulatif", "max"),
                                               p_lag3_maks=("p_lag3", "max"), b_lag3_min=("b_lag3", "min"), b_lag3_maks=("b_lag3", "max")).round(3).to_string())
    print(loo.sort_values("p_kumulatif", ascending=False).groupby("grup").head(3).round(3).to_string(index=False))


if __name__ == "__main__":
    run()
