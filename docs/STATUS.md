# Status proyek (per 20 Nov 2026)

Branch kerja: `phase-6-analysis` (di-push ke origin sampai `3cad150`). Paket cuaca dikerjakan di `weather-package` (D-56) dan sudah di-merge kembali ke `phase-6-analysis`. `phase-6-analysis` di-merge ke `main` setelah H1, H4, dan keputusan final H6. `main` berisi Fase 1-5 (sampai `02f8a56`).

## 0. Paket cuaca (selesai, menunggu tinjauan Fatan sebelum H1)

| Langkah | Status | Commit |
| --- | --- | --- |
| 4.1 Extract sisa lokasi | Selesai: 74 dari 74 lokasi valid | `430d0a2` |
| 4.2 Audit | Selesai: 74/74 valid, 0 hari kosong, 0 nilai di luar batas fisik, 2 hari hujan > 300 mm (ditandai). Laporan `pipeline/audit/reports/weather_audit.md` | `b973e1f` |
| 4.3 Transform dan integrasi | Selesai: `weather_features.py` (D-57); 6 kolom cuaca di `core_province_month` (`rain_total_mm`, `rain_anomaly_mm`, `rain_anomaly`, `rel_humidity_mean`, `weather_status`, `weather_n_points`); observed 3.074 sel (29 provinsi x komoditas), kosong 0; kolom lama tidak berubah | `bf9b7f9` |
| 4.4 Validate | Selesai: 53/53 cek lulus (7 cek cuaca baru); spot-check cuaca 8/8 cocok (5 sel vs raw harian, 3 lokasi x bulan vs Open-Meteo live) | `fbc180b` |
| Merge ke `phase-6-analysis` | Selesai (merge `--no-ff`, di-push) | merge commit "Merge weather-package" |

## 1. Yang sudah selesai

| Fase / hipotesis | Status | Commit |
| --- | --- | --- |
| Fase 1 Design | Selesai, di `main` | `bed84ca` |
| Fase 2 Extract | Selesai; cuaca 74 dari 74 lokasi (paket cuaca) | `4963713` (merge ke `main`) |
| Fase 3 Audit | Selesai; cuaca lewat paket cuaca | `69cb46c` |
| Fase 4 Transform | Selesai; cuaca lewat paket cuaca | `d11ac73` |
| Fase 5 Validate | Selesai; dengan cuaca 53/53 cek lulus | `02f8a56` |
| Fase 6 rencana, RTM, EDA | Disetujui (D-48) | `66b7b81` |
| Keputusan analisis, kolom jarak, koreksi geocoding Karangasem | Selesai (D-48 s/d D-51) | `9c17e12` |
| H2 rantai pasok | **Final: sebagian** | `1805c24` |
| H3 disparitas | **Tidak didukung (dibantah)** | `272b843` |
| H5 cobweb | **Tidak didukung** (rawit: arah positif, indikatif) | `272b843` |
| H6 hari besar | **Sementara: tidak didukung untuk "menambah kenaikan"**; final menunggu H1 | `272b843` |
| H1 cuaca | **Disetujui (D-59)**. Sebagian (rawit): kering -> harga produsen naik, lag 3; tidak didukung (merah); pola U tidak didukung. Lampiran eksploratif merah: indeks hujan nasional signifikan untuk harga pedagang besar nasional (lag 2), kelembapan tidak (D-60) | `883cc8d`, `07641c6`, (commit ini) |
| H4 early warning | Belum; menunggu review H1 | - |

Laporan hipotesis ada di `analysis/02_h2_report.md` sampai `analysis/06_h1_report.md`. Catatan untuk rekomendasi akhir ada di `analysis/notes_recommendations.md`.

## 2. Keputusan terakhir

- **D-52**: sensitivity periode spike H2 memakai spike harga pedagang besar. Uji lead-lag di provinsi dengan harga produsen sering berubah tidak bisa dijalankan (0 provinsi >= 50%).
- **D-53**: laporan hipotesis memisahkan temuan terbukti dari dugaan; rekomendasi kebijakan dikumpulkan di `analysis/notes_recommendations.md`.
- **D-54**: penyesuaian saat menjalankan H3, H5, H6 (penanda guncangan pedagang besar di H3, dummy Natal tidak bisa diidentifikasi di H6, event study dan FE tahun sebagai pemeriksaan pendukung, label indikatif H5).
- **D-55**: sinyal H4 = harga pedagang besar, cuaca, ONI (plus `months_to_idulfitri`); harga produsen tidak dipakai.

