# Harga Cabai Melonjak di Tengah Surplus Produksi

Kalau produksi cabai nasional cukup, kenapa harga tetap melonjak di banyak daerah?

Proyek ini menjawab pertanyaan itu dari data publik 2019-2026 untuk cabai merah dan cabai rawit di 34 provinsi. Ini portfolio project Business Analyst / Data Analyst yang dikerjakan end-to-end: problem framing, requirements, desain, pipeline data, validasi, uji hipotesis, skenario, dan rekomendasi. Setiap temuan bisa ditelusuri ke data, kode, dan keputusan di repository ini.

## Temuan utama

| Pertanyaan | Jawaban singkat | Laporan |
| --- | --- | --- |
| Apakah lonjakan terjadi karena satu-dua daerah kekurangan? | Tidak. Lonjakan terjadi serentak secara nasional, dan disparitas harga antarprovinsi justru menyempit saat guncangan. Daerah yang jauh dari sentra mahal secara struktural | [H3](analysis/03_h3_report.md) |
| Apakah cuaca di sentra menggerakkan harga? | Ya untuk musim yang lebih kering dari normal. Harga produsen cabai rawit naik sekitar 13% tiga bulan setelah kemarau sedang selama empat bulan; harga eceran di provinsi sentra naik sekitar 6%. Hujan berlebih tidak menaikkan harga, dan pola U tidak terbukti | [H1](analysis/06_h1_report.md), [H6](analysis/05_h6_report.md) |
| Apakah Lebaran pemicunya? | Bulan Idulfitri tidak lebih mahal setelah musim, pasokan, dan cuaca dikontrol. Cabai merah cenderung lebih mahal sebulan sebelumnya | [H6](analysis/05_h6_report.md) |
| Di level rantai pasok mana lonjakan dimulai? | Harga eceran bergerak sekitar satu minggu lebih dulu dari pedagang besar, dan transmisinya simetris. Peran petani belum terbaca karena harga produsen PIHPS hanya berubah di sekitar 22% minggu | [H2](analysis/02_h2_report.md) |
| Apakah harga tinggi mendorong petani menanam lebih banyak (cobweb)? | Tidak terdeteksi di data tahunan | [H5](analysis/04_h5_report.md) |
| Bisakah lonjakan dideteksi lebih awal? | Untuk cabai merah, sebagian: 59% episode besar mendapat peringatan minimal sebulan sebelumnya, alarmnya 1,8 kali lebih tepat dari acak, dengan false alarm lebih sedikit dari baseline. Untuk cabai rawit, belum | [H4](analysis/07_h4_report.md) |
| Berapa biayanya bagi rumah tangga? | Sekitar Rp 5,5 triliun (merah) dan Rp 10,3 triliun (rawit) di atas harga normal selama bulan lonjakan Jan 2023 - Okt 2026, hanya dari konsumsi rumah tangga | [Skenario what-if](analysis/08_scenario_report.md) |

Rekomendasi akhir (R1-R9) dan usulan yang sengaja ditahan ada di [rekomendasi akhir](analysis/09_final_recommendations.md). Setiap rekomendasi terlacak ke hipotesis atau skenario di [requirements traceability matrix](docs/06_requirements_traceability_matrix.md).

## Dokumen

Requirements dan desain:
- [Project charter](docs/00_project_charter.md) dan [alur kerja proyek](docs/00_project_workflow.md)
- [AS-IS process map rantai pasok](docs/01_as_is_process_map.md), [ERD core dataset](docs/02_erd_core_dataset.md), [data flow pipeline](docs/03_data_flow.md), [data dictionary](docs/04_data_dictionary.md)
- [Rencana analisis](docs/05_analysis_plan.md) dan [requirements traceability matrix](docs/06_requirements_traceability_matrix.md)
- [Decision log](docs/decision_log.md) (D-01 sampai D-65) dan [status proyek](docs/STATUS.md)

Data dan validasi:
- Laporan audit completeness di `pipeline/audit/reports/`
- Laporan transform di `pipeline/transform/reports/`
- [Laporan validasi](pipeline/validate/reports/validation_report.md): cek struktur core dataset, reconciliation tahunan, cross-check angka bulanan PIHPS, spot-check acak terhadap sumber, dan hold-out validation imputation

