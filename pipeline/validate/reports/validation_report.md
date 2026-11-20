# Laporan Fase 5 (Validate)

Core dataset termasuk cuaca (`data/final/`). Cek struktur: 55 dari 55 lulus. Reconciliation tahunan: cocok. Cross-check PIHPS bulanan: 21,186 sel dibandingkan. Spot-check: harga 30/30 cocok dengan raw, 10/10 cocok dengan PIHPS live; produksi 10/10 cocok dengan BDSP live; ONI 5/5; cuaca 8/8.

## 1. Cek struktur dan aturan core dataset

| cek | lulus | rincian |
| --- | --- | --- |
| core_province_month: key unik | True | 7,276 baris |
| core_province_month: lengkap 34 provinsi x 107 bulan x 2 grup | True | 34 provinsi, 107 bulan |
| core_province_month: rentang Jan 2018 - Nov 2026 | True | 2018-01-01 s/d 2026-11-01 |
| price_retail: semua harga positif dan < Rp500.000/kg | True | min 12,721, max 173,661 |
| price_wholesale: semua harga positif dan < Rp500.000/kg | True | min 6,320, max 153,198 |
| price_producer: semua harga positif dan < Rp500.000/kg | True | min 3,000, max 153,350 |
| price_retail: is_imputed TRUE tepat ketika impute_method terisi | True | 0 nilai imputed |
| price_retail: impute_method hanya linear_log (D-43) | True | [] |
| price_retail: tidak ada imputation di seri excluded | True |  |
| price_retail: tidak ada imputation di luar periode model (2018 boleh, Nov 2026 tidak) | True |  |
| price_retail: nilai imputed tidak pernah kosong | True |  |
| price_retail: tidak ada rangkaian imputed lebih dari 6 bulan | True | 0 rangkaian |
| price_retail: tidak ada imputation di awal atau akhir seri | True | 0 seri |
| price_retail: setiap sel kosong di periode model punya alasan | True | tidak ada sel kosong |
| price_wholesale: is_imputed TRUE tepat ketika impute_method terisi | True | 4 nilai imputed |
| price_wholesale: impute_method hanya linear_log (D-43) | True | ['linear_log'] |
| price_wholesale: tidak ada imputation di seri excluded | True |  |
| price_wholesale: tidak ada imputation di luar periode model (2018 boleh, Nov 2026 tidak) | True |  |
| price_wholesale: nilai imputed tidak pernah kosong | True |  |
| price_wholesale: tidak ada rangkaian imputed lebih dari 6 bulan | True | 0 rangkaian |
| price_wholesale: tidak ada imputation di awal atau akhir seri | True | 0 seri |
| price_wholesale: setiap sel kosong di periode model punya alasan | True | gap_tengah_lebih_6_bulan 7 |
| price_producer: is_imputed TRUE tepat ketika impute_method terisi | True | 109 nilai imputed |
| price_producer: impute_method hanya linear_log (D-43) | True | ['linear_log'] |
| price_producer: tidak ada imputation di seri excluded | True |  |
| price_producer: tidak ada imputation di luar periode model (2018 boleh, Nov 2026 tidak) | True |  |
| price_producer: nilai imputed tidak pernah kosong | True |  |
| price_producer: tidak ada rangkaian imputed lebih dari 6 bulan | True | 0 rangkaian |
| price_producer: tidak ada imputation di awal atau akhir seri | True | 0 seri |
| price_producer: setiap sel kosong di periode model punya alasan | True | gap_akhir_seri 68; gap_awal_seri 9; gap_tengah_lebih_6_bulan 9; tier_excluded 282 |
| NTT harga produsen sejak 2024 tetap kosong (tanpa ekstrapolasi) dan ditandai keluar analisis | True | 0 sel terisi |
| production_annual_ton sama untuk 12 bulan dalam tahunnya | True |  |
| production_annual_ton kosong untuk 2026 dan terisi untuk 2018-2025 | True |  |
| production_annual_preliminary hanya 2025 | True |  |
| tidak ada kolom produksi bulanan Denton | True |  |
| ONI kosong hanya Okt-Nov 2026 | True | 2026-10-01, 2026-11-01 |
| enso_phase konsisten dengan ambang +-0,5 | True |  |
| months_to_idulfitri = 0 tepat di bulan 1 Syawal | True | 9 bulan |
| n_holiday_days = jumlah libur nasional di dim_holiday | True | 44 hari |
| dim_holiday: source_level hanya official/secondary | True | {'official': 69, 'secondary': 16} |
| periode model = Jan 2019 - Okt 2026 | True |  |
| weather_status hanya observed / not_applicable / partial_month | True | {'not_applicable': 4173, 'observed': 3074, 'partial_month': 29} |
| cuaca observed tepat di provinsi x komoditas bertitik sentra (kecuali Nov 2026) | True | 29 provinsi x komoditas bertitik |
| not_applicable dan partial_month: semua nilai cuaca kosong | True |  |
| observed: tidak ada nilai cuaca kosong | True | 3074 baris |
| partial_month hanya November 2026 | True |  |
| hujan >= 0 dan kelembapan 0-100 | True | hujan maks 2,228 mm/bulan |
| rain_anomaly (rata-rata berbobot z per lokasi, D-58): rata-rata 0 per bulan kalender di 1991-2020 | True | 348 seri x bulan kalender |
| z per lokasi (akar hujan): SD 1 per lokasi x bulan kalender di 1991-2020 | True | 888 lokasi x bulan kalender |
| rain_is_extreme = TRUE tepat di bulan yang memuat lokasi tertandai audit | True | 118 bulan provinsi x komoditas |
| core_province_year: key unik dan lengkap 34 x 8 tahun x 2 grup | True | 544 baris |
| core_province_year: producer_price_n_months di 0-12 | True |  |
| core_province_year: is_preliminary hanya 2025 | True |  |
| core_province_year: is_outlier sesuai aturan 1-30 ton/ha | True | 16 baris outlier |
| production_annual_ton di core bulanan = production_ton di core tahunan | True | 544 provinsi-tahun |

