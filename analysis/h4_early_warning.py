"""H4: bisakah onset episode besar harga eceran dideteksi 1-2 bulan lebih awal?

Rencana: docs/05_analysis_plan.md bagian 8 (D-48), sinyal D-55, lag cuaca D-59/D-60, rincian D-61.
- Target: onset episode besar (spike eceran provinsi >= 2 bulan) tepat di t+1 (horizon 1) atau t+2 (horizon 2).
  Risk set: provinsi yang tidak sedang spike di bulan origin t.
- Sinyal di t: momentum harga pedagang besar (1 dan 3 bulan), rasio pedagang besar terhadap median 12 bulan,
  bulan target = Idulfitri / sebelum Idulfitri, ONI t-2, cuaca (rawit: anomali hujan lag 2-3 relatif ke bulan target;
  merah: indeks hujan nasional, lag 2-4 dipilih di data latih).
- Rolling-origin backtest Jan 2023 - Sep 2026 (bulan target), model dilatih ulang tiap origin dengan label yang sudah
  terkonfirmasi. Ambang probabilitas dipilih di data latih (F1 maksimum).
- Baseline: musiman naif dan charter (harga eceran naik bulan ini).

    python -m analysis.h4_early_warning
"""
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from analysis.spikes import MAIN_THRESHOLD, episodes, flag_spikes
from analysis.style import (ACCENT, FIGURES, GROUP_COLOR, GROUP_LABEL, INK_2, MUTED, ROOT, SURFACE, TABLES, load_core, national_prices, plt, setup)

FIRST_TRAIN = pd.Period("2019-01", "M")
FIRST_TARGET_TEST = pd.Period("2023-01", "M")
LAST_TARGET = pd.Period("2026-09", "M")      # onset Sep 2026 masih bisa dikonfirmasi oleh Okt 2026
LAST_OBSERVED = pd.Period("2026-10", "M")
HORIZONS = (1, 2)
MERAH_LAGS = (2, 3, 4)
RULE_RATIO = 1.20
BOOTSTRAP = 1000
SEED = 2026
BASE_FEATURES = ["dw1", "dw3", "w_ratio", "idul_target", "pre_idul_target", "oni_l2"]


def national_rain_index(core, group):
    points = pd.read_csv(ROOT / "data" / "interim" / "sentra_points.csv")
    weights = points[points["commodity_group"] == group].groupby("province_id")["mean_production_ton_2019_2025"].sum()
    weather = core[(core["commodity_group"] == group) & (core["weather_status"] == "observed")].copy()
    weather["weight"] = weather["province_id"].map(weights)
    return weather.groupby("month").apply(lambda m: np.average(m["rain_anomaly"], weights=m["weight"]), include_groups=False)


def province_frame(part, threshold, min_months):
    """Satu provinsi x komoditas: label onset, risk set, fitur dasar, dan sinyal baseline per bulan."""
    part = part.set_index("month").sort_index()
    retail = part["price_retail"].where(part.index <= LAST_OBSERVED)
    flags = flag_spikes(retail, threshold)
    flags.loc[flags.index < FIRST_TRAIN, ["ratio", "is_spike"]] = np.nan
    spike = flags["is_spike"]
    found = episodes(flags.dropna(subset=["is_spike"]))
    onset_months = set(found.loc[found["months"] >= min_months, "start"])
    frame = pd.DataFrame(index=part.index)
    frame["spike"] = spike
    frame["onset"] = [float(m in onset_months) if pd.notna(spike.get(m)) else np.nan for m in frame.index]
    wholesale = part["price_wholesale"]
    log_w = np.log(wholesale)
    frame["dw1"] = log_w - log_w.shift(1)
    frame["dw3"] = log_w - log_w.shift(3)
    frame["w_ratio"] = wholesale / wholesale.shift(1).rolling(12, min_periods=12).median()
    imputed = part["price_wholesale_is_imputed"].fillna(False).astype(bool)
    frame["w_imputed"] = imputed.rolling(13, min_periods=1).max().astype(bool)
    frame["retail_up"] = (retail > retail.shift(1)).astype(float).where(retail.notna() & retail.shift(1).notna())
    frame["months_to_idulfitri"] = part["months_to_idulfitri"]
    frame["oni_l2"] = part["oni_anomaly"].shift(2)
    frame["rain_anomaly"] = part["rain_anomaly"]
    frame["wholesale_tier"] = part["price_wholesale_tier"].iloc[0]
    return frame


