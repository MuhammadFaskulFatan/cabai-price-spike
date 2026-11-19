# Data Dictionary (Kerangka)

Dokumen ini berisi konvensi dan daftar kolom untuk setiap tabel di [ERD](02_erd_core_dataset.md). Kolom bertanda **TBD** akan dilengkapi setelah fase extract dan audit (misalnya kode wilayah resmi dan satuan asli sumber). Kerangka ini diperbarui di tiap fase; riwayat perubahan ada di `decision_log.md`.

## 1. Konvensi

| Hal | Aturan |
| --- | --- |
| Nama kolom | `snake_case`, huruf kecil, tanpa spasi |
| Tanggal | `month_start` selalu tanggal 1 (`YYYY-MM-01`); `week_start` hari awal minggu menurut PIHPS (dicek di fase extract) |
| Harga | Rupiah per kg, angka numerik. Koma ribuan PIHPS dibuang saat parsing; `-` menjadi `NULL` |
| Produksi | Ton |
| Luas panen | Hektar |
| Curah hujan | Milimeter per bulan (jumlah harian) |
| Kelembapan | Persen, rata-rata harian dalam bulan |
| Missing | `NULL`. Tidak ada kode angka khusus seperti 0 atau -1 |
| Flag imputation | `is_imputed` (boolean) dan `impute_method` (string, `NULL` kalau tidak di-impute) untuk setiap nilai yang diimpute atau diestimasi |
| Nilai `impute_method` | `linear_log`, `kalman`, `chow_lin` |
| Kunci provinsi | `province_id` mengikuti ID PIHPS (`GetRefProvince`); pemetaan ke nama BDSP dibuat di fase extract |
| Provenance | Setiap tabel fakta membawa `source_extract_date` dari metadata raw |

## 2. Dimensi

### `dim_province`

| Kolom | Tipe | Deskripsi | Sumber | Catatan |
| --- | --- | --- | --- | --- |
| `province_id` | int | ID provinsi PIHPS | `GetRefProvince` | PK. DKI Jakarta = 13 |
| `province_name` | string | Nama baku provinsi (34 provinsi) | PIHPS | Nama sumber lain dipetakan di tabel pemetaan; provinsi pemekaran dipetakan ke induknya (D-17) |
| `island_group` | string | Pulau atau kelompok pulau | Disusun sendiri | Untuk ringkasan analisis |
| `in_producer_price_analysis` | bool | `FALSE` kalau dikeluarkan dari analisis harga produsen | Keputusan D-03 | `FALSE` untuk NTT |

### `dim_commodity`

| Kolom | Tipe | Deskripsi | Sumber | Catatan |
| --- | --- | --- | --- | --- |
| `commodity_group` | string | `cabai_merah` atau `cabai_rawit` | Disusun sendiri | PK |
| `commodity_label` | string | Label tampilan | - | - |
| `pihps_category_id` | string | `cat_7` atau `cat_8` | PIHPS | Empat varian (ID `com_<id>`) ditarik ke raw untuk analisis deskriptif, tidak masuk core (D-10) |

### `dim_price_type`

| Kolom | Tipe | Deskripsi | Catatan |
| --- | --- | --- | --- |
| `price_type_id` | int | 1 pasar tradisional, 2 pasar modern, 3 pedagang besar, 4 produsen | PK |
| `level_name` | string | Eceran, pasar modern, pedagang besar, produsen | - |
| `supply_chain_stage` | string | Tahap rantai pasok yang diwakili | Lihat [process map](01_as_is_process_map.md) |
| `in_core` | bool | `TRUE` untuk 1, 3, 4 | D-11 |

### `dim_month`

