# Harga Cabai Melonjak di Tengah Surplus Produksi

Kalau produksi cabai nasional cukup, kenapa harga tetap melonjak di banyak daerah?

Project ini menjawabnya dari data publik 2019-2026 untuk cabai merah dan cabai rawit di 34 provinsi, dengan fokus pada empat hal: driver price spike, level supply chain tempat lonjakan dimulai, alasan daerah tertentu tetap mahal, dan kemungkinan early warning.

Ini portfolio project: dari problem framing sampai findings, dengan setiap langkah bisa ditelusuri ke data dan kode di repository ini.

## Status

| Fase | Isi | Status |
| --- | --- | --- |
| 1 | Design (`docs/`) | Selesai |
| 2 | Extract | Berjalan (tes koneksi) |
| 3 | Audit completeness | Belum |
| 4 | Transform dan integrasi | Belum |
| 5 | Validate | Belum |
| Setelahnya | Analisis dan findings | Belum; baru mulai setelah core dataset lolos validasi |

## Dokumen

- [Project Charter & Requirements](docs/00_project_charter.md)
- [AS-IS process map rantai pasok](docs/01_as_is_process_map.md)
- [ERD core dataset](docs/02_erd_core_dataset.md)
- [Data flow diagram pipeline](docs/03_data_flow.md)
- [Data dictionary](docs/04_data_dictionary.md)
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
