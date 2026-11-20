# Project Charter & Requirements: Harga Cabai Melonjak di Tengah Surplus Produksi

Versi baseline, 19 November 2026. Dokumen ini adalah requirements awal proyek dan tidak diubah lagi kecuali bagian H5 (D-27, D-56). Perubahan sesudahnya tercatat di [decision log](decision_log.md); aturan kualitas data yang berlaku ada di [alur kerja proyek](00_project_workflow.md), karena beberapa aturan di bawah (Kalman, Chow-Lin, gap 1-2 bulan) kemudian dibatalkan (D-42, D-43).

## Executive summary

Project ini menjawab satu pertanyaan: **kalau produksi cabai nasional cukup, kenapa harga tetap melonjak di banyak daerah?** Jawabannya dicari dari data publik 2019–2026 untuk cabai merah dan cabai rawit di 34 provinsi.

Tujuannya tiga:

1. Mengidentifikasi root cause price spike (lonjakan harga) dari hulu ke hilir: cuaca di sentra produksi, volume produksi, price transmission di supply chain, dan distribusi antardaerah.
2. Mengukur kontribusi setiap driver pada episode price spike yang benar-benar terjadi.
3. Menguji apakah price spike bisa dideteksi lebih awal lewat early warning signal, dan apa dampaknya kalau signal itu dipakai.

Dokumen ini mencakup tahap discovery dan requirements. Desain teknis (process map, data model, data flow) disusun setelah requirements disetujui.

## Background

