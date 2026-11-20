# Requirements Traceability Matrix

Menghubungkan setiap business requirement (BR) di Project Charter ke user story, hipotesis, data, metode, output, dan status. Metode rinci ada di [rencana analisis](05_analysis_plan.md). **Status final per 20 Nov 2026** (langkah 4.8). Rekomendasi akhir: [`analysis/09_final_recommendations.md`](../analysis/09_final_recommendations.md).

## 1. Matriks utama

| BR | User story | Hipotesis | Tabel / kolom data | Metode | Output | Status |
| --- | --- | --- | --- | --- | --- | --- |
| BR1: driver utama dan lag | US3 (durasi dan magnitude spike) | (deskriptif) | `price_monthly_national`, `core_province_month.price_retail`; `analysis/spikes.py` | Definisi spike 1,25 x median 12 bulan; episode | `analysis/01_eda_report.md`, `figures/01_national_retail_trend.png`, `figures/03_province_spike_months.png`, `tables/spike_episodes_*.csv` | Selesai (EDA) |
| BR1 | US3, US5 | H1: hujan ekstrem di sentra -> harga produsen, lag 1-4 | `rain_anomaly` (D-58), `rain_is_extreme`, `oni_anomaly`, `price_producer`, `production_annual_ton` | Panel FE provinsi x bulan, lag 1-4 + kuadrat (spesifikasi 1: FE month-of-year + ONI; spesifikasi 2: FE tahun-bulan); jalur produksi tahunan | `analysis/06_h1_report.md`, `figures/h1_rain_effect_curve.png`, `figures/h1_lag_profile.png`, `tables/h1_*.csv` | Final, disetujui (D-59): rawit sebagian (kering -> harga produsen naik, lag 3); merah tidak didukung; pola U tidak didukung. Lampiran eksploratif: indeks hujan nasional merah (D-60) |
| BR1 | US5 | H5: cobweb (luas panen t vs harga produsen t-1) | `core_province_year`: `harvested_area_ha`, `producer_price_annual_mean`, `is_outlier`, `is_preliminary` | Panel FE provinsi x tahun; pembanding dengan year FE | `analysis/04_h5_report.md`, `figures/h5_price_vs_area.png`, `tables/h5_results.csv` | Final, disetujui (D-63): tidak didukung (rawit: arah positif konsisten, indikatif) |
| BR1 | US3, US5 | H6: hari besar menambah, bukan pemicu utama | `price_retail`, `months_to_idulfitri`, `n_cuti_bersama_days`, `cuti_bersama_verified`, `production_annual_ton`, `oni_anomaly`, `rain_anomaly`; `dim_holiday` | Panel FE provinsi x bulan, dummy bulan Idulfitri dan sebelumnya | `analysis/05_h6_report.md`, `figures/h6_idulfitri_event.png`, `tables/h6_*.csv` | Final, disetujui (D-63): sebagian (bukan pemicu utama didukung; menambah kenaikan tidak didukung; D-62) |
| BR2: level rantai pasok tempat spike dimulai | US4 (lead-lag dalam minggu) | H2: produsen/pedagang besar mendahului eceran, transmisi asimetris | `fact_price_weekly` (nasional), `core_province_month`: `price_producer`, `price_wholesale`, `price_retail`, `_tier`, `_is_imputed` | Cross-correlation + Granger mingguan; kointegrasi lalu asymmetric ECM (atau first difference tanpa kointegrasi) per provinsi | `analysis/02_h2_report.md`, `figures/h2_*.png`, `tables/h2_*.csv` | Final, disetujui: sebagian (eceran mendahului pedagang besar ~1 minggu, transmisi simetris; temuan yang melibatkan harga produsen tertahan oleh frekuensi pembaruan data) |
| BR3: daerah tetap mahal saat produksi cukup | US2 (provinsi paling rentan) | H3: disparitas melebar saat guncangan, terutama jauh dari sentra | `price_retail` 34 provinsi; spike harga produsen nasional; `distance_to_sentra_km`, `is_different_island` | CV antarprovinsi per bulan; regresi premium pada jarak | `analysis/03_h3_report.md`, `figures/h3_*.png`, `tables/h3_*.csv` | Final, disetujui (D-63): tidak didukung (disparitas menyempit saat guncangan; daerah jauh mahal secara struktural) |
| BR4: early warning dan lead time | US1 (lead time >= 1 bulan, false alarm lebih rendah) | H4: cuaca sentra dan harga hulu sebagai leading indicator (sinyal: pedagang besar, cuaca, ONI; D-55) | Onset episode besar (spike provinsi >= 2 bulan) t+1/t+2; sinyal harga pedagang besar (tanpa harga produsen, D-55), `rain_anomaly` (rawit), indeks hujan nasional (merah, D-60), `oni_anomaly`, `months_to_idulfitri` | Logistic + aturan sederhana, rolling-origin backtest 2023-2026; berhasil hanya jika mengalahkan baseline terkuat (musiman naif atau naik bulan lalu) | `analysis/07_h4_report.md`, `figures/h4_metrics.png`, `figures/h4_alarm_timeline.png`, `tables/h4_*.csv` | Final, disetujui (D-64): merah sebagian (lift 1,81, PR-AUC 0,178 vs 0,087); rawit tidak didukung (lift 1,18, interval mencakup 1) |
| BR4 (nilai bisnis) | US1, US3 | Skenario what-if 4.7b (bukan hipotesis) | `price_monthly_national` eceran, konsumsi per kapita Susenas dan penduduk BPS dari Buletin Konsumsi Pangan (raw PDF), prediksi backtest H4 | Biaya lonjakan = kelebihan harga di bulan spike x konsumsi rumah tangga; skenario redaman 10/25/50% (asumsi); break-even per alarm palsu (D-64) | `analysis/08_scenario_report.md`, `figures/scenario_*.png`, `tables/scenario_*.csv` | Selesai: biaya lonjakan merah Rp 5,53 T, rawit Rp 10,31 T (Jan 2023 - Okt 2026); semua angka redaman berlabel asumsi |
| Semua | US5 (penjelasan yang bisa dicek ulang) | H1-H6 | Seluruh core dataset, `docs/decision_log.md` | Pipeline reproducible (`python -m pipeline.run`), script di `analysis/` | Setiap temuan menunjuk ke script, tabel, dan commit | Selesai: semua temuan menunjuk ke script, tabel, keputusan (D-01 s/d D-64), dan commit |

