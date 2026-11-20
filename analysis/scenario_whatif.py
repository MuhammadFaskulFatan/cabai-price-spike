"""Langkah 4.7b: skenario what-if biaya lonjakan dan manfaat peringatan dini (D-64).

1. Biaya lonjakan Jan 2023 - Okt 2026 per komoditas: di bulan spike nasional saja,
       (harga eceran nasional - median 12 bulan sebelumnya) x konsumsi rumah tangga nasional bulan itu.
   Konsumsi = konsumsi per kapita Susenas Maret (Tabel 7.1 Buletin Konsumsi Pangan 2026 Sem I) x penduduk proyeksi BPS
   (catatan kaki tabel prognosa Buletin Semester I) / 12. 2026 memakai Susenas 2025 (flag).
2. Redaman 10/25/50% adalah ASUMSI. Skenario (a) batas atas, (b) model merah H4, (c) baseline charter.
   Episode nasional dianggap diketahui lebih awal kalau alarm berbunyi di >= 50% provinsi risk set 1-2 bulan sebelumnya.
3. Alarm palsu dari backtest H4; break-even sebagai biaya maksimum per alarm palsu dan redaman minimum untuk rentang
   biaya per alarm Rp 100 juta - 1 miliar (asumsi, tanpa patokan resmi; D-65).

    python -m analysis.scenario_whatif
"""
import re

import numpy as np
import pandas as pd
import pdfplumber

from analysis.spikes import MAIN_THRESHOLD, episodes, flag_spikes
from analysis.style import FIGURES, GROUP_COLOR, GROUP_LABEL, INK_2, MUTED, ROOT, SURFACE, TABLES, national_prices, plt, setup

PDF_DIR = ROOT / "data" / "raw" / "buletin" / "pdf"
CONSUMPTION_PDF = "979_buletin_konsumsi_pangan_volume_17_nomor_1_tahun_2026.pdf"
POPULATION_PDFS = {2023: "480_buletin_konsumsi_pangan_volume_14_nomor_1_tahun_2023.pdf",
                   2024: "636_buletin_konsumsi_pangan_volume_15_nomor_1_tahun_2024.pdf",
                   2025: "825_buletin_konsumsi_pangan_volume_16_nomor_1_tahun_2025.pdf",
                   2026: "979_buletin_konsumsi_pangan_volume_17_nomor_1_tahun_2026.pdf"}
START, END = pd.Period("2023-01", "M"), pd.Period("2026-10", "M")
FIRST_EVALUABLE, LAST_EVALUABLE = pd.Period("2023-02", "M"), pd.Period("2026-09", "M")   # D-64
DAMPING = (0.10, 0.25, 0.50)                    # asumsi
COST_PER_FALSE_ALARM = (100e6, 250e6, 500e6, 1e9)   # rentang asumsi, Rp per alarm palsu provinsi-bulan (D-65)
NATIONAL_SHARE = 0.5


def to_number(text):
    return float(text.replace(".", "").replace(",", "."))


def per_capita_consumption():
    """Tabel 7.1: konsumsi rumah tangga per kapita (kg/tahun), Susenas Maret; baris prediksi (*) diabaikan."""
    with pdfplumber.open(PDF_DIR / CONSUMPTION_PDF) as pdf:
        for number, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            if "Tabel 7.1. Perkembangan Konsumsi dalam Rumah Tangga" in text:
                break
        else:
            raise RuntimeError("Tabel 7.1 tidak ditemukan")
    rows = []
    for line in text.splitlines():
        match = re.match(r"^(20\d\d) (\S+) (\S+) (\S+) (\S+) (\S+) (\S+) (\S+) (\S+)$", line.strip())
        if match:
            year, merah, *_, rawit, _ = match.groups()
            rows.append({"year": int(year), "cabai_merah": to_number(merah), "cabai_rawit": to_number(rawit), "page": number})
    return pd.DataFrame(rows).set_index("year")


def population():
    """Penduduk (ribu jiwa) dari catatan kaki tabel prognosa cabai tiap edisi Semester I."""
    rows = []
    for year, name in POPULATION_PDFS.items():
        with pdfplumber.open(PDF_DIR / name) as pdf:
            for number, page in enumerate(pdf.pages, start=1):
                text = (page.extract_text() or "").replace("\n", " ")
                match = re.search(rf"jumlah penduduk tahun {year} sebesar ([\d.]+) ribu jiwa", text)
                if match and "cabai" in text.lower():
                    rows.append({"year": year, "population_thousand": to_number(match.group(1)), "source_file": name, "page": number})
                    break
            else:
                raise RuntimeError(f"penduduk {year} tidak ditemukan di {name}")
    return pd.DataFrame(rows).set_index("year")


