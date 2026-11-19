"""Pembaca data raw untuk audit: tidak ada imputation atau pembersihan, hanya parsing apa adanya."""
import json
import re
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from pipeline.extract.common import EXTRACTION_DATE

RAW = Path(__file__).resolve().parents[2] / "data" / "raw"
REPORTS = Path(__file__).resolve().parent / "reports"

FIRST_MONTH = pd.Period("2018-01", "M")
LAST_MONTH = pd.Period(EXTRACTION_DATE, "M")  # November 2026, bulan parsial
CORE_START = pd.Period("2019-01", "M")
MODEL_END = pd.Period("2026-10", "M")
MIN_VALID_DAYS = 10  # aturan: minimal 10 hari kerja terisi, kurang dari itu = missing

COMMODITY_LABELS = {
    "cat_7": "cabai_merah",
    "cat_8": "cabai_rawit",
    "com_13": "merah_besar",
    "com_14": "merah_keriting",
    "com_16": "rawit_merah",
    "com_15": "rawit_hijau",
}
PRICE_TYPE_LABELS = {1: "eceran", 3: "pedagang_besar", 4: "produsen"}

DATE_COLUMN = re.compile(r"^\d{2}/\d{2}/\d{4}$")
FILE_NAME = re.compile(r"pt(\d)_(.+)_(\d{8})_(\d{8})\.json$")


def parse_price(text):
    if text is None or str(text).strip() in ("", "-"):
        return np.nan
    return float(str(text).replace(",", ""))


def parse_bdsp_number(text):
    text = text.strip()
    return float(text.replace(".", "").replace(",", ".")) if text else np.nan


def load_pihps_provinces():
    path = RAW / "pihps" / "ref" / "GetRefProvince.json"
    return {item["name"]: item["id"] for item in json.loads(path.read_text(encoding="utf-8"))["data"]}


def load_pihps_grid(report):
    """Baca semua file PIHPS satu tipe laporan ('daily' atau 'weekly') menjadi tabel panjang.

    Kolom: price_type_id, commodity_id, province (nama; 'Semua Provinsi' = nasional), level, date, price.
    """
    records = []
    for path in sorted((RAW / "pihps" / report).glob("pt*.json")):
        if path.name.endswith(".meta.json"):
            continue
        price_type, commodity, _, _ = FILE_NAME.match(path.name).groups()
        for row in json.loads(path.read_text(encoding="utf-8"))["data"]:
            for key, value in row.items():
                if DATE_COLUMN.match(key):
                    day, month, year = key.split("/")
                    records.append((int(price_type), commodity, row["name"], row["level"], date(int(year), int(month), int(day)), parse_price(value)))
    frame = pd.DataFrame(records, columns=["price_type_id", "commodity_id", "province", "level", "date", "price"])
    return frame


def weekdays_per_month():
    """Jumlah hari Senin-Jumat per bulan sampai tanggal extraction (survei PIHPS hanya hari kerja, D-18)."""
    days = pd.bdate_range(FIRST_MONTH.start_time, pd.Timestamp(EXTRACTION_DATE))
    return pd.Series(1, index=days).groupby(days.to_period("M")).sum()


def months(first=FIRST_MONTH, last=LAST_MONTH):
    return pd.period_range(first, last, freq="M")


def to_markdown(frame, index=False, floatfmt="{:.1f}"):
    """Tabel Markdown sederhana tanpa dependensi tambahan."""
    frame = frame.reset_index() if index else frame
    header = "| " + " | ".join(str(c) for c in frame.columns) + " |"
    divider = "| " + " | ".join("---" for _ in frame.columns) + " |"
    lines = [header, divider]
    for _, row in frame.iterrows():
        cells = []
        for value in row:
            if isinstance(value, (float, np.floating)):
                cells.append("" if np.isnan(value) else floatfmt.format(value))
            else:
                cells.append(str(value))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def write_report(name, text):
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / name).write_text(text, encoding="utf-8")
    print(f"ditulis: pipeline/audit/reports/{name}")
