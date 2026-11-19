"""H2: di level rantai pasok mana kenaikan dimulai, dan apakah transmisinya asimetris (naik cepat, turun lambat)?

Rencana: docs/05_analysis_plan.md bagian 3 (D-48). Dua bagian:
  A. Lead-lag mingguan nasional: cross-correlation perubahan log harga (lag -8..+8 minggu, interval bootstrap
     blok untuk lag puncak) dan uji Granger dua arah (lag dipilih AIC, maksimum 8).
  B. Transmisi bulanan per provinsi (tier main): uji kointegrasi Engle-Granger; kalau terkointegrasi -> asymmetric ECM,
     kalau tidak -> model asimetris first difference. Pasangan: produsen -> pedagang besar, pedagang besar -> eceran.
Sensitivity: tanpa bulan imputasi (D-44), tier descriptive ikut, data mingguan tiga provinsi sentra Jawa.

    python -m analysis.h2_transmission
"""
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import statsmodels.api as sm  # noqa: E402
from statsmodels.tsa.api import VAR  # noqa: E402
from statsmodels.tsa.stattools import coint  # noqa: E402

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[1]
FINAL, INTERIM = ROOT / "data" / "final", ROOT / "data" / "interim"
FIGURES, TABLES = ROOT / "analysis" / "figures", ROOT / "analysis" / "tables"

SEED = 2026
ALPHA = 0.05
MAX_LAG_WEEKS = 8
BOOTSTRAP = 1000
BLOCK = 8
HAC_LAGS = 3
GROUPS = {"cat_7": "cabai_merah", "cat_8": "cabai_rawit"}
LABEL = {"cabai_merah": "Cabai merah", "cabai_rawit": "Cabai rawit"}
LEVEL = {4: "produsen", 3: "pedagang_besar", 1: "eceran"}
WEEKLY_PAIRS = [(4, 3), (3, 1), (4, 1)]  # (hulu, hilir)
MONTHLY_PAIRS = [("price_producer", "price_wholesale"), ("price_wholesale", "price_retail")]
NICE = {"price_producer": "produsen", "price_wholesale": "pedagang besar", "price_retail": "eceran", "produsen": "produsen", "pedagang_besar": "pedagang besar", "eceran": "eceran"}
JAVA_SENTRA = {12: "Jawa Barat", 14: "Jawa Tengah", 16: "Jawa Timur"}

COLORS = {"up": "#eb6834", "down": "#2a78d6"}
INK, INK_2, GRID, SURFACE, MUTED = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb", "#c9c7c1"
plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "axes.edgecolor": GRID, "axes.labelcolor": INK_2,
    "xtick.color": INK_2, "ytick.color": INK_2, "text.color": INK, "font.size": 9, "axes.titlesize": 10,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "legend.frameon": False,
})


# =============================================================== A. mingguan
def weekly_panel(province_id=0):
    weekly = pd.read_parquet(INTERIM / "fact_price_weekly.parquet")
    weekly = weekly[weekly["province_id"] == province_id].copy()
    weekly["week_start"] = pd.to_datetime(weekly["week_start"])
    weekly = weekly[(weekly["week_start"] >= "2019-01-01") & (weekly["week_start"] <= "2026-10-31")]
    return weekly.pivot_table(index="week_start", columns=["commodity_id", "price_type_id"], values="price_idr_per_kg")


def pair_changes(panel, commodity, upstream, downstream):
    """Perubahan log mingguan; minggu yang kosong (tidak di-impute, D-12) dilewati."""
    pair = panel[[(commodity, upstream), (commodity, downstream)]].dropna()
    changes = np.log(pair).diff().dropna()
    return changes.iloc[:, 0].to_numpy(), changes.iloc[:, 1].to_numpy(), len(panel) - len(pair)