Dua cek sempat gagal pada versi pertama karena cara mengeceknya, bukan datanya: (1) imputation di awal 2019 dibaca sebagai gap awal seri karena cek hanya melihat periode model, padahal gap itu dijembatani observasi 2018 (cek kini memakai jendela imputation Jan 2018 - Okt 2026); (2) hitung ulang `n_holiday_days` ikut memasukkan Natal Desember 2026 yang berada di luar `dim_month`.

## 2. Reconciliation total tahunan (BDSP)

- Baris TOTAL nasional BDSP vs jumlah 34 provinsi di core, 48 kombinasi komoditas x indikator x tahun: selisih maksimum 0.04 ton/ha (BDSP membulatkan tiap baris provinsi ke 2 desimal; batas wajar 0,19). Lulus: True.
- core_province_year vs fact_production_annual: selisih maksimum 9.1e-13 pada 544 baris.
- Papua dan Papua Barat = jumlah induk + pemekaran BDSP: lulus True.

Informasi (bukan reconciliation): porsi realisasi Januari-Maret Buletin terhadap total tahunan BDSP.

| commodity_group | year | realisasi_jan_mar_ton | bdsp_tahunan | porsi_jan_mar_pct |
| --- | --- | --- | --- | --- |
| cabai_merah | 2022 | 337,291.0 | 1,475,821.3 | 22.9 |
| cabai_merah | 2023 | 347,244.0 | 1,554,498.4 | 22.3 |
| cabai_merah | 2024 | 339,730.0 | 1,469,325.1 | 23.1 |
| cabai_merah | 2025 | 400,105.0 | 1,715,029.2 | 23.3 |
| cabai_merah | 2026 | 388,473.0 |  |  |
| cabai_rawit | 2022 | 350,934.0 | 1,544,440.9 | 22.7 |
| cabai_rawit | 2023 | 365,077.0 | 1,506,762.1 | 24.2 |
| cabai_rawit | 2024 | 296,049.0 | 1,568,757.0 | 18.9 |
| cabai_rawit | 2025 | 408,094.0 | 1,743,125.4 | 23.4 |
| cabai_rawit | 2026 | 372,431.0 |  |  |

