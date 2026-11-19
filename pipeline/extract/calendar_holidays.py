"""Kalender hari besar 2018-2026, disusun sendiri (bukan hasil request).

Isinya hari libur nasional untuk empat perayaan yang relevan dengan permintaan cabai:
Idulfitri (1-2 Syawal), Iduladha, Natal, dan Tahun Baru Masehi.

Sumber tanggal: penetapan pemerintah lewat SKB 3 Menteri tiap tahun.
- 2026 sudah dicek langsung ke SKB (setneg.go.id): Idulfitri 21-22 Maret, Iduladha 27 Mei.
- 2018-2025 dicek di fase audit (D-32): sebagian tercantum di situs pemerintah (menpan, kemenag,
  kemnaker), sisanya hanya cocok dengan timeanddate.com (sumber sekunder); lihat calendar_audit.md.
Cuti bersama ada di file terpisah (cuti_bersama.csv, kolom is_cuti_bersama dan verification).
Tanggalnya berubah-ubah (misalnya 2021 dipangkas dari 4 hari menjadi 1 hari untuk Idulfitri, 2023 digeser),
jadi hanya tanggal pasca-revisi yang sudah terlihat di situs pemerintah yang dimasukkan; 2020 dan cuti
Natal 2018-2019 dan 2022 belum terverifikasi dan sengaja dikosongkan, bukan ditebak.

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

# cuti bersama pasca-revisi. verification: official = tercantum di halaman situs pemerintah (setneg, menpan,
# kemenag, kemnaker); secondary = hanya dari timeanddate.com. Dicek 19 Nov 2026.
CUTI_BERSAMA = {
    ("idulfitri", 2018): (["2018-06-11", "2018-06-12", "2018-06-13", "2018-06-14", "2018-06-18", "2018-06-19", "2018-06-20"], "official", "menpan.go.id, kemnaker.go.id: 4 hari awal + 3 hari tambahan (revisi April 2018)"),
    ("idulfitri", 2019): (["2019-06-03", "2019-06-04", "2019-06-07"], "official", "kemenag.go.id, menpan.go.id"),
    ("idulfitri", 2021): (["2021-05-12"], "official", "kemenag.go.id: revisi Februari 2021 memangkas 17-19 Mei"),
    ("idulfitri", 2022): (["2022-04-29", "2022-05-04", "2022-05-05", "2022-05-06"], "official", "menpan.go.id: perubahan SKB 7 April 2022"),
    ("idulfitri", 2023): (["2023-04-19", "2023-04-20", "2023-04-21", "2023-04-24", "2023-04-25"], "official", "kemnaker.go.id, menpan.go.id: perubahan SKB Maret 2023"),
    ("idulfitri", 2024): (["2024-04-08", "2024-04-09", "2024-04-12", "2024-04-15"], "official", "kemenag.go.id, menpan.go.id"),
    ("idulfitri", 2025): (["2025-04-02", "2025-04-03", "2025-04-04", "2025-04-07"], "secondary", "timeanddate.com; halaman kemnaker hanya memuat total hari"),
    ("idulfitri", 2026): (["2026-03-20", "2026-03-23", "2026-03-24"], "official", "setneg.go.id SKB 2026"),
    ("iduladha", 2023): (["2023-06-28", "2023-06-30"], "official", "menpan.go.id: perubahan kedua SKB 2023"),
    ("iduladha", 2024): (["2024-06-18"], "official", "kemenag.go.id, menpan.go.id"),
    ("iduladha", 2025): (["2025-06-09"], "secondary", "timeanddate.com"),
    ("iduladha", 2026): (["2026-05-28"], "official", "setneg.go.id SKB 2026"),
    ("natal", 2023): (["2023-12-26"], "official", "menpan.go.id, kemnaker.go.id"),
    ("natal", 2024): (["2024-12-26"], "official", "kemenag.go.id, menpan.go.id"),
    ("natal", 2025): (["2025-12-26"], "official", "menpan.go.id"),
    ("natal", 2026): (["2026-12-24"], "official", "setneg.go.id SKB 2026"),
}



def holiday_rows():
    rows = []
    for year in range(FIRST_YEAR, LAST_YEAR + 1):
        rows.append((date(year, 1, 1), "tahun_baru"))
        rows.append((IDULFITRI[year], "idulfitri"))
        rows.append((IDULFITRI[year] + timedelta(days=1), "idulfitri"))  # 2 Syawal
        rows.append((IDULADHA[year], "iduladha"))
        rows.append((date(year, 12, 25), "natal"))
    return sorted(rows)


def write_cuti_bersama(refresh):
    path = target_path(RAW_DIR / "calendar" / "cuti_bersama.csv", refresh)
    if path is None:
        print("cuti_bersama.csv sudah ada")
        return
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["date", "holiday", "is_cuti_bersama", "verification", "source"])
    rows = sorted((day, holiday, verification, source) for (holiday, _), (days, verification, source) in CUTI_BERSAMA.items() for day in days)
    writer.writerows((day, holiday, "TRUE", verification, source) for day, holiday, verification, source in rows)
    save_raw(
        path, buffer.getvalue(), "calendar_manual",
        {"basis": "SKB 3 Menteri pasca-revisi, dicek ke situs pemerintah dan timeanddate.com pada 19 Nov 2026"},
        n_rows=len(rows),
        notes="Belum terverifikasi dan dikosongkan: seluruh cuti bersama 2020, cuti Natal 2018, 2019, 2021 (dihapus di revisi Juni 2021), 2022, dan cuti Idulfitri/Iduladha 2018-2022 selain yang tercantum.",
    )
    print(f"{len(rows)} hari cuti bersama ditulis")


def main():
    parser = argparse.ArgumentParser(description="Susun kalender hari besar ke data/raw/calendar")
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()

    write_cuti_bersama(args.refresh)
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