def ccf(x, y, max_lag=MAX_LAG_WEEKS):
    """corr(x_t, y_(t+k)); k > 0 berarti hulu (x) mendahului hilir (y)."""
    out = {}
    for k in range(-max_lag, max_lag + 1):
        if k >= 0:
            a, b = x[: len(x) - k], y[k:]
        else:
            a, b = x[-k:], y[: len(y) + k]
        out[k] = np.corrcoef(a, b)[0, 1]
    return pd.Series(out)


def bootstrap_peak(x, y, rng):
    n = len(x)
    starts_max = n - BLOCK
    peaks = []
    for _ in range(BOOTSTRAP):
        starts = rng.integers(0, starts_max, size=int(np.ceil(n / BLOCK)))
        idx = np.concatenate([np.arange(s, s + BLOCK) for s in starts])[:n]
        peaks.append(ccf(x[idx], y[idx]).idxmax())
    return np.percentile(peaks, [2.5, 97.5])


def granger(x, y):
    data = pd.DataFrame({"x": x, "y": y})
    model = VAR(data)
    lag = max(1, model.select_order(MAX_LAG_WEEKS).aic)
    fitted = model.fit(lag)
    return lag, fitted.test_causality("y", ["x"], kind="f").pvalue, fitted.test_causality("x", ["y"], kind="f").pvalue


def weekly_lead_lag(province_id=0, with_bootstrap=True):
    panel = weekly_panel(province_id)
    rng = np.random.default_rng(SEED)
    rows, curves = [], {}
    for commodity, group in GROUPS.items():
        for upstream, downstream in WEEKLY_PAIRS:
            x, y, skipped = pair_changes(panel, commodity, upstream, downstream)
            curve = ccf(x, y)
            curves[(group, upstream, downstream)] = curve
            low, high = bootstrap_peak(x, y, rng) if with_bootstrap else (np.nan, np.nan)
            lag, p_forward, p_reverse = granger(x, y)
            rows.append({"grup": group, "hulu": LEVEL[upstream], "hilir": LEVEL[downstream], "n_minggu": len(x), "minggu_dilewati": skipped,
                         "lag_puncak": int(curve.idxmax()), "korelasi_puncak": curve.max(), "ci_lag_bawah": low, "ci_lag_atas": high,
                         "korelasi_lag0": curve[0], "lag_var": lag, "p_hulu_ke_hilir": p_forward, "p_hilir_ke_hulu": p_reverse})
    return pd.DataFrame(rows), curves


# =============================================================== B. bulanan
def load_core():
    core = pd.read_csv(FINAL / "core_province_month.csv")
    core["month"] = pd.PeriodIndex(core["month_start"].str[:7], freq="M")
    core = core[~core["is_partial_month"]]
    return core


def eligible(part, column, tiers):
    if column == "price_producer" and not part["in_producer_price_analysis"].iloc[0]:
        return False
    return part[f"{column}_tier"].iloc[0] in tiers


def design(part, upstream, downstream, exclude_imputed):
    frame = part.set_index("month").sort_index()
    y, x = np.log(frame[downstream]), np.log(frame[upstream])
    if exclude_imputed:
        y = y.where(frame[f"{downstream}_is_imputed"] != True)
        x = x.where(frame[f"{upstream}_is_imputed"] != True)
    data = pd.DataFrame({"y": y, "x": x})
    data["dy"], data["dx"] = data["y"].diff(), data["x"].diff()
    data["dx_up"], data["dx_down"] = data["dx"].clip(lower=0), data["dx"].clip(upper=0)
    data["dx_up_l1"], data["dx_down_l1"] = data["dx_up"].shift(1), data["dx_down"].shift(1)
    data["dy_l1"] = data["dy"].shift(1)
    return data


def cointegration(data):
    level = data[["y", "x"]].loc["2019-01":"2026-10"].dropna()
    if len(level) < 36:
        return np.nan, None
    p_value = coint(level["y"], level["x"], trend="c")[1]
    longrun = sm.OLS(level["y"], sm.add_constant(level["x"])).fit()
    return p_value, longrun


