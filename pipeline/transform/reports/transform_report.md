# Laporan Fase 4 (Transform)

Sumber angka: `data/interim/` dan `data/final/`. Aturan dan ambang ada di `pipeline/rules.py` (D-35, D-43).

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

### Hold-out validation metode imputation (D-09, D-43)

Success criterion: metode imputasi dipilih lewat hold-out; jika tidak lebih akurat dari baseline linear, baseline yang dipakai. Kandidat `kalman` tidak lebih akurat di bucket mana pun, jadi semua gap 1-6 bulan memakai `linear_log` (D-43).

| bucket | mape_linear_pct | mape_kalman_pct | mape_locf_pct | kalman_lebih_akurat | metode_dipakai |
| --- | --- | --- | --- | --- | --- |
| 1-2 bulan | 17.01 | 17.20 | 24.47 | False | linear_log |
| 3-6 bulan | 24.55 | 24.80 | 32.25 | False | linear_log |
| 1-6 bulan | 23.47 | 23.71 | 31.14 | False | linear_log |

Rincian di `pipeline/validate/reports/holdout_imputation.md`.

## 2. Nilai yang di-impute

| price_type | commodity | impute_method | nilai |
| --- | --- | --- | --- |
| eceran | merah_besar | linear_log | 10 |
| pedagang_besar | cabai_merah | linear_log | 1 |
| pedagang_besar | cabai_rawit | linear_log | 3 |
| pedagang_besar | merah_besar | linear_log | 16 |
| pedagang_besar | merah_keriting | linear_log | 1 |
| pedagang_besar | rawit_hijau | linear_log | 15 |
| pedagang_besar | rawit_merah | linear_log | 8 |
| produsen | cabai_merah | linear_log | 51 |
| produsen | cabai_rawit | linear_log | 58 |
| produsen | merah_besar | linear_log | 53 |
| produsen | merah_keriting | linear_log | 56 |
| produsen | rawit_hijau | linear_log | 57 |
| produsen | rawit_merah | linear_log | 62 |

Total 391 nilai dari 60,089 bulan berharga, semuanya linear interpolation pada log price. Gap > 6 bulan, gap awal/akhir, dan seri excluded tidak diisi. Setiap uji H2/H4 wajib punya sensitivity check tanpa bulan imputasi (D-44).

## 3. Sel harga kosong di core_province_month (periode model Jan 2019 - Okt 2026)

| variabel | sel_kosong | tier_excluded | tier_descriptive_atau_main | dari_itu_di_NTT |
| --- | --- | --- | --- | --- |
| price_retail | 0 | 0 | 0 | 0 |
| price_wholesale | 7 | 0 | 7 | 0 |
| price_producer | 368 | 282 | 86 | 68 |

`tier_excluded`: seri di bawah 50% bulan valid (tidak di-impute). Sisanya adalah gap awal atau akhir seri dan gap tengah lebih dari 6 bulan pada seri main atau descriptive.

## 4. Produksi

- `fact_production_annual`: 816 baris (34 provinsi x 8 tahun x 3 grup). `is_preliminary` = 2025; `is_outlier` = 21 baris; `suspect_copy` = 8 baris (cabai_keriting).
- `core_province_month` memakai `production_annual_ton`: angka tahunan BDSP yang sama untuk 12 bulan dalam tahunnya; 2026 NULL. Disagregasi bulanan (Denton) dibatalkan (D-42).

### Dokumentasi: hold-out disagregasi bulanan yang membuat Denton dibatalkan (D-42)

Realisasi SPH-BPS Januari-Maret 2022-2025 (24 nilai), leave-one-year-out. MAPE nasional (persen):

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

Pola musiman dari tabel prognosa Buletin tidak membuat tebakan lebih baik dari flat (tahunan / 12). Rincian di `pipeline/validate/reports/holdout_production.md`.

## 5. Core dataset

- `core_province_month.csv`: 7,276 baris x 43 kolom; key (provinsi, bulan, grup) unik: True.
- `core_province_year.csv`: 544 baris x 13 kolom; produksi dan luas panen 2018-2025, 2026 tidak ada.
- Pasangan flag konsisten (is_imputed TRUE hanya jika impute_method terisi): True.
- Kolom cuaca ikut di core (paket cuaca, D-57); ringkasan di bagian 6.

## 6. Cuaca (D-19, D-24, D-25, D-57, D-58)

- Status di core: {'not_applicable': 4173, 'observed': 3074, 'partial_month': 29}. Provinsi bertitik sentra: cabai merah 14, cabai rawit 15; provinsi lain `not_applicable` (bukan missing, tidak di-impute).
- Per provinsi x komoditas: rata-rata berbobot produksi kabupaten sentra (bobot produksi rata-rata 2019-2025). Bulan dengan hari tidak lengkap di salah satu titik = NULL; tidak ada kasus seperti itu sampai Oktober 2026.
- `rain_anomaly` (D-58) = rata-rata berbobot produksi dari z-score per lokasi: akar kuadrat hujan bulanan terhadap rata-rata dan simpangan baku bulan kalender 1991-2020 di lokasi itu. `rain_anomaly_plain_z` = versi tanpa akar (untuk sensitivity). `rain_anomaly_mm` = hujan provinsi dikurangi normal bulan kalender (mm). November 2026 `partial_month`, nilai NULL.
- `rain_is_extreme` (D-58): 109 bulan observed di periode model memuat lokasi dengan |z| >= 3 atau hujan harian > 300 mm (daftar di audit cuaca). Nilai tidak diubah.
- Periode model (observed, 2,726 sel): hujan median 235 mm/bulan, kelembapan rata-rata 85.9%, `rain_anomaly` rata-rata +0.18 (2019-2026 sedikit lebih basah dari normal 1991-2020).
- Bulan terbasah: 2020-07, province_id 26 (2,228 mm, `rain_anomaly` +3.2), titik sentra: Kab. Enrekang. Nilai tidak diubah. Data Open-Meteo adalah reanalysis model, bukan pengamatan stasiun; besarnya hujan ekstrem di titik pegunungan perlu dibaca hati-hati.
