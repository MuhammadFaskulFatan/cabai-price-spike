# Status proyek (per 20 Nov 2026)

Branch kerja: `weather-package` (dibuat dari `phase-6-analysis`, D-56). Setelah paket cuaca lolos validasi, branch ini di-merge kembali ke `phase-6-analysis`. `phase-6-analysis` di-merge ke `main` setelah H1, H4, dan keputusan final H6. `main` berisi Fase 1-5 (sampai `02f8a56`).

## 0. Paket cuaca (berjalan)

| Langkah | Status | Commit |
| --- | --- | --- |
| 4.1 Extract sisa lokasi | Selesai: 74 dari 74 lokasi valid | `430d0a2` |
| 4.2 Audit | Selesai: 74/74 valid, 0 hari kosong, 0 nilai di luar batas fisik, 2 hari hujan > 300 mm (ditandai). Laporan `pipeline/audit/reports/weather_audit.md` | (commit ini) |
| 4.3 Transform dan integrasi | Berikutnya | - |
| 4.4 Validate | Belum | - |
| Merge ke `phase-6-analysis` | Belum | - |

## 1. Yang sudah selesai

| Fase / hipotesis | Status | Commit |
| --- | --- | --- |
| Fase 1 Design | Selesai, di `main` | `bed84ca` |
| Fase 2 Extract | Selesai; cuaca 74 dari 74 lokasi (paket cuaca) | `4963713` (merge ke `main`) |
| Fase 3 Audit | Selesai; cuaca lewat paket cuaca | `69cb46c` |
| Fase 4 Transform | Selesai kecuali cuaca | `d11ac73` |
| Fase 5 Validate | Selesai kecuali cuaca; 46/46 cek lulus | `02f8a56` |
| Fase 6 rencana, RTM, EDA | Disetujui (D-48) | `66b7b81` |
| Keputusan analisis, kolom jarak, koreksi geocoding Karangasem | Selesai (D-48 s/d D-51) | `9c17e12` |
| H2 rantai pasok | **Final: sebagian** | `1805c24` |
| H3 disparitas | **Tidak didukung (dibantah)** | `272b843` |
| H5 cobweb | **Tidak didukung** (rawit: arah positif, indikatif) | `272b843` |
| H6 hari besar | **Sementara: tidak didukung untuk "menambah kenaikan"**; final menunggu H1 | `272b843` |
| H1 cuaca | Belum; menunggu paket cuaca | - |
| H4 early warning | Belum; menunggu paket cuaca | - |

Laporan hipotesis ada di `analysis/02_h2_report.md` sampai `analysis/05_h6_report.md`. Catatan untuk rekomendasi akhir ada di `analysis/notes_recommendations.md`.

## 2. Keputusan terakhir

- **D-52**: sensitivity periode spike H2 memakai spike harga pedagang besar. Uji lead-lag di provinsi dengan harga produsen sering berubah tidak bisa dijalankan (0 provinsi >= 50%).
- **D-53**: laporan hipotesis memisahkan temuan terbukti dari dugaan; rekomendasi kebijakan dikumpulkan di `analysis/notes_recommendations.md`.
- **D-54**: penyesuaian saat menjalankan H3, H5, H6 (penanda guncangan pedagang besar di H3, dummy Natal tidak bisa diidentifikasi di H6, event study dan FE tahun sebagai pemeriksaan pendukung, label indikatif H5).
- **D-55**: sinyal H4 = harga pedagang besar, cuaca, ONI (plus `months_to_idulfitri`); harga produsen tidak dipakai.

- **D-56**: empat hal terbuka di bagian 3 diputuskan.
- **D-57**: definisi variabel cuaca (anomali terstandar terhadap normal 1991-2020, November 2026 `partial_month`).

Rincian lengkap ada di `docs/decision_log.md` (D-01 s/d D-57).

## 3. Yang belum diputuskan