- **D-56**: empat hal terbuka di bagian 3 diputuskan.
- **D-57**: definisi variabel cuaca (November 2026 `partial_month`; poin 2 diganti D-58).
- **D-59**: H1 disetujui; uji eksploratif merah dan kriterianya; lag H4 (rawit lag 2-3; merah hanya kalau sinyal konsisten, lag nested).
- **D-60**: indeks hujan nasional masuk H4 merah (kriteria (ii) D-59); kelembapan tidak.
- **D-58**: ketentuan H1: anomali = rata-rata berbobot z-score per lokasi dari akar kuadrat hujan (baseline 1991-2020), flag `rain_is_extreme`, sensitivity wajib (a)-(d), pola U hanya kalau bertahan di (a) dan (b).

Rincian lengkap ada di `docs/decision_log.md` (D-01 s/d D-60).

## 3. Yang belum diputuskan

Tidak ada. Empat hal terbuka sebelumnya diputuskan di D-56: branch `weather-package` dari `phase-6-analysis`; merge ke `main` setelah H1, H4, dan keputusan final H6; teks H5 di charter sudah diganti ke versi tahunan (D-27); verifikasi eksternal tidak dikerjakan, dicatat sebagai keterbatasan data (frekuensi pembaruan harga produsen PIHPS; cuti bersama 2020 dan Natal 2018, 2019, 2022).

## 4. Langkah berikutnya (urut)

Semua perintah dijalankan dari folder repo.

### 4.1-4.4 Paket cuaca: selesai

Extract, audit, transform, dan validate cuaca sudah selesai (lihat bagian 0). Laporan:
- `pipeline/audit/reports/weather_audit.md`
- `pipeline/transform/reports/transform_report.md` bagian 6
- `pipeline/validate/reports/validation_report.md`

Catatan untuk H1: hujan bulanan ekstrem (misalnya Enrekang Juli 2020, 2.228 mm, +4,1 SD) dibiarkan apa adanya. Data Open-Meteo adalah reanalysis, jadi sensitivity H1 sebaiknya memeriksa pengaruh bulan ekstrem.

### 4.5 H1: selesai, menunggu review

Laporan `analysis/06_h1_report.md` (format D-53, ketentuan D-58). Ringkasan:
- rawit: musim lebih kering dari normal -> harga produsen naik sekitar 3 bulan kemudian (+12,9% untuk anomali -1 selama 4 bulan); lebih basah -> harga turun; tahan di sensitivity (a)-(d) dan leave-one-out;
- merah: tidak ada hubungan signifikan;
- pola U tidak didukung untuk keduanya; jalur produksi tahunan tidak terdeteksi;
- lag terkuat: rawit lag 3 (harga pedagang besar rawit: lag 2); merah tidak ada lag signifikan.

Yang perlu diputuskan Fatan saat review: lag cuaca untuk sinyal H4 (usulan: rawit lag 2-3, merah lag 1-4 dicoba di backtest tanpa prioritas).

### 4.6 H4 (early warning), setelah review H1

Buat `analysis/h4_early_warning.py` sesuai rencana bagian 8 dan D-55:
- target: onset episode besar t+1/t+2;
- sinyal: harga pedagang besar, `rain_anomaly`, ONI, `months_to_idulfitri`;
- rolling-origin backtest 2023-2026;
- berhasil hanya jika mengalahkan baseline yang lebih kuat (musiman naif atau "harga naik bulan lalu").

```powershell
python -m analysis.h4_early_warning
```

Laporan ke `analysis/07_h4_report.md`.

### 4.7 Keputusan final H6

Jalankan ulang `analysis/h6_holidays.py` dengan `rain_anomaly` sebagai kontrol tambahan (provinsi bertitik sentra). Bandingkan efek bulan dan jendela Idulfitri (persen) dengan efek 1 SD anomali hujan dari H1. Perbarui `analysis/05_h6_report.md` dengan keputusan final.

```powershell
python -m analysis.h6_holidays
```

### 4.8 Setelah semua hipotesis

Susun Requirements Traceability Matrix final dan rekomendasi akhir dari `analysis/notes_recommendations.md`. Setelah disetujui, merge `phase-6-analysis` ke `main`.