| Kolom | Tipe | Deskripsi | Catatan |
| --- | --- | --- | --- |
| `month_start` | date | Tanggal 1 tiap bulan, Jan 2018 sampai Nov 2026 | PK |
| `year`, `month` | int | Komponen tanggal | - |
| `in_core_period` | bool | `TRUE` mulai Jan 2019 | 2018 hanya untuk lagged variables |
| `is_partial_month` | bool | `TRUE` untuk bulan yang belum penuh saat extraction | Nov 2026 |
| `in_model_period` | bool | `TRUE` untuk Jan 2019 sampai Okt 2026 | Model dan uji hipotesis hanya memakai bulan ini (D-16). Nov 2026 hanya deskriptif |
| `n_weekdays` | int | Jumlah hari Senin-Jumat | Dasar aturan minimal 10 hari kerja. Survei pasar tradisional PIHPS dilakukan Senin-Jumat (D-18); hari libur nasional yang kosong dicek di fase audit |
| `n_holiday_days` | int | Jumlah hari libur nasional dan cuti bersama dalam bulan | Dari kalender hari besar |
| `months_to_idulfitri` | int | Jarak bulan ke Idulfitri terdekat; negatif = sebelum, positif = sesudah | Definisi "terdekat" ditetapkan di fase transform dan dicatat |

### `dim_sentra_point`

| Kolom | Tipe | Deskripsi | Sumber | Catatan |
| --- | --- | --- | --- | --- |
| `regency_code` | string | Kode kabupaten BDSP | BDSP level kabupaten | PK bersama `commodity_group` |
| `commodity_group` | string | Komoditas yang diwakili baris | - | PK, FK |
| `province_id` | int | Provinsi PIHPS induk kabupaten | Pemetaan D-17 | FK |
| `regency_name` | string | Nama kabupaten sentra | BDSP | Dipilih dari produksi nasional teratas sampai kumulatif sekitar 80% (D-24) |
| `latitude`, `longitude` | float | Koordinat kabupaten | Nominatim (OpenStreetMap) | Hasil geocoding, titik pusat wilayah administratif |
| `anchor_id`, `anchor_latitude`, `anchor_longitude` | string, float | Lokasi Open-Meteo yang dipakai; kabupaten berjarak < 10 km memakai anchor yang sama | Disusun sendiri | Nama file cuaca raw mengikuti koordinat anchor |
| `production_weight` | float | Bobot produksi kabupaten dalam provinsi × komoditas, jumlah per grup = 1 | BDSP | Dihitung di fase transform |
| `weight_basis_year` | int | Tahun produksi yang jadi dasar bobot | BDSP | Satu tahun tetap atau rata-rata beberapa tahun: TBD fase transform |

## 3. Tabel fakta

### `fact_price_monthly`

PK: `province_id`, `month_start`, `commodity_group`, `price_type_id`.

| Kolom | Tipe | Deskripsi | Aturan null |
| --- | --- | --- | --- |
| `price_idr_per_kg` | float | Rata-rata harga bulan itu | `NULL` kalau hari terisi < 10 hari kerja dan tidak lolos aturan imputation |
| `n_days_observed` | int | Jumlah hari kerja terisi dari data harian | 0 kalau tidak ada data |
| `is_imputed` | bool | `TRUE` kalau nilai bukan hasil rata-rata observed | Wajib terisi |
| `impute_method` | string | `linear_log` atau `kalman` | `NULL` kalau `is_imputed = FALSE` |
| `source_extract_date` | date | Tanggal extraction | Wajib |

Sumber: PIHPS, `price_type_id` 1/3/4. Hipotesis: H1-H4.

### `fact_price_weekly`

PK: `province_id`, `week_start`, `commodity_group`, `price_type_id`. Sumber: PIHPS tipe laporan mingguan. Hanya untuk lead-lag (H2). Tidak ada imputation (D-12); minggu kosong tetap `NULL`.

| Kolom | Tipe | Deskripsi |
| --- | --- | --- |
| `price_idr_per_kg` | float | Harga mingguan |
| `source_extract_date` | date | Tanggal extraction |

### `fact_production_annual`

PK: `province_id`, `year`, `commodity_group`. Sumber: BDSP, 2018-2025. Dipakai sebagai benchmark Chow-Lin dan Denton, serta untuk reconciliation.

| Kolom | Tipe | Deskripsi | Catatan |
| --- | --- | --- | --- |
| `production_ton` | float | Produksi tahunan | `cabai_merah` = cabe besar + cabe keriting |
| `harvested_area_ha` | float | Luas panen | Dari indikator LUAS PANEN BDSP |
| `source_extract_date` | date | Tanggal extraction | - |

### `fact_production_national_monthly`

PK: `month_start`, `commodity_group`. Sumber: Buletin Konsumsi Pangan.