## 2. Data pendukung per hipotesis

| Hipotesis | Kolom wajib | Keterbatasan yang sudah tercatat |
| --- | --- | --- |
| H1 | `rain_anomaly`, `rain_is_extreme`, `weather_status`, `oni_anomaly`, `price_producer` | Cuaca hanya 14-15 provinsi bertitik sentra (D-25); reanalysis sekitar 25 km, bukan stasiun (D-58); produksi hanya tahunan (D-42); harga produsen jarang diperbarui (D-56) |
| H2 | Tiga level harga + flag imputasi + tier | Harga produsen: 109 nilai imputasi linear, 108 di periode model (D-43), wajib sensitivity tanpa imputasi (D-44) |
| H3 | `price_retail`, penanda guncangan, jarak ke sentra | Arus distribusi antarprovinsi tidak tersedia; disparitas harga dipakai sebagai proxy (charter) |
| H4 | Fitur hulu + target spike | Hanya sekitar 6-10 episode nasional; metrik per episode bergejolak; ambang alarm rawit tidak diubah (future work, D-64) |
| Skenario 4.7b | Biaya lonjakan, konsumsi, penduduk, prediksi H4 | Konsumsi rumah tangga saja (understate); harga nominal; Susenas 2026 belum ada (pakai 2025, flag); redaman adalah asumsi; hanya satu episode nasional merah yang bisa dinilai |
| H5 | `core_province_year` | Sekitar 34 x 6 observasi perubahan; 2025 preliminary; 16 provinsi-tahun outlier di core tahunan |
| H6 | Kalender, cuti bersama | Cuti bersama 2020 dan sebagian Natal belum terverifikasi (D-38, D-41) |