def consumption_table():
    per_capita = per_capita_consumption()
    people = population()
    rows = []
    for year in range(START.year, END.year + 1):
        used = year if year in per_capita.index else max(y for y in per_capita.index if y <= year)
        for group in GROUP_LABEL:
            kg = per_capita.loc[used, group]
            rows.append({"year": year, "commodity": group, "per_capita_kg_year": kg, "susenas_year_used": used,
                         "flag_nearest_year": used != year, "population_thousand": people.loc[year, "population_thousand"],
                         "national_kg_month": kg * people.loc[year, "population_thousand"] * 1000 / 12,
                         "source_consumption": f"{CONSUMPTION_PDF} hlm {per_capita.loc[used, 'page']} (Tabel 7.1, Susenas Maret {used})",
                         "source_population": f"{people.loc[year, 'source_file']} hlm {people.loc[year, 'page']}"})
    return pd.DataFrame(rows)


def spike_costs(consumption):
    national = national_prices()
    retail = national[national["price_type"] == "eceran"]
    monthly, episode_rows = [], []
    for group in GROUP_LABEL:
        series = retail[retail["commodity"] == group].set_index("month")["price_idr_per_kg"].sort_index()
        flags = flag_spikes(series[series.index <= END], MAIN_THRESHOLD)
        window = flags[(flags.index >= START) & (flags.index <= END)].copy()
        kg = consumption[consumption["commodity"] == group].set_index("year")["national_kg_month"]
        window["kg"] = [kg[m.year] for m in window.index]
        window["excess_idr_per_kg"] = (window["price"] - window["baseline"]).where(window["is_spike"] == True, 0.0)  # noqa: E712
        window["cost_idr"] = window["excess_idr_per_kg"] * window["kg"]
        window["commodity"] = group
        monthly.append(window.rename_axis("month").reset_index())
        found = episodes(flags.dropna(subset=["is_spike"]))
        found = found[(found["end"] >= START) & (found["start"] <= END)]
        for item in found.itertuples():
            months = window[(window.index >= item.start) & (window.index <= item.end)]
            episode_rows.append({"commodity": group, "start": item.start, "end": item.end, "months": item.months,
                                 "months_in_window": len(months), "peak_ratio": item.peak_ratio, "cost_idr": months["cost_idr"].sum(),
                                 "evaluable": FIRST_EVALUABLE <= item.start <= LAST_EVALUABLE})
    return pd.concat(monthly, ignore_index=True), pd.DataFrame(episode_rows)


def load_predictions(group):
    predictions = pd.read_csv(TABLES / f"h4_predictions_{group}.csv")
    for column in ("month", "target_month"):
        predictions[column] = pd.PeriodIndex(predictions[column], freq="M")
    return predictions


def national_alarm_share(predictions, signal):
    """Porsi provinsi risk set yang beralarm per (bulan target, horizon)."""
    return predictions.groupby(["target_month", "horizon"])[signal].mean()


def detect_episodes(episode_table, group, signal):
    share = national_alarm_share(load_predictions(group), signal)
    detected = []
    for item in episode_table.itertuples():
        best = max((share.get((item.start, h), np.nan) for h in (1, 2)), key=lambda v: -1 if np.isnan(v) else v)
        detected.append(bool(item.evaluable and best >= NATIONAL_SHARE))
    return detected


def false_alarms(group, signal, national_onsets):
    predictions = load_predictions(group)
    province_fp = int((predictions[signal].astype(bool) & (predictions["label"] == 0)).sum())
    share = national_alarm_share(predictions, signal)
    alarm_origins = sorted({target - h for (target, h), value in share.items() if value >= NATIONAL_SHARE})
    onsets = set(national_onsets)
    national_fp = sum(1 for origin in alarm_origins if not ({origin + 1, origin + 2} & onsets))
    months = predictions["month"].nunique()
    return {"alarm_palsu_provinsi_bulan": province_fp, "alarm_palsu_per_bulan": province_fp / months,
            "bulan_alarm_nasional": len(alarm_origins), "alarm_nasional_palsu": national_fp}


