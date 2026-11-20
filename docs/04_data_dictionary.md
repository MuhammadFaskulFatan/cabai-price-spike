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
| Nilai `impute_method` | `linear_log` (satu-satunya metode; Kalman dan Denton dibatalkan, D-42, D-43) |
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
| `n_holiday_days` | int | Jumlah hari libur nasional (Idulfitri, Iduladha, Natal, Tahun Baru) dalam bulan | Dari `holidays.csv`; cuti bersama tidak dihitung di sini |
| `n_holiday_weekdays` | int | Jumlah libur nasional yang jatuh di Senin-Jumat | Relevan untuk jumlah hari kerja PIHPS |
| `n_cuti_bersama_days` | int | Jumlah hari cuti bersama dalam bulan | Dari `cuti_bersama.csv` (`is_cuti_bersama`); 2020 dan sebagian Natal kosong karena belum terverifikasi (D-38), jadi dihitung 0 dan ditandai oleh `cuti_bersama_verified` |
| `cuti_bersama_verified` | bool | `TRUE` kalau semua cuti bersama di bulan itu terlihat di situs pemerintah dan bulan itu tidak termasuk bulan yang cutinya belum terverifikasi | `FALSE` untuk seluruh 2020, Agustus 2018 dan 2019, Juli 2021 dan 2022, Desember 2018, 2019, 2022 (cuti belum terverifikasi), serta April dan Juni 2025 (hanya sekunder) (D-41) |
| `months_to_idulfitri` | int | Selisih bulan terhadap bulan 1 Syawal terdekat; negatif = sebelum, 0 = bulan Idulfitri, positif = sesudah | Kalau dua Idulfitri berjarak sama (6 bulan) dipilih yang akan datang. Bulan akhir 2026 memakai Idulfitri 2027 (10-11 Maret 2027 menurut SKB 2027, menunggu sidang isbat), hanya sebagai jangkar dan tidak masuk kalender raw (D-41) |

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
| `tier` | string | `main`, `descriptive`, atau `excluded` (D-35); sama untuk semua bulan satu seri | Wajib. `excluded` tidak di-impute dan tidak dipakai di model |
| `impute_method` | string | `linear_log` | `NULL` kalau `is_imputed = FALSE` |
| `source_extract_date` | date | Tanggal extraction | Wajib |

Sumber: PIHPS, `price_type_id` 1/3/4. Hipotesis: H1-H4.

### `fact_price_weekly`

PK: `province_id`, `week_start`, `commodity_group`, `price_type_id`. Sumber: PIHPS tipe laporan mingguan. Hanya untuk lead-lag (H2). Tidak ada imputation (D-12); minggu kosong tetap `NULL`.

| Kolom | Tipe | Deskripsi |
| --- | --- | --- |
| `price_idr_per_kg` | float | Harga mingguan |
| `source_extract_date` | date | Tanggal extraction |

### `fact_production_annual`

PK: `province_id`, `year`, `commodity_group`. Sumber: BDSP, 2018-2025. Dipakai untuk `production_annual_ton` di `core_province_month`, bahan `core_province_year`, dan reconciliation. Angka 2025 `is_preliminary` (D-29).

| Kolom | Tipe | Deskripsi | Catatan |
| --- | --- | --- | --- |
| `production_ton` | float | Produksi tahunan | `cabai_merah` = cabe besar saja (D-28). Cabe keriting disimpan terpisah sebagai `cabai_keriting` (referensi), sudah dikonversi dari kuintal ke ton |
| `is_preliminary` | bool | `TRUE` untuk 2025 | Belum diverifikasi ke rilis BPS; tetap di analisis utama, sensitivity check tanpa 2025 (D-40) |
| `is_outlier` | bool | `TRUE` kalau produktivitas (produksi / luas panen) di luar 1-30 ton/ha, dihitung setelah agregasi ke 34 provinsi | Nilai tidak diubah (D-37) |
| `suspect_copy` | bool | `TRUE` kalau nilai cabe keriting persis sama dengan cabe besar | Hanya berlaku untuk baris `cabai_keriting`; dari `data/raw/bdsp/flags/suspect_copy.csv` (D-39) |
| `harvested_area_ha` | float | Luas panen | Dari indikator LUAS PANEN BDSP |
| `source_extract_date` | date | Tanggal extraction | - |

### `fact_production_national_monthly`

PK: `month_start`, `commodity_group`. Sumber: Buletin Konsumsi Pangan.

