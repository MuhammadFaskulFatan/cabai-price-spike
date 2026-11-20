# Audit cuaca (Open-Meteo)

Lokasi cuaca (anchor) di `sentra_points.csv`: 74; file valid: 74; belum ada atau tidak valid: 0. Provinsi bertitik sentra: 18 (cabai merah 14, cabai rawit 15).

## 1. Kelengkapan dan nilai per lokasi

- Rentang data: mulai 1991-01-01; tanggal akhir 2026-11-14 s/d 2026-11-15 (bergantung tanggal extraction; arsip tertinggal sekitar 5 hari).
- Hari kosong: hujan 0, kelembapan 0 dari 969,572 lokasi-hari.
- Hari tidak sesuai rentang (hari < hari seharusnya): 0 lokasi.
- Hujan negatif: 0; kelembapan di luar 0-100: 0.
- Hujan harian > 300 mm (ditandai, tidak diubah): 2 lokasi-hari; maksimum 539.9 mm di Kab. Aceh Besar. Hujan harian di atas 300 mm jarang tetapi mungkin di Indonesia, jadi tidak dianggap error.
- Lokasi dengan masalah di atas: 0.

Rincian per lokasi ada di `weather_locations.csv`.

## 2. File raw yang tidak dipakai

`-6.4912_106.8793.json`. Ini lokasi Sentul (-6,49; 106,88) hasil geocoding salah untuk Kab. Karang Asem; tetap di raw, tidak dipakai (D-51).

## 3. Kelengkapan per provinsi x tahun (persen lokasi-hari terisi, 2018-2026)

Provinsi tanpa titik sentra tidak muncul (cuaca `not_applicable`, D-25). Tahun 2026 di bawah 100% hanya karena November 2026 baru terisi sampai tanggal akhir file (bulan parsial).

| provinsi | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Aceh | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 95.3 |
| Sumatera Utara | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 95.3 |
| Sumatera Barat | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 95.2 |
| Jambi | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 95.2 |
| Bengkulu | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 95.2 |
| Sumatera Selatan | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 95.5 |
| Lampung | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 95.5 |
| Jawa Barat | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 95.2 |
| Jawa Tengah | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 95.2 |
| DI Yogyakarta | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 95.2 |
| Jawa Timur | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 95.2 |
| Bali | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 95.3 |
| Nusa Tenggara Barat | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 95.3 |
| Kalimantan Selatan | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 95.5 |
| Gorontalo | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 95.5 |
| Sulawesi Selatan | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 95.2 |
| Sulawesi Tengah | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 95.2 |
| Sulawesi Utara | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 95.5 |