def build_panel(threshold=MAIN_THRESHOLD, min_months=2):
    core = load_core()
    rows = []
    for (group, province), part in core.groupby(["commodity_group", "province_id"]):
        frame = province_frame(part, threshold, min_months)
        frame["commodity_group"], frame["province_id"] = group, province
        frame["is_sentra"] = (part["weather_status"] == "observed").any()
        rows.append(frame.rename_axis("month").reset_index())
    panel = pd.concat(rows, ignore_index=True)
    indices = {group: national_rain_index(core, group) for group in GROUP_LABEL}
    stacked = []
    for h in HORIZONS:
        data = panel.copy()
        data["horizon"] = h
        data["target_month"] = data["month"] + h
        keys = ["commodity_group", "province_id"]
        shifted = data.groupby(keys)
        data["label"] = shifted["onset"].shift(-h)
        data["idul_target"] = (shifted["months_to_idulfitri"].shift(-h) == 0).astype(float)
        data["pre_idul_target"] = (shifted["months_to_idulfitri"].shift(-h) == -1).astype(float)
        data["seasonal_naive"] = shifted["spike"].shift(12 - h)          # spike di bulan target tahun lalu
        for lag in (2, 3, 4):
            months_back = lag - h                                         # bulan anomali = target - lag = t - (lag - h)
            local = shifted["rain_anomaly"].shift(months_back)
            national = pd.Series([indices[g].get(m - months_back, np.nan) for g, m in zip(data["commodity_group"], data["month"])], index=data.index)
            data[f"rain_nat_l{lag}"] = national
            data[f"rain_l{lag}"] = local.where(data["is_sentra"], national)
        stacked.append(data)
    panel = pd.concat(stacked, ignore_index=True)
    in_range = (panel["month"] >= FIRST_TRAIN) & (panel["target_month"] <= LAST_TARGET)
    risk = panel["spike"] == False  # noqa: E712 (NaN = belum bisa dinilai, bukan risk set)
    return panel[in_range & risk & panel["label"].notna()].copy()


def feature_sets(group, spec):
    if spec.get("weather", True) is False:
        return [BASE_FEATURES]
    if group == "cabai_rawit":
        return [BASE_FEATURES + ["rain_l2", "rain_l3"]]
    return [BASE_FEATURES + [f"rain_nat_l{lag}"] for lag in MERAH_LAGS]


def best_threshold(labels, scores):
    order = np.unique(np.quantile(scores, np.linspace(0.5, 0.995, 120)))
    best, best_f1 = order[0], -1
    for cut in order:
        alarm = scores >= cut
        tp = np.sum(alarm & (labels == 1))
        precision = tp / max(alarm.sum(), 1)
        recall = tp / max((labels == 1).sum(), 1)
        f1 = 2 * precision * recall / (precision + recall) if precision + recall > 0 else 0
        if f1 > best_f1:
            best, best_f1 = cut, f1
    return best


def fit_predict(train, test, candidate_sets):
    """Latih tiap set fitur kandidat, pilih log-likelihood latih terbaik (jumlah parameter sama), prediksi test."""
    best = None
    for features in candidate_sets:
        tr = train.dropna(subset=features)
        scaler = StandardScaler().fit(tr[features])
        model = LogisticRegression(C=1.0, max_iter=2000).fit(scaler.transform(tr[features]), tr["label"])
        prob = model.predict_proba(scaler.transform(tr[features]))[:, 1]
        loglik = np.sum(tr["label"] * np.log(prob) + (1 - tr["label"]) * np.log(1 - prob))
        if best is None or loglik > best[0]:
            best = (loglik, features, scaler, model, tr, prob)
    _, features, scaler, model, tr, prob = best
    threshold = best_threshold(tr["label"].to_numpy(), prob)
    te = test.dropna(subset=features)
    scores = model.predict_proba(scaler.transform(te[features]))[:, 1]
    return te.assign(score=scores, threshold=threshold, alarm=scores >= threshold, features_used=",".join(f for f in features if f.startswith("rain")))


