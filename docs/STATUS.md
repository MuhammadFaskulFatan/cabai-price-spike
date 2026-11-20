# Status proyek (per 20 Nov 2026)

Branch kerja: `phase-6-analysis`. Di-merge ke `main` (fast-forward) dan di-push di `9d1a572` setelah H1, H4 final, dan H6 final (D-56, D-63). Langkah 4.7b dan 4.8 (disetujui, D-65) di-merge ke `main` dan di-push.

## 0. Paket cuaca (selesai)

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
| Fase 5 Validate | Selesai; dengan cuaca 55/55 cek lulus (termasuk anomali per lokasi D-58 dan kelembapan D-59) | `02f8a56` |
| Fase 6 rencana, RTM, EDA | Disetujui (D-48) | `66b7b81` |
| Keputusan analisis, kolom jarak, koreksi geocoding Karangasem | Selesai (D-48 s/d D-51) | `9c17e12` |
| H2 rantai pasok | **Final: sebagian** | `1805c24` |
| H3 disparitas | **Tidak didukung (dibantah)**; disetujui (D-63) | `272b843` |
| H5 cobweb | **Tidak didukung** (rawit: arah positif, indikatif); disetujui (D-63) | `272b843` |
| H6 hari besar | **Final: sebagian**, disetujui (D-63). Bukan pemicu utama (didukung: efek cuaca kering sekitar +6% harga eceran, bulan Idulfitri tidak terdeteksi); menambah kenaikan (tidak didukung) (D-62) | `d449b9f` |
| H1 cuaca | **Disetujui (D-59)**. Sebagian (rawit): kering -> harga produsen naik, lag 3; tidak didukung (merah); pola U tidak didukung. Lampiran eksploratif merah: indeks hujan nasional signifikan untuk harga pedagang besar nasional (lag 2), kelembapan tidak (D-60) | `883cc8d`, `07641c6`, `ca9769f` |
| H4 early warning | **Final, disetujui (D-63, D-64): merah sebagian** (lift 1,81, PR-AUC 0,178 vs 0,087 charter; FAR 27% vs 42% pada recall setara; US1 59%). **Rawit tidak didukung** (lift 1,18, interval 0,92-1,50 mencakup 1). Cuaca membantu rawit, tidak cukup | `f0405a4`, `5c53e8a`, `9d1a572` |
| 4.7b Skenario what-if | Selesai: biaya lonjakan rumah tangga Jan 2023 - Okt 2026 merah Rp 5,53 T, rawit Rp 10,31 T; skenario redaman (asumsi) dan break-even untuk merah (D-64) | `a5b5827` (D-64), `7cd59b4` |
| 4.8 RTM final dan rekomendasi akhir | Selesai: 9 rekomendasi (R1-R9) dan 6 usulan ditahan, masing-masing dilacak ke hipotesis/skenario di RTM bagian 4; `analysis/09_final_recommendations.md` | `c653ba5`, D-65 (commit ini) |

Laporan hipotesis ada di `analysis/02_h2_report.md` sampai `analysis/07_h4_report.md`. Catatan untuk rekomendasi akhir ada di `analysis/notes_recommendations.md`.

## 2. Keputusan terakhir

- D-52: sensitivity periode spike H2 memakai spike harga pedagang besar. Uji lead-lag di provinsi dengan harga produsen sering berubah tidak bisa dijalankan (0 provinsi >= 50%).
- D-53: laporan hipotesis memisahkan temuan terbukti dari dugaan; rekomendasi kebijakan dikumpulkan di `analysis/notes_recommendations.md`.
- D-54: penyesuaian saat menjalankan H3, H5, H6 (penanda guncangan pedagang besar di H3, dummy Natal tidak bisa diidentifikasi di H6, event study dan FE tahun sebagai pemeriksaan pendukung, label indikatif H5).
- D-55: sinyal H4 = harga pedagang besar, cuaca, ONI (plus `months_to_idulfitri`); harga produsen tidak dipakai.

- D-56: empat hal terbuka di bagian 3 diputuskan.
- D-57: definisi variabel cuaca (November 2026 `partial_month`; poin 2 diganti D-58).
- D-59: H1 disetujui; uji eksploratif merah dan kriterianya; lag H4 (rawit lag 2-3; merah hanya kalau sinyal konsisten, lag nested).
- D-65: 4.7b dan 4.8 disetujui; break-even menjadi rentang biaya per alarm palsu Rp 100 juta - 1 miliar (tanpa patokan resmi).
- D-64: H4 final disetujui; ambang alarm rawit tidak diubah (future work); desain skenario what-if 4.7b.
- D-63: H3, H5, H6 final, eksploratif, D-59 s/d D-62 disetujui; aturan final H4 (lift dan PR-AUC) ditulis sebelum dihitung.
- D-62: keputusan final H6 (kontrol cuaca, perbandingan di model yang sama, label sebagian).
- D-61: rincian dan aturan keputusan H4 (ditulis sebelum backtest).
- D-60: indeks hujan nasional masuk H4 merah (kriteria (ii) D-59); kelembapan tidak.
- D-58: ketentuan H1: anomali = rata-rata berbobot z-score per lokasi dari akar kuadrat hujan (baseline 1991-2020), flag `rain_is_extreme`, sensitivity wajib (a)-(d), pola U hanya kalau bertahan di (a) dan (b).

Rincian lengkap ada di `docs/decision_log.md` (D-01 s/d D-65).

## 3. Yang belum diputuskan

Tidak ada untuk Fase 6. Berikutnya Fase 7 (pre-publish cleanup) di branch `phase-7-cleanup`.

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

Yang perlu diputuskan saat review: lag cuaca untuk sinyal H4 (usulan: rawit lag 2-3, merah lag 1-4 dicoba di backtest tanpa prioritas).

### 4.6 H4: final

Laporan `analysis/07_h4_report.md` (D-61, D-63). Merah sebagian, rawit tidak didukung.

### 4.7 Keputusan final H6: selesai

Laporan `analysis/05_h6_report.md` diperbarui (D-62).

### 4.7b Skenario what-if: selesai

Laporan `analysis/08_scenario_report.md` (D-64). Semua angka redaman adalah asumsi.

### 4.8 RTM final dan rekomendasi akhir: selesai

Rekomendasi akhir di `analysis/09_final_recommendations.md`; RTM final di `docs/06_requirements_traceability_matrix.md` (status final per hipotesis dan pemetaan R1-R9 ke bukti). Future work tercatat di rekomendasi akhir bagian 4.