def asymmetric_fit(data, longrun):
    regressors = ["dx_up", "dx_down", "dx_up_l1", "dx_down_l1", "dy_l1"]
    if longrun is not None:
        ect = (data["y"] - longrun.predict(sm.add_constant(data["x"], has_constant="add"))).shift(1)
        data = data.assign(ect_up=ect.clip(lower=0), ect_down=ect.clip(upper=0))
        regressors += ["ect_up", "ect_down"]
    sample = data.loc["2019-01":"2026-10", ["dy"] + regressors].dropna()
    fitted = sm.OLS(sample["dy"], sm.add_constant(sample[regressors])).fit(cov_type="HAC", cov_kwds={"maxlags": HAC_LAGS})
    result = {"n_bulan": len(sample)}
    pass_test = fitted.t_test("dx_up + dx_up_l1 - dx_down - dx_down_l1 = 0")
    result["pass_naik"] = fitted.params["dx_up"] + fitted.params["dx_up_l1"]
    result["pass_turun"] = fitted.params["dx_down"] + fitted.params["dx_down_l1"]
    result["selisih_pass"] = float(pass_test.effect[0])
    result["p_pass"] = float(pass_test.pvalue)
    if longrun is not None:
        adjust_test = fitted.t_test("ect_up - ect_down = 0")
        result["adj_di_atas"], result["adj_di_bawah"] = fitted.params["ect_up"], fitted.params["ect_down"]
        result["selisih_adj"] = float(adjust_test.effect[0])
        result["p_adj"] = float(adjust_test.pvalue)
    return result


def classify(row):
    """Naik cepat turun lambat: pass-through naik > turun, atau koreksi saat harga hilir terlalu tinggi lebih lambat
    (koefisien ECT di atas keseimbangan kurang negatif). Signifikan arah berlawanan = arah sebaliknya."""
    expected = (row["p_pass"] < ALPHA and row["selisih_pass"] > 0) or (row.get("p_adj", 1) < ALPHA and row.get("selisih_adj", 0) > 0)
    opposite = (row["p_pass"] < ALPHA and row["selisih_pass"] < 0) or (row.get("p_adj", 1) < ALPHA and row.get("selisih_adj", 0) < 0)
    if expected and not opposite:
        return "naik_cepat_turun_lambat"
    if opposite and not expected:
        return "arah_sebaliknya"
    if expected and opposite:
        return "campuran"
    return "tidak_signifikan"


def province_models(core, tiers=("main",), exclude_imputed=False):
    rows = []
    for (province, group), part in core.groupby(["province_id", "commodity_group"]):
        for upstream, downstream in MONTHLY_PAIRS:
            if not (eligible(part, upstream, tiers) and eligible(part, downstream, tiers)):
                continue
            data = design(part, upstream, downstream, exclude_imputed)
            p_coint, longrun = cointegration(data)
            if np.isnan(p_coint):
                continue
            cointegrated = p_coint < ALPHA
            result = asymmetric_fit(data, longrun if cointegrated else None)
            row = {"province_id": province, "grup": group, "hulu": NICE[upstream], "hilir": NICE[downstream],
                   "p_kointegrasi": p_coint, "model": "ECM" if cointegrated else "first_difference", **result}
            row["klasifikasi"] = classify(row)
            rows.append(row)
    return pd.DataFrame(rows)