def scenarios(episode_table, group):
    table = episode_table[episode_table["commodity"] == group].copy()
    table["detected_model"] = detect_episodes(table, group, "alarm")
    table["detected_charter"] = detect_episodes(table, group, "charter")
    onsets = list(table["start"])
    total = table["cost_idr"].sum()
    rows = []
    for label, detected_cost, alarms in (
        ("(a) batas atas: semua episode diketahui lebih awal", total, {"alarm_palsu_provinsi_bulan": 0, "alarm_palsu_per_bulan": 0.0, "bulan_alarm_nasional": np.nan, "alarm_nasional_palsu": 0}),
        ("(b) model merah H4", table.loc[table["detected_model"], "cost_idr"].sum(), false_alarms(group, "alarm", onsets)),
        ("(c) baseline charter", table.loc[table["detected_charter"], "cost_idr"].sum(), false_alarms(group, "charter", onsets)),
    ):
        for damping in DAMPING:
            row = {"commodity": group, "skenario": label, "redaman_asumsi": damping, "biaya_episode_terdeteksi_idr": detected_cost,
                   "porsi_biaya_terdeteksi": detected_cost / total if total else np.nan, "biaya_dihindari_idr": damping * detected_cost, **alarms}
            fp = alarms["alarm_palsu_provinsi_bulan"]
            row["biaya_maks_per_alarm_palsu_idr"] = damping * detected_cost / fp if fp else np.nan
            for cost in COST_PER_FALSE_ALARM:
                row[f"redaman_min_jika_biaya_alarm_{cost / 1e6:.0f}jt"] = cost * fp / detected_cost if detected_cost else np.nan
            rows.append(row)
    return pd.DataFrame(rows), table


def chart_costs(monthly, path):
    fig, axes = plt.subplots(2, 1, figsize=(9.5, 5.2), sharex=True)
    for ax, group in zip(axes, GROUP_LABEL):
        part = monthly[monthly["commodity"] == group]
        x = part["month"].dt.to_timestamp()
        ax.bar(x, part["cost_idr"] / 1e9, width=22, color=GROUP_COLOR[group])
        ax.set_ylabel("Rp miliar")
        total = part["cost_idr"].sum() / 1e12
        ax.set_title(f"{GROUP_LABEL[group]}: total Rp {total:,.2f} triliun di {int((part['is_spike'] == True).sum())} bulan spike".replace(",", "X").replace(".", ",").replace("X", "."),
                     loc="left", fontsize=9, color=INK_2)
    fig.suptitle("Biaya lonjakan bagi rumah tangga: kelebihan harga eceran nasional di bulan spike x konsumsi rumah tangga", x=0.01, ha="left", fontweight="bold", fontsize=10)
    fig.text(0.01, 0.92, "Jan 2023 - Okt 2026; kelebihan = harga - median 12 bulan sebelumnya; harga nominal; konsumsi Susenas x penduduk BPS", fontsize=7.5, color=INK_2)
    fig.tight_layout(rect=(0, 0, 1, 0.91))
    fig.savefig(path, dpi=150)
    plt.close(fig)


def breakeven_table(table):
    part = table[(table["commodity"] == "cabai_merah") & (table["redaman_asumsi"] == DAMPING[0]) & (table["alarm_palsu_provinsi_bulan"] > 0)]
    rows = []
    for item in part.itertuples():
        for cost in COST_PER_FALSE_ALARM:
            rows.append({"skenario": item.skenario, "biaya_per_alarm_palsu_idr": cost, "alarm_palsu_provinsi_bulan": item.alarm_palsu_provinsi_bulan,
                         "biaya_episode_terdeteksi_idr": item.biaya_episode_terdeteksi_idr,
                         "redaman_minimum": cost * item.alarm_palsu_provinsi_bulan / item.biaya_episode_terdeteksi_idr})
    return pd.DataFrame(rows)


def chart_breakeven(breakeven, path):
    labels = {"(b) model merah H4": ("Model merah H4", GROUP_COLOR["cabai_merah"]), "(c) baseline charter": ("Baseline charter", MUTED)}
    costs = list(COST_PER_FALSE_ALARM)
    fig, ax = plt.subplots(figsize=(8, 3.6))
    width = 0.36
    for i, (scenario, (label, color)) in enumerate(labels.items()):
        values = breakeven[breakeven["skenario"] == scenario].set_index("biaya_per_alarm_palsu_idr").loc[costs, "redaman_minimum"] * 100
        bars = ax.bar(np.arange(len(costs)) + (i - 0.5) * width, values, width=width, color=color, label=label)
        for bar, value in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, value + 0.4, f"{value:.1f}%".replace(".", ","), ha="center", fontsize=7.5, color=INK_2)
    ax.set_xticks(range(len(costs)), ["Rp 100 juta", "Rp 250 juta", "Rp 500 juta", "Rp 1 miliar"])
    ax.set_xlabel("biaya menindaklanjuti satu alarm palsu provinsi-bulan (asumsi)")
    ax.set_ylabel("redaman minimum (%)")
    ax.legend(loc="upper left", fontsize=8)
    fig.suptitle("Break-even cabai merah: redaman minimum agar manfaat menutup biaya alarm palsu", x=0.01, ha="left", fontweight="bold", fontsize=10)
    fig.text(0.01, 0.9, "Biaya per alarm dan redaman adalah asumsi; tidak ada patokan anggaran resmi per kegiatan yang bisa dikutip (D-65)", fontsize=7.5, color=INK_2)
    fig.tight_layout(rect=(0, 0, 1, 0.88))
    fig.savefig(path, dpi=150)
    plt.close(fig)


