# Alur kerja proyek

Dokumen ini menjelaskan cara saya mengerjakan proyek ini: urutan fase, aturan kerja, dan aturan kualitas data. Tujuan proyeknya menunjukkan cara kerja end-to-end seorang Business Analyst / Data Analyst, dari problem framing, requirements, desain, build, dan validasi sampai temuan dan rekomendasi. Acuan requirements ada di [Project Charter](00_project_charter.md). Setiap perubahan rencana tercatat di [decision log](decision_log.md) dengan nomor D-xx.

## Pertanyaan dan scope

Pertanyaan inti: kalau produksi cabai nasional cukup, kenapa harga tetap melonjak di banyak daerah?

Scope:
- Komoditas: cabai merah (besar dan keriting) dan cabai rawit (merah dan hijau).
- Wilayah: 34 provinsi.
- Periode: Januari 2019 sampai November 2026. Data 2018 hanya dipakai untuk lagged variables. Model dan uji hipotesis memakai data sampai Oktober 2026; November 2026 adalah bulan parsial (flag `is_partial_month`) dan hanya dipakai untuk deskripsi (D-16).
- Grain utama: provinsi × bulan. Data mingguan hanya untuk lead-lag analysis.

Core dataset memakai dua grup komoditas, `cabai_merah` (`cat_7` di PIHPS) dan `cabai_rawit` (`cat_8`), supaya bisa dipasangkan dengan data produksi. Empat varian per jenis cabai tetap saya tarik ke `data/raw` untuk deskripsi, di luar core (D-10). Produksi `cabai_merah` memakai cabe besar BDSP saja; cabe keriting dikonversi dari kuintal ke ton dan disimpan terpisah (D-28).

Provinsi dibakukan ke 34 provinsi versi PIHPS. Sumber yang sudah memakai 38 provinsi dipetakan ke induknya: Papua Selatan, Papua Tengah, dan Papua Pegunungan ke Papua; Papua Barat Daya ke Papua Barat (D-17).

## Fase

| Fase | Isi | Output utama |
| --- | --- | --- |
| 1. Design | AS-IS process map rantai pasok, ERD core dataset, data flow pipeline, kerangka data dictionary. Diagram ditulis dalam Mermaid supaya ter-render di GitHub | `docs/01` sampai `docs/04` |
| 2. Extract | Menarik semua sumber ke `data/raw/` | `pipeline/extract/`, `data/raw/` |
| 3. Audit | Completeness report per sumber × provinsi × bulan, termasuk heatmap missing value dalam bentuk tabel | `pipeline/audit/reports/` |
| 4. Transform | Imputation dan integrasi sesuai aturan kualitas data | `data/final/`, `pipeline/transform/reports/` |
| 5. Validate | Hold-out validation untuk imputation, reconciliation total tahunan, cross-check angka bulanan PIHPS, spot-check acak terhadap sumber | `pipeline/validate/reports/` |
| 6. Analysis | Rencana analisis, uji H1-H6, skenario what-if, RTM final, rekomendasi | `analysis/`, `docs/05`, `docs/06` |
| 7. Cleanup | Merapikan dokumen, kode, dan README sebelum publikasi, lalu memastikan hasil tetap identik | README, dokumen ini |

Analisis, chart, dan model baru dimulai setelah core dataset lolos validasi di fase 5.

## Aturan kerja

- Setiap fase selesai dengan laporan dan review sebelum fase berikutnya dimulai.
- Kalau ada beberapa pilihan, saya menulis pilihan terbaik beserta alasannya, lalu mencatat keputusannya di decision log. Aturan keputusan untuk uji yang sensitif (misalnya H4 dan skenario) ditulis sebelum angkanya dihitung.
- Bahasa dokumen: Indonesia, dengan istilah teknis dalam bentuk yang lazim dipakai praktisi (price spike, lag, imputation, hold-out validation, core dataset).
- Git: satu branch per fase (`phase-N-nama`). Fase yang selesai di-merge ke `main`. Pekerjaan cuaca dikerjakan di branch `weather-package` lalu di-merge ke `phase-6-analysis` (D-56).
- Data raw tidak pernah diedit dan tetap disimpan di git tanpa LFS. Hasil Open-Meteo disimpan satu file per lokasi (D-31).
- Script extract resumable: hasil disimpan per potongan (per kuartal, per file, per lokasi), setiap file punya sidecar metadata (tanggal extraction, request, sha256), dan potongan yang sudah ada dan valid dilewati saat dijalankan ulang.
- Pipeline reproducible: `python -m pipeline.run` menjalankan extract sampai validate.

## Sumber data