def pooled(core, tiers=("main",), exclude_imputed=False):
    """Model first difference asimetris gabungan semua provinsi eligible, FE provinsi, SE cluster provinsi."""
    rows = []
    for group in GROUPS.values():
        for upstream, downstream in MONTHLY_PAIRS:
            frames = []
            for province, part in core[core["commodity_group"] == group].groupby("province_id"):
                if eligible(part, upstream, tiers) and eligible(part, downstream, tiers):
                    data = design(part, upstream, downstream, exclude_imputed).loc["2019-01":"2026-10"]
                    frames.append(data.assign(province_id=province))
            stacked = pd.concat(frames)[["dy", "dx_up", "dx_down", "dx_up_l1", "dx_down_l1", "dy_l1", "province_id"]].dropna()
            dummies = pd.get_dummies(stacked["province_id"], prefix="p", drop_first=True, dtype=float)
            X = sm.add_constant(pd.concat([stacked[["dx_up", "dx_down", "dx_up_l1", "dx_down_l1", "dy_l1"]], dummies], axis=1))
            fitted = sm.OLS(stacked["dy"], X).fit(cov_type="cluster", cov_kwds={"groups": stacked["province_id"]})
            test = fitted.t_test("dx_up + dx_up_l1 - dx_down - dx_down_l1 = 0")
            ci = test.conf_int()[0]
            rows.append({"grup": group, "hulu": NICE[upstream], "hilir": NICE[downstream], "provinsi": stacked["province_id"].nunique(), "n": len(stacked),
                         "pass_naik": fitted.params["dx_up"] + fitted.params["dx_up_l1"], "pass_turun": fitted.params["dx_down"] + fitted.params["dx_down_l1"],
                         "selisih": float(test.effect[0]), "ci_bawah": ci[0], "ci_atas": ci[1], "p": float(test.pvalue)})
    return pd.DataFrame(rows)


# =============================================================== keputusan
def decide(weekly, share, pooled_main):
    rows = []
    for group in GROUPS.values():
        w = weekly[(weekly["grup"] == group) & (weekly["hilir"] == "eceran")]
        leads = w[(w["p_hulu_ke_hilir"] < ALPHA) & (w["p_hilir_ke_hulu"] >= ALPHA) & (w["lag_puncak"] > 0)]
        reverse = w[(w["p_hilir_ke_hulu"] < ALPHA) & (w["p_hulu_ke_hilir"] >= ALPHA)]
        criterion_1 = len(leads) > 0 and len(reverse) == 0
        s = share[(share["grup"] == group)]
        majority = bool((s["porsi_naik_cepat_turun_lambat"] >= 0.5).any())
        p = pooled_main[pooled_main["grup"] == group]
        pooled_sig = bool(((p["p"] < ALPHA) & (p["selisih"] > 0)).any())
        criterion_2 = majority or pooled_sig
        verdict = "didukung" if criterion_1 and criterion_2 else ("sebagian" if criterion_1 or criterion_2 else "tidak didukung")
        rows.append({"grup": group, "kriteria_1_hulu_mendahului_eceran": criterion_1,
                     "pasangan_yang_mendahului": ", ".join(f"{a}->{b}" for a, b in zip(leads["hulu"], leads["hilir"])) or "-",
                     "kriteria_2_asimetri": criterion_2, "mayoritas_provinsi": majority, "panel_signifikan": pooled_sig, "keputusan": verdict})
    return pd.DataFrame(rows)


def share_table(models):
    counts = models.groupby(["grup", "hulu", "hilir", "klasifikasi"]).size().unstack("klasifikasi", fill_value=0)
    for column in ("naik_cepat_turun_lambat", "arah_sebaliknya", "campuran", "tidak_signifikan"):
        if column not in counts.columns:
            counts[column] = 0
    counts["provinsi"] = counts.sum(axis=1)
    counts["porsi_naik_cepat_turun_lambat"] = counts["naik_cepat_turun_lambat"] / counts["provinsi"]
    model_counts = models.groupby(["grup", "hulu", "hilir", "model"]).size().unstack("model", fill_value=0)
    return counts.join(model_counts).reset_index()