Menurut Kementan, produksi cabai Oktober 2026 diperkirakan 133 ribu ton untuk cabai rawit dan sekitar 115 ribu ton untuk cabai besar, sementara kebutuhan konsumsi berkisar 70 ribu ton ([iNews](https://www.rctiplus.com/news/detail/berita-utama/5494867/kementan-ungkap-biang-kerok-harga-cabai-melonjak-meski-pasokan-surplus)). Pada periode yang sama, harga cabai rawit di konsumen masih sekitar Rp93.629/kg. Kementan sendiri menyebut masalahnya ada di sejumlah daerah yang defisit walaupun secara nasional surplus.

Dampaknya luas:

- Awal November 2026, cabai rawit merah sempat Rp124.400/kg, lebih dari dua kali Harga Acuan Pemerintah Rp57.000/kg ([BCA Sekuritas/IQPlus](https://bcasekuritas.co.id/latest-news/news/mendag-sebut-faktor-cuaca-jadi-penyebab-kenaikan-harga-cabai)).
- Cabai merah menyumbang sekitar 59% dari inflasi bulanan Oktober 2026 ([Katadata](https://katadata.co.id/finansial/makro/6ae986942d480/lonjakan-harga-cabai-jadi-biang-kerok-inflasi-oktober-ini-penjelasan-mendag)).
- Lonjakan serupa terjadi berulang: Juli 2022, akhir 2023, dan Oktober–November 2026. EDA pada harga eceran nasional PIHPS 2019–2025 menunjukkan seasonality (rata-rata per bulan kalender, setelah trend rata-rata 12 bulan terpusat dikeluarkan dari log harga) hanya menjelaskan 8% variasi untuk cabai merah dan 23% untuk cabai rawit. Artinya, price spike lebih dipicu shock di tahun tertentu daripada pola musiman yang berulang.

Penjelasan yang beredar (cuaca, El Niño, hama) benar tapi belum lengkap. Belum ada gambaran terukur tentang bagaimana supply shock di sentra produksi ditransmisikan lewat supply chain dan distribusi sampai ke konsumen di provinsi lain.

## Stakeholder

Kebutuhan stakeholder di bawah diturunkan dari secondary research (pernyataan pejabat, pedagang, petani, dan penelitian yang dikutip media), bukan dari wawancara langsung.

| Stakeholder | Dampak yang dirasakan | Pertanyaan yang ingin dijawab |
| --- | --- | --- |
| Rumah tangga | Belanja dapur naik, mengganti atau mengurangi cabai | Kapan harga biasanya mereda? |
| Warung, resto, katering | Food cost naik saat harga menu tetap, margin tergerus | Seberapa sering dan seberapa lama lonjakan terjadi, dan adakah tanda awalnya? |
| Ritel dan distributor | Harga beli fluktuatif, stok cepat rusak | Dari mana dan kapan sebaiknya membeli? |
| Pemda / TPID dan Bapanas | Inflasi daerah, perlu memindahkan pasokan dari daerah surplus ke defisit | Daerah mana yang paling rentan, dan berapa lama waktu untuk bertindak? |
| Petani | Harga anjlok setelah panen ramai, rugi saat gagal panen | Kapan menanam supaya tidak ikut-ikutan dan berakhir rugi? |

## Scope

**Masuk:**

- Komoditas: cabai merah (besar dan keriting) dan cabai rawit (merah dan hijau).
- Wilayah: 34 provinsi, dengan perhatian khusus ke provinsi sentra dan DKI Jakarta sebagai pasar konsumsi terbesar.
- Periode inti: Januari 2019–November 2026. Data 2018 hanya dipakai untuk membentuk lagged variables.
- Grain utama: provinsi × bulan. Data mingguan dipakai khusus untuk lead-lag analysis antar level supply chain.

**Tidak masuk:**

- Komoditas lain (bawang, beras), walaupun metodenya bisa dipakai ulang.
- Forecasting harga harian.
- Policy evaluation untuk intervensi pemerintah tertentu, karena data intervensinya tidak tersedia lengkap.
- Dashboard. Dibuat sebagai tahap terpisah setelah temuan final.

## Business requirements & hypotheses

Analisis harus menjawab empat business requirements (BR). Setiap BR diuji lewat hipotesis yang punya cara uji dan kondisi yang akan membantahnya. H1–H4 adalah hipotesis prioritas; H5–H6 pendukung.

- **BR1:** Apa driver utama price spike, dan berapa lag dari driver ke harga konsumen?
- **BR2:** Di level supply chain mana price spike dimulai dan membesar?
- **BR3:** Kenapa daerah tertentu tetap mahal saat produksi nasional cukup?
- **BR4:** Bisakah price spike dideteksi lebih awal (early warning), dan berapa lead time-nya?

| ID | BR | Hipotesis | Cara uji | Dibantah jika |
| --- | --- | --- | --- | --- |
| H1 | BR1 | Curah hujan ekstrem di sentra, baik terlalu kering maupun terlalu basah, menurunkan produksi dan menaikkan harga produsen dengan lag 1–4 bulan | Bandingkan produksi dan harga produsen antara bulan kering, normal, dan basah, dengan lag 0–6 bulan | Tidak ada perbedaan harga yang konsisten antara bulan anomali dan bulan normal di semua lag |
| H2 | BR2 | Kenaikan dimulai di level produsen dan pedagang besar, lalu ditransmisikan ke harga eceran secara asimetris (asymmetric price transmission: naik cepat, turun lambat) | Lead-lag analysis mingguan antar level supply chain dan uji asymmetric price transmission | Harga eceran bergerak lebih dulu, atau transmisi naik dan turun simetris |
| H3 | BR3 | Saat supply shock, price disparity antarprovinsi melebar, terutama di provinsi yang jauh dari sentra | Price disparity antarprovinsi saat price spike vs kondisi normal, dihubungkan dengan jarak ke sentra | Disparity tidak melebar, atau tidak berkaitan dengan jarak ke sentra |
| H4 | BR4 | Cuaca di sentra dan harga produsen menjadi leading indicator sebelum harga eceran melonjak | Backtest early warning signal pada episode price spike 2019–2026 | Signal tidak memberi lead time lebih panjang atau akurasi lebih baik dari naive baseline "harga naik bulan lalu" |
| H5 | BR1 | Harga produsen tinggi mendorong petani menanam lebih luas, sehingga luas panen dan produksi naik pada tahun berikutnya (cobweb cycle) | Panel fixed effect provinsi × tahun: perubahan luas panen tahun t terhadap harga produsen tahun t−1 (BDSP tahunan); year FE sebagai pembanding | Tidak ada kenaikan luas panen yang konsisten pada tahun setelah harga tinggi |
| H6 | BR1 | Hari besar menambah kenaikan, tapi bukan pemicu utama | Efek hari besar setelah faktor lain dikontrol | Efek hari besar sebesar atau lebih besar dari efek cuaca |

H2 dan H3 adalah jawaban langsung atas paradoks surplus. Tanpa keduanya, kesimpulan berhenti di "cuaca buruk" yang tidak actionable.

## User stories

Setiap story punya acceptance criteria yang bisa dicek. Threshold tidak ditetapkan di awal; setiap metrik dibandingkan dengan naive baseline, supaya hasil tidak terlihat bagus hanya karena target dibuat rendah.

| ID | User story | Acceptance criteria | BR |
| --- | --- | --- | --- |
| US1 | Sebagai pemda/TPID, saya ingin mendapat early warning sebelum price spike terjadi, agar bisa menyiapkan pasokan dari daerah surplus | Early warning signal memberi lead time minimal 1 bulan pada mayoritas episode price spike, dengan false alarm rate lebih rendah dari baseline | BR4 |
| US2 | Sebagai pemda/TPID, saya ingin tahu provinsi mana yang paling rentan saat supply shock | Ranking provinsi berdasarkan price premium terhadap rata-rata nasional saat price spike, konsisten di minimal dua episode | BR3 |
| US3 | Sebagai pemilik warung atau resto, saya ingin tahu berapa lama price spike biasanya bertahan, agar bisa memutuskan menahan harga menu atau menyesuaikannya | Durasi dan magnitude price spike per episode tersedia per jenis cabai, dengan rentang min–maks | BR1 |
| US4 | Sebagai ritel atau distributor, saya ingin tahu level supply chain mana yang bergerak lebih dulu, agar keputusan pembelian bisa lebih cepat | Lead-lag antar level supply chain terukur dalam satuan minggu, beserta confidence interval-nya | BR2 |
| US5 | Sebagai pembaca umum, saya ingin penjelasan penyebab lonjakan yang bisa dicek ulang | Setiap finding traceable ke data dan kode di repository | Semua |

## Data requirements

Semua sumber inti sudah dicek langsung pada 19 November 2026. Sumber yang belum lengkap tidak digabung ke core dataset; penanganannya ada di bagian data quality rules.

| Kebutuhan | Sumber | Granularity | Hasil audit | Hipotesis |
| --- | --- | --- | --- | --- |
| Harga eceran (retail) dan pedagang besar (wholesale) | [PIHPS Nasional, Bank Indonesia](https://www.bi.go.id/hargapangan) | Harian dan bulanan, per provinsi dan kota | Lengkap Jan 2018–Nov 2026 di tingkat nasional (107 bulan). Cabai rawit: 34 dari 35 baris eceran dan 33 dari 34 provinsi pedagang besar terisi minimal 95% | H2, H3, H4 |
| Harga produsen (farm-gate) | PIHPS Nasional | Harian dan bulanan, per provinsi | Seri baru mulai pertengahan 2018 (Jawa Timur Juli, Jawa Barat September). Sekitar 93% bulan terisi di hampir semua provinsi; NTT kosong hampir terus sejak 2024 | H1, H2, H4 |
| Curah hujan di sentra | [Open-Meteo Historical API](https://open-meteo.com/) | Harian per titik koordinat | Lengkap, sudah diuji untuk 2010–2026 di Garut, Magelang, Kediri, Malang, Brebes | H1, H4 |
| El Niño / La Niña | [NOAA ONI](https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt) | 3-month running mean | Lengkap sampai Agustus–Oktober 2026 | H1 |
| Produksi tahunan per provinsi | [BDSP Kementan](https://bdsp2.pertanian.go.id/bdsp/id/lokasi) | Tahunan, provinsi dan kabupaten | Lengkap 2018–2025 untuk cabai rawit dan cabai besar di semua provinsi; level kabupaten tersedia, belum ditarik | Production weight sentra, H5 |
| Produksi bulanan nasional | [Buletin Konsumsi Pangan, Kementan](https://satudata.pertanian.go.id/assets/docs/publikasi/Buletin_Konsumsi_Pangan_Semester_I_2024.pdf) | Bulanan, nasional | Tabel Januari–Desember per tahun, campuran realisasi SPH-BPS dan proyeksi. Edisi 2022, Semester I 2024, dan Semester I 2025 sudah ditemukan; kelengkapan edisi lain belum dicek | H1 (deskriptif) |
| Kalender hari besar | Disusun sendiri | Harian | Lengkap | H6 |

Dua data belum tersedia publik dan tidak masuk core dataset:

- **Luas tanam bulanan:** dikumpulkan BPS lewat formulir SPH-SBS, tapi tidak dipublikasikan. Bisa diminta lewat PST BPS atau PPID Kementan. H5 diuji di grain tahunan memakai luas panen dan produksi BDSP; luas tanam bulanan tetap akan memperkuat uji ini.
- **Pasokan harian Pasar Induk Kramat Jati:** Info Pangan Jakarta hanya menampilkan harga. Bisa diminta lewat PPID Perumda Pasar Jaya. Untuk H3, price disparity antarprovinsi dan price spread antar level supply chain dipakai sebagai proxy.

## Data quality rules

Prinsip utamanya: imputation hanya dilakukan kalau ada anchor dari data nyata, dan variabel yang dipakai untuk imputation tidak boleh variabel yang nanti diuji hubungannya. Tanpa aturan kedua, hasilnya circular: korelasi yang keluar hanya cerminan metode imputation.

| Kondisi | Treatment |
| --- | --- |
| Missing days dalam satu bulan | Monthly average dari hari yang tersedia, minimal 10 hari kerja terisi; jika kurang, bulan tersebut dianggap missing |
| Gap 1–2 bulan berturut-turut | Linear interpolation pada log price |
| Gap lebih panjang di tengah time series | Kalman smoothing dengan state-space model (trend + seasonal) |
| Missing di awal series atau hampir seluruhnya | Tidak di-impute. Periode analisis dimulai Januari 2019; NTT dikeluarkan dari analisis harga produsen |
| Temporal disaggregation produksi tahunan per provinsi ke bulanan | Chow-Lin dengan produksi bulanan nasional sebagai indicator series; total 12 bulan selalu sama dengan angka tahunan resmi (benchmarking). Denton sebagai pembanding |
| Produksi bulanan nasional | Hanya bulan berstatus realisasi SPH-BPS dari edisi buletin terbaru; bulan yang hanya punya proyeksi dibiarkan kosong |
| Produksi 2026 (angka tahunan belum terbit) | Tidak di-extrapolate; sensitivity check dengan dan tanpa data 2026 |
| Cuaca per provinsi | Production-weighted average dari titik kabupaten sentra |
| ONI | Nilai tiap 3-month season dipetakan ke bulan tengahnya (DJF → Januari), sama untuk semua provinsi |
| Variabel tanpa observed data sama sekali | Tidak di-impute |

Tiga aturan pendukung:

1. Setiap imputed value diberi flag `is_imputed` dan `impute_method`.
2. Metode imputation dipilih lewat hold-out validation: sebagian observed value sengaja di-mask, di-impute ulang, lalu error-nya (MAPE) dibandingkan antar metode. Hasilnya dilaporkan.
3. Pipeline reproducible: bisa di-rerun end-to-end dengan satu command, sehingga data bulan baru bisa ditambahkan tanpa proses manual.

## Success criteria

Project dianggap berhasil kalau empat hal ini terpenuhi:

1. **Data:** core dataset provinsi × bulan tanpa missing value yang tidak ter-flag, dan metode imputasi dipilih lewat hold-out; jika tidak lebih akurat dari baseline linear, baseline yang dipakai.
2. **Explanatory power:** secara out-of-sample (episode price spike yang tidak dipakai saat training model), driver di H1–H3 menjelaskan arah dan magnitude kenaikan harga lebih baik dari baseline seasonal average.
3. **Early warning:** signal dari H4 memberi lead time lebih panjang atau false alarm rate lebih rendah dibanding baseline "harga naik bulan lalu".
4. **Jawaban:** setiap BR terjawab, termasuk jawaban "tidak terbukti" kalau hipotesisnya dibantah data.

## Assumptions, risks & constraints

| Tipe | Isi | Mitigasi |
| --- | --- | --- |
| Batasan | Hanya sekitar 4–5 episode price spike besar dalam 2019–2026 | Finding disajikan sebagai association yang konsisten, bukan bukti causality |
| Asumsi | Pola musiman produksi tiap provinsi mirip pola nasional (dasar Chow-Lin) | Dibandingkan dengan Denton; perbedaan hasil dilaporkan |
| Asumsi | Curah hujan reanalysis Open-Meteo mewakili kondisi di lahan | Dicek terhadap kejadian cuaca yang dilaporkan media pada episode 2022 dan 2023 |
| Risiko | Edisi buletin tidak lengkap sehingga beberapa bulan produksi tanpa angka realisasi | Bulan itu dibiarkan kosong dan ditandai; H5 tidak memakai produksi bulanan karena diuji di grain tahunan |
| Risiko | PIHPS bisa direvisi | Tanggal extraction dicatat di metadata |
| Batasan | Data distribusi langsung (pasokan pasar induk, arus antarprovinsi) tidak tersedia publik | H3 memakai price disparity sebagai proxy; keterbatasan ini ditulis terbuka |
| Batasan | Kebutuhan stakeholder berasal dari secondary research | Ditulis jelas sebagai secondary research, bukan wawancara |

## Decision log

| Tanggal | Keputusan | Alasan |
| --- | --- | --- |
| 19 Nov 2026 | Pertanyaan inti diganti menjadi paradoks surplus produksi vs harga melonjak | Lebih tajam dan actionable daripada "kenapa harga naik-turun" |
| 19 Nov 2026 | Periode analisis dimulai Januari 2019 | Harga produsen di PIHPS baru tersedia sejak pertengahan 2018 |
| 19 Nov 2026 | NTT dikeluarkan dari analisis harga produsen | Data kosong hampir terus sejak 2024; NTT bukan sentra cabai |
| 19 Nov 2026 | Pasokan Pasar Induk Kramat Jati tidak masuk core dataset | Tidak ada seri publik; angka di berita hanya potongan tanggal tertentu |
| 19 Nov 2026 | Cabai rawit masuk scope bersama cabai merah | Dampak dan keluhan sama; kelengkapan datanya setara |
| 19 Nov 2026 | Premis "price spike menjelang Lebaran" ditinggalkan | Data PIHPS 2018–2026 menunjukkan puncak harga cabai tidak jatuh di bulan Lebaran |
| 19 Nov 2026 | Fokus bergeser dari satu jenis usaha (warung) ke causal chain | Cerita warung terlalu sempit; pertanyaan yang lebih berguna adalah mekanisme penyebabnya |
| 19 Nov 2026 | Studi kasus Citi Bike (New York) tidak dipakai | Masalahnya tidak relevan untuk pembaca di Indonesia |

## Next steps

1. **Review dan sign-off dokumen ini.** Requirements yang disetujui menjadi baseline; perubahan berikutnya dicatat di decision log.
2. **Design:** AS-IS process map rantai pasok cabai, data model (ERD) core dataset, data flow diagram pipeline, dan data dictionary.
3. **Build:** tarik semua sumber, data completeness audit per provinsi × bulan, imputation sesuai data quality rules, lalu integrasi ke grain provinsi × bulan. Belum ada analisis di tahap ini.
4. **Validation:** hold-out validation untuk metode imputation dan reconciliation dataset final terhadap sumber.
5. **Analysis:** uji H1–H6, lalu susun Requirements Traceability Matrix yang menghubungkan setiap BR → hipotesis → data → metode → temuan.
6. **Delivery:** findings dan what-if scenario ("kalau root cause-nya diatasi"), lalu case study di portfolio. Dashboard menyusul sebagai tahap terpisah.

## Sumber

Data:

- [PIHPS Nasional, Bank Indonesia](https://www.bi.go.id/hargapangan)
- [Open-Meteo Historical Weather API](https://open-meteo.com/)
- [NOAA Oceanic Niño Index (ONI)](https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt)
- [Basis Data Statistik Pertanian (BDSP), Kementan](https://bdsp2.pertanian.go.id/bdsp/id/lokasi)
- [Buletin Konsumsi Pangan Semester I 2024, Pusdatin Kementan](https://satudata.pertanian.go.id/assets/docs/publikasi/Buletin_Konsumsi_Pangan_Semester_I_2024.pdf)
- [Statistik Hortikultura 2021, BPS](https://bps.go.id/en/publication/2022/06/08/44e935e8c141bcb37569aed3/horticultural-statistics-2021.html) (pengumpulan bulanan SPH-SBS)

Konteks dan secondary research:

- [Kementan ungkap biang kerok harga cabai melonjak meski pasokan surplus, iNews (Okt 2026)](https://www.rctiplus.com/news/detail/berita-utama/5494867/kementan-ungkap-biang-kerok-harga-cabai-melonjak-meski-pasokan-surplus)
- [Mendag sebut faktor cuaca jadi penyebab kenaikan harga cabai, IQPlus via BCA Sekuritas (3 Nov 2026)](https://bcasekuritas.co.id/latest-news/news/mendag-sebut-faktor-cuaca-jadi-penyebab-kenaikan-harga-cabai)
- [Lonjakan harga cabai jadi biang kerok inflasi Oktober, Katadata (3 Nov 2026)](https://katadata.co.id/finansial/makro/6ae986942d480/lonjakan-harga-cabai-jadi-biang-kerok-inflasi-oktober-ini-penjelasan-mendag)
- [Ini penjelasan Mentan soal penyebab harga cabai melonjak, Bisnis.com (Jul 2022)](https://ekonomi.bisnis.com/read/20220703/12/1550717/ini-penjelasan-mentan-syahrul-soal-penyebab-harga-cabai-melonjak)
- [Harga cabai makin pedas jelang akhir tahun, Bisnis.com (Okt 2023)](https://ekonomi.bisnis.com/read/20231030/99/1709199/harga-cabai-makin-pedas-jelang-akhir-tahun-ini-biang-keroknya)
- [Serangan penyakit jadi alasan harga cabai melonjak, Bisnis.com (Jun 2022)](https://ekonomi.bisnis.com/read/20220607/12/1540848/serangan-penyakit-jadi-alasan-harga-cabai-melonjak)
- [Pakar agribisnis IPB soal harga cabai, Kemdiktisaintek (Mar 2021)](https://kemdiktisaintek.go.id/news/article/pakar-agribisnis-ipb-university-beri-penjelasan-soal-harga-cabai-melambung-tinggi)