| Sumber | Isi | Catatan teknis |
| --- | --- | --- |
| [PIHPS Nasional, Bank Indonesia](https://www.bi.go.id/hargapangan) | Harga eceran, pedagang besar, dan produsen, harian per provinsi | Endpoint JSON `GetGridDataKomoditas`, ditarik per kuartal karena request satu tahun sering timeout, berurutan dengan jeda. Rata-rata bulanan dihitung sendiri dari hari kerja; angka bulanan PIHPS hanya untuk cross-check (D-18) |
| [Open-Meteo Historical API](https://open-meteo.com/) | Curah hujan dan kelembapan harian, 1991-2026 | Titik = kabupaten sentra dengan produksi terbesar sampai kumulatif sekitar 80% produksi nasional per komoditas; titik berjarak < 10 km digabung (D-24). Mulai 1991 karena normal iklim memakai 1991-2020 (D-19). Batas gratis 10.000 call/hari, jadi extract berjalan beberapa hari |
| [NOAA ONI](https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt) | El Niño / La Niña | Tiap 3-month season dipetakan ke bulan tengahnya (DJF ke Januari) |
| [BDSP Kementan](https://bdsp2.pertanian.go.id/bdsp/id/lokasi) | Produksi dan luas panen tahunan per provinsi dan kabupaten, 2018-2025 | Form `POST /bdsp/id/lokasi/result`. Angka 2025 ditandai `is_preliminary` (D-29). Provinsi pemekaran Papua dijumlahkan ke induk (D-36) |
| [Buletin Konsumsi Pangan, Pusdatin Kementan](https://satudata.pertanian.go.id/) | Tabel prognosa produksi bulanan nasional; konsumsi per kapita Susenas dan jumlah penduduk untuk skenario | Hanya bulan berstatus realisasi SPH-BPS yang dipakai (D-23, D-42). Ekstraksi dengan `pdfplumber` |
| Kalender hari besar | Idulfitri, Iduladha, Natal-Tahun Baru, cuti bersama 2018-2026 | Disusun sendiri; kolom `source_level` official/secondary (D-38, D-46) |

Luas tanam bulanan dan pasokan harian Pasar Induk Kramat Jati tidak tersedia publik, jadi tidak masuk core dataset dan tidak diisi dari potongan angka di berita.

## Aturan kualitas data

Prinsipnya, imputation hanya dilakukan kalau ada anchor dari data nyata, dan variabel yang dipakai untuk imputation tidak boleh variabel yang nanti diuji hubungannya. Tanpa aturan kedua, hasilnya circular.

| Kondisi | Treatment |
| --- | --- |
| Missing days dalam satu bulan | Rata-rata dari hari tersedia, minimal 10 hari kerja; kurang dari itu = missing |
| Gap 1-6 bulan di tengah seri | Linear interpolation pada log price. Kalman dibatalkan karena di hold-out tidak lebih akurat dari linear (D-43) |
| Gap tengah lebih dari 6 bulan | Tetap NULL; seri tetap dipakai (D-35) |
| Missing di awal atau akhir seri | Tidak di-impute dan tidak diekstrapolasi. NTT keluar dari analisis harga produsen |
| Tier seri harga (Jan 2019 - Okt 2026) | `main`: bulan valid ≥ 80% dan gap tengah terpanjang ≤ 6 bulan. `descriptive`: 50-80% (atau gap tengah > 6), hanya untuk deskripsi dan sensitivity check. `excluded`: < 50%, tidak di-impute dan tidak dipakai di model. Ambang ada di `pipeline/rules.py` (D-35) |
| Produktivitas BDSP di luar 1-30 ton/ha | Flag `is_outlier`, nilai tidak diubah (D-37) |
| Cabe keriting persis sama dengan cabe besar | Flag `suspect_copy`, tanpa koreksi (D-39) |
| Produksi bulanan per provinsi | Tidak ada disagregasi bulanan (Chow-Lin dan Denton dibatalkan, D-42). Core bulanan memakai `production_annual_ton`, angka tahunan yang sama untuk 12 bulan; 2026 NULL |
| Produksi 2026 | Tidak diekstrapolasi; sensitivity check dengan dan tanpa 2026 |
| Cuaca per provinsi | Rata-rata berbobot produksi dari titik kabupaten sentra. Provinsi tanpa titik sentra: `weather_status = not_applicable` dengan nilai NULL, bukan missing (D-25). November 2026 `partial_month` (D-57) |
| Anomali hujan dan kelembapan | `rain_anomaly`: rata-rata berbobot produksi dari z-score per lokasi × bulan kalender, dari akar kuadrat hujan bulanan, baseline 1991-2020. Lokasi-bulan dengan \|z\| ≥ 3 atau hujan harian > 300 mm diberi flag `rain_is_extreme`, nilainya tidak diubah (D-58). `rh_anomaly` memakai cara yang sama dengan logit kelembapan relatif (D-59) |
| Variabel tanpa observed data | Tidak di-impute |

Setiap nilai punya kolom `is_imputed` dan `impute_method`. Metode imputation dipilih lewat hold-out validation (sebagian nilai observed di-mask, di-impute ulang, lalu MAPE dibandingkan); kalau tidak lebih akurat dari baseline linear, baseline yang dipakai (D-43). Uji H2 dan H4 selalu punya sensitivity check tanpa bulan imputasi (D-44). Harga produsen tidak pernah diisi dari harga pedagang besar.

## Aturan analisis

Rencana analisis ada di [05_analysis_plan.md](05_analysis_plan.md) dan keterlacakan di [RTM](06_requirements_traceability_matrix.md).

- Price spike: harga eceran bulanan ≥ 1,25 × median 12 bulan sebelumnya (trailing), dengan sensitivity 1,15 dan 1,35. Episode besar = spike provinsi ≥ 2 bulan berturut-turut. Spike nasional = spike serentak di ≥ 50% provinsi (D-48).
- Setiap laporan hipotesis memuat hasil utama dan effect size, keputusan terhadap aturan di rencana (didukung, tidak didukung, atau sebagian), sensitivity check, chart pendukung, temuan yang terbukti terpisah dari dugaan yang perlu verifikasi, dan satu paragraf "so what". Rekomendasi kebijakan dikumpulkan terpisah (D-53).
- Di skenario what-if, angka redaman dan biaya per alarm selalu diberi label asumsi; efektivitas intervensi tidak diklaim (D-64, D-65).
- Keterbatasan yang diterima tanpa verifikasi eksternal disebut di laporan saat relevan: frekuensi pembaruan harga produsen PIHPS (sekitar 22% minggu) serta cuti bersama 2020 dan Natal 2018, 2019, 2022 yang belum terverifikasi (D-56).
