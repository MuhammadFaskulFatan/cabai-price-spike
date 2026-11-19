# Hold-out validation: disagregasi produksi bulanan (D-26)

Kebenaran: realisasi SPH-BPS Januari-Maret dari tabel prognosa Buletin, 2022-2025 (3 bulan x 4 tahun x 2 komoditas = 24 nilai). Januari-Maret 2026 (3 bulan per komoditas) tidak bisa diuji karena benchmark tahunan BDSP 2026 belum ada. Pola musiman tahun uji dilepas dari indikator (leave-one-year-out).

Hasil di tingkat nasional (MAPE, persen):

| commodity_group | denton | flat | profile |
| --- | --- | --- | --- |
| cabai_merah | 15.54 | 10.81 | 14.92 |
| cabai_rawit | 17.76 | 17.26 | 17.55 |

Gabungan dua komoditas:

| method | mape | n |
| --- | --- | --- |
| denton | 16.65 | 24 |
| flat | 14.04 | 24 |
| profile | 16.23 | 24 |

Per tahun uji (MAPE, persen):

| commodity_group | year | denton | flat | profile |
| --- | --- | --- | --- | --- |
| cabai_merah | 2022 | 11.37 | 10.64 | 16.19 |
| cabai_merah | 2023 | 19.16 | 16.73 | 17.62 |
| cabai_merah | 2024 | 17.65 | 8.14 | 13.10 |
| cabai_merah | 2025 | 13.99 | 7.73 | 12.76 |
| cabai_rawit | 2022 | 15.16 | 13.15 | 15.19 |
| cabai_rawit | 2023 | 12.40 | 8.00 | 13.25 |
| cabai_rawit | 2024 | 28.09 | 33.57 | 29.52 |
| cabai_rawit | 2025 | 15.37 | 14.33 | 12.23 |

Catatan: realisasi Januari-Maret berasal dari edisi yang sama dengan pola musiman yang dilepas, tetapi pola tahun uji tidak dipakai saat menebak. Keterbatasan: hanya 3 bulan pertama tiap tahun yang bisa diuji, jadi akurasi untuk bulan lain (misalnya Juli-Desember, yang di tabel prognosa sendiri berasal dari rata-rata tahun sebelumnya) tidak teruji.
