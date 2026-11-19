# Rencana Analisis (Fase 6)

Status: **disetujui 19 Nov 2026 (D-48)**. Rincian keputusan atas usulan ada di bagian 9. Hasil uji per hipotesis dilaporkan di `analysis/` dengan format: hasil utama dan effect size, keputusan, sensitivity (termasuk D-44), chart, dan "so what".

Dokumen ini menetapkan, untuk H1-H6, pertanyaan bisnis, data, metode, metrik, aturan keputusan, dan sensitivity check. Usulan yang berbeda dari arah awal Fatan ditulis di bagian **Usulan** masing-masing dan di bagian 9; tidak ada yang diganti diam-diam.

## 1. Aturan umum

| Aturan | Isi |
| --- | --- |
| Periode model | Jan 2019 - Okt 2026 (`in_model_period`). 2018 hanya untuk lag; November 2026 parsial hanya deskriptif (D-16) |
| Seri harga di model utama | Tier `main` saja; tier `descriptive` hanya di sensitivity check; tier `excluded` tidak dipakai (D-35) |
| Bulan imputasi | Setiap uji H2 dan H4 wajib diulang tanpa bulan `<harga>_is_imputed = TRUE` (D-44). Aturan yang sama dipakai untuk H3, H5, H6 sebagai sensitivity |
| Harga produsen | NTT keluar (`in_producer_price_analysis = FALSE`, D-03); tidak pernah diisi dari harga pedagang besar |
| Produksi | Hanya angka tahunan BDSP (`production_annual_ton`, `core_province_year`); 2025 preliminary masuk analisis utama, sensitivity tanpa 2025 (D-29, D-40) |
| Cuaca | Hanya provinsi bertitik sentra (`weather_status = observed`; 14 provinsi untuk cabai merah, 15 untuk rawit); `not_applicable` tidak dipakai (D-25). Menunggu paket cuaca |
| Inferensi | Standard error robust terhadap korelasi antar provinsi di bulan yang sama (Driscoll-Kraay) atau cluster per provinsi; disebut per uji |
| Ambang signifikansi | p < 0,05, dua sisi, kecuali disebut lain. Hasil dibaca sebagai asosiasi yang konsisten, bukan bukti kausal (charter: hanya sekitar 6-7 episode besar) |
| Grup komoditas | Semua uji dijalankan terpisah untuk `cabai_merah` dan `cabai_rawit` |

## 2. Definisi price spike

Price spike: harga eceran bulanan provinsi (atau nasional) >= **1,25 x median 12 bulan sebelumnya** (t-12 sampai t-1, trailing, tanpa look-ahead). Bulan spike berurutan = satu episode. Sensitivity: ambang 1,15 dan 1,35. Kode: `analysis/spikes.py`.

Hasil EDA dengan definisi ini: 6 episode nasional cabai merah dan 10 cabai rawit (Jan 2019 - Okt 2026); 651 episode provinsi; **27% bulan provinsi tergolong spike** (36% di ambang 1,15, 21% di ambang 1,35).

**Keputusan (D-48):** 1,25x dipakai untuk deskriptif dan H3. Target H4 = onset **episode besar** (spike provinsi yang bertahan >= 2 bulan berturut-turut). Label **spike nasional** = spike serentak di >= 50% provinsi, untuk narasi dan chart.

Latar usulan: 27% bulan terlalu sering untuk disebut "lonjakan" di level provinsi, karena median trailing 12 bulan ikut tertinggal ketika harga naik bertahap. Saya usulkan dua tambahan sebagai sensitivity, bukan pengganti:
1. **Episode besar**: spike yang bertahan >= 2 bulan berturut-turut, atau terjadi serentak di >= 50% provinsi (sesuai pola "spike serentak" di EDA: Maret 2021 rawit 97% provinsi).
2. **Spike nasional** sebagai unit kejadian untuk H4 dan H6, provinsi sebagai unit untuk H3.