Analisis: [EDA](analysis/01_eda_report.md), laporan H1-H6, skenario, dan rekomendasi di `analysis/`; chart di `analysis/figures/`, tabel di `analysis/tables/`.

## Struktur repo

```
.
├── docs/            # charter, alur kerja, process map, ERD, data flow, data dictionary, rencana analisis, RTM, decision log
├── pipeline/
│   ├── extract/     # satu script per sumber, resumable, metadata extraction per file
│   ├── audit/       # laporan completeness per sumber x provinsi x bulan
│   ├── transform/   # agregasi bulanan, imputation, fitur cuaca dan kalender, integrasi core dataset
│   └── validate/    # cek struktur, reconciliation, cross-check, spot-check, hold-out
├── data/
│   ├── raw/         # hasil extract apa adanya, tidak pernah diedit
│   ├── interim/     # hasil antara (parquet tidak disimpan di git)
│   └── final/       # core dataset dan tabel dimensi
└── analysis/        # script uji hipotesis, laporan, chart, tabel
```

## Menjalankan

Diuji dengan Python 3.14.

```
pip install -r requirements.txt
```

Seluruh pipeline, dari extract sampai validate:

```
python -m pipeline.run
```

Per tahap: `python -m pipeline.run --stage extract` (atau `audit`, `transform`, `validate`). Data raw sudah ada di repository, sehingga tahap extract hanya menarik potongan yang belum ada. `--refresh` menarik ulang tanpa menimpa file raw lama. Extract Open-Meteo dibatasi kuota harian API dan bisa berjalan beberapa hari; script-nya resumable. Tahap transform termasuk hold-out validation imputation dan butuh sekitar 15 menit. Tahap validate mengirim beberapa request live ke sumber untuk spot-check (lewati dengan `python -m pipeline.validate.report --skip-live`).

Analisis dijalankan per script setelah core dataset tersedia di `data/final/`:

```
python -m analysis.eda
python -m analysis.h2_transmission
python -m analysis.h2_followup
python -m analysis.h3_disparity
python -m analysis.h5_cobweb
python -m analysis.h6_holidays
python -m analysis.h1_weather
python -m analysis.h1_exploratory_merah
python -m analysis.h4_early_warning
python -m analysis.scenario_whatif
```

## Sumber data

| Sumber | Isi | Periode |
| --- | --- | --- |
| [PIHPS Nasional, Bank Indonesia](https://www.bi.go.id/hargapangan) | Harga eceran, pedagang besar, dan produsen harian per provinsi; data mingguan dan bulanan untuk lead-lag dan cross-check | 2018 - Nov 2026 |
| [Open-Meteo Historical API](https://open-meteo.com/) | Curah hujan dan kelembapan harian di 74 lokasi kabupaten sentra (reanalysis, sekitar 25 km) | 1991 - Nov 2026 |
| [NOAA Oceanic Niño Index](https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt) | El Niño / La Niña | 2018 - ASO 2026 |
| [BDSP Kementan](https://bdsp2.pertanian.go.id/bdsp/id/lokasi) | Produksi dan luas panen tahunan per provinsi dan kabupaten | 2018 - 2025 |
| [Buletin Konsumsi Pangan, Pusdatin Kementan](https://satudata.pertanian.go.id/) | Produksi bulanan nasional (realisasi SPH-BPS), konsumsi per kapita Susenas, jumlah penduduk BPS | Edisi 2020 - 2026 |
| Kalender hari besar | Idulfitri, Iduladha, Natal-Tahun Baru, cuti bersama; disusun sendiri dengan tingkat verifikasi per tanggal | 2018 - 2026 |

Tanggal extraction, request, dan hash setiap file raw dicatat di file metadata di sebelahnya (`*.meta.json`).

## Keterbatasan utama

Hasil analisis adalah asosiasi yang konsisten, bukan bukti kausal. Cuaca berasal dari reanalysis, bukan stasiun. Produksi hanya tersedia tahunan. Harga produsen PIHPS jarang diperbarui. Angka redaman di skenario adalah asumsi, karena data intervensi tidak tersedia. Rincian per analisis ada di bagian keterbatasan setiap laporan.
