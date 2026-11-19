"""Spot-check kalender hari besar 2018-2026 terhadap tanggal yang dilaporkan sumber (D-30).

Sumber pembanding: timeanddate.com untuk 2018-2025 (sumber sekunder yang memuat tanggal libur nasional dan cuti bersama
menurut SKB 3 Menteri) dan SKB 2026 di setneg.go.id. Dicek pada 19 Nov 2026. Dokumen SKB 2018-2025 sendiri belum dibuka.
Hanya libur nasional yang masuk kalender raw (D-21); cuti bersama di bawah ini hanya untuk informasi.
"""
import pandas as pd

from pipeline.audit.loaders import RAW, to_markdown, write_report

# tanggal yang dilaporkan sumber pembanding
REFERENCE = {
    2018: {"idulfitri": ["2018-06-15", "2018-06-16"], "iduladha": ["2018-08-22"], "cuti_bersama": ["2018-06-11", "2018-06-12", "2018-06-13", "2018-06-14", "2018-06-18", "2018-06-19", "2018-06-20"]},
    2019: {"idulfitri": ["2019-06-05", "2019-06-06"], "iduladha": ["2019-08-11"], "cuti_bersama": ["2019-06-03", "2019-06-04", "2019-06-07"]},
    2020: {"idulfitri": ["2020-05-24", "2020-05-25"], "iduladha": ["2020-07-31"], "cuti_bersama": []},
    2021: {"idulfitri": ["2021-05-13", "2021-05-14"], "iduladha": ["2021-07-20"], "cuti_bersama": ["2021-05-12", "2021-05-17", "2021-05-18", "2021-05-19"]},
    2022: {"idulfitri": ["2022-05-02", "2022-05-03"], "iduladha": ["2022-07-10"], "cuti_bersama": ["2022-04-29", "2022-05-04", "2022-05-05", "2022-05-06"]},
    2023: {"idulfitri": ["2023-04-22", "2023-04-23"], "iduladha": ["2023-06-29"], "cuti_bersama": ["2023-04-19", "2023-04-20", "2023-04-21", "2023-04-24", "2023-04-25"]},
    2024: {"idulfitri": ["2024-04-10", "2024-04-11"], "iduladha": ["2024-06-17"], "cuti_bersama": ["2024-04-08", "2024-04-09", "2024-04-12", "2024-04-15", "2024-06-18"]},
    2025: {"idulfitri": ["2025-03-31", "2025-04-01"], "iduladha": ["2025-06-06"], "cuti_bersama": ["2025-04-02", "2025-04-03", "2025-04-04", "2025-04-07", "2025-06-09"]},
    2026: {"idulfitri": ["2026-03-21", "2026-03-22"], "iduladha": ["2026-05-27"], "cuti_bersama": ["2026-03-20", "2026-03-23", "2026-03-24", "2026-05-28"]},
}


def run():
    raw = pd.read_csv(RAW / "calendar" / "holidays.csv", parse_dates=["date"])
    rows = []
    for year, reference in REFERENCE.items():
        for holiday in ("idulfitri", "iduladha"):
            ours = sorted(raw[(raw["holiday"] == holiday) & (raw["date"].dt.year == year)]["date"].dt.strftime("%Y-%m-%d"))
            expected = reference[holiday]
            rows.append({"tahun": str(year), "perayaan": holiday, "kalender_raw": ", ".join(ours), "sumber_pembanding": ", ".join(expected), "cocok": ours == expected})
        for fixed, month_day in (("tahun_baru", "01-01"), ("natal", "12-25")):
            ours = sorted(raw[(raw["holiday"] == fixed) & (raw["date"].dt.year == year)]["date"].dt.strftime("%Y-%m-%d"))
            rows.append({"tahun": str(year), "perayaan": fixed, "kalender_raw": ", ".join(ours), "sumber_pembanding": f"{year}-{month_day}", "cocok": ours == [f"{year}-{month_day}"]})
    result = pd.DataFrame(rows)
    weekend = raw[raw["date"].dt.dayofweek >= 5]
    cuti = pd.DataFrame([{"tahun": str(y), "cuti_bersama_idulfitri_iduladha": len(r["cuti_bersama"])} for y, r in REFERENCE.items()])

    lines = ["# Audit kalender hari besar (spot-check 2018-2026)", "",
             "Pembanding: timeanddate.com untuk 2018-2025 dan SKB 3 Menteri 2026 (setneg.go.id), dicek 19 Nov 2026. timeanddate adalah sumber sekunder; dokumen SKB 2018-2025 belum dibuka satu per satu.", "",
             f"- Idulfitri dan Iduladha 2018-2026 (perbandingan sebenarnya): {int(result[result['perayaan'].isin(['idulfitri', 'iduladha'])]['cocok'].sum())} dari {int(result['perayaan'].isin(['idulfitri', 'iduladha']).sum())} cocok. "
        "Tahun Baru dan Natal tanggalnya tetap (1 Januari, 25 Desember) sehingga barisnya hanya pemeriksaan format.",
             f"- Libur nasional yang jatuh di Sabtu atau Minggu (tidak memengaruhi hari kerja PIHPS): {len(weekend)} dari {len(raw)} hari.", "",
             "## 1. Hasil perbandingan", "", to_markdown(result), "",
             "## 2. Cuti bersama (tidak masuk kalender raw, D-21)", "",
             "Jumlah cuti bersama Idulfitri dan Iduladha per tahun menurut sumber pembanding. Karena banyak (3-7 hari per tahun), `n_holiday_days` di bulan Idulfitri akan lebih rendah daripada hari libur yang dirasakan. "
             "Sumber pembanding sudah memuat tanggalnya, jadi cuti bersama bisa ditambahkan sebagai kolom terpisah kalau Fatan mau.", "", to_markdown(cuti), ""]
    write_report("calendar_audit.md", "\n".join(lines))