## 3. H2: asal dan transmisi lonjakan di rantai pasok (BR2)

| Elemen | Isi |
| --- | --- |
| Pertanyaan bisnis | Di level mana price spike dimulai, dan apakah kenaikan diteruskan ke konsumen lebih cepat daripada penurunan? |
| Data | `core_province_month`: `price_producer`, `price_wholesale`, `price_retail` (+ `_tier`, `_is_imputed`); `fact_price_weekly` (nasional, `province_id = 0`, tipe 1/3/4) |
| Metode | (a) **Lead-lag mingguan nasional**: log-difference, cross-correlation produsen -> pedagang besar -> eceran pada lag -8 sampai +8 minggu, uji Granger dua arah (lag dipilih AIC, maks 8). (b) **Asymmetric ECM bulanan per provinsi** (tier main di kedua level yang dipasangkan): hubungan jangka panjang log eceran vs log pedagang besar dan log pedagang besar vs log produsen; jangka pendek memisahkan error-correction term positif dan negatif serta perubahan harga hulu naik dan turun. Uji Wald kesamaan koefisien naik vs turun |
| Metrik | Lag dengan korelasi tertinggi (minggu) + interval kepercayaan bootstrap; p-value Granger; koefisien penyesuaian naik vs turun dan p-value Wald; porsi provinsi dengan asimetri signifikan |
| Aturan keputusan | **Didukung** kalau (1) harga produsen atau pedagang besar Granger-mendahului eceran (p < 0,05) dan arah sebaliknya tidak, dengan puncak cross-correlation di lag positif, dan (2) asimetri "naik cepat, turun lambat" signifikan di >= 50% provinsi tier main atau di model panel gabungan. **Dibantah** kalau eceran bergerak lebih dulu atau transmisi simetris (sesuai charter) |
| Sensitivity | Tanpa bulan imputasi (D-44, wajib); tier descriptive ikut; ambang spike 1,15/1,35 untuk analisis khusus periode spike; per komoditas; mingguan per provinsi sentra besar (Jawa Barat, Jawa Tengah, Jawa Timur) |

**Keputusan (D-48):** uji kointegrasi Engle-Granger dulu; provinsi tanpa kointegrasi memakai model asimetris dalam first difference, dan daftar provinsinya dicatat di laporan H2. Latar usulan: tambahkan uji kointegrasi sebelum ECM per provinsi; provinsi tanpa kointegrasi dilaporkan terpisah dan dianalisis dengan model perubahan (tanpa ECT). Alasannya: ECM hanya sah kalau ada hubungan jangka panjang. Data mingguan provinsi juga tersedia; dipakai sebagai sensitivity karena seri nasional bisa menyamarkan perbedaan antar daerah.

## 4. H3: disparitas antarprovinsi saat guncangan pasokan (BR3)

| Elemen | Isi |
| --- | --- |
| Pertanyaan bisnis | Kenapa daerah tertentu tetap mahal saat produksi nasional cukup, dan daerah mana paling rentan? |
| Data | `price_retail` 34 provinsi; penanda guncangan pasokan; jarak provinsi ke sentra (variabel baru, lihat Usulan) |
| Metode | (a) **Koefisien variasi (CV) harga eceran antarprovinsi per bulan**, dibandingkan antara bulan guncangan dan bulan normal, dengan kontrol month-of-year. (b) **Price premium provinsi** (harga provinsi / median nasional) saat spike nasional vs normal, diregresikan pada jarak ke sentra |
| Penanda guncangan | Utama: bulan spike harga **produsen** nasional (hulu, bukan eceran, supaya tidak circular dengan CV eceran). Setelah paket cuaca: anomali hujan ekstrem di sentra |
| Metrik | Selisih CV (poin persen) guncangan vs normal + interval bootstrap; koefisien jarak (premium per 100 km) |
| Aturan keputusan | **Didukung** kalau CV naik signifikan saat guncangan dan premium meningkat dengan jarak ke sentra (koefisien positif, p < 0,05). **Dibantah** kalau disparitas tidak melebar atau tidak berkaitan dengan jarak (charter) |
| Sensitivity | Tanpa DKI (pasar konsumsi, bukan provinsi biasa); ranking provinsi rentan harus konsisten di >= 2 episode (US2); ambang 1,15/1,35; penanda guncangan dari cuaca setelah tersedia |

