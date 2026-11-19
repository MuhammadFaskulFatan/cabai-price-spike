# Audit kalender hari besar

Pembanding libur nasional: timeanddate.com (sumber sekunder) untuk 2018-2025 dan SKB 2026 di setneg.go.id. Sebagian tanggal juga terlihat di halaman situs pemerintah (menpan.go.id, kemenag.go.id, kemnaker.go.id). Dokumen SKB asli 2018-2025 (PDF) tidak dibuka; verifikasi dibatasi sekitar 10 menit sesuai instruksi (D-38). Dicek 19 Nov 2026.

- Libur Idulfitri dan Iduladha 2018-2026: 18 dari 18 baris cocok dengan pembanding; 10 baris terkonfirmasi situs pemerintah, 8 baris hanya sekunder (timeanddate).
- Libur nasional yang jatuh di Sabtu atau Minggu (tidak memengaruhi hari kerja PIHPS): 12 dari 45 hari.
- Tahun Baru (1 Januari) dan Natal (25 Desember) berupa tanggal tetap sehingga tidak diperbandingkan.
- Catatan sumber: timeanddate.com ternyata memuat daftar cuti bersama 2021 dan 2023 yang belum mengikuti revisi SKB (Idulfitri 2021 dipangkas menjadi 12 Mei saja; Iduladha 2023 mendapat cuti 28 dan 30 Juni). Untuk cuti bersama, halaman pemerintah didahulukan.

## 1. Libur nasional Idulfitri dan Iduladha

| tahun | perayaan | kalender_raw | pembanding | cocok | verifikasi |
| --- | --- | --- | --- | --- | --- |
| 2018 | idulfitri | 2018-06-15, 2018-06-16 | 2018-06-15, 2018-06-16 | True | sekunder (timeanddate) |
| 2018 | iduladha | 2018-08-22 | 2018-08-22 | True | sekunder (timeanddate) |
| 2019 | idulfitri | 2019-06-05, 2019-06-06 | 2019-06-05, 2019-06-06 | True | resmi (situs pemerintah) |
| 2019 | iduladha | 2019-08-11 | 2019-08-11 | True | sekunder (timeanddate) |
| 2020 | idulfitri | 2020-05-24, 2020-05-25 | 2020-05-24, 2020-05-25 | True | sekunder (timeanddate) |
| 2020 | iduladha | 2020-07-31 | 2020-07-31 | True | sekunder (timeanddate) |
| 2021 | idulfitri | 2021-05-13, 2021-05-14 | 2021-05-13, 2021-05-14 | True | resmi (situs pemerintah) |
| 2021 | iduladha | 2021-07-20 | 2021-07-20 | True | sekunder (timeanddate) |
| 2022 | idulfitri | 2022-05-02, 2022-05-03 | 2022-05-02, 2022-05-03 | True | resmi (situs pemerintah) |
| 2022 | iduladha | 2022-07-10 | 2022-07-10 | True | resmi (situs pemerintah) |
| 2023 | idulfitri | 2023-04-22, 2023-04-23 | 2023-04-22, 2023-04-23 | True | resmi (situs pemerintah) |
| 2023 | iduladha | 2023-06-29 | 2023-06-29 | True | resmi (situs pemerintah) |
| 2024 | idulfitri | 2024-04-10, 2024-04-11 | 2024-04-10, 2024-04-11 | True | resmi (situs pemerintah) |
| 2024 | iduladha | 2024-06-17 | 2024-06-17 | True | resmi (situs pemerintah) |
| 2025 | idulfitri | 2025-03-31, 2025-04-01 | 2025-03-31, 2025-04-01 | True | sekunder (timeanddate) |
| 2025 | iduladha | 2025-06-06 | 2025-06-06 | True | sekunder (timeanddate) |
| 2026 | idulfitri | 2026-03-21, 2026-03-22 | 2026-03-21, 2026-03-22 | True | resmi (situs pemerintah) |
| 2026 | iduladha | 2026-05-27 | 2026-05-27 | True | resmi (situs pemerintah) |

## 2. Cuti bersama (`data/raw/calendar/cuti_bersama.csv`, kolom `is_cuti_bersama`)

40 hari: 35 terlihat di halaman pemerintah, 5 hanya dari timeanddate.com. Dikosongkan karena belum terverifikasi: seluruh cuti bersama 2020 (direvisi beberapa kali), cuti Natal 2018, 2019, dan 2022; cuti Natal 2021 dihapus di revisi Juni 2021.

| tahun | holiday | verification | hari | tanggal |
| --- | --- | --- | --- | --- |
| 2018 | idulfitri | official | 7 | 06-11, 06-12, 06-13, 06-14, 06-18, 06-19, 06-20 |
| 2019 | idulfitri | official | 3 | 06-03, 06-04, 06-07 |
| 2021 | idulfitri | official | 1 | 05-12 |
| 2022 | idulfitri | official | 4 | 04-29, 05-04, 05-05, 05-06 |
| 2023 | iduladha | official | 2 | 06-28, 06-30 |
| 2023 | idulfitri | official | 5 | 04-19, 04-20, 04-21, 04-24, 04-25 |
| 2023 | natal | official | 1 | 12-26 |
| 2024 | iduladha | official | 1 | 06-18 |
| 2024 | idulfitri | official | 4 | 04-08, 04-09, 04-12, 04-15 |
| 2024 | natal | official | 1 | 12-26 |
| 2025 | iduladha | secondary | 1 | 06-09 |
| 2025 | idulfitri | secondary | 4 | 04-02, 04-03, 04-04, 04-07 |
| 2025 | natal | official | 1 | 12-26 |
| 2026 | iduladha | official | 1 | 05-28 |
| 2026 | idulfitri | official | 3 | 03-20, 03-23, 03-24 |
| 2026 | natal | official | 1 | 12-24 |
