"""Audit Buletin Konsumsi Pangan: edisi yang tersedia dan cakupan bulan realisasi pada tabel prognosa.

Output: pipeline/audit/reports/buletin_audit.md dan buletin_prognosa_months.csv.
Pembacaan tabel ada di pipeline.readers (angka bulanan dibaca dari teks halaman dan dicek terhadap baris Total).
"""
import pandas as pd

from pipeline.audit.loaders import REPORTS, to_markdown, write_report
from pipeline.readers import RAW, read_prognosa

MONTHS = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]


def run():
    editions, rows, notes = read_prognosa()

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
