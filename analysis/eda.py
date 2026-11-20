"""EDA deskriptif (Fase 6, tahap perencanaan): tidak ada uji hipotesis di sini.

Isi: tren harga eceran nasional 2019-2026, episode price spike nasional dan per provinsi, pola musiman, dan
perbandingan cabai merah vs cabai rawit. Data dari data/final (core dataset tervalidasi, tanpa cuaca).

    python -m analysis.eda

Output: analysis/figures/*.png, analysis/tables/*.csv, analysis/01_eda_report.md
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from analysis.spikes import MAIN_THRESHOLD, SENSITIVITY_THRESHOLDS, episodes, flag_spikes  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / "data" / "final"
FIGURES = ROOT / "analysis" / "figures"
TABLES = ROOT / "analysis" / "tables"

START, END = "2019-01", "2026-10"  # periode model; November 2026 parsial tidak dipakai menilai spike
GROUPS = {"cabai_merah": "Cabai merah", "cabai_rawit": "Cabai rawit"}
NATIONAL_COMMODITY = {"cabai_merah": "cabai_merah", "cabai_rawit": "cabai_rawit"}

# palet referensi (slot kategori 1-2), teks, grid
COLORS = {"cabai_merah": "#2a78d6", "cabai_rawit": "#eb6834"}
INK, INK_2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "axes.edgecolor": GRID, "axes.labelcolor": INK_2,
    "xtick.color": INK_2, "ytick.color": INK_2, "text.color": INK, "font.size": 9, "axes.titlesize": 10,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "legend.frameon": False,
})


def rupiah(value, _=None):
    return f"Rp{value / 1000:,.0f} rb".replace(",", ".")


def load():
    national = pd.read_csv(FINAL / "price_monthly_national.csv")
    national = national[(national["price_type"] == "eceran") & national["commodity"].isin(GROUPS)]
    national["month"] = pd.PeriodIndex(national["month_start"].str[:7], freq="M")
    core = pd.read_csv(FINAL / "core_province_month.csv")
    core["month"] = pd.PeriodIndex(core["month_start"].str[:7], freq="M")
    provinces = pd.read_csv(FINAL / "dim_province.csv").set_index("province_id")["province_name"]
    return national, core, provinces


def national_series(national, group):
    return national[national["commodity"] == group].set_index("month")["price_idr_per_kg"].sort_index()


# --- episode ---
def national_episodes(national):
    rows, flags_out = [], {}
    for group in GROUPS:
        flags = flag_spikes(national_series(national, group))
        flags_out[group] = flags
        found = episodes(flags.loc[START:END])
        found.insert(0, "commodity_group", group)
        rows.append(found)
    return pd.concat(rows, ignore_index=True), flags_out


def province_episodes(core, threshold=MAIN_THRESHOLD):
    rows = []
    for (province, group), part in core.groupby(["province_id", "commodity_group"]):
        flags = flag_spikes(part.set_index("month")["price_retail"].sort_index(), threshold)
        found = episodes(flags.loc[START:END])
        found.insert(0, "province_id", province)
        found.insert(1, "commodity_group", group)
        rows.append(found)
    return pd.concat(rows, ignore_index=True)


def province_spike_months(core, threshold=MAIN_THRESHOLD):
    rows = []
    for (province, group), part in core.groupby(["province_id", "commodity_group"]):
        flags = flag_spikes(part.set_index("month")["price_retail"].sort_index(), threshold).loc[START:END]
        rows.append(pd.DataFrame({"province_id": province, "commodity_group": group, "month": flags.index, "is_spike": flags["is_spike"].to_numpy()}))
    return pd.concat(rows, ignore_index=True)


# --- musiman ---
def seasonal_profile(series):
    """Deviasi log harga dari rata-rata 12 bulan terpusat (trend dikeluarkan), dirangkum per bulan kalender."""
    logged = np.log(series.loc["2018-07":"2026-10"])
    trend = logged.rolling(12, center=True, min_periods=12).mean()
    deviation = (logged - trend).loc[START:"2025-12"].dropna()
    frame = pd.DataFrame({"dev": deviation, "moy": deviation.index.month})
    month_means = frame.groupby("moy")["dev"].transform("mean")
    share = 1 - ((frame["dev"] - month_means) ** 2).sum() / ((frame["dev"] - frame["dev"].mean()) ** 2).sum()
    summary = frame.groupby("moy")["dev"].agg(["mean", "min", "max"]) * 100
    return summary, share


# --- chart ---
def chart_national_trend(flags_by_group, path):
    fig, axes = plt.subplots(2, 1, figsize=(9, 5.6), sharex=True)
    for ax, group in zip(axes, GROUPS):
        flags = flags_by_group[group].loc[START:"2026-11"]
        x = flags.index.to_timestamp()
        ax.plot(x, flags["price"], color=COLORS[group], linewidth=2, label="Harga eceran nasional")
        ax.plot(x, flags["baseline"] * MAIN_THRESHOLD, color=INK_2, linewidth=1, linestyle=(0, (4, 3)), label=f"Ambang spike ({MAIN_THRESHOLD:.2f} x median 12 bulan sebelumnya)")
        spike = flags["is_spike"].fillna(False).astype(bool)
        spike.loc["2026-11"] = False  # bulan parsial tidak dinilai
        ax.scatter(x[spike.to_numpy()], flags["price"][spike], s=28, color=COLORS[group], edgecolor=SURFACE, linewidth=1.5, zorder=3, label="Bulan spike")
        ax.set_title(GROUPS[group], loc="left", fontweight="bold")
        ax.yaxis.set_major_formatter(rupiah)
        ax.set_ylabel("Rp/kg")
        last = flags.iloc[-1]
        ax.annotate("Nov 2026 (parsial)", (x[-1], last["price"]), xytext=(-4, 8), textcoords="offset points", ha="right", fontsize=8, color=INK_2)
    axes[0].legend(loc="upper left", fontsize=8)
    fig.suptitle("Harga eceran nasional (PIHPS, rata-rata bulanan), Jan 2019 - Nov 2026", x=0.01, ha="left", fontsize=11, fontweight="bold")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def chart_seasonality(profiles, path):
    fig, ax = plt.subplots(figsize=(8, 3.8))
    labels = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
    offsets = {"cabai_merah": -0.15, "cabai_rawit": 0.15}
    for group, (summary, share) in profiles.items():
        x = summary.index + offsets[group]
        ax.errorbar(x, summary["mean"], yerr=[summary["mean"] - summary["min"], summary["max"] - summary["mean"]], fmt="o", color=COLORS[group],
                    ecolor=COLORS[group], elinewidth=1.2, capsize=0, markersize=6, markeredgecolor=SURFACE, label=f"{GROUPS[group]} (bulan kalender menjelaskan {share:.0%} variasi)")
    ax.axhline(0, color=INK_2, linewidth=0.8)
    ax.set_xticks(range(1, 13), labels)
    ax.set_ylabel("Deviasi dari trend 12 bulan (%)")
    ax.set_title("Pola musiman harga eceran nasional, 2019-2025", loc="left", fontsize=10, fontweight="bold", pad=16)
    ax.text(0, 1.01, "Titik = rata-rata per bulan kalender, garis = rentang min-maks antar tahun", transform=ax.transAxes, fontsize=8, color=INK_2, va="bottom")
    ax.legend(loc="upper left", fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def chart_province_heatmap(spike_months, provinces, path):
    months = pd.period_range(START, END, freq="M")
    fig, axes = plt.subplots(1, 2, figsize=(11, 7.2), sharey=True)
    order = provinces.sort_values().index
    for ax, group in zip(axes, GROUPS):
        part = spike_months[spike_months["commodity_group"] == group].pivot(index="province_id", columns="month", values="is_spike").reindex(index=order, columns=months)
        matrix = part.astype(float).to_numpy()
        shown = np.where(np.isnan(matrix), np.nan, matrix)
        cmap = matplotlib.colors.ListedColormap(["#eceae6", COLORS[group]])
        cmap.set_bad("#ffffff")
        ax.imshow(shown, aspect="auto", cmap=cmap, interpolation="nearest", vmin=0, vmax=1)
        ax.set_title(f"{GROUPS[group]}: bulan spike per provinsi", loc="left", fontweight="bold")
        years = [i for i, m in enumerate(months) if m.month == 1]
        ax.set_xticks(years, [str(months[i].year) for i in years])
        ax.grid(False)
    axes[0].set_yticks(range(len(order)), [provinces[i] for i in order], fontsize=7)
    fig.text(0.01, 0.01, f"Warna = bulan dengan harga eceran >= {MAIN_THRESHOLD:.2f} x median 12 bulan sebelumnya; abu-abu = bukan spike.", fontsize=8, color=INK_2)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(path, dpi=150)
    plt.close(fig)


def chart_merah_vs_rawit(national, path):
    merah, rawit = national_series(national, "cabai_merah").loc[START:END], national_series(national, "cabai_rawit").loc[START:END]
    ratio = rawit / merah
    fig, ax = plt.subplots(figsize=(8, 3.4))
    ax.plot(ratio.index.to_timestamp(), ratio, color=COLORS["cabai_rawit"], linewidth=2)
    ax.axhline(1, color=INK_2, linewidth=0.8)
    ax.text(ratio.index.to_timestamp()[2], 1.02, "rawit = merah", fontsize=8, color=INK_2)
    ax.set_ylabel("Rasio harga rawit / merah")
    ax.set_title("Harga eceran nasional cabai rawit relatif terhadap cabai merah, 2019-2026", loc="left", fontweight="bold")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


# --- laporan ---
def md_table(frame, floatfmt="{:,.2f}"):
    lines = ["| " + " | ".join(map(str, frame.columns)) + " |", "| " + " | ".join("---" for _ in frame.columns) + " |"]
    for _, row in frame.iterrows():
        cells = [floatfmt.format(v) if isinstance(v, (float, np.floating)) and not np.isnan(v) else ("" if isinstance(v, float) else str(v)) for v in row]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def run():
    FIGURES.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)
    national, core, provinces = load()

    nat_episodes, flags_by_group = national_episodes(national)
    prov_episodes = province_episodes(core)
    spike_months = province_spike_months(core)
    profiles = {group: seasonal_profile(national_series(national, group)) for group in GROUPS}

    sensitivity = []
    for threshold in (SENSITIVITY_THRESHOLDS[0], MAIN_THRESHOLD, SENSITIVITY_THRESHOLDS[1]):
        nat = [episodes(flag_spikes(national_series(national, g), threshold).loc[START:END]) for g in GROUPS]
        prov = province_episodes(core, threshold)
        sensitivity.append({"ambang": threshold,
                            "episode_nasional_merah": len(nat[0]), "episode_nasional_rawit": len(nat[1]),
                            "episode_provinsi_merah": int((prov["commodity_group"] == "cabai_merah").sum()),
                            "episode_provinsi_rawit": int((prov["commodity_group"] == "cabai_rawit").sum()),
                            "bulan_spike_provinsi_pct": float(province_spike_months(core, threshold)["is_spike"].mean() * 100)})
    sensitivity = pd.DataFrame(sensitivity)

    prov_episodes["province"] = prov_episodes["province_id"].map(provinces)
    per_province = prov_episodes.groupby(["province", "commodity_group"]).agg(episode=("months", "size"), bulan_spike=("months", "sum"), rasio_puncak_maks=("peak_ratio", "max")).reset_index()
    wide = per_province.pivot(index="province", columns="commodity_group", values=["episode", "bulan_spike"]).fillna(0).astype(int)
    wide.columns = [f"{a}_{b.replace('cabai_', '')}" for a, b in wide.columns]
    wide = wide.reindex(provinces.sort_values().to_numpy()).fillna(0).astype(int).reset_index().rename(columns={"index": "province"})

    # serentak: berapa provinsi spike di bulan yang sama
    breadth = spike_months.groupby(["commodity_group", "month"])["is_spike"].mean().mul(100).rename("pct_provinsi_spike").reset_index()
    top_breadth = breadth.sort_values("pct_provinsi_spike", ascending=False).groupby("commodity_group").head(5)

    merah, rawit = national_series(national, "cabai_merah").loc[START:END], national_series(national, "cabai_rawit").loc[START:END]
    log_change_corr = np.log(merah).diff().corr(np.log(rawit).diff())
    level_stats = pd.DataFrame({
        "komoditas": [GROUPS[g] for g in GROUPS],
        "rata2_rp": [merah.mean(), rawit.mean()], "min_rp": [merah.min(), rawit.min()], "maks_rp": [merah.max(), rawit.max()],
        "cv_perubahan_bulanan_pct": [np.log(merah).diff().std() * 100, np.log(rawit).diff().std() * 100],
    })
    episodes_merah = set(spike_months[(spike_months.commodity_group == "cabai_merah") & (spike_months.is_spike == True)][["province_id", "month"]].itertuples(index=False, name=None))
    episodes_rawit = set(spike_months[(spike_months.commodity_group == "cabai_rawit") & (spike_months.is_spike == True)][["province_id", "month"]].itertuples(index=False, name=None))
    overlap = len(episodes_merah & episodes_rawit) / max(1, len(episodes_merah | episodes_rawit)) * 100

    chart_national_trend(flags_by_group, FIGURES / "01_national_retail_trend.png")
    chart_seasonality(profiles, FIGURES / "02_seasonality.png")
    chart_province_heatmap(spike_months, provinces, FIGURES / "03_province_spike_months.png")
    chart_merah_vs_rawit(national, FIGURES / "04_rawit_vs_merah_ratio.png")

    nat_episodes.to_csv(TABLES / "spike_episodes_national.csv", index=False)
    prov_episodes.to_csv(TABLES / "spike_episodes_province.csv", index=False)
    sensitivity.to_csv(TABLES / "spike_threshold_sensitivity.csv", index=False)

    nat_view = nat_episodes.assign(commodity_group=nat_episodes["commodity_group"].map(GROUPS)).astype({"start": str, "end": str, "peak_month": str})
    lines = [
        "# EDA deskriptif: harga cabai 2019-2026", "",
        "Hanya deskripsi: tidak ada uji hipotesis. Data: `data/final` (core dataset tervalidasi, tanpa cuaca). Harga eceran PIHPS (pasar tradisional), rata-rata bulanan dari hari kerja. "
        f"Price spike = harga eceran bulanan >= {MAIN_THRESHOLD:.2f} x median 12 bulan sebelumnya (trailing, tanpa look-ahead); dinilai Jan 2019 - Okt 2026; November 2026 parsial tidak dinilai.", "",
        "Script: `analysis/eda.py` (definisi spike di `analysis/spikes.py`). Tabel lengkap di `analysis/tables/`.", "",
        "## 1. Tren harga eceran nasional", "",
        "![Tren harga eceran nasional](figures/01_national_retail_trend.png)", "",
        md_table(level_stats.round(1), "{:,.1f}"), "",
        "`cv_perubahan_bulanan_pct` = simpangan baku perubahan log bulanan (persen).", "",
        "## 2. Episode price spike nasional", "",
        md_table(nat_view, "{:,.2f}"), "",
        "## 3. Episode per provinsi", "",
        f"Total {len(prov_episodes)} episode di 34 provinsi (cabai merah {int((prov_episodes.commodity_group == 'cabai_merah').sum())}, cabai rawit {int((prov_episodes.commodity_group == 'cabai_rawit').sum())}).", "",
        "![Bulan spike per provinsi](figures/03_province_spike_months.png)", "",
        md_table(wide, "{:,.0f}"), "",
        "Bulan dengan porsi provinsi spike terbanyak (spike serentak):", "",
        md_table(top_breadth.assign(commodity_group=top_breadth["commodity_group"].map(GROUPS), month=top_breadth["month"].astype(str)), "{:,.0f}"), "",
        "## 4. Sensitivity ambang spike", "",
        md_table(sensitivity, "{:,.2f}"), "",
        "Jumlah episode tidak selalu turun saat ambang naik: satu episode panjang di ambang 1,25 bisa pecah menjadi dua episode pendek di ambang 1,35 (contoh: cabai merah nasional). "
        "Porsi bulan spike provinsi turun monoton (36% -> 27% -> 21%), jadi ukuran itu lebih stabil untuk membandingkan ambang.", "",
        "## 5. Pola musiman", "",
        "![Pola musiman](figures/02_seasonality.png)", "",
        f"Setelah trend 12 bulan dikeluarkan, bulan kalender menjelaskan {profiles['cabai_merah'][1]:.0%} variasi deviasi log harga cabai merah dan {profiles['cabai_rawit'][1]:.0%} untuk cabai rawit (2019-2025). "
        "Rentang min-maks per bulan jauh lebih lebar dari rata-ratanya: lonjakan lebih banyak ditentukan kejadian tahun tertentu daripada pola musiman yang berulang. "
        "Angka ini lebih tinggi dari exploratory check di Project Charter (sekitar 2%) karena cara mengeluarkan trend berbeda (di sini rata-rata 12 bulan terpusat pada harga eceran nasional); kesimpulannya sama: musiman bukan penjelas utama, terutama untuk cabai merah.", "",
        "## 6. Cabai merah vs cabai rawit", "",
        "![Rasio rawit terhadap merah](figures/04_rawit_vs_merah_ratio.png)", "",
        f"- Korelasi perubahan log bulanan harga eceran nasional merah vs rawit: {log_change_corr:.2f}.",
        f"- Tumpang tindih bulan spike provinsi (bulan dan provinsi yang sama) antara merah dan rawit: {overlap:.0f}% dari gabungan bulan spike keduanya.", "",
        "## 7. Catatan untuk analisis", "",
        "- Episode didefinisikan di level harga eceran; hipotesis yang memakai harga produsen atau pedagang besar memakai episode yang sama sebagai penanda kejadian.",
        "- Harga eceran inti tidak punya bulan imputasi; pembatasan D-44 terutama berlaku untuk harga produsen dan pedagang besar.",
        "- Cuaca belum ada di core dataset; H1 dan H4 menunggu paket cuaca.", ""]
    (ROOT / "analysis" / "01_eda_report.md").write_text("\n".join(lines), encoding="utf-8")
    print(nat_view.to_string(index=False))
    print(sensitivity.round(2).to_string(index=False))
    print({g: round(s, 3) for g, (_, s) in profiles.items()}, "corr", round(log_change_corr, 2), "overlap", round(overlap, 1))


if __name__ == "__main__":
    run()
