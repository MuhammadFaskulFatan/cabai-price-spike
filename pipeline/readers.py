"""Pembaca data raw yang dipakai audit dan transform: hanya parsing apa adanya, tanpa imputation atau pembersihan."""
import json
import re
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from bs4 import BeautifulSoup

from pipeline.extract.common import EXTRACTION_DATE
from pipeline.provinces import BPS_TO_PIHPS
from pipeline.rules import MIN_VALID_DAYS  # noqa: F401  (diekspor ke modul audit)

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"

FIRST_MONTH = pd.Period("2018-01", "M")
LAST_MONTH = pd.Period(EXTRACTION_DATE, "M")  # November 2026, bulan parsial
CORE_START = pd.Period("2019-01", "M")
MODEL_END = pd.Period("2026-10", "M")

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


# ---- Buletin Konsumsi Pangan: tabel Prognosa Cabai Besar dan Rawit ----
MONTHS = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
MONTH_PREFIX = {name[:3].lower(): index for index, name in enumerate(MONTHS, start=1)}
NUMBER = re.compile(r"\d{1,3}(?:[.,]\d{3})+|\d+")
LINE = re.compile(r"^(Jan\w*|Feb\w*|Mar\w*|Apr\w*|Mei|Jun\w*|Jul\w*|Agu\w*|Sep\w*|Okt\w*|No\w*|Des\w*)\s+(.*)$")
TITLE = re.compile(r"Tabel\s*7\.\d+\.?\s*Prognosa\s+Cabai\s+(Besar|Rawit)", re.IGNORECASE)
# kolom Produksi: edisi 2022-2023 menaruhnya di kolom pertama, edisi 2024 ke atas setelah Stok Awal dan Susut
PREFERRED_INDEX = {2022: 0, 2023: 0, 2024: 2, 2025: 2, 2026: 2}
REALISED_END = re.compile(r"Januari\s*[-–—]\s*(Februari|Maret|April|Mei)", re.IGNORECASE)


def to_number(token):
    return int(re.sub(r"[.,]", "", token))


def normalize(line):
    """Gabungkan angka yang terpotong di teks PDF, misalnya '1 72.886' -> '172.886' dan '1 .385.035' -> '1.385.035'."""
    return re.sub(r"(?<![\d.,])(\d) (?=\d{0,2}[.,]\d{3}\b)", r"\1", line)


def edition_year(name):
    return int(re.search(r"tahun_(\d{4})", name).group(1))


def parse_table(text, index):
    """Baca 12 baris bulan dan baris Total dari teks halaman: kembalikan (produksi per bulan, produksi total)."""
    produksi, total = {}, None
    for raw_line in text.splitlines():
        line = normalize(raw_line.strip())
        match = LINE.match(line)
        if match:
            tokens = NUMBER.findall(match.group(2))
            month = MONTH_PREFIX.get(match.group(1)[:3].lower())
            if month and len(tokens) > index and month not in produksi:
                produksi[month] = to_number(tokens[index])
        elif line.startswith("Total"):
            tokens = NUMBER.findall(line)
            if len(tokens) > index:
                total = to_number(tokens[index])
    return produksi, total


def realised_months(text):
    """Bulan terakhir yang berdasar SPH-BPS, dari kalimat catatan kaki 'Produksi Januari-Maret ... SPH'."""
    for sentence in re.split(r"(?<=[.;])\s+|\n", text):
        if re.search(r"SPH|SBH|Statistik Pertanian", sentence, re.IGNORECASE) and REALISED_END.search(sentence):
            end = REALISED_END.search(sentence).group(1).lower()
            return {"februari": 2, "maret": 3, "april": 4, "mei": 5}[end], sentence.strip()[:160]
    return None, ""