Porsi 19-24% untuk tiga bulan pertama masuk akal (sedikit di bawah 25%); rawit 2024 paling rendah (18,9%).

## 3. Cross-check harga bulanan vs angka bulanan PIHPS (D-18)

Rata-rata dari hari terisi (sebelum imputation) vs `tipe_laporan=3`, cabai_merah dan cabai_rawit, 34 provinsi + nasional, Jan 2018 - Okt 2026. Selisih dalam persen:

| tipe_harga | n | median | p95 | maks | dalam_1pct | dalam_5pct |
| --- | --- | --- | --- | --- | --- | --- |
| eceran | 7420 | 0.03 | 0.07 | 4.17 | 99.54 | 100.00 |
| pedagang_besar | 7409 | 0.21 | 1.45 | 5.74 | 88.61 | 99.99 |
| produsen | 6357 | 0.16 | 1.54 | 8.58 | 88.53 | 99.87 |

- Sel yang hanya terisi di PIHPS bulanan: 157 (bulan kita kosong karena hanya 1-9 hari kerja terisi, di bawah aturan minimal 10 hari). Sel yang hanya terisi di data kita: 0.
- Eceran praktis identik. Pedagang besar dan produsen sedikit berbeda (88-89% dalam 1%, hampir semua dalam 5%), kemungkinan karena PIHPS menghitung angka bulanan dengan cara lain (misalnya rata-rata pasar atau minggu, bukan rata-rata hari). Angka PIHPS bulanan tetap hanya pembanding.

Sepuluh selisih terbesar:

| tipe_harga | komoditas | province_id | month | n_days_observed | price_observed | price_pihps | selisih_pct |
| --- | --- | --- | --- | --- | --- | --- | --- |
| produsen | cabai_rawit | 26 | 2021-12 | 23 | 21,228.3 | 19,550.0 | 8.6 |
| produsen | cabai_rawit | 19 | 2021-01 | 21 | 13,733.3 | 12,900.0 | 6.5 |
| produsen | cabai_merah | 25 | 2024-08 | 22 | 17,954.5 | 19,150.0 | 6.2 |
| pedagang_besar | cabai_merah | 20 | 2026-03 | 22 | 53,636.4 | 56,900.0 | 5.7 |
| produsen | cabai_merah | 31 | 2025-01 | 23 | 18,219.6 | 19,250.0 | 5.4 |
| produsen | cabai_rawit | 29 | 2021-12 | 23 | 33,913.0 | 32,200.0 | 5.3 |
| produsen | cabai_merah | 33 | 2019-11 | 21 | 18,059.5 | 17,150.0 | 5.3 |
| produsen | cabai_rawit | 21 | 2024-02 | 21 | 14,659.5 | 15,450.0 | 5.1 |
| produsen | cabai_rawit | 20 | 2021-12 | 23 | 44,673.9 | 42,500.0 | 5.1 |
| produsen | cabai_merah | 15 | 2020-10 | 22 | 14,725.0 | 15,500.0 | 5.0 |

### Sel kosong karena kurang dari 10 hari kerja: bulan Idulfitri vs bulan lain

Sel yang terisi di PIHPS bulanan tetapi kosong di data kita, dibagi menurut bulan 1 Syawal, bulan sesudahnya, dan bulan lain. Periode 2019-2026 dipisah karena sebagian besar sel kosong 2018 berasal dari masa awal seri harga produsen (Juli-September 2018).

