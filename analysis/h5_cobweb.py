"""H5: apakah harga produsen tinggi mendorong luas panen naik tahun berikutnya (cobweb)?

Rencana: docs/05_analysis_plan.md bagian 5 (D-48). Panel provinsi x tahun (core_province_year, 2018-2025):
    dlog(luas panen)_t = b * log(harga produsen)_(t-1) + FE provinsi [+ FE tahun] + e
SE cluster provinsi. Outcome kedua: dlog(produksi)_t. Provinsi yang keluar dari analisis harga produsen (NTT) dan
seri harga produsen tier excluded tidak dipakai; provinsi-tahun dengan luas panen 0 tidak bisa di-log.
Sensitivity: tanpa is_outlier (t atau t-1), tanpa 2025, hanya tahun dengan >= 9 bulan harga, rata-rata harga tanpa
bulan imputasi (D-44), dan year FE (menyerap variasi harga nasional, sehingga hanya variasi antarprovinsi yang tersisa).

    python -m analysis.h5_cobweb
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm

from analysis.style import FIGURES, FINAL, GROUP_COLOR, GROUP_LABEL, INK_2, SURFACE, TABLES, load_core, md, plt, setup

ALPHA = 0.05


def annual_price_without_imputed():
    core = load_core()
    producer = core[(~core["is_partial_month"]) & (core["price_producer_is_imputed"] != True)]
    producer = producer.assign(year=producer["month"].dt.year)
    return producer.groupby(["province_id", "year", "commodity_group"])["price_producer"].mean().rename("price_no_imputed").reset_index()


def panel():
    year = pd.read_csv(FINAL / "core_province_year.csv")
    year = year.merge(annual_price_without_imputed(), on=["province_id", "year", "commodity_group"], how="left")
    year = year.sort_values(["commodity_group", "province_id", "year"])
    rows = []
    for (group, province), part in year.groupby(["commodity_group", "province_id"]):
        part = part.set_index("year")
        frame = pd.DataFrame(index=part.index)
        frame["d_log_area"] = np.log(part["harvested_area_ha"].where(part["harvested_area_ha"] > 0)).diff()
        frame["d_log_production"] = np.log(part["production_ton"].where(part["production_ton"] > 0)).diff()
        frame["log_price_l1"] = np.log(part["producer_price_annual_mean"]).shift(1)
        frame["log_price_l1_no_imputed"] = np.log(part["price_no_imputed"]).shift(1)
        frame["price_months_l1"] = part["producer_price_n_months"].shift(1)
        frame["outlier_t_or_l1"] = part["is_outlier"] | part["is_outlier"].shift(1, fill_value=False)
        frame["eligible"] = bool(part["in_producer_price_analysis"].iloc[0]) and part["producer_price_tier"].dropna().iloc[0] != "excluded" if part["producer_price_tier"].notna().any() else False
        rows.append(frame.reset_index().assign(commodity_group=group, province_id=province))
    data = pd.concat(rows, ignore_index=True)
    return data[data["eligible"]]


def estimate(data, outcome="d_log_area", price="log_price_l1", year_fe=False):
    sample = data.dropna(subset=[outcome, price]).copy()
    regressors = [sample[[price]]]
    regressors.append(pd.get_dummies(sample["province_id"], prefix="p", drop_first=True, dtype=float))
    if year_fe:
        regressors.append(pd.get_dummies(sample["year"], prefix="y", drop_first=True, dtype=float))
    X = sm.add_constant(pd.concat(regressors, axis=1))
    fitted = sm.OLS(sample[outcome], X).fit(cov_type="cluster", cov_kwds={"groups": sample["province_id"]})
    low, high = fitted.conf_int().loc[price]
    return {"n": len(sample), "provinsi": sample["province_id"].nunique(), "tahun": f"{sample['year'].min()}-{sample['year'].max()}",
            "elastisitas": fitted.params[price], "ci_bawah": low, "ci_atas": high, "p": fitted.pvalues[price]}


def specifications(data):
    specs = {
        "utama (FE provinsi)": (data, {}),
        "tanpa is_outlier (t atau t-1)": (data[~data["outlier_t_or_l1"]], {}),
        "tanpa 2025": (data[data["year"] < 2025], {}),
        "harga t-1 dari >= 9 bulan": (data[data["price_months_l1"] >= 9], {}),
        "harga t-1 tanpa bulan imputasi (D-44)": (data, {"price": "log_price_l1_no_imputed"}),
        "pembanding: + year FE": (data, {"year_fe": True}),
    }
    rows = []
    for group in GROUP_LABEL:
        for outcome, outcome_label in (("d_log_area", "luas panen"), ("d_log_production", "produksi")):
            for label, (subset, kwargs) in specs.items():
                result = estimate(subset[subset["commodity_group"] == group], outcome=outcome, **kwargs)
                rows.append({"grup": group, "outcome": outcome_label, "spesifikasi": label, **result})
    return pd.DataFrame(rows)


def decide(results):
    rows = []
    for group in GROUP_LABEL:
        area = results[(results["grup"] == group) & (results["outcome"] == "luas panen")]
        main = area[area["spesifikasi"] == "utama (FE provinsi)"].iloc[0]
        all_positive = bool((area["elastisitas"] > 0).all())
        supported = main["elastisitas"] > 0 and main["p"] < ALPHA and all_positive
        rows.append({"grup": group, "elastisitas_utama": main["elastisitas"], "p_utama": main["p"], "positif_di_semua_sensitivity": all_positive,
                     "keputusan": "didukung" if supported else ("tidak didukung; arah positif konsisten (indikatif)" if all_positive else "tidak didukung")})
    return pd.DataFrame(rows)


def chart(data, results, path):
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=True)
    for ax, group in zip(axes, GROUP_LABEL):
        part = data[(data["commodity_group"] == group)].dropna(subset=["d_log_area", "log_price_l1"]).copy()
        part["x"] = part["log_price_l1"] - part.groupby("province_id")["log_price_l1"].transform("mean")
        part["y"] = part["d_log_area"] - part.groupby("province_id")["d_log_area"].transform("mean")
        bins = pd.qcut(part["x"], 10, duplicates="drop")
        binned = part.groupby(bins, observed=True)[["x", "y"]].mean()
        ax.scatter(part["x"] * 100, part["y"] * 100, s=10, color=GROUP_COLOR[group], alpha=0.25, edgecolor="none", label="provinsi-tahun")
        ax.scatter(binned["x"] * 100, binned["y"] * 100, s=40, color=GROUP_COLOR[group], edgecolor=SURFACE, linewidth=1.2, zorder=3, label="rata-rata per desil harga")
        main = results[(results["grup"] == group) & (results["outcome"] == "luas panen") & (results["spesifikasi"] == "utama (FE provinsi)")].iloc[0]
        xs = np.linspace(part["x"].min(), part["x"].max(), 20)
        ax.plot(xs * 100, main["elastisitas"] * xs * 100, color=INK_2, linewidth=1.2, linestyle=(0, (4, 3)))
        ax.axhline(0, color=INK_2, linewidth=0.8)
        ax.axvline(0, color=INK_2, linewidth=0.8)
        ax.set_title(f"{GROUP_LABEL[group]}: elastisitas {main['elastisitas']:.2f} (p {main['p']:.2f})", loc="left", fontweight="bold")
        ax.set_xlabel("harga produsen tahun lalu (% di atas rata-rata provinsi)")
        ax.set_ylim(-150, 150)
    axes[0].set_ylabel("perubahan luas panen tahun ini (%)")
    axes[0].legend(loc="upper left", fontsize=8)
    fig.suptitle("H5: harga produsen tahun lalu vs perubahan luas panen tahun ini, 2019-2025", x=0.01, ha="left", fontsize=11, fontweight="bold")
    fig.text(0.01, 0.01, "Kedua sumbu: deviasi dari rata-rata provinsi. Garis putus-putus = elastisitas spesifikasi utama.", fontsize=8, color=INK_2)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(path, dpi=150)
    plt.close(fig)


def run():
    setup()
    data = panel()
    results = specifications(data)
    decision = decide(results)
    chart(data, results, FIGURES / "h5_price_vs_area.png")
    results.to_csv(TABLES / "h5_results.csv", index=False)
    pd.to_pickle({"results": results, "decision": decision, "n_panel": data.groupby("commodity_group")["province_id"].nunique().to_dict(),
                  "excluded": sorted(set(pd.read_csv(FINAL / "core_province_year.csv")["province_id"]) - set(data["province_id"]))}, TABLES / "h5_results.pkl")
    print(results.round(3).to_string(index=False))
    print(decision.round(3).to_string(index=False))


if __name__ == "__main__":
    run()