def backtest(panel, group, spec):
    data = panel[(panel["commodity_group"] == group) & (panel["wholesale_tier"] == "main")]
    if spec.get("sentra_only"):
        data = data[data["is_sentra"]]
    if spec.get("no_imputed"):
        data = data[~data["w_imputed"]]
    out = []
    for h in HORIZONS:
        part = data[data["horizon"] == h]
        for origin in pd.period_range(FIRST_TARGET_TEST - h, LAST_TARGET - h, freq="M"):
            train = part[part["month"] + h + 1 <= origin]
            test = part[part["month"] == origin]
            if test.empty:
                continue
            out.append(fit_predict(train, test, feature_sets(group, spec)))
    predictions = pd.concat(out, ignore_index=True)
    predictions["rule"] = predictions["w_ratio"] >= RULE_RATIO
    predictions["seasonal"] = predictions["seasonal_naive"] == True  # noqa: E712
    predictions["charter"] = predictions["retail_up"] == 1
    return predictions


def scores_table(predictions, columns=("alarm", "rule", "seasonal", "charter")):
    rows = []
    labels = predictions["label"] == 1
    for column in columns:
        alarm = predictions[column].astype(bool)
        tp, fp = int((alarm & labels).sum()), int((alarm & ~labels).sum())
        fn, tn = int((~alarm & labels).sum()), int((~alarm & ~labels).sum())
        recall = tp / max(tp + fn, 1)
        precision = tp / max(tp + fp, 1)
        rows.append({"sinyal": column, "tp": tp, "fp": fp, "fn": fn, "tn": tn, "recall": recall, "precision": precision,
                     "false_alarm_rate": fp / max(fp + tn, 1), "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
                     "porsi_alarm": alarm.mean()})
    return pd.DataFrame(rows)


def far_at_recall(predictions, recall_target):
    labels = (predictions["label"] == 1).to_numpy()
    scores = predictions["score"].to_numpy()
    for cut in np.sort(np.unique(scores))[::-1]:
        alarm = scores >= cut
        if alarm[labels].mean() >= recall_target:
            return float((alarm & ~labels).sum() / max((~labels).sum(), 1))
    return 1.0


def f1_of(alarm, labels):
    tp = np.sum(alarm & labels)
    denominator = alarm.sum() + labels.sum()
    return 2 * tp / denominator if denominator else 0.0


def bootstrap_f1_gap(predictions, baseline):
    rng = np.random.default_rng(SEED)
    groups = {origin: frame for origin, frame in predictions.groupby("month")}
    origins = list(groups)
    gaps = []
    for _ in range(BOOTSTRAP):
        sample = pd.concat([groups[o] for o in rng.choice(origins, size=len(origins), replace=True)])
        labels = (sample["label"] == 1).to_numpy()
        gaps.append(f1_of(sample["alarm"].to_numpy(), labels) - f1_of(sample[baseline].astype(bool).to_numpy(), labels))
    return np.percentile(gaps, [5, 95])


def episode_table(predictions, panel, group):
    """Episode di periode uji: terdeteksi kalau ada alarm 1 atau 2 bulan sebelum onset."""
    onsets = panel[(panel["commodity_group"] == group) & (panel["horizon"] == 1) & (panel["label"] == 1)]
    onsets = onsets.assign(onset=onsets["target_month"])[["province_id", "onset"]]
    onsets = onsets[(onsets["onset"] >= FIRST_TARGET_TEST + 1) & (onsets["onset"] <= LAST_TARGET) & onsets["province_id"].isin(predictions["province_id"].unique())]
    keyed = predictions.set_index(["province_id", "target_month", "horizon"])
    rows = []
    for item in onsets.itertuples():
        row = {"province_id": item.province_id, "onset": str(item.onset)}
        for column in ("alarm", "rule", "seasonal", "charter"):
            lead = 0
            for h in (2, 1):
                key = (item.province_id, item.onset, h)
                if key in keyed.index and bool(keyed.loc[key, column]):
                    lead = h
                    break
            row[f"lead_{column}"] = lead
        rows.append(row)
    return pd.DataFrame(rows)


def national_onsets(threshold=MAIN_THRESHOLD):
    national = national_prices()
    retail = national[(national["price_type"] == "eceran")]
    out = []
    for group in GROUP_LABEL:
        series = retail[retail["commodity"] == group].set_index("month")["price_idr_per_kg"].sort_index()
        series = series[series.index <= LAST_OBSERVED]
        found = episodes(flag_spikes(series, threshold).dropna(subset=["is_spike"]))
        found = found[(found["months"] >= 2) & (found["start"] >= FIRST_TARGET_TEST + 1) & (found["start"] <= LAST_TARGET)]
        out += [{"grup": group, "onset": m} for m in found["start"]]
    return pd.DataFrame(out)