Periode 2018-2026:

| tipe_harga | kategori | sel | kosong | pct_kosong |
| --- | --- | --- | --- | --- |
| eceran | bulan_idulfitri | 630 | 0 | 0.00 |
| eceran | bulan_lain | 6160 | 0 | 0.00 |
| eceran | bulan_sesudah | 630 | 0 | 0.00 |
| pedagang_besar | bulan_idulfitri | 630 | 2 | 0.32 |
| pedagang_besar | bulan_lain | 6152 | 1 | 0.02 |
| pedagang_besar | bulan_sesudah | 630 | 0 | 0.00 |
| produsen | bulan_idulfitri | 533 | 9 | 1.69 |
| produsen | bulan_lain | 5436 | 126 | 2.32 |
| produsen | bulan_sesudah | 542 | 19 | 3.51 |

Periode 2019-2026:

| tipe_harga | kategori | sel | kosong | pct_kosong |
| --- | --- | --- | --- | --- |
| eceran | bulan_idulfitri | 560 | 0 | 0.00 |
| eceran | bulan_lain | 5460 | 0 | 0.00 |
| eceran | bulan_sesudah | 560 | 0 | 0.00 |
| pedagang_besar | bulan_idulfitri | 560 | 0 | 0.00 |
| pedagang_besar | bulan_lain | 5452 | 1 | 0.02 |
| pedagang_besar | bulan_sesudah | 560 | 0 | 0.00 |
| produsen | bulan_idulfitri | 527 | 9 | 1.71 |
| produsen | bulan_lain | 5141 | 72 | 1.40 |
| produsen | bulan_sesudah | 526 | 9 | 1.71 |

Kesimpulan: sel kosong hampir seluruhnya di harga produsen, dan proporsinya di bulan Idulfitri tidak jauh lebih tinggi daripada bulan lain (2019-2026: 1,71% di bulan Idulfitri dan bulan sesudahnya vs 1,40% di bulan lain, masing-masing 9 sel). Tidak dicatat sebagai risiko H6; hasil ini cukup didokumentasikan di sini.

## 4. Spot-check terhadap sumber (seed 2026)

Harga: 30 sel observed acak dihitung ulang dari file raw harian dengan kode terpisah; 10 pertama juga ditarik ulang dari PIHPS live pada 19 Nov 2026.

