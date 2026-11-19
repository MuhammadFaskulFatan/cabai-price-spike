"""Kalender hari besar 2018-2026, disusun sendiri (bukan hasil request).

Isinya hari libur nasional untuk empat perayaan yang relevan dengan permintaan cabai:
Idulfitri (1-2 Syawal), Iduladha, Natal, dan Tahun Baru Masehi.

Sumber tanggal: penetapan pemerintah lewat SKB 3 Menteri tiap tahun.
- 2026 sudah dicek langsung ke SKB (setneg.go.id): Idulfitri 21-22 Maret, Iduladha 27 Mei.
- 2018-2025 diisi dari penetapan tahunan; belum dicek ulang satu per satu ke dokumen SKB
  dan masuk daftar spot-check di fase validate.
Cuti bersama sengaja tidak dimasukkan: tanggalnya berubah-ubah dari tahun ke tahun dan
tidak semuanya sudah diverifikasi. Konsekuensinya n_holiday_days sedikit di bawah jumlah
hari libur yang dirasakan masyarakat di bulan Idulfitri.

Jalankan:  python -m pipeline.extract.calendar_holidays [--refresh]
"""
import argparse
import csv
import io
from datetime import date, timedelta

from pipeline.extract.common import RAW_DIR, save_raw, target_path

# tanggal 1 Syawal / 10 Zulhijah menurut penetapan pemerintah
IDULFITRI = {
    2018: date(2018, 6, 15), 2019: date(2019, 6, 5), 2020: date(2020, 5, 24),
    2021: date(2021, 5, 13), 2022: date(2022, 5, 2), 2023: date(2023, 4, 22),
    2024: date(2024, 4, 10), 2025: date(2025, 3, 31), 2026: date(2026, 3, 21),
}
IDULADHA = {
    2018: date(2018, 8, 22), 2019: date(2019, 8, 11), 2020: date(2020, 7, 31),
    2021: date(2021, 7, 20), 2022: date(2022, 7, 10), 2023: date(2023, 6, 29),
    2024: date(2024, 6, 17), 2025: date(2025, 6, 6), 2026: date(2026, 5, 27),
}
FIRST_YEAR, LAST_YEAR = 2018, 2026


def holiday_rows():
    rows = []
    for year in range(FIRST_YEAR, LAST_YEAR + 1):
        rows.append((date(year, 1, 1), "tahun_baru"))
        rows.append((IDULFITRI[year], "idulfitri"))
        rows.append((IDULFITRI[year] + timedelta(days=1), "idulfitri"))  # 2 Syawal
        rows.append((IDULADHA[year], "iduladha"))
        rows.append((date(year, 12, 25), "natal"))
    return sorted(rows)


def main():
    parser = argparse.ArgumentParser(description="Susun kalender hari besar ke data/raw/calendar")
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()

    path = target_path(RAW_DIR / "calendar" / "holidays.csv", args.refresh)
    if path is None:
        print("holidays.csv sudah ada")
        return
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["date", "holiday"])
    rows = holiday_rows()
    writer.writerows((day.isoformat(), name) for day, name in rows)
    save_raw(
        path,
        buffer.getvalue(),
        "calendar_manual",
        {"basis": "SKB 3 Menteri; 2026 dicek ke setneg.go.id, 2018-2025 belum dicek ulang"},
        n_rows=len(rows),
        notes="Hanya libur nasional; cuti bersama tidak dimasukkan.",
    )
    print(f"{len(rows)} hari libur ditulis")


if __name__ == "__main__":
    main()