| Kolom | Tipe | Deskripsi | Aturan null |
| --- | --- | --- | --- |
| `production_ton` | float | Produksi bulanan nasional | `NULL` kalau hanya ada proyeksi |
| `status` | string | `realisasi` atau `missing` | Wajib. Hanya realisasi SPH-BPS dari edisi terbaru yang dihitung sebagai `realisasi` |
| `bulletin_edition` | string | Edisi buletin asal angka, misalnya `2025-S1` | `NULL` kalau `status = missing` |

### `fact_production_monthly` (dibatalkan)

Tidak dibuat lagi (D-42). Estimasi Denton tidak lebih akurat dari flat pada hold-out; core memakai angka tahunan.

### `dim_holiday`

Satu baris per hari libur nasional atau cuti bersama, 2018-2026 (D-46).

| Kolom | Tipe | Deskripsi | Catatan |
| --- | --- | --- | --- |
| `date` | date | Tanggal | PK bersama `is_cuti_bersama` |
| `holiday` | string | `idulfitri`, `iduladha`, `natal`, `tahun_baru` | Perayaan yang terkait |
| `is_cuti_bersama` | bool | `TRUE` = cuti bersama, `FALSE` = libur nasional | - |
| `source_level` | string | `official` atau `secondary` | official = terlihat di situs pemerintah (atau tanggal tetap); secondary = hanya timeanddate.com. Cuti yang belum terverifikasi tidak ada di tabel |

### `fact_weather_monthly`

PK: `province_id`, `month_start`, `commodity_group`. Sumber: Open-Meteo, diagregasi dari harian per titik sentra lalu dirata-rata berbobot produksi (`mean_production_ton_2019_2025` tiap kabupaten sentra; kabupaten memakai cuaca anchor-nya). File: `data/interim/fact_weather_monthly.parquet` (Jan 2018 - Nov 2026, 34 provinsi x 2 grup); seri panjang 1991-2026 hanya untuk provinsi bertitik di `weather_monthly_full.parquet` (D-57); seri per lokasi di `weather_site_monthly.parquet` (D-58).

| Kolom | Tipe | Deskripsi | Catatan |
| --- | --- | --- | --- |
| `rain_total_mm` | float | Jumlah hujan bulanan (mm), rata-rata berbobot titik sentra | Bulan dengan hari tidak lengkap di salah satu titik = `NULL` |
| `rain_anomaly_mm` | float | `rain_total_mm` dikurangi normal bulan kalender (mm) | Normal = rata-rata 1991-2020 (WMO climate normal, D-19) |
| `rain_anomaly` | float | Rata-rata berbobot produksi dari z-score per lokasi: akar kuadrat hujan bulanan terhadap rata-rata dan SD bulan kalender 1991-2020 di lokasi itu | Variabel utama H1 dan H4 (D-58). Rata-rata 0 di baseline; SD 1 untuk provinsi satu titik, lebih kecil (sampai 0,66) untuk provinsi banyak titik karena dirata-rata |
| `rh_anomaly` | float | Rata-rata berbobot produksi dari z-score per lokasi: logit kelembapan relatif bulanan terhadap rata-rata dan SD bulan kalender 1991-2020 di lokasi itu | Untuk uji eksploratif cabai merah (antraknosa) dan H4 (D-59) |
| `rain_anomaly_plain_z` | float | Sama, tetapi z-score dari hujan bulanan tanpa akar | Hanya sensitivity; meledak di bulan kemarau yang normalnya hampir nol (D-58) |
| `rain_is_extreme` | bool | `TRUE` kalau ada lokasi penyumbang dengan \|z\| >= 3 atau hujan harian > 300 mm di bulan itu | Flag dari audit cuaca; nilai tidak diubah (D-58). `NULL` untuk `not_applicable` dan `partial_month` |
| `rel_humidity_mean` | float | Rata-rata kelembapan relatif harian (%) | - |
| `n_points` | int | Jumlah kabupaten sentra yang dirata-rata | 0 untuk `not_applicable` |
| `weather_status` | string | `observed`, `not_applicable`, atau `partial_month` | `partial_month` = November 2026 (arsip Open-Meteo tertinggal beberapa hari), nilai `NULL` (D-57).  `not_applicable` untuk provinsi × komoditas tanpa titik sentra (D-25); nilai cuaca `NULL` dan bukan missing. Provinsi bertitik: 14 untuk cabai merah (mencakup 94,1% produksi nasional rata-rata BDSP 2019-2025) dan 15 untuk cabai rawit (92,4%); gabungan 18 provinsi mencakup 95,7% (cabe besar) dan 94,8% (cabe rawit) |
| `source_extract_date` | date | Tanggal extraction | - |

Kategori kering/normal/basah untuk H1 diturunkan dari `rain_anomaly` saat analisis, bukan disimpan di sini. Di `core_province_month` kolom cuaca ikut dengan nama yang sama; `n_points` menjadi `weather_n_points`.