Tidak ada. Empat hal terbuka sebelumnya diputuskan di D-56: branch `weather-package` dari `phase-6-analysis`; merge ke `main` setelah H1, H4, dan keputusan final H6; teks H5 di charter sudah diganti ke versi tahunan (D-27); verifikasi eksternal tidak dikerjakan, dicatat sebagai keterbatasan data (frekuensi pembaruan harga produsen PIHPS; cuti bersama 2020 dan Natal 2018, 2019, 2022).

## 4. Langkah berikutnya (urut)

Semua perintah dijalankan dari folder repo.

### 4.1 Paket cuaca: sisa extract (24 lokasi)

```powershell
git switch -c weather-package
```

```powershell
python -m pipeline.extract.open_meteo --only weather
```

- Kebutuhannya sekitar 24 x 187 = 4.500 call API, di bawah kuota harian 10.000. Batas per jam (5.000) bisa memaksa script menunggu sampai satu jam.
- Script resumable dan berhenti sendiri kalau kuota harian habis. Kalau berhenti, jalankan ulang perintah yang sama.
- Termasuk lokasi Karangasem yang benar (-8,36; 115,55). File raw lokasi Sentul yang salah (`-6.4912_106.8793.json`) tetap di raw dan tidak dipakai (D-51).
- Setelah selesai, cek bahwa 74 dari 74 lokasi valid, lalu commit `data/raw/open_meteo`.

### 4.2 Paket cuaca: audit

Belum ada modulnya. Yang perlu dibuat adalah `pipeline/audit/weather_audit.py`, lalu didaftarkan di `pipeline/audit/completeness.py`. Isinya:
- kelengkapan harian per lokasi 1991-2026 (hari kosong, nilai negatif atau ekstrem);
- cek bahwa setiap `anchor_id` di `sentra_points.csv` punya file valid;
- daftar file cuaca yang tidak dipakai (Sentul).

```powershell
python -m pipeline.audit.completeness --only weather
```

### 4.3 Paket cuaca: transform dan integrasi

Belum ada modulnya. Yang perlu dibuat adalah `pipeline/transform/weather_features.py`, lalu didaftarkan di `TRANSFORM_STEPS` sebelum `integrate`. Isinya:
- hujan bulanan per lokasi (jumlah) dan kelembapan rata-rata;
- normal per bulan kalender 1991-2020 (D-19) dan `rain_anomaly`;
- rata-rata berbobot produksi per provinsi x komoditas (bobot dari `mean_production_ton_2019_2025`);
- `weather_status = observed` untuk provinsi bertitik, `not_applicable` untuk lainnya (D-25).

Setelah itu tambahkan `rain_total_mm`, `rain_anomaly`, `rel_humidity_mean`, dan `weather_status` ke `integrate.py`.

```powershell
python -m pipeline.run --stage transform
```

### 4.4 Paket cuaca: validate

Tambahkan cek cuaca di `pipeline/validate/checks_core.py`:
- `not_applicable` hanya di provinsi tanpa titik;
- tidak ada `NULL` cuaca tanpa alasan;
- spot-check beberapa lokasi ke Open-Meteo live.

```powershell
python -m pipeline.validate.report
```

Setelah lolos: commit, merge `weather-package` ke `phase-6-analysis`, lalu laporkan sebelum H1.

### 4.5 H1 (cuaca di sentra -> harga)

Buat `analysis/h1_weather.py` sesuai `docs/05_analysis_plan.md` bagian 7. Ringkasnya:
- panel provinsi bertitik sentra;
- `rain_anomaly` dan kuadratnya lag 1-4;
- **spesifikasi 1**: FE provinsi + month-of-year + ONI;
- **spesifikasi 2**: FE tahun-bulan (efek ONI hanya terbaca di spesifikasi 1, D-48);
- outcome utama harga produsen, dengan catatan H2 soal frekuensi pembaruannya, plus harga pedagang besar sebagai sensitivity;
- jalur produksi di grain tahunan;
- sensitivity sesuai rencana, termasuk D-44.

```powershell
python -m analysis.h1_weather
```

Laporan ke `analysis/06_h1_report.md` dengan format D-53.

### 4.6 H4 (early warning)

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