def national_coverage(predictions_by_group, onsets):
    rows = []
    for item in onsets.itertuples():
        predictions = predictions_by_group[item.grup]
        for h in HORIZONS:
            at = predictions[(predictions["target_month"] == item.onset) & (predictions["horizon"] == h)]
            row = {"grup": item.grup, "onset_nasional": str(item.onset), "horizon": h, "provinsi_risk_set": len(at)}
            for column in ("alarm", "rule", "seasonal", "charter"):
                row[f"porsi_{column}"] = at[column].mean() if len(at) else np.nan
            rows.append(row)
    return pd.DataFrame(rows)


SPECS = {
    "utama": ({}, {}),
    "tanpa fitur cuaca": ({}, {"weather": False}),
    "tanpa bulan imputasi pada fitur (D-44)": ({}, {"no_imputed": True}),
    "ambang spike 1,15": ({"threshold": 1.15}, {}),
    "ambang spike 1,35": ({"threshold": 1.35}, {}),
    "target onset spike apa pun (>= 1 bulan)": ({"min_months": 1}, {}),
    "hanya provinsi bertitik sentra": ({}, {"sentra_only": True}),
    "hanya provinsi bertitik sentra, tanpa cuaca": ({}, {"sentra_only": True, "weather": False}),
}


def run_specs():
    panels, summary, main = {}, [], {}
    for label, (panel_kwargs, spec) in SPECS.items():
        key = tuple(sorted(panel_kwargs.items()))
        if key not in panels:
            panels[key] = build_panel(**panel_kwargs)
        panel = panels[key]
        for group in GROUP_LABEL:
            predictions = backtest(panel, group, spec)
            table = scores_table(predictions)
            baselines = table[table["sinyal"].isin(["seasonal", "charter"])]
            stronger = baselines.loc[baselines["f1"].idxmax()]
            model = table[table["sinyal"] == "alarm"].iloc[0]
            episodes_ = episode_table(predictions, panel, group)
            row = {"grup": group, "spesifikasi": label, "baris_uji": len(predictions), "onset_uji": int((predictions["label"] == 1).sum()),
                   "episode_uji": len(episodes_), "baseline_kuat": stronger["sinyal"],
                   **{f"model_{m}": model[m] for m in ("recall", "precision", "false_alarm_rate", "f1")},
                   **{f"baseline_{m}": stronger[m] for m in ("recall", "precision", "false_alarm_rate", "f1")},
                   "model_far_pada_recall_baseline": far_at_recall(predictions, stronger["recall"]),
                   "episode_terdeteksi_model": (episodes_["lead_alarm"] >= 1).mean(),
                   "episode_lead2_model": (episodes_["lead_alarm"] == 2).mean(),
                   "episode_terdeteksi_baseline": (episodes_[f"lead_{stronger['sinyal']}"] >= 1).mean()}
            if label in ("utama", "tanpa fitur cuaca"):
                low, high = bootstrap_f1_gap(predictions, stronger["sinyal"])
                row["f1_gap_p5"], row["f1_gap_p95"] = low, high
            summary.append(row)
            if label == "utama":
                main[group] = {"predictions": predictions, "table": table, "episodes": episodes_, "panel": panel}
    return pd.DataFrame(summary), main


def decide(row):
    a = row["model_f1"] > row["baseline_f1"] and row.get("f1_gap_p5", np.nan) > 0
    b = row["model_far_pada_recall_baseline"] < row["baseline_false_alarm_rate"]
    c = row["episode_terdeteksi_model"] >= 0.5
    verdict = "didukung" if a and b and c else ("dibantah" if not a and not b else "sebagian")
    return pd.Series({"a_f1_lebih_baik": a, "b_far_lebih_rendah": b, "c_us1": c, "keputusan": verdict})