**Keputusan (D-48, D-50):** `distance_to_sentra_km` dan `is_different_island` ditambahkan ke `core_province_month` (definisi di data dictionary).

Latar usulan:
1. **Jarak ke sentra** belum ada di core dataset. Usul: jarak garis lurus dari ibu kota provinsi ke titik tengah produksi sentra nasional (rata-rata koordinat kabupaten sentra berbobot produksi, dari `data/interim/sentra_points.csv`), dihitung per komoditas. Karena Indonesia kepulauan, tambahkan dummy "beda pulau dengan sentra terdekat", sebab ongkos antarpulau lebih menentukan daripada kilometer. Ini perlu persetujuan karena menambah variabel ke core.
2. Penanda guncangan memakai harga produsen, bukan produksi bulanan (produksi bulanan dibatalkan, D-42).

## 5. H5: siklus cobweb di grain provinsi x tahun (BR1)

| Elemen | Isi |
| --- | --- |
| Pertanyaan bisnis | Apakah harga tinggi mendorong petani menanam lebih luas sehingga produksi naik dan harga turun? |
| Data | `core_province_year`: `harvested_area_ha`, `production_ton`, `producer_price_annual_mean`, `producer_price_n_months`, `is_outlier`, `is_preliminary` (2018-2025) |
| Metode | Panel fixed effect provinsi x tahun: Δ log luas panen_t terhadap log harga produsen_(t-1) (deviasi dari rata-rata provinsi), FE provinsi, SE cluster provinsi. Lanjutan: Δ log produksi_t sebagai outcome kedua |
| Metrik | Elastisitas luas panen terhadap harga tahun lalu, interval kepercayaan 95% |
| Aturan keputusan | **Didukung** kalau koefisien positif dan signifikan di spesifikasi utama dan tanda tetap positif di semua sensitivity. **Dibantah** kalau tidak ada kenaikan luas panen yang konsisten setelah harga tinggi (charter) |
| Sensitivity | Tanpa `is_outlier` (D-37); tanpa 2025 (D-40); hanya provinsi-tahun dengan `producer_price_n_months` >= 9; tanpa bulan imputasi saat menghitung rata-rata harga tahunan; dengan year FE |

**Keputusan (D-48):** year FE dipakai sebagai spesifikasi pembanding. Catatan: year FE menyerap variasi harga nasional, sehingga spesifikasi itu hanya memakai variasi antarprovinsi. Latar usulan: sampel hanya sekitar 34 provinsi x 6 tahun perubahan (2019/2020-2025), jadi daya uji rendah. Tambahkan **year FE** sebagai spesifikasi pembanding: tanpa year FE, guncangan nasional (misalnya La Nina 2022) bisa terbaca sebagai respons terhadap harga. Hasil dibaca sebagai indikatif.

## 6. H6: efek hari besar setelah kontrol (BR1)

