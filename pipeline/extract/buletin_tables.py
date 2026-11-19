"""Ekstrak halaman tabel "Prognosa Cabai Besar/Rawit" dari PDF Buletin Konsumsi Pangan.

Yang disimpan ke data/raw/buletin/tables/ adalah hasil baca mentah (teks halaman dan tabel
dari pdfplumber) untuk halaman judul tabel plus halaman sesudahnya, karena catatan kaki
yang menjelaskan bulan mana yang realisasi SPH-BPS sering jatuh di halaman berikutnya.
Parsing angka dan catatan kaki ke status realisasi/proyeksi dilakukan di fase transform.

Dari 13 edisi yang diunduh, hanya edisi Nomor 1 (Semester I) tahun 2022-2026 yang memuat
tabel prognosa bulanan cabai; edisi lain tidak, sehingga tidak menghasilkan file.
Jalankan:  python -m pipeline.extract.buletin_tables [--refresh]
"""
import argparse
import json
import re

import pdfplumber

from pipeline.extract.common import RAW_DIR, save_raw, target_path

PDF_DIR = RAW_DIR / "buletin" / "pdf"
OUT = RAW_DIR / "buletin" / "tables"
TITLE = re.compile(r"Tabel\s*7\.\d+\.?\s*Prognosa\s+Cabai\s+(Besar|Rawit)", re.IGNORECASE)


def table_pages(pdf):
    """Nomor halaman (mulai 1) yang memuat judul tabel prognosa, ditambah halaman setelahnya."""
    wanted = set()
    for number, page in enumerate(pdf.pages, start=1):
        if TITLE.search(page.extract_text() or ""):
            wanted.update({number, min(number + 1, len(pdf.pages))})
    return sorted(wanted)


def main():
    parser = argparse.ArgumentParser(description="Ekstrak tabel prognosa cabai dari PDF buletin")
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()

    for pdf_path in sorted(PDF_DIR.glob("*.pdf")):
        with pdfplumber.open(pdf_path) as pdf:
            pages = table_pages(pdf)
            if not pages:
                continue
            path = target_path(OUT / f"{pdf_path.stem}.json", args.refresh)
            if path is None:
                continue
            content = {
                "pdf": pdf_path.name,
                "pages": [
                    {
                        "page": number,
                        "text": pdf.pages[number - 1].extract_text(),
                        "tables": pdf.pages[number - 1].extract_tables(),
                    }
                    for number in pages
                ],
            }
        save_raw(
            path,
            json.dumps(content, ensure_ascii=False, indent=1),
            "buletin_pusdatin",
            {"pdf": pdf_path.name, "pages": pages, "tool": f"pdfplumber {pdfplumber.__version__}"},
            n_rows=len(pages),
        )
        print(f"{pdf_path.name}: halaman {pages}")


if __name__ == "__main__":
    main()