| variabel | grup | province_id | bulan | core | raw | hari_raw | live | hari_live | raw_cocok | live_selisih_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| price_retail | cabai_rawit | 2 | 2024-03 | 59,278.57 | 59,278.57 | 21 | 59,278.57 | 21.00 | True | 0.00 |
| price_wholesale | cabai_rawit | 22 | 2023-01 | 37,613.64 | 37,613.64 | 22 | 37,613.64 | 22.00 | True | 0.00 |
| price_wholesale | cabai_rawit | 8 | 2026-04 | 57,045.45 | 57,045.45 | 22 | 57,045.45 | 22.00 | True | 0.00 |
| price_retail | cabai_rawit | 21 | 2026-01 | 42,247.73 | 42,247.73 | 22 | 42,247.73 | 22.00 | True | 0.00 |
| price_wholesale | cabai_merah | 34 | 2026-03 | 51,661.36 | 51,661.36 | 22 | 51,661.36 | 22.00 | True | 0.00 |
| price_retail | cabai_rawit | 33 | 2022-03 | 100,909.09 | 100,909.09 | 22 | 100,909.09 | 22.00 | True | 0.00 |
| price_retail | cabai_rawit | 24 | 2026-10 | 123,545.45 | 123,545.45 | 22 | 123,545.45 | 22.00 | True | 0.00 |
| price_wholesale | cabai_rawit | 33 | 2019-02 | 46,250.00 | 46,250.00 | 20 | 46,250.00 | 20.00 | True | 0.00 |
| price_retail | cabai_rawit | 7 | 2020-09 | 22,859.09 | 22,859.09 | 22 | 22,859.09 | 22.00 | True | 0.00 |
| price_wholesale | cabai_merah | 18 | 2019-07 | 41,608.70 | 41,608.70 | 23 | 41,608.70 | 23.00 | True | 0.00 |
| price_producer | cabai_merah | 7 | 2021-09 | 12,964.29 | 12,964.29 | 21 |  |  | True |  |
| price_producer | cabai_merah | 1 | 2022-02 | 9,681.58 | 9,681.58 | 19 |  |  | True |  |
| price_retail | cabai_rawit | 27 | 2019-04 | 42,450.00 | 42,450.00 | 19 |  |  | True |  |
| price_producer | cabai_merah | 33 | 2023-11 | 39,654.55 | 39,654.55 | 22 |  |  | True |  |
| price_wholesale | cabai_rawit | 7 | 2022-12 | 38,838.64 | 38,838.64 | 22 |  |  | True |  |
| price_producer | cabai_merah | 27 | 2025-11 | 29,700.00 | 29,700.00 | 20 |  |  | True |  |
| price_retail | cabai_rawit | 8 | 2021-07 | 50,552.38 | 50,552.38 | 21 |  |  | True |  |
| price_producer | cabai_rawit | 15 | 2019-08 | 49,854.55 | 49,854.55 | 22 |  |  | True |  |
| price_retail | cabai_merah | 22 | 2020-12 | 71,689.47 | 71,689.47 | 19 |  |  | True |  |
| price_retail | cabai_merah | 13 | 2021-02 | 65,900.00 | 65,900.00 | 19 |  |  | True |  |
| price_retail | cabai_merah | 7 | 2019-11 | 38,654.76 | 38,654.76 | 21 |  |  | True |  |
| price_retail | cabai_merah | 25 | 2022-09 | 50,193.18 | 50,193.18 | 22 |  |  | True |  |
| price_wholesale | cabai_rawit | 1 | 2020-02 | 32,222.50 | 32,222.50 | 20 |  |  | True |  |
| price_producer | cabai_merah | 31 | 2023-05 | 26,141.30 | 26,141.30 | 23 |  |  | True |  |
| price_producer | cabai_merah | 3 | 2019-04 | 16,459.09 | 16,459.09 | 22 |  |  | True |  |
| price_retail | cabai_rawit | 31 | 2024-02 | 55,723.68 | 55,723.68 | 19 |  |  | True |  |
| price_producer | cabai_merah | 9 | 2025-07 | 30,154.35 | 30,154.35 | 23 |  |  | True |  |
| price_wholesale | cabai_rawit | 9 | 2019-07 | 48,413.04 | 48,413.04 | 23 |  |  | True |  |
| price_retail | cabai_merah | 20 | 2023-01 | 53,920.45 | 53,920.45 | 22 |  |  | True |  |
| price_retail | cabai_rawit | 10 | 2023-08 | 36,760.87 | 36,760.87 | 23 |  |  | True |  |

Produksi: 10 provinsi-tahun acak vs HTML raw BDSP dan tabel BDSP yang ditarik ulang live.

| grup | province_id | tahun | core | raw | live | raw_cocok | live_cocok |
| --- | --- | --- | --- | --- | --- | --- | --- |
| cabai_merah | 18 | 2020 | 20,092.39 | 20,092.39 | 20,092.39 | True | True |
| cabai_merah | 21 | 2021 | 8,976.63 | 8,976.63 | 8,976.63 | True | True |
| cabai_merah | 9 | 2024 | 7,774.53 | 7,774.53 | 7,774.53 | True | True |
| cabai_merah | 6 | 2018 | 38,002.50 | 38,002.50 | 38,002.50 | True | True |
| cabai_merah | 21 | 2019 | 11,392.00 | 11,392.00 | 11,392.00 | True | True |
| cabai_rawit | 29 | 2022 | 19,006.22 | 19,006.22 | 19,006.22 | True | True |
| cabai_rawit | 19 | 2020 | 10,467.90 | 10,467.90 | 10,467.90 | True | True |
| cabai_rawit | 28 | 2021 | 22,198.53 | 22,198.53 | 22,198.53 | True | True |
| cabai_rawit | 5 | 2018 | 1,715.70 | 1,715.70 | 1,715.70 | True | True |
| cabai_rawit | 12 | 2024 | 163,755.89 | 163,755.89 | 163,755.89 | True | True |