| Elemen | Isi |
| --- | --- |
| Pertanyaan bisnis | Seberapa besar hari besar menambah kenaikan harga, dan apakah ia pemicu utama? |
| Data | `price_retail` (log), `months_to_idulfitri`, `n_holiday_days`, `n_holiday_weekdays`, `n_cuti_bersama_days`, `cuti_bersama_verified`, `production_annual_ton`, `oni_anomaly` |
| Metode | Panel FE provinsi x bulan: log harga eceran pada dummy bulan Idulfitri dan bulan sebelum Idulfitri, dengan FE provinsi, FE month-of-year, trend, kontrol pasokan (produksi tahunan, ONI; anomali hujan setelah paket cuaca), dan `n_cuti_bersama_days` sebagai kontrol. Idulfitri bergeser sekitar 11 hari per tahun, sehingga efeknya bisa dipisah dari month-of-year |
| Metrik | Efek dalam persen harga (exp(β)-1) + interval kepercayaan; perbandingan dengan efek cuaca dari H1 dalam satuan yang sama (persen per 1 SD anomali hujan) |
| Aturan keputusan | **Didukung ("menambah, bukan pemicu utama")** kalau efek bulan Idulfitri positif dan signifikan tetapi lebih kecil dari efek cuaca H1. **Dibantah** kalau efek hari besar sebesar atau lebih besar dari efek cuaca (charter) |
| Sensitivity | Hanya bulan `cuti_bersama_verified = TRUE`; tanpa 2020 (pandemi dan cuti bersama yang direvisi); Natal-Tahun Baru sebagai dummy terpisah; tier descriptive ikut |

Catatan urutan: perbandingan dengan efek cuaca membutuhkan H1. Karena H6 dijalankan sebelum H1, kesimpulan akhir H6 menunggu H1; estimasi efek hari besar sendiri bisa dilaporkan lebih dulu. Validasi Fase 5 menunjukkan bulan kosong karena < 10 hari kerja tidak menumpuk di bulan Lebaran, jadi tidak ada bias data yang perlu dikoreksi khusus.

## 7. H1: cuaca di sentra -> produksi dan harga produsen (BR1)

| Elemen | Isi |
| --- | --- |
| Pertanyaan bisnis | Apakah curah hujan ekstrem di sentra (terlalu kering atau terlalu basah) menaikkan harga produsen, dan berapa lag-nya? |
| Data | `rain_anomaly` (berbobot produksi, baseline 1991-2020; menunggu paket cuaca), `oni_anomaly`, `price_producer` (log), `production_annual_ton` |
| Metode | Panel FE provinsi x bulan (provinsi bertitik sentra): log harga produsen pada `rain_anomaly` dan `rain_anomaly^2` lag 1-4 (bentuk U), FE provinsi dan month-of-year, ONI sebagai driver hulu. Jalur produksi diuji di grain tahunan: Δ log produksi pada anomali hujan tahunan (rata-rata absolut atau jumlah bulan ekstrem) |
| Metrik | Efek marginal hujan sangat kering dan sangat basah (persen harga per 1 SD) per lag; uji gabungan lag 1-4; lag dengan efek terbesar |
| Aturan keputusan | **Didukung** kalau suku kuadrat positif dan signifikan (uji gabungan lag 1-4) sehingga kedua ekstrem menaikkan harga, dengan lag terbesar di 1-4 bulan. **Dibantah** kalau tidak ada perbedaan harga yang konsisten antara bulan anomali dan normal di semua lag (charter) |
| Sensitivity | Kategori kering/normal/basah (tercile atau +-1 SD) menggantikan kuadrat; lag 0-6; tanpa bulan imputasi; harga pedagang besar sebagai outcome; dengan dan tanpa ONI |

**Keputusan (D-48):** dua spesifikasi dipakai. Efek ONI hanya terbaca di spesifikasi pertama, karena FE tahun-bulan menyerap semua variabel yang sama untuk seluruh provinsi. Latar usulan: dengan FE month-of-year saja, ONI dan semua guncangan nasional ikut terbaca sebagai efek hujan lokal. Saya usulkan dua spesifikasi: (a) arahan Fatan: FE provinsi + month-of-year + ONI, untuk efek total termasuk iklim nasional; (b) FE provinsi + **FE tahun-bulan** (ONI otomatis terserap), untuk efek hujan lokal bersih dari guncangan nasional. Kalau keduanya sejalan, kesimpulan lebih kuat. Catatan: produksi bulanan tidak ada (D-42), jadi bagian "menurunkan produksi" hanya bisa diuji tahunan.

## 8. H4: early warning (BR4)

