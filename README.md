# Harga Cabai Melonjak di Tengah Surplus Produksi

Kalau produksi cabai nasional cukup, kenapa harga tetap melonjak di banyak daerah?

Project ini menjawabnya dari data publik 2019-2026 untuk cabai merah dan cabai rawit di 34 provinsi, dengan fokus pada empat hal: driver price spike, level supply chain tempat lonjakan dimulai, alasan daerah tertentu tetap mahal, dan kemungkinan early warning.

Ini portfolio project: dari problem framing sampai findings, dengan setiap langkah bisa ditelusuri ke data dan kode di repository ini.

## Status

| Fase | Isi | Status |
| --- | --- | --- |
| 1 | Design (`docs/`) | Selesai |
| 2 | Extract | Selesai kecuali cuaca (Open-Meteo berjalan, lanjut besok) |
| 3 | Audit completeness | Selesai kecuali cuaca (menunggu data Open-Meteo lengkap) |
| 4 | Transform dan integrasi | Selesai kecuali cuaca |
| 5 | Validate | Selesai kecuali cuaca |
| 6 | Analisis | Perencanaan: rencana, RTM, dan EDA deskriptif selesai; uji hipotesis menunggu persetujuan |

## Dokumen

- [Project Charter & Requirements](docs/00_project_charter.md)
- [AS-IS process map rantai pasok](docs/01_as_is_process_map.md)
- [ERD core dataset](docs/02_erd_core_dataset.md)
- [Data flow diagram pipeline](docs/03_data_flow.md)
- [Data dictionary](docs/04_data_dictionary.md)
- [Rencana analisis](docs/05_analysis_plan.md)
- [Requirements traceability matrix](docs/06_requirements_traceability_matrix.md)
- [EDA deskriptif](analysis/01_eda_report.md)
- [Decision log](docs/decision_log.md)

## Struktur repo

```
.
├── docs/            # artefak BA
├── pipeline/
│   ├── extract/     # satu script per sumber
│   ├── audit/       # laporan completeness
│   ├── transform/   # imputation, temporal disaggregation, integrasi
│   └── validate/
├── data/
│   ├── raw/         # hasil extract apa adanya, tidak pernah diedit
│   ├── interim/
│   └── final/       # core dataset
└── analysis/        # dipakai setelah core dataset tervalidasi
```

## Menjalankan pipeline

Belum tersedia; dibangun di fase 2-5. Targetnya satu command dari extract sampai final:

```
python -m pipeline.run
```

## Sumber data

PIHPS Nasional (Bank Indonesia), Open-Meteo Historical API, NOAA ONI, BDSP Kementan, Buletin Konsumsi Pangan (Pusdatin Kementan), dan kalender hari besar yang disusun sendiri. Tanggal extraction dicatat di metadata setiap file raw.