def chart_scenarios(table, path):
    part = table[table["commodity"] == "cabai_merah"]
    labels = list(dict.fromkeys(part["skenario"]))
    short = {labels[0]: "(a) batas atas:\nsemua episode diketahui", labels[1]: "(b) model merah H4", labels[2]: "(c) baseline charter"}
    fig, ax = plt.subplots(figsize=(9.5, 4.0))
    width = 0.25
    shades = {0.10: MUTED, 0.25: INK_2, 0.50: GROUP_COLOR["cabai_merah"]}
    top = 0.0
    for i, damping in enumerate(DAMPING):
        values = [part[(part["skenario"] == s) & (part["redaman_asumsi"] == damping)]["biaya_dihindari_idr"].iloc[0] / 1e9 for s in labels]
        top = max(top, max(values))
        ax.barh(np.arange(len(labels)) + (i - 1) * width, values, height=width, color=shades[damping], label=f"redaman {damping:.0%} (asumsi)")
    ax.set_xlim(0, top * 1.38)
    for j, s in enumerate(labels):
        fp = part[part["skenario"] == s]["alarm_palsu_provinsi_bulan"].iloc[0]
        ax.text(top * 1.36, j, f"alarm palsu\nprovinsi-bulan: {int(fp):,}".replace(",", "."), ha="right", va="center", fontsize=8, color=INK_2)
    ax.set_yticks(range(len(labels)), [short[s] for s in labels])
    ax.invert_yaxis()
    ax.set_xlabel("biaya lonjakan yang dihindari (Rp miliar), cabai merah, Jan 2023 - Okt 2026")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=3, fontsize=7.5)
    fig.suptitle("Skenario what-if cabai merah: semua angka redaman adalah asumsi, bukan hasil", x=0.01, ha="left", fontweight="bold", fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(path, dpi=150)
    plt.close(fig)


def run():
    setup()
    consumption = consumption_table()
    monthly, episode_table = spike_costs(consumption)
    merah, merah_episodes = scenarios(episode_table, "cabai_merah")
    rawit_episodes = episode_table[episode_table["commodity"] == "cabai_rawit"]
    summary = monthly.groupby("commodity").agg(bulan_spike=("is_spike", lambda s: int((s == True).sum())), biaya_idr=("cost_idr", "sum"),  # noqa: E712
                                                kelebihan_rata2_idr_per_kg=("excess_idr_per_kg", lambda s: s[s > 0].mean()))
    summary["episode"] = episode_table.groupby("commodity").size()
    consumption.to_csv(TABLES / "scenario_consumption.csv", index=False)
    monthly.assign(month=monthly["month"].astype(str)).to_csv(TABLES / "scenario_monthly_cost.csv", index=False)
    episodes_out = pd.concat([merah_episodes, rawit_episodes], ignore_index=True)
    episodes_out.assign(start=episodes_out["start"].astype(str), end=episodes_out["end"].astype(str)).to_csv(TABLES / "scenario_episodes.csv", index=False)
    merah.to_csv(TABLES / "scenario_merah.csv", index=False)
    breakeven = breakeven_table(merah)
    breakeven.to_csv(TABLES / "scenario_breakeven.csv", index=False)
    chart_breakeven(breakeven, FIGURES / "scenario_breakeven.png")
    summary.to_csv(TABLES / "scenario_summary.csv")
    chart_costs(monthly, FIGURES / "scenario_spike_cost.png")
    chart_scenarios(merah, FIGURES / "scenario_merah.png")
    pd.set_option("display.width", 250)
    print(consumption.drop(columns=["source_consumption", "source_population"]).to_string(index=False))
    print(consumption[["year", "source_consumption", "source_population"]].drop_duplicates().to_string(index=False))
    print(summary.to_string())
    print(episodes_out.assign(start=episodes_out["start"].astype(str), end=episodes_out["end"].astype(str)).round(3).to_string(index=False))
    print(merah.round(4).to_string(index=False))
    print(breakeven.round(4).to_string(index=False))


if __name__ == "__main__":
    run()
