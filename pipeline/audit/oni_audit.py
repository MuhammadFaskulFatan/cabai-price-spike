"""Audit NOAA ONI: kontinuitas bulan setelah season dipetakan ke bulan tengahnya (DJF -> Januari)."""
import pandas as pd

from pipeline.audit.loaders import FIRST_MONTH, LAST_MONTH, RAW, to_markdown, write_report

SEASON_TO_MONTH = {"DJF": 1, "JFM": 2, "FMA": 3, "MAM": 4, "AMJ": 5, "MJJ": 6, "JJA": 7, "JAS": 8, "ASO": 9, "SON": 10, "OND": 11, "NDJ": 12}


def load_oni():
    frame = pd.read_csv(RAW / "noaa_oni" / "oni.ascii.txt", sep=r"\s+")
    frame["month"] = [pd.Period(year=int(year), month=SEASON_TO_MONTH[season], freq="M") for season, year in zip(frame["SEAS"], frame["YR"])]
    return frame


def run():
    oni = load_oni()
    wanted = pd.period_range(FIRST_MONTH, LAST_MONTH, freq="M")
    present = set(oni["month"])
    missing = [str(month) for month in wanted if month not in present]
    in_range = oni[(oni["month"] >= FIRST_MONTH) & (oni["month"] <= LAST_MONTH)].copy()
    in_range["phase"] = pd.cut(in_range["ANOM"], [-10, -0.5, 0.5, 10], labels=["la_nina", "neutral", "el_nino"], right=False)
    in_range["year"] = in_range["month"].dt.year
    phases = in_range.groupby(["year", "phase"], observed=False).size().unstack("phase").reset_index()
    phases["year"] = phases["year"].astype(str)

    lines = ["# Audit NOAA ONI", "",
             f"{len(oni)} season dari {oni['month'].min()} sampai {oni['month'].max()} (season terakhir {oni.iloc[-1]['SEAS']} {oni.iloc[-1]['YR']}, dipetakan ke bulan tengahnya). "
             f"Rentang yang dibutuhkan {FIRST_MONTH} sampai {LAST_MONTH}.", "",
             f"- Bulan di rentang tanpa nilai ONI: {', '.join(missing) or 'tidak ada'}. Sesuai aturan, bulan ini tidak di-impute (D-16).",
             f"- Duplikat bulan: {int(oni['month'].duplicated().sum())}. Nilai ANOM kosong: {int(oni['ANOM'].isna().sum())}.",
             f"- Rentang ANOM pada periode kerja: {in_range['ANOM'].min():.2f} sampai {in_range['ANOM'].max():.2f}.",
             "- Pemetaan season ke bulan tengah memakai kolom YR sebagai tahun bulan tengah (DJF 1950 = Januari 1950).", "",
             "Jumlah bulan per fase ENSO per tahun (ambang +-0,5):", "", to_markdown(phases), ""]
    write_report("oni_audit.md", "\n".join(lines))