## 3. Status ringkas (final)

| Hipotesis / langkah | Keputusan final | Keputusan terkait |
| --- | --- | --- |
| EDA deskriptif | Selesai | D-48 |
| H1 cuaca -> harga produsen | Rawit sebagian; merah tidak didukung; pola U tidak didukung | D-58, D-59, D-60 |
| H2 rantai pasok | Sebagian | D-52, D-53 |
| H3 disparitas | Tidak didukung (dibantah) | D-54, D-63 |
| H4 peringatan dini | Merah sebagian; rawit tidak didukung | D-55, D-61, D-63, D-64 |
| H5 cobweb | Tidak didukung | D-54, D-63 |
| H6 hari besar | Sebagian (bukan pemicu utama; tidak menambah kenaikan) | D-54, D-62, D-63 |
| Skenario what-if 4.7b | Selesai (angka redaman = asumsi) | D-64 |
| Rekomendasi akhir 4.8 | Selesai: 9 rekomendasi, 6 usulan ditahan | bagian 4 |

## 4. Rekomendasi -> bukti

Kekuatan bukti: **terbukti** = temuan yang lolos uji; **implikasi** = langkah dari temuan terbukti yang efeknya belum diuji.

| ID | Rekomendasi (ringkas) | BR | Hipotesis / skenario | Bagian laporan | Kekuatan bukti |
| --- | --- | --- | --- | --- | --- |
| R1 | Peringatan dini cabai merah sebagai daftar pantau bulanan | BR4 | H4 (merah), skenario | `07_h4_report.md` bagian 2, 2b, 5; `08_scenario_report.md` bagian 3, 5 | Terbukti (kinerja backtest); manfaat = implikasi |
| R2 | Pantau kekeringan di sentra rawit sebagai tanda awal 2-3 bulan | BR1, BR4 | H1 (rawit), H6 final, H4 | `06_h1_report.md` bagian 4, 5; `05_h6_report.md` bagian 2a; `07_h4_report.md` bagian 4 | Terbukti (asosiasi); pemakaian = implikasi |
| R3 | Perbaiki frekuensi pencatatan harga produsen PIHPS | BR2, BR4 | H2, H1, H4 (rawit), skenario | `02_h2_report.md` bagian 1.1; `06_h1_report.md` bagian 6; `08_scenario_report.md` bagian 4 | Terbukti (masalah data); manfaat = implikasi |
| R4 | Pemantauan mingguan bertumpu pada harga eceran dan pedagang besar | BR2 | H2 | `02_h2_report.md` | Terbukti |
| R5 | Tangani lonjakan sebagai masalah nasional | BR3, BR4 | H3, H4, skenario | `03_h3_report.md` bagian 1.1; `07_h4_report.md` bagian 6; `08_scenario_report.md` bagian 5 | Terbukti (pola serentak); kebijakan = implikasi |
| R6 | Perbaikan rantai pasok jangka panjang untuk daerah mahal struktural | BR3 | H3 | `03_h3_report.md` | Terbukti (pola harga); kebijakan = implikasi |
| R7 | Kesiapan stok sebulan sebelum Lebaran, bukan operasi besar di bulan Lebaran | BR1 | H6 final | `05_h6_report.md` bagian 1, 2a, 4 | Terbukti (uji utama); kebijakan = implikasi |
| R8 | Catat data intervensi untuk mengukur redaman | BR4 | Skenario | `08_scenario_report.md` bagian 3, 6 | Terbukti (kesenjangan data); dampak = implikasi |
| R9 | Data luas tanam/panen bulanan per kabupaten sebelum kebijakan pola tanam | BR1 | H5, H1 | `04_h5_report.md`; `06_h1_report.md` bagian 1, 7 | Terbukti (keterbatasan data); kebutuhan = implikasi |

Usulan yang ditahan beserta dasarnya ada di `analysis/09_final_recommendations.md` bagian 3. Catatan per hipotesis yang menjadi bahan rekomendasi ada di `analysis/notes_recommendations.md`.