| Kolom | Tipe | Deskripsi | Aturan null |
| --- | --- | --- | --- |
| `production_ton` | float | Produksi bulanan nasional | `NULL` kalau hanya ada proyeksi |
| `status` | string | `realisasi` atau `missing` | Wajib. Hanya realisasi SPH-BPS dari edisi terbaru yang dihitung sebagai `realisasi` |
| `bulletin_edition` | string | Edisi buletin asal angka, misalnya `2025-S1` | `NULL` kalau `status = missing` |

### `fact_production_monthly`

PK: `province_id`, `month_start`, `commodity_group`. Hasil disagregasi.

| Kolom | Tipe | Deskripsi | Catatan |
| --- | --- | --- | --- |
| `production_ton_chow_lin` | float | Estimasi bulanan, utama | Total 12 bulan = angka tahunan BDSP |
| `production_ton_denton` | float | Estimasi pembanding | Dipakai di sensitivity check |
| `is_imputed` | bool | Selalu `TRUE` | Semua nilai adalah estimasi |
| `impute_method` | string | `chow_lin` | - |

`NULL` untuk 2026 (angka tahunan belum terbit) dan untuk kombinasi yang tidak punya benchmark.

### `fact_weather_monthly`

PK: `province_id`, `month_start`, `commodity_group`. Sumber: Open-Meteo, diagregasi dari harian per titik sentra lalu dibobot dengan `production_weight`.

| Kolom | Tipe | Deskripsi | Catatan |
| --- | --- | --- | --- |
| `rain_total_mm` | float | Jumlah hujan bulanan | - |
| `rain_anomaly` | float | Selisih terhadap normal bulan kalender | Normal = rata-rata 1991-2020 (WMO climate normal, D-19) |
| `rel_humidity_mean` | float | Rata-rata kelembapan relatif | - |
| `weather_status` | string | `observed` atau `not_applicable` | `not_applicable` untuk provinsi × komoditas tanpa titik sentra (D-25); nilai cuaca `NULL` dan bukan missing |
| `source_extract_date` | date | Tanggal extraction | - |

Kategori kering/normal/basah untuk H1 diturunkan dari `rain_anomaly` saat analisis, bukan disimpan di sini.

### `fact_oni_monthly`

PK: `month_start`. Sumber: NOAA ONI, nasional.

| Kolom | Tipe | Deskripsi | Catatan |
| --- | --- | --- | --- |
| `season_label` | string | Season 3 bulan asal, misalnya `DJF` | Dipetakan ke bulan tengah |
| `oni_anomaly` | float | Kolom `ANOM` | `NULL` untuk Okt-Nov 2026 |
| `enso_phase` | string | `el_nino` (>= 0.5), `la_nina` (<= -0.5), `neutral` | Ambang standar NOAA |

## 4. Tabel akhir: `core_province_month`

Definisi kolom sudah ada di [ERD, bagian 3](02_erd_core_dataset.md). Aturan kualitasnya:

1. Key `province_id` + `month_start` + `commodity_group` unik.
2. Setiap kolom variabel yang bisa di-impute punya pasangan `<variabel>_is_imputed` dan `<variabel>_impute_method`.
3. Sel `NULL` hanya sah dengan alasan yang tercatat: di luar periode inti, variabel tanpa observed data, NTT pada harga produsen, produksi 2026, bulan parsial, ONI setelah ASO 2026.
4. Harga produsen tidak pernah diisi dari harga pedagang besar.

## 5. Yang masih TBD

| Item | Dilengkapi di fase |
| --- | --- |
| Tabel pemetaan nama provinsi PIHPS dan BDSP ke 34 provinsi, kode BPS, dan pemetaan pemekaran ke induk (D-17) | Extract |
| Satuan asli dan format angka tiap sumber | Extract |
| Daftar provinsi × komoditas tanpa titik sentra (`weather_status = not_applicable`) | Transform |
| Hari libur nasional yang kosong di PIHPS (survei sendiri Senin-Jumat, D-18) | Audit |
| Tahun dasar bobot sentra | Transform |
| Definisi `months_to_idulfitri` untuk bulan di antara dua Idulfitri | Transform |
