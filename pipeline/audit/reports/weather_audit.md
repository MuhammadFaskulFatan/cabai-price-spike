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

## 4. Bulan ekstrem per lokasi (D-58)

Aturan: |z| >= 3 untuk akar kuadrat hujan bulanan terhadap rata-rata dan simpangan baku bulan kalender 1991-2020 di lokasi itu, atau ada hari dengan hujan > 300 mm. Di baseline, 0.36% lokasi-bulan tertandai (distribusi normal: 0,27% untuk |z| >= 3).

- 2018-2026: 112 dari 7,918 lokasi-bulan (87 basah, 24 kering, 1 hanya karena hujan harian).
- Nilai tidak diubah. Bulan provinsi x komoditas yang memuat lokasi tertandai diberi `rain_is_extreme = TRUE` di core; sensitivity (b) H1 mengeluarkannya.
- Daftar lengkap di `weather_extreme_months.csv`. Lima belas terbesar menurut |z|:

| anchor_id | kabupaten | provinsi | bulan | hujan_mm | hujan_harian_maks_mm | z_akar | z_biasa | sebab |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 3512 | Kab. Situbondo | Jawa Timur | 2022-08 | 18.4 | 11.4 | 5.5 | 14.7 | z |
| 3512 | Kab. Situbondo | Jawa Timur | 2025-08 | 16.2 | 6.4 | 5.1 | 12.9 | z |
| 3511 | Kab. Bondowoso | Jawa Timur | 2025-02 | 150.4 | 25.3 | -5.1 | -4.1 | z |
| 1602 | Kab. Ogan Komering Ilir | Sumatera Selatan | 2024-01 | 574.6 | 45.7 | 5.0 | 6.2 | z |
| 1106 | Kab. Aceh Tengah | Aceh | 2025-11 | 714.8 | 234.1 | 4.8 | 5.9 | z |
| 3513 | Kab. Probolinggo | Jawa Timur | 2022-08 | 71.3 | 29.4 | 4.8 | 10.7 | z |
| 3329 | Kab. Brebes | Jawa Tengah | 2023-12 | 84.2 | 18.1 | -4.8 | -3.7 | z |
| 7316 | Kab. Enrekang | Sulawesi Selatan | 2025-11 | 97.9 | 22.4 | -4.7 | -3.3 | z |
| 3529 | Kab. Sumenep | Jawa Timur | 2022-08 | 47.5 | 20.1 | 4.5 | 7.7 | z |
| 1219 | Kab. Batubara | Sumatera Utara | 2022-06 | 457.2 | 41.5 | 4.4 | 5.4 | z |
| 7105 | Kab. Minahasa Selatan | Sulawesi Utara | 2021-01 | 667.7 | 170.3 | 4.3 | 5.8 | z |
| 6306 | Kab. Hulu Sungai Selatan | Kalimantan Selatan | 2021-11 | 572.4 | 54.4 | 4.3 | 5.2 | z |
| 1108 | Kab. Aceh Besar | Aceh | 2020-05 | 997.1 | 539.9 | 4.3 | 4.8 | z dan harian |
| 1312 | Kab. Pasaman Barat | Sumatera Barat | 2022-06 | 545.5 | 68.2 | 4.2 | 5.2 | z |
| 1708 | Kab. Kepahiang | Bengkulu | 2022-06 | 510.0 | 223.7 | 4.2 | 5.8 | z |

Enrekang Juli 2020 (2,228 mm, z +3.2) termasuk yang tertandai.