| Elemen | Isi |
| --- | --- |
| Pertanyaan bisnis | Bisakah price spike eceran dideteksi 1-2 bulan lebih awal, dan berapa lead time-nya? |
| Data | Target: onset episode besar (spike eceran provinsi yang bertahan >= 2 bulan) pada t+1 dan t+2. Fitur pada t: perubahan harga produsen dan pedagang besar (1 dan 3 bulan), rasio produsen terhadap median 12 bulan, `rain_anomaly` sentra (setelah paket cuaca), `oni_anomaly`, `months_to_idulfitri` |
| Metode | (a) Logistic regression sederhana dan (b) aturan sederhana (misalnya harga produsen >= 1,20 x median 12 bulan). **Rolling-origin backtest**: latih pada data sampai t, prediksi t+1/t+2, origin bergeser per bulan sepanjang 2023-2026. Ambang probabilitas dipilih di data latih saja |
| Baseline | Baseline musiman naif (spike diprediksi kalau bulan yang sama tahun lalu spike) dan baseline charter "harga eceran naik bulan lalu" |
| Metrik | Recall, precision, false alarm rate, lead time (bulan antara peringatan pertama dan awal episode) per episode |
| Aturan keputusan | **Didukung** kalau signal mengalahkan **baseline yang lebih kuat** dari keduanya: lead time lebih panjang atau false alarm rate lebih rendah pada recall yang setara, dan US1 terpenuhi (lead time >= 1 bulan pada mayoritas episode). **Dibantah** kalau tidak lebih baik dari baseline (charter) |
| Sensitivity | Tanpa bulan imputasi pada fitur (D-44, wajib); ambang spike 1,15/1,35; unit episode besar (bagian 2); tanpa fitur cuaca (agar bisa dibandingkan sebelum dan sesudah paket cuaca) |

**Keputusan (D-48):** dua baseline; model dinyatakan berhasil hanya jika mengalahkan baseline yang lebih kuat. Target = onset episode besar (spike provinsi >= 2 bulan berturut-turut). Latar usulan: charter memakai baseline "harga naik bulan lalu", sedangkan arahan memakai baseline musiman naif. Saya usulkan **keduanya** dilaporkan, karena baseline yang lebih kuat menentukan apakah signal benar-benar berguna. Dengan sekitar 6-10 episode nasional, metrik per episode akan sangat bergejolak; evaluasi utama memakai unit provinsi-bulan, dan per episode nasional sebagai pelengkap.

## 9. Usulan dan keputusannya (D-48)

| No | Usulan | Keputusan |
| --- | --- | --- |
| 1 | Episode besar sebagai sensitivity definisi spike | 1,25x untuk deskriptif dan H3; target H4 = onset episode besar (>= 2 bulan); spike nasional = serentak >= 50% provinsi, untuk narasi dan chart |
| 2 | Uji kointegrasi sebelum ECM (H2) | Disetujui; tanpa kointegrasi -> model asimetris first difference, daftar provinsi dicatat |
| 3 | Jarak ke sentra + dummy beda pulau (H3) | Disetujui: `distance_to_sentra_km`, `is_different_island` di core (D-50) |
| 4 | Year FE sebagai pembanding (H5) | Disetujui; year FE menyerap variasi harga nasional |
| 5 | Spesifikasi kedua H1 dengan FE tahun-bulan | Disetujui; efek ONI hanya terbaca di spesifikasi pertama |
| 6 | Dua baseline di H4 | Disetujui; model berhasil hanya jika mengalahkan baseline yang lebih kuat |

## 10. Urutan kerja

EDA (selesai) -> H2 -> H3 -> H5 -> H6 -> H1 -> H4. H1 dan H4 menunggu paket cuaca; H3 memakai penanda guncangan harga produsen lebih dulu dan diulang dengan cuaca setelah tersedia. Hasil tiap hipotesis dilaporkan sebelum lanjut ke hipotesis berikutnya.
