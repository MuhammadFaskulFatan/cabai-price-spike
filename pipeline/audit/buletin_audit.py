"""Audit Buletin Konsumsi Pangan: edisi yang tersedia dan cakupan bulan realisasi pada tabel prognosa.

Output: pipeline/audit/reports/buletin_audit.md dan buletin_prognosa_months.csv.
Parsing di sini hanya untuk audit (angka bulanan dibaca dari teks halaman dan dicek terhadap baris Total);
nilai yang dipakai di pipeline baru dibentuk di fase transform.
"""
import json
import re

import pandas as pd

from pipeline.audit.loaders import RAW, REPORTS, to_markdown, write_report

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


def run():
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

    table = pd.DataFrame(rows)
    REPORTS.mkdir(parents=True, exist_ok=True)
    table.to_csv(REPORTS / "buletin_prognosa_months.csv", index=False)

    lines = ["# Audit Buletin Konsumsi Pangan", "",
             f"{len(editions)} edisi ditemukan di satudata.pertanian.go.id dan diunduh (D-23). Tidak ada edisi 2018-2019. Tabel Prognosa Cabai Besar dan Rawit hanya ada di edisi Nomor 1 (Semester I) 2022-2026; edisi lain tidak memuatnya.", "",
             "## 1. Edisi", "",
             to_markdown(pd.DataFrame([{"id": e["publication_id"], "judul": e["judul"], "tabel_prognosa_cabai": "ada" if e["has_prognosa_table"] else "tidak ada"} for e in editions])), ""]

    lines += ["## 2. Hasil baca tabel prognosa", "",
              "Angka produksi dibaca dari teks halaman (kolom Produksi: kolom pertama pada edisi 2022-2023, kolom ketiga setelah Stok Awal dan Susut pada edisi 2024 ke atas) dan jumlah 12 bulan dicek terhadap baris Total. Kolom `realisasi_sampai_bulan` diambil dari catatan kaki yang menyebut produksi berdasarkan SPH-BPS.", "",
              to_markdown(pd.DataFrame(notes).drop(columns=["kutipan_catatan_kaki"]), floatfmt="{:,.0f}"), "",
              "Kutipan catatan kaki yang dibaca:", ""]
    for note in notes:
        lines.append(f"- {note['edisi']} {note['komoditas']}: {note['kutipan_catatan_kaki'] or '(tidak terbaca otomatis)'}")
    lines.append("")

    lines += ["## 3. Cakupan bulan realisasi (R) vs proyeksi (P)", "", "Satu baris per tahun edisi; bulan Januari sampai Desember. `-` = tidak ada tabel.", ""]
    for commodity in ("besar", "rawit"):
        lines += [f"### cabai {commodity}", ""]
        matrix = []
        for year in range(2019, 2027):
            part = table[(table["edition_year"] == year) & (table["commodity"] == commodity)] if len(table) else pd.DataFrame()
            if part.empty:
                matrix.append({"tahun": str(year), **{name[:3]: "-" for name in MONTHS}})
            else:
                symbol = {"realisasi": "R", "proyeksi": "P", "tidak ada tabel": "-"}
                matrix.append({"tahun": str(year), **{MONTHS[m - 1][:3]: symbol[part[part["month"] == m]["status"].iloc[0]] for m in range(1, 13)}})
        lines += [to_markdown(pd.DataFrame(matrix)), ""]
    realised = table[table["status"] == "realisasi"] if len(table) else table
    lines += ["Jumlah bulan realisasi (kandidat hold-out MAPE untuk Denton, D-26):", "",
              to_markdown(realised.groupby("commodity").size().rename("bulan_realisasi").reset_index()) if len(realised) else "0", "",
              "Dari 95 bulan periode inti (2019-01 sampai 2026-11), bulan tanpa angka realisasi dibiarkan missing sesuai data quality rules.", ""]

    lines += ["## 4. Angka produksi bulanan (ton) per edisi", ""]
    for commodity in ("besar", "rawit"):
        wide = table[table["commodity"] == commodity].pivot(index="edition_year", columns="month", values="production_ton")
        wide.columns = [MONTHS[m - 1][:3] for m in wide.columns]
        wide.insert(0, "total", wide.sum(axis=1))
        lines += [f"### cabai {commodity}", "", to_markdown(wide.reset_index().astype({"edition_year": str}), floatfmt="{:,.0f}"), ""]

    bdsp = pd.read_csv(REPORTS / "bdsp_province_year.csv") if (REPORTS / "bdsp_province_year.csv").exists() else None
    if bdsp is not None:
        lines += ["## 5. Total prognosa vs produksi tahunan BDSP (informasi, bukan rekonsiliasi resmi)", ""]
        comparison = []
        for _, row in table.groupby(["edition_year", "commodity"])["production_ton"].sum().reset_index().iterrows():
            key = "cabe_besar" if row["commodity"] == "besar" else "cabe_rawit"
            bdsp_total = bdsp[(bdsp["commodity"] == key) & (bdsp["indicator"] == "produksi") & (bdsp["year"] == row["edition_year"])]["value"].sum()
            comparison.append({"tahun": str(row["edition_year"]), "komoditas": row["commodity"], "prognosa_ton": row["production_ton"], "bdsp_ton": bdsp_total or None,
                               "rasio": row["production_ton"] / bdsp_total if bdsp_total else None})
        lines += [to_markdown(pd.DataFrame(comparison), floatfmt="{:,.2f}"), "",
                  "Angka prognosa adalah campuran realisasi dan proyeksi untuk tahun berjalan, jadi selisih terhadap BDSP wajar; rekonsiliasi resmi dikerjakan di fase validate.", ""]

    write_report("buletin_audit.md", "\n".join(lines))