def chart_metrics(main, path):
    labels = {"alarm": "Model (logistic)", "rule": "Aturan pedagang besar >= 1,20x", "seasonal": "Baseline musiman naif", "charter": "Baseline charter (eceran naik)"}
    metrics = [("recall", "Recall"), ("precision", "Precision"), ("false_alarm_rate", "False alarm rate"), ("f1", "F1")]
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 3.8), sharex=True)
    markers = {"alarm": "o", "rule": "D", "seasonal": "s", "charter": "^"}
    colors = {"alarm": None, "rule": ACCENT, "seasonal": INK_2, "charter": MUTED}
    for ax, group in zip(axes, GROUP_LABEL):
        table = main[group]["table"].set_index("sinyal")
        for i, (metric, metric_label) in enumerate(metrics):
            for j, signal in enumerate(labels):
                color = GROUP_COLOR[group] if signal == "alarm" else colors[signal]
                ax.scatter(table.loc[signal, metric], i + (j - 1.5) * 0.12, marker=markers[signal], s=42, color=color, edgecolor=SURFACE, zorder=3,
                           label=labels[signal] if (i == 0) else None)
        ax.set_yticks(range(len(metrics)), [m[1] for m in metrics])
        ax.invert_yaxis()
        ax.set_xlim(0, 1)
        ax.set_title(GROUP_LABEL[group], loc="left", fontsize=9, color=INK_2)
    axes[0].legend(loc="lower right", fontsize=7, frameon=False)
    fig.suptitle("H4: onset episode besar 1-2 bulan ke depan, backtest Jan 2023 - Sep 2026 (unit provinsi-bulan)", x=0.01, ha="left", fontweight="bold", fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(path, dpi=150)
    plt.close(fig)


def chart_timeline(main, path):
    fig, axes = plt.subplots(2, 1, figsize=(9.5, 5.2), sharex=True)
    for ax, group in zip(axes, GROUP_LABEL):
        predictions = main[group]["predictions"]
        h1 = predictions[predictions["horizon"] == 1]
        by_month = h1.groupby("target_month").agg(onset=("label", "sum"), alarm=("alarm", "sum"))
        x = by_month.index.to_timestamp()
        ax.bar(x, by_month["onset"], width=20, color=GROUP_COLOR[group], alpha=0.85, label="provinsi dengan onset episode besar")
        ax.plot(x, by_month["alarm"], color=INK_2, linewidth=1.3, label="provinsi dengan alarm model (1 bulan sebelumnya)")
        ax.set_title(GROUP_LABEL[group], loc="left", fontsize=9, color=INK_2)
        ax.set_ylabel("jumlah provinsi")
    axes[0].legend(loc="upper left", fontsize=7.5)
    fig.suptitle("H4: onset vs alarm per bulan target (horizon 1)", x=0.01, ha="left", fontweight="bold", fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(path, dpi=150)
    plt.close(fig)


def run():
    setup()
    summary, main = run_specs()
    decisions = summary.join(summary.apply(decide, axis=1))
    onsets = national_onsets()
    coverage = national_coverage({g: main[g]["predictions"] for g in GROUP_LABEL}, onsets)
    per_horizon = pd.concat([scores_table(main[g]["predictions"][main[g]["predictions"]["horizon"] == h]).assign(grup=g, horizon=h)
                             for g in GROUP_LABEL for h in HORIZONS], ignore_index=True)
    merah_lags = main["cabai_merah"]["predictions"].groupby(["horizon", "features_used"]).size().rename("origin_x_provinsi").reset_index()
    chart_metrics(main, FIGURES / "h4_metrics.png")
    chart_timeline(main, FIGURES / "h4_alarm_timeline.png")
    decisions.to_csv(TABLES / "h4_results.csv", index=False)
    per_horizon.to_csv(TABLES / "h4_per_horizon.csv", index=False)
    coverage.to_csv(TABLES / "h4_national_episodes.csv", index=False)
    merah_lags.to_csv(TABLES / "h4_merah_lag_choice.csv", index=False)
    for group in GROUP_LABEL:
        main[group]["table"].to_csv(TABLES / f"h4_scores_{group}.csv", index=False)
        main[group]["episodes"].to_csv(TABLES / f"h4_episodes_{group}.csv", index=False)
        main[group]["predictions"].drop(columns=["wholesale_tier"]).to_csv(TABLES / f"h4_predictions_{group}.csv", index=False)
    pd.set_option("display.width", 260)
    print(decisions.round(3).to_string(index=False))
    for group in GROUP_LABEL:
        print(group); print(main[group]["table"].round(3).to_string(index=False))
    print(per_horizon.round(3).to_string(index=False))
    print(coverage.round(2).to_string(index=False))
    print(merah_lags.to_string(index=False))


if __name__ == "__main__":
    run()