### `fact_oni_monthly`

PK: `month_start`. Sumber: NOAA ONI, nasional.

| Kolom | Tipe | Deskripsi | Catatan |
| --- | --- | --- | --- |
| `season_label` | string | Season 3 bulan asal, misalnya `DJF` | Dipetakan ke bulan tengah |
| `oni_anomaly` | float | Kolom `ANOM` | `NULL` untuk Okt-Nov 2026 |
| `enso_phase` | string | `el_nino` (>= 0.5), `la_nina` (<= -0.5), `neutral` | Ambang standar NOAA |

## 4. Tabel akhir: `core_province_month`

Kolom geografi (D-48, D-50), sama untuk semua bulan satu provinsi x komoditas:

| Kolom | Tipe | Deskripsi | Catatan |
| --- | --- | --- | --- |
| `distance_to_sentra_km` | float | Jarak great-circle (km) dari ibu kota provinsi ke titik sentra berbobot produksi terdekat untuk komoditas itu | Titik sentra = rata-rata koordinat kabupaten sentra satu provinsi, berbobot produksi rata-rata 2019-2025 (`sentra_points.csv`); provinsi sendiri ikut dihitung. Ibu kota digeocode lewat Nominatim |
| `is_different_island` | bool | `TRUE` kalau pulau ibu kota berbeda dengan pulau titik sentra terdekat | Pulau utama per provinsi, tabel di `pipeline/transform/geography.py` |
| `nearest_sentra_province_id` | int | Provinsi tempat titik sentra terdekat | Untuk menelusuri jarak |

`dim_province` juga memuat `capital`, `island`, `capital_lat`, `capital_lon`.

Kolom cuaca: `rain_total_mm`, `rain_anomaly_mm`, `rain_anomaly`, `rain_anomaly_plain_z`, `rain_is_extreme`, `rel_humidity_mean`, `rh_anomaly`, `weather_status`, `weather_n_points` (lihat `fact_weather_monthly`).

Kolom produksi: `production_annual_ton` (ton, angka tahunan BDSP diulang untuk 12 bulan dalam tahunnya, 2026 NULL) dan `production_annual_preliminary` (`TRUE` untuk 2025) (D-42).

Definisi kolom sudah ada di [ERD, bagian 3](02_erd_core_dataset.md). Aturan kualitasnya:

1. Key `province_id` + `month_start` + `commodity_group` unik.
2. Setiap kolom variabel yang bisa di-impute punya pasangan `<variabel>_is_imputed` dan `<variabel>_impute_method`.
3. Sel `NULL` hanya sah dengan alasan yang tercatat: di luar periode inti, variabel tanpa observed data, NTT pada harga produsen, produksi 2026, bulan parsial, ONI setelah ASO 2026, cuaca `not_applicable` atau `partial_month`.
4. Harga produsen tidak pernah diisi dari harga pedagang besar.

## 5. Tabel akhir: `core_province_year`

Key: `province_id`, `year`, `commodity_group`. Dipakai untuk uji H5: luas panen t terhadap harga produsen t-1 (D-27). Struktur kolom ada di [ERD, bagian 4](02_erd_core_dataset.md).

| Kolom | Tipe | Deskripsi | Aturan null |
| --- | --- | --- | --- |
| `harvested_area_ha` | float | Luas panen tahunan BDSP | `NULL` untuk 2026 |
| `production_ton` | float | Produksi tahunan BDSP | `NULL` untuk 2026 |
| `is_preliminary` | bool | `TRUE` untuk 2025 | Wajib |
| `producer_price_annual_mean` | float | Rata-rata bulanan harga produsen dalam tahun itu | `NULL` kalau tidak ada bulan terisi; NTT dikeluarkan (D-03) |
| `producer_price_n_months` | int | Jumlah bulan terisi (observed atau imputed) di tahun itu | Wajib |

## 6. Yang masih TBD

| Item | Dilengkapi di fase |
| --- | --- |
| Tabel pemetaan nama provinsi PIHPS dan BDSP ke 34 provinsi, kode BPS, dan pemetaan pemekaran ke induk (D-17) | Extract |
| Satuan asli dan format angka tiap sumber | Extract |
| Daftar provinsi × komoditas tanpa titik sentra (`weather_status = not_applicable`) | Transform |
| Hari libur nasional yang kosong di PIHPS (survei sendiri Senin-Jumat, D-18) | Audit |
| Tahun dasar bobot sentra | Transform |
| Definisi `months_to_idulfitri` untuk bulan di antara dua Idulfitri | Transform |
