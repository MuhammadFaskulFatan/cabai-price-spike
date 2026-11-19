# Laporan Fase 4 (Transform)

Sumber angka: `data/interim/` dan `data/final/`. Aturan dan ambang ada di `pipeline/rules.py` (D-35).

## 1. Seri per tier (tipe harga x komoditas)

Satu seri = satu provinsi (atau baris nasional). Tier dihitung pada Jan 2019 - Okt 2026.

| price_type | commodity | main | descriptive | excluded |
| --- | --- | --- | --- | --- |
| eceran | cabai_merah | 35 | 0 | 0 |
| eceran | cabai_rawit | 35 | 0 | 0 |
| eceran | merah_besar | 28 | 0 | 7 |
| eceran | merah_keriting | 35 | 0 | 0 |
| eceran | rawit_hijau | 32 | 1 | 2 |
| eceran | rawit_merah | 32 | 0 | 3 |
| pedagang_besar | cabai_merah | 35 | 0 | 0 |
| pedagang_besar | cabai_rawit | 34 | 1 | 0 |
| pedagang_besar | merah_besar | 28 | 1 | 6 |
| pedagang_besar | merah_keriting | 35 | 0 | 0 |
| pedagang_besar | rawit_hijau | 30 | 3 | 2 |
| pedagang_besar | rawit_merah | 30 | 2 | 3 |
| produsen | cabai_merah | 33 | 1 | 1 |
| produsen | cabai_rawit | 31 | 2 | 2 |
| produsen | merah_besar | 23 | 2 | 10 |
| produsen | merah_keriting | 30 | 2 | 3 |
| produsen | rawit_hijau | 23 | 2 | 10 |
| produsen | rawit_merah | 28 | 2 | 5 |

## 2. Nilai yang di-impute

| price_type | commodity | linear_log | kalman | total_imputed |
| --- | --- | --- | --- | --- |
| eceran | merah_besar | 5 | 5 | 10 |
| pedagang_besar | cabai_merah | 1 | 0 | 1 |
| pedagang_besar | cabai_rawit | 3 | 0 | 3 |
| pedagang_besar | merah_besar | 5 | 11 | 16 |
| pedagang_besar | merah_keriting | 1 | 0 | 1 |
| pedagang_besar | rawit_hijau | 5 | 10 | 15 |
| pedagang_besar | rawit_merah | 3 | 5 | 8 |
| produsen | cabai_merah | 45 | 6 | 51 |
| produsen | cabai_rawit | 55 | 3 | 58 |
| produsen | merah_besar | 37 | 16 | 53 |
| produsen | merah_keriting | 45 | 11 | 56 |
| produsen | rawit_hijau | 32 | 25 | 57 |
| produsen | rawit_merah | 52 | 10 | 62 |

Total 391 nilai dari 60,089 bulan berharga. Gap > 6 bulan, gap awal/akhir, dan seri excluded tidak diisi.

## 3. Sel harga kosong di core_province_month (periode model Jan 2019 - Okt 2026)

| variabel | sel_kosong | tier_excluded | tier_descriptive_atau_main | dari_itu_di_NTT |
| --- | --- | --- | --- | --- |
| price_retail | 0 | 0 | 0 | 0 |
| price_wholesale | 7 | 0 | 7 | 0 |
| price_producer | 368 | 282 | 86 | 68 |

`tier_excluded`: seri di bawah 50% bulan valid (tidak di-impute). Sisanya adalah gap awal atau akhir seri dan gap tengah lebih dari 6 bulan pada seri main atau descriptive.

## 4. Produksi

- `fact_production_annual`: 816 baris (34 provinsi x 8 tahun x 3 grup). `is_preliminary` = 2025; `is_outlier` = 21 baris; `suspect_copy` = 8 baris (cabai_keriting).
- `fact_production_monthly` (Denton, deskriptif): 6,528 nilai estimasi, seluruhnya `is_imputed = TRUE`, `impute_method = denton`; 2026 NULL (tanpa ekstrapolasi). Total 12 bulan sama dengan angka tahunan BDSP (selisih maksimum 1.2e-10 ton).
- Seri provinsi x grup yang hasil Denton tanpa batas bawah sempat negatif lalu diselesaikan dengan batas x >= 0: 2.

Hold-out MAPE Denton (rincian di `pipeline/validate/reports/holdout_production.md`):

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

## 5. Core dataset

- `core_province_month.csv`: 7,276 baris x 34 kolom; key (provinsi, bulan, grup) unik: True.
- `core_province_year.csv`: 544 baris x 13 kolom; produksi dan luas panen 2018-2025, 2026 tidak ada.
- Pasangan flag konsisten (is_imputed TRUE hanya jika impute_method terisi): True.
- Kolom cuaca belum ada; menyusul setelah data Open-Meteo lengkap.