def read_prognosa():
    """Baca semua edisi buletin: kembalikan (editions, rows per bulan, catatan hasil baca)."""
    editions = []
    for meta_path in sorted((RAW / "buletin" / "pdf").glob("*.pdf.meta.json")):
        request = json.loads(meta_path.read_text(encoding="utf-8"))["request"]
        pdf_name = meta_path.name.replace(".meta.json", "")
        table_file = RAW / "buletin" / "tables" / (pdf_name.replace(".pdf", "") + ".json")
        editions.append({"publication_id": request["publication_id"], "judul": request["title"], "has_prognosa_table": table_file.exists(), "pdf": pdf_name, "table_file": table_file})

    rows, notes = [], []
    for edition in editions:
        if not edition["has_prognosa_table"]:
            continue
        year = edition_year(edition["pdf"])
        pages = json.loads(edition["table_file"].read_text(encoding="utf-8"))["pages"]
        texts = {page["page"]: page["text"] or "" for page in pages}
        for commodity in ("Besar", "Rawit"):
            start = [number for number, text in texts.items() if any(m.group(1).lower() == commodity.lower() for m in TITLE.finditer(text))]
            numbers = sorted(texts)
            candidate_pages = []
            if start:
                first = start[0]
                candidate_pages = [first] + ([first + 1] if first + 1 in texts else [])
            produksi, total = {}, None
            for index in [PREFERRED_INDEX[year]] + [i for i in range(4) if i != PREFERRED_INDEX[year]]:
                produksi, total = {}, None
                for number in candidate_pages:
                    found, found_total = parse_table(texts[number], index)
                    for month, value in found.items():
                        produksi.setdefault(month, value)
                    total = total or found_total
                if len(produksi) == 12 and total and abs(sum(produksi.values()) - total) <= max(12, 0.002 * total):
                    break
            end_month, excerpt = None, ""
            for number in candidate_pages:
                end_month, excerpt = realised_months(texts[number])
                if end_month:
                    break
            parsed_sum = sum(produksi.values()) if len(produksi) == 12 else None
            checks = "ok" if parsed_sum and total and abs(parsed_sum - total) <= max(12, 0.002 * total) else ("total tidak cocok" if produksi else "tabel tidak terbaca")
            notes.append({"edisi": f"{edition['publication_id']} ({year})", "komoditas": commodity.lower(), "bulan_terbaca": len(produksi), "jumlah_12_bulan": parsed_sum, "total_tabel": total,
                          "cek_jumlah": checks, "realisasi_sampai_bulan": end_month or "tidak terbaca", "kutipan_catatan_kaki": excerpt})
            for month in range(1, 13):
                status = "tidak ada tabel" if month not in produksi else ("realisasi" if end_month and month <= end_month else "proyeksi")
                rows.append({"edition_year": year, "publication_id": edition["publication_id"], "commodity": commodity.lower(), "month": month, "production_ton": produksi.get(month), "status": status})
    return editions, rows, notes


# ---- BDSP: tabel produksi dan luas panen tahunan ----
YEARS = list(range(2018, 2026))
COMMODITIES = {"cabe_besar": "cabe besar", "cabe_keriting": "cabe keriting", "cabe_rawit": "cabe rawit"}
INDICATORS = {"produksi": "produksi", "luas_panen": "luas panen"}
TO_BASE_UNIT = {"Ton": 1.0, "Kuintal": 0.1, "Ha": 1.0}  # produksi dalam ton


def read_table(path):
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "lxml")
    rows = {}
    for tr in soup.find_all("tr"):
        cells = [cell.get_text(strip=True) for cell in tr.find_all(["th", "td"])]
        if len(cells) >= 10 and re.match(r"^\d{2,4} - ", cells[1]):
            rows[cells[1]] = [parse_bdsp_number(value) for value in cells[2:10]]
        elif cells and cells[0] == "TOTAL":
            rows["TOTAL"] = [parse_bdsp_number(value) for value in cells[1:9]]
    return rows


def unit_of(path):
    meta = json.loads(path.with_name(path.name + ".meta.json").read_text(encoding="utf-8"))
    return meta["request"]["body"]["satuannm"]


def load_province_tables():
    """Tabel panjang: commodity, indicator, bps_code, bdsp_name, parent_id, year, value (ton atau ha)."""
    records, units = [], {}
    for commodity in COMMODITIES:
        for indicator in INDICATORS:
            path = RAW / "bdsp" / "provinsi" / f"{commodity}_{indicator}.html"
            unit = unit_of(path)
            units[(commodity, indicator)] = unit
            for label, values in read_table(path).items():
                if label == "TOTAL":
                    continue
                code, name = label.split(" - ", 1)
                for year, value in zip(YEARS, values):
                    records.append((commodity, indicator, code, name, BPS_TO_PIHPS[code][0], year, value * TO_BASE_UNIT[unit]))
    return pd.DataFrame(records, columns=["commodity", "indicator", "bps_code", "bdsp_name", "province_id", "year", "value"]), units