# =============================================================== chart
def chart_ccf(curves, weekly, path):
    fig, axes = plt.subplots(2, 3, figsize=(11, 5.4), sharey=True)
    for row, group in enumerate(GROUPS.values()):
        for col, (upstream, downstream) in enumerate(WEEKLY_PAIRS):
            ax = axes[row, col]
            curve = curves[(group, upstream, downstream)]
            peak = curve.idxmax()
            colors = [COLORS["up"] if k == peak else MUTED for k in curve.index]
            ax.bar(curve.index, curve.values, color=colors, width=0.7)
            ax.axhline(0, color=INK_2, linewidth=0.8)
            ax.axvline(0, color=INK_2, linewidth=0.6, linestyle=(0, (3, 3)))
            info = weekly[(weekly["grup"] == group) & (weekly["hulu"] == LEVEL[upstream]) & (weekly["hilir"] == LEVEL[downstream])].iloc[0]
            ax.set_title(f"{LABEL[group]}: {NICE[LEVEL[upstream]]} -> {NICE[LEVEL[downstream]]}", loc="left", fontsize=9, fontweight="bold", pad=14)
            ax.text(0, 1.01, f"puncak di lag {peak:+d} minggu (95% CI {info['ci_lag_bawah']:+.0f} s/d {info['ci_lag_atas']:+.0f})", transform=ax.transAxes, fontsize=7.5, color=INK_2, va="bottom")
            if row == 1:
                ax.set_xlabel("lag k (minggu); k > 0 = hulu mendahului hilir")
            if col == 0:
                ax.set_ylabel("korelasi perubahan log")
    fig.suptitle("H2: korelasi silang perubahan harga mingguan nasional antar level rantai pasok, 2019-2026", x=0.01, ha="left", fontsize=11, fontweight="bold")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def chart_asymmetry(models, provinces, path):
    pairs = [("pedagang besar", "eceran"), ("produsen", "pedagang besar")]
    fig, axes = plt.subplots(1, 4, figsize=(14.5, 8.8), sharey=False)
    for col, (group, (upstream, downstream)) in enumerate([(g, p) for g in GROUPS.values() for p in pairs]):
        ax = axes[col]
        part = models[(models["grup"] == group) & (models["hulu"] == upstream) & (models["hilir"] == downstream)].copy()
        part["nama"] = part["province_id"].map(provinces)
        part = part.sort_values("selisih_pass")
        y = np.arange(len(part))
        ax.hlines(y, part["pass_turun"], part["pass_naik"], color=MUTED, linewidth=1.5)
        ax.scatter(part["pass_naik"], y, color=COLORS["up"], s=24, zorder=3, label="saat harga hulu naik", edgecolor=SURFACE, linewidth=1)
        ax.scatter(part["pass_turun"], y, color=COLORS["down"], s=24, zorder=3, label="saat harga hulu turun", edgecolor=SURFACE, linewidth=1)
        labels = [f"{n} *" if k == "naik_cepat_turun_lambat" else (f"{n} °" if k == "arah_sebaliknya" else n) for n, k in zip(part["nama"], part["klasifikasi"])]
        ax.set_yticks(y, labels, fontsize=7)
        ax.axvline(0, color=INK_2, linewidth=0.8)
        ax.set_title(f"{LABEL[group]}\n{upstream} -> {downstream}", loc="left", fontsize=9, fontweight="bold")
        ax.set_xlabel("pass-through 2 bulan (elastisitas)")
        ax.grid(axis="y", visible=False)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower right", fontsize=8, ncol=2)
    fig.suptitle("H2: pass-through kenaikan vs penurunan harga hulu per provinsi (tier main)", x=0.01, ha="left", fontsize=11, fontweight="bold")
    fig.text(0.01, 0.005, "* = asimetri 'naik cepat, turun lambat' signifikan (p < 0,05); ° = asimetri arah sebaliknya signifikan. Diurutkan dari selisih pass-through.", fontsize=8, color=INK_2)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(path, dpi=150)
    plt.close(fig)


def reporting_cadence():
    """Seberapa sering harga harian nasional berubah dari hari kerja sebelumnya (indikasi frekuensi pembaruan data)."""
    import sys
    sys.path.insert(0, str(ROOT))
    from pipeline.readers import load_pihps_grid

    daily = load_pihps_grid("daily")
    national = daily[(daily["level"] == 0) & daily["commodity_id"].isin(GROUPS)]
    national = national[(national["date"] >= pd.Timestamp("2019-01-01").date()) & (national["date"] <= pd.Timestamp("2026-10-31").date())]
    rows = []
    for (commodity, price_type), part in national.groupby(["commodity_id", "price_type_id"]):
        series = part.sort_values("date")["price"].dropna()
        rows.append({"grup": GROUPS[commodity], "level": NICE[LEVEL[price_type]], "porsi_hari_berubah_pct": (series.diff().iloc[1:] != 0).mean() * 100})
    return pd.DataFrame(rows)


