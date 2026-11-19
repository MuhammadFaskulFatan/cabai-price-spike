"""Spot-check kalender hari besar 2018-2026 (D-30, D-32, D-38).

Pembanding libur nasional: timeanddate.com (sumber sekunder) untuk 2018-2025 dan SKB 2026 di setneg.go.id.
Untuk sebagian tanggal ada konfirmasi dari halaman situs pemerintah (menpan.go.id, kemenag.go.id, kemnaker.go.id);
dokumen SKB aslinya (PDF) tidak dibuka. Verifikasi dibatasi sekitar 10 menit sesuai instruksi, dicek 19 Nov 2026.
Cuti bersama dibaca dari data/raw/calendar/cuti_bersama.csv beserta status verifikasinya.
"""
import pandas as pd

from pipeline.audit.loaders import RAW, to_markdown, write_report
from pipeline.extract.calendar_holidays import holiday_source_level

# tanggal libur nasional menurut timeanddate.com (2018-2025) dan setneg.go.id (2026)
REFERENCE = {
    2018: {"idulfitri": ["2018-06-15", "2018-06-16"], "iduladha": ["2018-08-22"]},
    2019: {"idulfitri": ["2019-06-05", "2019-06-06"], "iduladha": ["2019-08-11"]},
    2020: {"idulfitri": ["2020-05-24", "2020-05-25"], "iduladha": ["2020-07-31"]},
    2021: {"idulfitri": ["2021-05-13", "2021-05-14"], "iduladha": ["2021-07-20"]},
    2022: {"idulfitri": ["2022-05-02", "2022-05-03"], "iduladha": ["2022-07-10"]},
    2023: {"idulfitri": ["2023-04-22", "2023-04-23"], "iduladha": ["2023-06-29"]},
    2024: {"idulfitri": ["2024-04-10", "2024-04-11"], "iduladha": ["2024-06-17"]},
    2025: {"idulfitri": ["2025-03-31", "2025-04-01"], "iduladha": ["2025-06-06"]},
    2026: {"idulfitri": ["2026-03-21", "2026-03-22"], "iduladha": ["2026-05-27"]},
}

def run():
    raw = pd.read_csv(RAW / "calendar" / "holidays.csv", parse_dates=["date"])
    cuti = pd.read_csv(RAW / "calendar" / "cuti_bersama.csv", parse_dates=["date"])

    rows = []
    for year, reference in REFERENCE.items():
        for holiday in ("idulfitri", "iduladha"):
            ours = sorted(raw[(raw["holiday"] == holiday) & (raw["date"].dt.year == year)]["date"].dt.strftime("%Y-%m-%d"))
            status = "resmi (situs pemerintah)" if holiday_source_level(holiday, year) == "official" else "sekunder (timeanddate)"
            rows.append({"tahun": str(year), "perayaan": holiday, "kalender_raw": ", ".join(ours), "pembanding": ", ".join(reference[holiday]),
                         "cocok": ours == reference[holiday], "verifikasi": status})
    result = pd.DataFrame(rows)
    weekend = raw[raw["date"].dt.dayofweek >= 5]
    official_count = int(result["verifikasi"].str.startswith("resmi").sum())

    cuti_summary = (
        cuti.assign(tahun=cuti["date"].dt.year.astype(str))
        .groupby(["tahun", "holiday", "verification"]).agg(hari=("date", "size"), tanggal=("date", lambda s: ", ".join(s.dt.strftime("%m-%d")))).reset_index()
    )

    lines = ["# Audit kalender hari besar", "",
             "Pembanding libur nasional: timeanddate.com (sumber sekunder) untuk 2018-2025 dan SKB 2026 di setneg.go.id. Sebagian tanggal juga terlihat di halaman situs pemerintah "
             "(menpan.go.id, kemenag.go.id, kemnaker.go.id). Dokumen SKB asli 2018-2025 (PDF) tidak dibuka; verifikasi dibatasi sekitar 10 menit sesuai instruksi (D-38). Dicek 19 Nov 2026.", "",
             f"- Libur Idulfitri dan Iduladha 2018-2026: {int(result['cocok'].sum())} dari {len(result)} baris cocok dengan pembanding; "
             f"{official_count} baris terkonfirmasi situs pemerintah, {len(result) - official_count} baris hanya sekunder (timeanddate).",
             f"- Libur nasional yang jatuh di Sabtu atau Minggu (tidak memengaruhi hari kerja PIHPS): {len(weekend)} dari {len(raw)} hari.",
             "- Tahun Baru (1 Januari) dan Natal (25 Desember) berupa tanggal tetap sehingga tidak diperbandingkan.",
             "- Catatan sumber: timeanddate.com ternyata memuat daftar cuti bersama 2021 dan 2023 yang belum mengikuti revisi SKB (Idulfitri 2021 dipangkas menjadi 12 Mei saja; "
             "Iduladha 2023 mendapat cuti 28 dan 30 Juni). Untuk cuti bersama, halaman pemerintah didahulukan.", "",
             "## 1. Libur nasional Idulfitri dan Iduladha", "", to_markdown(result), "",
             "## 2. Cuti bersama (`data/raw/calendar/cuti_bersama.csv`, kolom `is_cuti_bersama`)", "",
             f"{len(cuti)} hari: {int((cuti['verification'] == 'official').sum())} terlihat di halaman pemerintah, {int((cuti['verification'] == 'secondary').sum())} hanya dari timeanddate.com. "
             "Dikosongkan karena belum terverifikasi: seluruh cuti bersama 2020 (direvisi beberapa kali), cuti Natal 2018, 2019, dan 2022; cuti Natal 2021 dihapus di revisi Juni 2021.", "",
             to_markdown(cuti_summary), ""]
    write_report("calendar_audit.md", "\n".join(lines))
