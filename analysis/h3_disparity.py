"""H3: saat guncangan pasokan, apakah disparitas harga eceran antarprovinsi melebar, terutama di provinsi jauh dari sentra?

Rencana: docs/05_analysis_plan.md bagian 4 (D-48, D-50).
  (a) Koefisien variasi (CV) harga eceran 34 provinsi per bulan, bulan guncangan vs normal: regresi dengan FE
      month-of-year dan trend, SE HAC, plus interval bootstrap blok (12 bulan).
  (b) Price premium provinsi = harga provinsi / median 34 provinsi di bulan itu. Kenaikan premium saat guncangan
      (rata-rata bulan guncangan - bulan normal) diregresikan pada jarak ke sentra (per 100 km) dan dummy beda pulau.
  Penanda guncangan utama: spike harga produsen nasional (1,25 x median 12 bulan). Spike nasional (>= 50% provinsi)
  hanya untuk narasi dan chart. Ranking provinsi rentan: premium per episode spike nasional, konsisten di >= 2 episode.

    python -m analysis.h3_disparity
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm

from analysis.spikes import MAIN_THRESHOLD, SENSITIVITY_THRESHOLDS, episodes, flag_spikes
from analysis.style import (
    FIGURES, GROUP_COLOR, GROUP_LABEL, INK_2, MUTED, SHADE, SURFACE, TABLES, load_core, md, national_prices, plt, province_names, setup,
)

SEED = 2026
ALPHA = 0.05
START, END = "2019-01", "2026-10"
BOOTSTRAP, BLOCK = 1000, 12
DKI = 13


def shock_months(national, level, threshold=MAIN_THRESHOLD):
    """Bulan spike harga nasional pada satu level harga (produsen/pedagang_besar/eceran) per komoditas."""
    out = {}
    for group in GROUP_LABEL:
        series = national[(national["commodity"] == group) & (national["price_type"] == level)].set_index("month")["price_idr_per_kg"].sort_index()
        flags = flag_spikes(series, threshold).loc[START:END]
        out[group] = flags["is_spike"].fillna(False).astype(bool)
    return out


def spike_share(core, threshold=MAIN_THRESHOLD):
    """Porsi provinsi yang harga ecerannya spike, per komoditas x bulan."""
    out = {}
    for group in GROUP_LABEL:
        flags = [flag_spikes(part.set_index("month")["price_retail"].sort_index(), threshold)["is_spike"].rename(province)
                 for province, part in core[core["commodity_group"] == group].groupby("province_id")]
        out[group] = pd.concat(flags, axis=1).loc[START:END].mean(axis=1)
    return out


def national_spike_label(core, threshold=MAIN_THRESHOLD, share=0.5):
    """Spike nasional untuk narasi/chart: spike eceran serentak di >= 50% provinsi."""
    out = {}
    for group in GROUP_LABEL:
        flags = []
        for province, part in core[core["commodity_group"] == group].groupby("province_id"):
            flags.append(flag_spikes(part.set_index("month")["price_retail"].sort_index(), threshold)["is_spike"].rename(province))
        matrix = pd.concat(flags, axis=1).loc[START:END]
        out[group] = matrix.mean(axis=1) >= share
    return out


def cv_series(core, exclude=()):
    retail = core[(~core["province_id"].isin(exclude)) & core["in_model_period"]]
    stats = retail.groupby(["commodity_group", "month"])["price_retail"].agg(["std", "mean", "count"])
    stats["cv_pct"] = stats["std"] / stats["mean"] * 100
    return stats.reset_index()


def cv_effect(cv, shocks, group, rng):
    data = cv[cv["commodity_group"] == group].set_index("month").sort_index()
    data["shock"] = shocks[group].reindex(data.index).fillna(False).astype(float)
    data["trend"] = np.arange(len(data)) / 12
    moy = pd.get_dummies(data.index.month, prefix="m", drop_first=True, dtype=float).set_index(data.index)
    X = sm.add_constant(pd.concat([data[["shock", "trend"]], moy], axis=1))
    fitted = sm.OLS(data["cv_pct"], X).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
    estimates = []
    n = len(data)
    for _ in range(BOOTSTRAP):
        starts = rng.integers(0, n - BLOCK, size=int(np.ceil(n / BLOCK)))
        idx = np.concatenate([np.arange(s, s + BLOCK) for s in starts])[:n]
        sample_X, sample_y = X.iloc[idx], data["cv_pct"].iloc[idx]
        if sample_X["shock"].nunique() < 2:
            continue
        estimates.append(sm.OLS(sample_y.to_numpy(), sample_X.to_numpy()).fit().params[1])
    low, high = np.percentile(estimates, [2.5, 97.5])
    return {"grup": group, "bulan": n, "bulan_guncangan": int(data["shock"].sum()), "cv_normal_pct": data.loc[data["shock"] == 0, "cv_pct"].mean(),
            "cv_guncangan_pct": data.loc[data["shock"] == 1, "cv_pct"].mean(), "efek_pp": fitted.params["shock"], "p_hac": fitted.pvalues["shock"],
            "ci_boot_bawah": low, "ci_boot_atas": high}


def premiums(core):
    retail = core[core["in_model_period"]].copy()
    retail["median_nasional"] = retail.groupby(["commodity_group", "month"])["price_retail"].transform("median")
    retail["premium"] = retail["price_retail"] / retail["median_nasional"]
    return retail


def premium_vs_distance(prem, shocks, group, exclude=()):
    part = prem[(prem["commodity_group"] == group) & (~prem["province_id"].isin(exclude))].copy()
    part["shock"] = part["month"].map(shocks[group]).fillna(False)
    per = part.groupby(["province_id", "shock"])["premium"].mean().unstack()
    per = per.rename(columns={True: "premium_guncangan", False: "premium_normal"})
    per["kenaikan_premium_pct"] = (per["premium_guncangan"] - per["premium_normal"]) * 100
    geo = part.drop_duplicates("province_id").set_index("province_id")[["distance_to_sentra_km", "is_different_island"]]
    per = per.join(geo)
    X = sm.add_constant(pd.DataFrame({"jarak_100km": per["distance_to_sentra_km"] / 100, "beda_pulau": per["is_different_island"].astype(float)}))
    fitted = sm.OLS(per["kenaikan_premium_pct"], X).fit(cov_type="HC3")
    distance_only = sm.OLS(per["kenaikan_premium_pct"], sm.add_constant(per["distance_to_sentra_km"] / 100)).fit(cov_type="HC3")
    result = {"grup": group, "provinsi": len(per),
              "koef_jarak_per_100km_pp": fitted.params["jarak_100km"], "p_jarak": fitted.pvalues["jarak_100km"],
              "ci_jarak_bawah": fitted.conf_int().loc["jarak_100km", 0], "ci_jarak_atas": fitted.conf_int().loc["jarak_100km", 1],
              "koef_beda_pulau_pp": fitted.params["beda_pulau"], "p_beda_pulau": fitted.pvalues["beda_pulau"],
              "koef_jarak_saja": distance_only.params.iloc[1], "p_jarak_saja": distance_only.pvalues.iloc[1]}
    return result, per


def vulnerable_ranking(prem, core, provinces):
    """Premium rata-rata tiap provinsi per episode spike nasional (>= 50% provinsi); provinsi di 10 teratas di >= 2 episode."""
    shares = spike_share(core)
    rows = []
    for group in GROUP_LABEL:
        flags = pd.DataFrame({"is_spike": shares[group] >= 0.5, "ratio": shares[group], "price": np.nan})
        found = episodes(flags)
        part = prem[prem["commodity_group"] == group]
        for number, episode in found.iterrows():
            window = part[(part["month"] >= episode["start"]) & (part["month"] <= episode["end"])]
            premium = window.groupby("province_id")["premium"].mean().sort_values(ascending=False)
            for rank, (province, value) in enumerate(premium.items(), start=1):
                rows.append({"grup": group, "episode": f"{episode['start']} s/d {episode['end']}", "province_id": province, "provinsi": provinces[province], "premium": value, "peringkat": rank})
    ranking = pd.DataFrame(rows)
    top = ranking[ranking["peringkat"] <= 10].groupby(["grup", "provinsi"]).agg(episode_top10=("episode", "size"), premium_rata2=("premium", "mean")).reset_index()
    episodes_count = ranking.groupby("grup")["episode"].nunique()
    top["episode_total"] = top["grup"].map(episodes_count)
    consistent = top[top["episode_top10"] >= 2].sort_values(["grup", "episode_top10", "premium_rata2"], ascending=[True, False, False])
    return ranking, consistent


def chart_cv(cv, shocks, label, path):
    fig, axes = plt.subplots(2, 1, figsize=(9, 5.4), sharex=True)
    for ax, group in zip(axes, GROUP_LABEL):
        data = cv[cv["commodity_group"] == group].set_index("month").sort_index()
        x = data.index.to_timestamp()
        for month in label[group][label[group]].index:
            ax.axvspan(month.to_timestamp(), (month + 1).to_timestamp(), color=SHADE, linewidth=0)
        shock = shocks[group].reindex(data.index).fillna(False)
        ax.plot(x, data["cv_pct"], color=GROUP_COLOR[group], linewidth=2, label="CV harga eceran antarprovinsi")
        ax.scatter(x[shock.to_numpy()], data["cv_pct"][shock], s=26, color=GROUP_COLOR[group], edgecolor=SURFACE, linewidth=1.2, zorder=3, label="bulan spike harga produsen nasional")
        ax.set_title(GROUP_LABEL[group], loc="left", fontweight="bold")
        ax.set_ylabel("CV (%)")
    axes[0].legend(loc="upper left", fontsize=8)
    fig.suptitle("H3: disparitas harga eceran antarprovinsi (koefisien variasi), 2019-2026", x=0.01, ha="left", fontsize=11, fontweight="bold")
    fig.text(0.01, 0.01, "Area abu-abu = spike nasional (spike eceran serentak di >= 50% provinsi).", fontsize=8, color=INK_2)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(path, dpi=150)
    plt.close(fig)


def chart_distance(per_group, provinces, path):
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=True)
    for ax, (group, per) in zip(axes, per_group.items()):
        same, other = per[~per["is_different_island"]], per[per["is_different_island"]]
        ax.scatter(same["distance_to_sentra_km"], same["kenaikan_premium_pct"], s=30, color=GROUP_COLOR[group], edgecolor=SURFACE, linewidth=1, label="satu pulau dengan sentra")
        ax.scatter(other["distance_to_sentra_km"], other["kenaikan_premium_pct"], s=34, facecolor=SURFACE, edgecolor=GROUP_COLOR[group], linewidth=1.5, label="beda pulau")
        fit = np.polyfit(per["distance_to_sentra_km"], per["kenaikan_premium_pct"], 1)
        xs = np.linspace(0, per["distance_to_sentra_km"].max(), 50)
        ax.plot(xs, np.polyval(fit, xs), color=INK_2, linewidth=1, linestyle=(0, (4, 3)))
        ax.axhline(0, color=INK_2, linewidth=0.8)
        for province, row in per.nsmallest(3, "kenaikan_premium_pct").iterrows():
            ax.annotate(provinces[province], (row["distance_to_sentra_km"], row["kenaikan_premium_pct"]), xytext=(4, 2), textcoords="offset points", fontsize=7, color=INK_2)
        ax.set_title(GROUP_LABEL[group], loc="left", fontweight="bold")
        ax.set_xlabel("jarak ibu kota ke titik sentra terdekat (km)")
    axes[0].set_ylabel("kenaikan premium saat guncangan (poin %)")
    axes[0].legend(loc="lower left", fontsize=8)
    fig.suptitle("H3: kenaikan premium harga eceran provinsi saat spike harga produsen nasional vs jarak ke sentra", x=0.01, ha="left", fontsize=10.5, fontweight="bold")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def run():
    setup()
    rng = np.random.default_rng(SEED)
    core = load_core()
    provinces = province_names()
    national = national_prices()
    prem = premiums(core)

    main_shocks = shock_months(national, "produsen")
    cv_all = cv_series(core)
    cv_main = pd.DataFrame([cv_effect(cv_all, main_shocks, g, rng) for g in GROUP_LABEL])
    dist_main, per_main = zip(*[premium_vs_distance(prem, main_shocks, g) for g in GROUP_LABEL])
    dist_main = pd.DataFrame(dist_main)

    sens = []
    def add(label, shocks, exclude=()):
        cv = cv_series(core, exclude)
        for group in GROUP_LABEL:
            c = cv_effect(cv, shocks, group, rng)
            d, _ = premium_vs_distance(prem, shocks, group, exclude)
            sens.append({"spesifikasi": label, "grup": group, "bulan_guncangan": c["bulan_guncangan"], "efek_cv_pp": c["efek_pp"], "p_cv": c["p_hac"],
                         "koef_jarak_per_100km": d["koef_jarak_per_100km_pp"], "p_jarak": d["p_jarak"], "koef_beda_pulau": d["koef_beda_pulau_pp"], "p_beda_pulau": d["p_beda_pulau"]})
    add("utama: spike produsen 1,25", main_shocks)
    add("tanpa DKI Jakarta", main_shocks, exclude=(DKI,))
    for threshold in SENSITIVITY_THRESHOLDS:
        add(f"spike produsen {threshold:.2f}", shock_months(national, "produsen", threshold))
    add("penanda dari spike pedagang besar 1,25", shock_months(national, "pedagang_besar"))
    sens = pd.DataFrame(sens)

    ranking, consistent = vulnerable_ranking(prem, core, provinces)
    label = national_spike_label(core)
    chart_cv(cv_all, main_shocks, label, FIGURES / "h3_cv_over_time.png")
    chart_distance(dict(zip(GROUP_LABEL, per_main)), provinces, FIGURES / "h3_premium_vs_distance.png")

    for name, frame in {"h3_cv_effect": cv_main, "h3_distance": dist_main, "h3_sensitivity": sens, "h3_episode_ranking": ranking, "h3_vulnerable_consistent": consistent}.items():
        frame.to_csv(TABLES / f"{name}.csv", index=False)
    per_out = pd.concat([p.assign(grup=g) for g, p in zip(GROUP_LABEL, per_main)]).reset_index()
    per_out["provinsi"] = per_out["province_id"].map(provinces)
    per_out.to_csv(TABLES / "h3_premium_by_province.csv", index=False)
    pd.to_pickle({"cv": cv_main, "dist": dist_main, "sens": sens, "consistent": consistent, "ranking": ranking, "per": per_out,
                  "shock_months": {g: [str(m) for m in s[s].index] for g, s in main_shocks.items()},
                  "national_spike": {g: [str(m) for m in s[s].index] for g, s in label.items()}}, TABLES / "h3_results.pkl")
    print(cv_main.round(3).to_string(index=False))
    print(dist_main.round(3).to_string(index=False))
    print(sens.round(3).to_string(index=False))
    print(consistent.round(3).to_string(index=False))


if __name__ == "__main__":
    run()