# =============================================================== laporan
def md(frame, fmt="{:,.3f}"):
    lines = ["| " + " | ".join(map(str, frame.columns)) + " |", "| " + " | ".join("---" for _ in frame.columns) + " |"]
    for _, row in frame.iterrows():
        cells = []
        for v in row:
            if isinstance(v, (float, np.floating)):
                cells.append("" if np.isnan(v) else fmt.format(v))
            else:
                cells.append(str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def run():
    FIGURES.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)
    provinces = pd.read_csv(FINAL / "dim_province.csv").set_index("province_id")["province_name"]
    core = load_core()

    weekly, curves = weekly_lead_lag()
    models = province_models(core)
    models_no_imputed = province_models(core, exclude_imputed=True)
    models_descriptive = province_models(core, tiers=("main", "descriptive"))
    pooled_main = pooled(core)
    pooled_no_imputed = pooled(core, exclude_imputed=True)
    pooled_descriptive = pooled(core, tiers=("main", "descriptive"))
    share = share_table(models)
    decision = decide(weekly, share, pooled_main)
    java = pd.concat([weekly_lead_lag(pid, with_bootstrap=False)[0].assign(provinsi=name) for pid, name in JAVA_SENTRA.items()])

    no_coint = models[models["model"] == "first_difference"].assign(provinsi=lambda d: d["province_id"].map(provinces))
    for name, frame in {"h2_weekly_national": weekly, "h2_province_models": models, "h2_province_models_no_imputed": models_no_imputed,
                        "h2_province_models_with_descriptive": models_descriptive, "h2_pooled": pooled_main, "h2_weekly_java": java}.items():
        frame.to_csv(TABLES / f"{name}.csv", index=False)
    chart_ccf(curves, weekly, FIGURES / "h2_weekly_ccf.png")
    chart_asymmetry(models, provinces, FIGURES / "h2_asymmetry_provinces.png")

    sens = []
    for label, m, p in (("utama (tier main)", models, pooled_main), ("tanpa bulan imputasi (D-44)", models_no_imputed, pooled_no_imputed),
                        ("tier main + descriptive", models_descriptive, pooled_descriptive)):
        s = share_table(m)
        for _, row in s.iterrows():
            pr = p[(p["grup"] == row["grup"]) & (p["hulu"] == row["hulu"]) & (p["hilir"] == row["hilir"])].iloc[0]
            sens.append({"spesifikasi": label, "grup": row["grup"], "pasangan": f"{row['hulu']} -> {row['hilir']}", "provinsi": int(row["provinsi"]),
                         "porsi_naik_cepat_turun_lambat": row["porsi_naik_cepat_turun_lambat"], "panel_selisih": pr["selisih"], "panel_p": pr["p"]})
    sens = pd.DataFrame(sens)
    sens.to_csv(TABLES / "h2_sensitivity.csv", index=False)

    report = {"weekly": weekly, "models": models, "share": share, "pooled": pooled_main, "decision": decision, "sensitivity": sens,
              "no_coint": no_coint, "java": java, "cadence": reporting_cadence(), "imputed_rows": int(core["price_producer_is_imputed"].fillna(False).sum() + core["price_wholesale_is_imputed"].fillna(False).sum())}
    pd.to_pickle(report, TABLES / "h2_results.pkl")
    print(decision.to_string(index=False))
    print(share.to_string(index=False))
    print(pooled_main.round(3).to_string(index=False))
    print(weekly.round(3).to_string(index=False))
    print(sens.round(3).to_string(index=False))
    print(java[["provinsi", "grup", "hulu", "hilir", "lag_puncak", "korelasi_puncak", "p_hulu_ke_hilir", "p_hilir_ke_hulu"]].round(3).to_string(index=False))
    return report


if __name__ == "__main__":
    run()
