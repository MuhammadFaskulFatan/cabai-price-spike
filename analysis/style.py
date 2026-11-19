"""Gaya chart dan helper tabel yang dipakai bersama oleh script analisis."""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / "data" / "final"
FIGURES = ROOT / "analysis" / "figures"
TABLES = ROOT / "analysis" / "tables"

GROUP_LABEL = {"cabai_merah": "Cabai merah", "cabai_rawit": "Cabai rawit"}
GROUP_COLOR = {"cabai_merah": "#2a78d6", "cabai_rawit": "#eb6834"}
ACCENT = "#1baf7a"
INK, INK_2, GRID, SURFACE, MUTED, SHADE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb", "#c9c7c1", "#eceae6"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "axes.edgecolor": GRID, "axes.labelcolor": INK_2,
    "xtick.color": INK_2, "ytick.color": INK_2, "text.color": INK, "font.size": 9, "axes.titlesize": 10,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "legend.frameon": False,
})


def setup():
    FIGURES.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)


def md(frame, fmt="{:,.3f}"):
    """Tabel Markdown; angka desimal memakai format yang diberikan."""
    lines = ["| " + " | ".join(map(str, frame.columns)) + " |", "| " + " | ".join("---" for _ in frame.columns) + " |"]
    for _, row in frame.iterrows():
        cells = []
        for value in row:
            if isinstance(value, (float, np.floating)):
                cells.append("" if np.isnan(value) else fmt.format(value))
            else:
                cells.append(str(value))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def load_core():
    core = pd.read_csv(FINAL / "core_province_month.csv")
    core["month"] = pd.PeriodIndex(core["month_start"].str[:7], freq="M")
    return core


def province_names():
    return pd.read_csv(FINAL / "dim_province.csv").set_index("province_id")["province_name"]


def national_prices():
    national = pd.read_csv(FINAL / "price_monthly_national.csv")
    national = national[national["commodity"].isin(GROUP_LABEL)].copy()
    national["month"] = pd.PeriodIndex(national["month_start"].str[:7], freq="M")
    return national
