"""H2 lanjutan sebelum final: kualitas pembaruan harga, lead-lag di provinsi yang harga produsennya sering diperbarui,
margin pedagang besar, dan sensitivity periode spike pedagang besar (D-52).

1. Frekuensi perubahan: persen minggu yang harganya berubah dari minggu sebelumnya, per provinsi x tipe harga x komoditas.
2. Lead-lag (cross-correlation + Granger mingguan) hanya di provinsi yang harga produsennya berubah di >= 70% minggu;
   kalau kurang dari 5 provinsi, ambang 50% (dicatat).
3. Margin pedagang besar terhadap produsen (selisih Rp/kg dan rasio), bulan saat harga produsen turun vs naik.
   Bulan yang salah satu harganya hasil imputasi dikeluarkan.
4. Sensitivity D-52: asimetri pass-through dihitung terpisah untuk bulan spike harga pedagang besar dan bulan lain.

    python -m analysis.h2_followup
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm

from analysis.h2_transmission import (
    ALPHA, FINAL, GROUPS, INTERIM, LEVEL, MONTHLY_PAIRS, NICE, TABLES, ccf, design, eligible, granger, load_core,
)
from analysis.spikes import MAIN_THRESHOLD, SENSITIVITY_THRESHOLDS, flag_spikes

PRIMARY_SHARE, FALLBACK_SHARE, MIN_PROVINCES = 70.0, 50.0, 5
PAIRS = [(4, 3), (3, 1), (4, 1)]


def weekly_provinces():
    weekly = pd.read_parquet(INTERIM / "fact_price_weekly.parquet")
    weekly = weekly[weekly["province_id"] > 0].copy()
    weekly["week_start"] = pd.to_datetime(weekly["week_start"])
    return weekly[(weekly["week_start"] >= "2019-01-01") & (weekly["week_start"] <= "2026-10-31")]


def change_frequency(weekly):
    rows = []
    for (province, commodity, price_type), part in weekly.groupby(["province_id", "commodity_id", "price_type_id"]):
        series = part.sort_values("week_start")["price_idr_per_kg"]
        valid = series.notna() & series.shift(1).notna()
        if valid.sum() < 52:
            continue
        changed = (series.diff() != 0)[valid]
        rows.append({"province_id": province, "grup": GROUPS[commodity], "level": NICE[LEVEL[price_type]], "minggu": int(valid.sum()), "pct_minggu_berubah": changed.mean() * 100})
    return pd.DataFrame(rows)


def lead_lag_subset(weekly, frequency):
    """Pilih provinsi sesuai aturan (>= 70%, kalau < 5 provinsi -> >= 50%). Kalau ambang 50% pun < 5 provinsi,
    uji aturan tidak bisa dijalankan; sebagai pemeriksaan eksploratif (bukan pengganti aturan) dipakai 5 provinsi
    dengan frekuensi perubahan harga produsen tertinggi per komoditas."""
    producer = frequency[frequency["level"] == "produsen"]
    threshold = PRIMARY_SHARE
    chosen = producer[producer["pct_minggu_berubah"] >= threshold]
    if chosen.groupby("grup").size().reindex(GROUPS.values(), fill_value=0).min() < MIN_PROVINCES:
        threshold = FALLBACK_SHARE
        chosen = producer[producer["pct_minggu_berubah"] >= threshold]
    if chosen.groupby("grup").size().reindex(GROUPS.values(), fill_value=0).min() < MIN_PROVINCES:
        threshold = "eksploratif: 5 provinsi tertinggi"
        chosen = producer.sort_values("pct_minggu_berubah", ascending=False).groupby("grup").head(MIN_PROVINCES)
    rows = []
    for _, item in chosen.iterrows():
        commodity = [c for c, g in GROUPS.items() if g == item["grup"]][0]
        panel = weekly[(weekly["province_id"] == item["province_id"]) & (weekly["commodity_id"] == commodity)].pivot_table(index="week_start", columns="price_type_id", values="price_idr_per_kg")
        for upstream, downstream in PAIRS:
            if upstream not in panel or downstream not in panel:
                continue
            changes = np.log(panel[[upstream, downstream]].dropna()).diff().dropna()
            if len(changes) < 100:
                continue
            x, y = changes[upstream].to_numpy(), changes[downstream].to_numpy()
            curve = ccf(x, y)
            lag, p_forward, p_reverse = granger(x, y)
            rows.append({"province_id": item["province_id"], "grup": item["grup"], "pct_produsen_berubah": item["pct_minggu_berubah"],
                         "hulu": NICE[LEVEL[upstream]], "hilir": NICE[LEVEL[downstream]], "lag_puncak": int(curve.idxmax()), "korelasi_puncak": curve.max(),
                         "p_hulu_ke_hilir": p_forward, "p_hilir_ke_hulu": p_reverse})
    return pd.DataFrame(rows), threshold, chosen


def summarize_lead_lag(results):
    def direction(row):
        forward, reverse = row["p_hulu_ke_hilir"] < ALPHA, row["p_hilir_ke_hulu"] < ALPHA
        return "hulu memimpin" if forward and not reverse else "hilir memimpin" if reverse and not forward else "dua arah" if forward and reverse else "tidak signifikan"
    results = results.assign(arah_granger=results.apply(direction, axis=1))
    summary = results.groupby(["grup", "hulu", "hilir"]).agg(
        provinsi=("province_id", "size"), lag_puncak_median=("lag_puncak", "median"),
        lag_negatif=("lag_puncak", lambda s: int((s < 0).sum())), lag_nol=("lag_puncak", lambda s: int((s == 0).sum())), lag_positif=("lag_puncak", lambda s: int((s > 0).sum())),
    ).reset_index()
    directions = results.pivot_table(index=["grup", "hulu", "hilir"], columns="arah_granger", values="province_id", aggfunc="count", fill_value=0).reset_index()
    return summary.merge(directions, on=["grup", "hulu", "hilir"]), results


def margins(core):
    rows = []
    for (province, group), part in core.groupby(["province_id", "commodity_group"]):
        if not (eligible(part, "price_producer", ("main",)) and eligible(part, "price_wholesale", ("main",))):
            continue
        frame = part.set_index("month").sort_index().loc["2018-12":"2026-10"]
        keep = (frame["price_producer_is_imputed"] != True) & (frame["price_wholesale_is_imputed"] != True)
        producer = frame["price_producer"].where(keep)
        wholesale = frame["price_wholesale"].where(keep)
        data = pd.DataFrame({"producer": producer, "wholesale": wholesale})
        data["margin_rp"] = data["wholesale"] - data["producer"]
        data["ratio"] = data["wholesale"] / data["producer"]
        data["d_producer"] = np.log(data["producer"]).diff()
        data["d_margin_rp"] = data["margin_rp"].diff()
        data["d_ratio"] = data["ratio"].diff()
        data = data.loc["2019-01":].dropna()
        data["arah_produsen"] = np.where(data["d_producer"] < 0, "produsen turun", np.where(data["d_producer"] > 0, "produsen naik", "tetap"))
        rows.append(data.assign(province_id=province, grup=group))
    frame = pd.concat(rows).reset_index()
    frame = frame[frame["arah_produsen"] != "tetap"]
    summary = frame.groupby(["grup", "arah_produsen"]).agg(
        bulan=("ratio", "size"), margin_rp_rata2=("margin_rp", "mean"), rasio_rata2=("ratio", "mean"),
        perubahan_margin_rp_rata2=("d_margin_rp", "mean"), perubahan_margin_rp_median=("d_margin_rp", "median"),
        perubahan_rasio_rata2=("d_ratio", "mean"), porsi_margin_melebar_pct=("d_margin_rp", lambda s: (s > 0).mean() * 100),
    ).reset_index()
    tests = []
    for group, part in frame.groupby("grup"):
        part = part.assign(turun=(part["arah_produsen"] == "produsen turun").astype(float))
        dummies = pd.get_dummies(part["province_id"], prefix="p", drop_first=True, dtype=float)
        for outcome in ("d_margin_rp", "d_ratio", "margin_rp", "ratio"):
            fitted = sm.OLS(part[outcome], sm.add_constant(pd.concat([part[["turun"]], dummies], axis=1))).fit(cov_type="cluster", cov_kwds={"groups": part["province_id"]})
            low, high = fitted.conf_int().loc["turun"]
            tests.append({"grup": group, "ukuran": outcome, "selisih_turun_vs_naik": fitted.params["turun"], "ci_bawah": low, "ci_atas": high, "p": fitted.pvalues["turun"]})
    return summary, pd.DataFrame(tests), frame


def spike_period_asymmetry(core):
    """D-52: periode spike dari harga pedagang besar provinsi (trailing 12 bulan), asimetri pooled di bulan spike vs bulan lain."""
    rows = []
    for threshold in (SENSITIVITY_THRESHOLDS[0], MAIN_THRESHOLD, SENSITIVITY_THRESHOLDS[1]):
        for group in GROUPS.values():
            for upstream, downstream in MONTHLY_PAIRS:
                frames = []
                for province, part in core[core["commodity_group"] == group].groupby("province_id"):
                    if not (eligible(part, upstream, ("main",)) and eligible(part, downstream, ("main",))):
                        continue
                    data = design(part, upstream, downstream, exclude_imputed=False)
                    wholesale = part.set_index("month").sort_index()["price_wholesale"]
                    data["spike"] = flag_spikes(wholesale, threshold)["is_spike"].reindex(data.index)
                    frames.append(data.loc["2019-01":"2026-10"].assign(province_id=province))
                stacked = pd.concat(frames)[["dy", "dx_up", "dx_down", "dx_up_l1", "dx_down_l1", "dy_l1", "province_id", "spike"]].dropna()
                for label, subset in (("bulan spike pedagang besar", stacked[stacked["spike"] == True]), ("bulan lain", stacked[stacked["spike"] == False])):
                    dummies = pd.get_dummies(subset["province_id"], prefix="p", drop_first=True, dtype=float)
                    X = sm.add_constant(pd.concat([subset[["dx_up", "dx_down", "dx_up_l1", "dx_down_l1", "dy_l1"]], dummies], axis=1))
                    fitted = sm.OLS(subset["dy"], X).fit(cov_type="cluster", cov_kwds={"groups": subset["province_id"]})
                    test = fitted.t_test("dx_up + dx_up_l1 - dx_down - dx_down_l1 = 0")
                    rows.append({"ambang": threshold, "grup": group, "pasangan": f"{NICE[upstream]} -> {NICE[downstream]}", "periode": label, "n": len(subset),
                                 "pass_naik": fitted.params["dx_up"] + fitted.params["dx_up_l1"], "pass_turun": fitted.params["dx_down"] + fitted.params["dx_down_l1"],
                                 "selisih": float(test.effect[0]), "p": float(test.pvalue)})
    return pd.DataFrame(rows)


def run():
    provinces = pd.read_csv(FINAL / "dim_province.csv").set_index("province_id")["province_name"]
    weekly = weekly_provinces()
    frequency = change_frequency(weekly)
    lead_lag, threshold, chosen = lead_lag_subset(weekly, frequency)
    lead_summary, lead_detail = summarize_lead_lag(lead_lag)
    core = load_core()
    margin_summary, margin_tests, _ = margins(core)
    spikes = spike_period_asymmetry(core)

    frequency["provinsi"] = frequency["province_id"].map(provinces)
    lead_detail["provinsi"] = lead_detail["province_id"].map(provinces)
    for name, frame in {"h2_change_frequency": frequency, "h2_frequent_lead_lag": lead_detail, "h2_frequent_lead_lag_summary": lead_summary,
                        "h2_margin_summary": margin_summary, "h2_margin_tests": margin_tests, "h2_spike_period_asymmetry": spikes}.items():
        frame.to_csv(TABLES / f"{name}.csv", index=False)
    freq_summary = frequency.groupby(["grup", "level"])["pct_minggu_berubah"].describe()[["count", "min", "25%", "50%", "75%", "max"]].round(1)
    pd.to_pickle({"frequency": frequency, "freq_summary": freq_summary, "threshold": threshold, "chosen": chosen.assign(provinsi=chosen["province_id"].map(provinces)),
                  "lead_summary": lead_summary, "lead_detail": lead_detail, "margin_summary": margin_summary, "margin_tests": margin_tests, "spikes": spikes}, TABLES / "h2_followup.pkl")
    print(freq_summary.to_string())
    print("ambang dipakai:", threshold, "| provinsi:", chosen.groupby("grup").size().to_dict())
    print(chosen.assign(provinsi=chosen["province_id"].map(provinces))[["grup", "provinsi", "pct_minggu_berubah"]].round(1).to_string(index=False))
    print(lead_summary.to_string(index=False))
    print(margin_summary.round(3).to_string(index=False))
    print(margin_tests.round(4).to_string(index=False))
    print(spikes.round(3).to_string(index=False))




def charts():
    """Dua chart pendukung: frekuensi perubahan harga mingguan per level, dan perubahan margin saat harga produsen turun vs naik."""
    import matplotlib.pyplot as plt

    from analysis.h2_transmission import COLORS, FIGURES, INK_2, LABEL, MUTED, SURFACE

    results = pd.read_pickle(TABLES / "h2_followup.pkl")
    frequency = results["frequency"]
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6), sharey=True)
    levels = ["produsen", "pedagang besar", "eceran"]
    rng = np.random.default_rng(1)
    for ax, group in zip(axes, GROUPS.values()):
        for i, level in enumerate(levels):
            values = frequency[(frequency["grup"] == group) & (frequency["level"] == level)]["pct_minggu_berubah"]
            ax.scatter(values, i + rng.uniform(-0.15, 0.15, len(values)), s=16, color=COLORS["down"] if level != "produsen" else COLORS["up"], edgecolor=SURFACE, linewidth=0.8)
            ax.plot([values.median()] * 2, [i - 0.3, i + 0.3], color="#0b0b0b", linewidth=2)
        ax.axvline(70, color=INK_2, linewidth=0.8, linestyle=(0, (4, 3)))
        ax.axvline(50, color=INK_2, linewidth=0.8, linestyle=(0, (1, 2)))
        ax.text(70.5, 2.45, "ambang 70%", fontsize=7.5, color=INK_2)
        ax.text(50.5, 2.45, "50%", fontsize=7.5, color=INK_2)
        ax.set_yticks(range(3), levels)
        ax.set_xlim(0, 102)
        ax.set_xlabel("% minggu harganya berubah dari minggu sebelumnya")
        ax.set_title(LABEL[group], loc="left", fontweight="bold")
    fig.suptitle("Seberapa sering harga mingguan provinsi berubah, 2019-2026 (titik = provinsi, garis hitam = median)", x=0.01, ha="left", fontsize=10.5, fontweight="bold")
    fig.tight_layout()
    fig.savefig(FIGURES / "h2_change_frequency.png", dpi=150)
    plt.close(fig)

    summary = results["margin_summary"]
    fig, ax = plt.subplots(figsize=(7.5, 3.4))
    x = np.arange(len(GROUPS))
    for offset, direction, color in ((-0.18, "produsen naik", COLORS["up"]), (0.18, "produsen turun", COLORS["down"])):
        values = [summary[(summary["grup"] == g) & (summary["arah_produsen"] == direction)]["perubahan_margin_rp_rata2"].iloc[0] for g in GROUPS.values()]
        bars = ax.bar(x + offset, values, width=0.34, color=color, label=f"bulan harga {direction}")
        for bar, value in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, value + (150 if value > 0 else -150), f"{value:+,.0f}".replace(",", "."), ha="center", va="bottom" if value > 0 else "top", fontsize=8, color=INK_2)
    ax.axhline(0, color=INK_2, linewidth=0.8)
    ax.set_xticks(x, [LABEL[g] for g in GROUPS.values()])
    ax.set_ylabel("perubahan margin (Rp/kg per bulan)")
    ax.set_ylim(-5500, 5500)
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2, fontsize=8)
    ax.set_title("Rata-rata perubahan margin pedagang besar - produsen dalam sebulan", loc="left", fontweight="bold", pad=22)
    fig.tight_layout()
    fig.savefig(FIGURES / "h2_margin_change.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    run()
    charts()