ONI: 5 bulan acak vs file NOAA live.

| bulan | core | live | cocok |
| --- | --- | --- | --- |
| 2022-12 | -0.70 | -0.70 | True |
| 2018-05 | -0.07 | -0.07 | True |
| 2019-07 | 0.38 | 0.38 | True |
| 2023-06 | 0.73 | 0.73 | True |
| 2018-09 | 0.52 | 0.52 | True |

Cuaca: 5 sel acak dihitung ulang dari file raw harian (rata-rata berbobot produksi), dan 3 lokasi x 1 bulan acak ditarik ulang dari Open-Meteo live (untuk baris live, `core_mm` = jumlah hujan dari file raw lokasi itu).

| jenis | province_id | grup | bulan | core_mm | pembanding_mm | cocok |
| --- | --- | --- | --- | --- | --- | --- |
| raw | 14 | cabai_rawit | 2019-06 | 17.96 | 17.96 | True |
| raw | 16 | cabai_rawit | 2019-04 | 239.41 | 239.41 | True |
| raw | 18 | cabai_rawit | 2025-12 | 214.41 | 214.41 | True |
| raw | 6 | cabai_merah | 2024-04 | 431.70 | 431.70 | True |
| raw | 2 | cabai_rawit | 2019-09 | 207.02 | 207.02 | True |
| live | 2 | Kab. Humbang Hasundutan | 2025-09 | 222.10 | 222.10 | True |
| live | 3 | Kab. Solok | 2020-05 | 356.00 | 356.00 | True |
| live | 10 | Kab. Lampung Selatan | 2019-03 | 328.20 | 328.20 | True |

Tidak ada revisi sumber yang terdeteksi pada sampel live.

## 5. Hold-out validation imputation (D-09, D-43)

Success criterion: metode imputasi dipilih lewat hold-out; jika tidak lebih akurat dari baseline linear, baseline yang dipakai. Kandidat `kalman` tidak lebih akurat di bucket mana pun, jadi semua gap 1-6 bulan memakai `linear_log` (D-43).

| bucket | mape_linear_pct | mape_kalman_pct | mape_locf_pct | kalman_lebih_akurat | metode_dipakai |
| --- | --- | --- | --- | --- | --- |
| 1-2 bulan | 17.01 | 17.20 | 24.47 | False | linear_log |
| 3-6 bulan | 24.55 | 24.80 | 32.25 | False | linear_log |
| 1-6 bulan | 23.47 | 23.71 | 31.14 | False | linear_log |

Hold-out produksi bulanan (Denton) terdokumentasi di `holdout_production.md`; metode itu dibatalkan (D-42).

## 6. Belum tercakup

- Cuaca hanya untuk 18 provinsi bertitik sentra (14 untuk cabai merah, 15 untuk cabai rawit); provinsi lain `not_applicable` (D-25). Data reanalysis Open-Meteo belum dibandingkan dengan pengamatan stasiun BMKG.
- Cross-check mingguan PIHPS tidak dilakukan; data mingguan tidak di-impute dan hanya dipakai untuk lead-lag (D-12).
- Spot-check live hanya sampel (10 harga, 2 tabel BDSP, 1 file ONI, 3 lokasi cuaca); revisi PIHPS di luar sampel tidak terdeteksi. Tanggal extraction tersimpan di metadata raw (D-14).
