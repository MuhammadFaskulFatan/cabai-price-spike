# Requirements Traceability Matrix

Menghubungkan setiap business requirement (BR) di Project Charter ke user story, hipotesis, data, metode, output, dan status. Metode rinci ada di [rencana analisis](05_analysis_plan.md). Status per 19 Nov 2026.

## 1. Matriks utama

| BR | User story | Hipotesis | Tabel / kolom data | Metode | Output | Status |
| --- | --- | --- | --- | --- | --- | --- |
| BR1: driver utama dan lag | US3 (durasi dan magnitude spike) | (deskriptif) | `price_monthly_national`, `core_province_month.price_retail`; `analysis/spikes.py` | Definisi spike 1,25 x median 12 bulan; episode | `analysis/01_eda_report.md`, `figures/01_national_retail_trend.png`, `figures/03_province_spike_months.png`, `tables/spike_episodes_*.csv` | Selesai (EDA) |
| BR1 | US3, US5 | H1: hujan ekstrem di sentra -> harga produsen, lag 1-4 | `rain_anomaly` (D-58), `rain_is_extreme`, `oni_anomaly`, `price_producer`, `production_annual_ton` | Panel FE provinsi x bulan, lag 1-4 + kuadrat (spesifikasi 1: FE month-of-year + ONI; spesifikasi 2: FE tahun-bulan); jalur produksi tahunan | `analysis/06_h1_report.md`, `figures/h1_rain_effect_curve.png`, `figures/h1_lag_profile.png`, `tables/h1_*.csv` | Selesai, menunggu review: rawit sebagian (kering -> harga naik, lag 3), merah tidak didukung, pola U tidak didukung |
| BR1 | US5 | H5: cobweb (luas panen t vs harga produsen t-1) | `core_province_year`: `harvested_area_ha`, `producer_price_annual_mean`, `is_outlier`, `is_preliminary` | Panel FE provinsi x tahun; pembanding dengan year FE | `analysis/04_h5_report.md`, `figures/h5_price_vs_area.png`, `tables/h5_results.csv` | Selesai, menunggu review: tidak didukung (rawit: arah positif konsisten, indikatif) |
| BR1 | US3, US5 | H6: hari besar menambah, bukan pemicu utama | `price_retail`, `months_to_idulfitri`, `n_cuti_bersama_days`, `cuti_bersama_verified`, `production_annual_ton`, `oni_anomaly`, `rain_anomaly`; `dim_holiday` | Panel FE provinsi x bulan, dummy bulan Idulfitri dan sebelumnya | `analysis/05_h6_report.md`, `figures/h6_idulfitri_event.png`, `tables/h6_*.csv` | Final: sebagian (bukan pemicu utama didukung; menambah kenaikan tidak didukung; D-62) |
| BR2: level rantai pasok tempat spike dimulai | US4 (lead-lag dalam minggu) | H2: produsen/pedagang besar mendahului eceran, transmisi asimetris | `fact_price_weekly` (nasional), `core_province_month`: `price_producer`, `price_wholesale`, `price_retail`, `_tier`, `_is_imputed` | Cross-correlation + Granger mingguan; kointegrasi lalu asymmetric ECM (atau first difference tanpa kointegrasi) per provinsi | `analysis/02_h2_report.md`, `figures/h2_*.png`, `tables/h2_*.csv` | Final: sebagian (eceran mendahului pedagang besar ~1 minggu, transmisi simetris; temuan yang melibatkan harga produsen tertahan oleh frekuensi pembaruan data) |
| BR3: daerah tetap mahal saat produksi cukup | US2 (provinsi paling rentan) | H3: disparitas melebar saat guncangan, terutama jauh dari sentra | `price_retail` 34 provinsi; spike harga produsen nasional; `distance_to_sentra_km`, `is_different_island` | CV antarprovinsi per bulan; regresi premium pada jarak | `analysis/03_h3_report.md`, `figures/h3_*.png`, `tables/h3_*.csv` | Selesai, menunggu review: tidak didukung (disparitas menyempit saat guncangan; daerah jauh mahal secara struktural) |
| BR4: early warning dan lead time | US1 (lead time >= 1 bulan, false alarm lebih rendah) | H4: cuaca sentra dan harga hulu sebagai leading indicator (sinyal: pedagang besar, cuaca, ONI; D-55) | Onset episode besar (spike provinsi >= 2 bulan) t+1/t+2; sinyal harga pedagang besar (tanpa harga produsen, D-55), `rain_anomaly` (menunggu), `oni_anomaly`, `months_to_idulfitri` | Logistic + aturan sederhana, rolling-origin backtest 2023-2026; berhasil hanya jika mengalahkan baseline terkuat (musiman naif atau naik bulan lalu) | `analysis/07_h4_report.md`, `figures/h4_metrics.png`, `figures/h4_alarm_timeline.png`, `tables/h4_*.csv` | Final (D-63): merah sebagian (lift 1,81, PR-AUC 0,178 vs 0,087); rawit tidak didukung (lift 1,18, interval mencakup 1) |
| Semua | US5 (penjelasan yang bisa dicek ulang) | H1-H6 | Seluruh core dataset, `docs/decision_log.md` | Pipeline reproducible (`python -m pipeline.run`), script di `analysis/` | Setiap temuan menunjuk ke script, tabel, dan commit | Berjalan |

## 2. Data pendukung per hipotesis

| Hipotesis | Kolom wajib | Keterbatasan yang sudah tercatat |
| --- | --- | --- |
| H1 | `rain_anomaly`, `rain_is_extreme`, `weather_status`, `oni_anomaly`, `price_producer` | Cuaca hanya 14-15 provinsi bertitik sentra (D-25); reanalysis sekitar 25 km, bukan stasiun (D-58); produksi hanya tahunan (D-42); harga produsen jarang diperbarui (D-56) |
| H2 | Tiga level harga + flag imputasi + tier | Harga produsen: 109 nilai imputasi linear, 108 di periode model (D-43), wajib sensitivity tanpa imputasi (D-44) |
| H3 | `price_retail`, penanda guncangan, jarak ke sentra | Arus distribusi antarprovinsi tidak tersedia; disparitas harga dipakai sebagai proxy (charter) |
| H4 | Fitur hulu + target spike | Hanya sekitar 6-10 episode nasional; metrik per episode bergejolak |
| H5 | `core_province_year` | Sekitar 34 x 6 observasi perubahan; 2025 preliminary; 16 provinsi-tahun outlier di core tahunan |
| H6 | Kalender, cuti bersama | Cuti bersama 2020 dan sebagian Natal belum terverifikasi (D-38, D-41) |

## 3. Status ringkas

| Status | Jumlah |
| --- | --- |
| Selesai | EDA deskriptif |
| Selesai | H2 |
| Selesai | H1 (disetujui, D-59) |
| Selesai, disetujui | H3, H5, H6 final (D-63) |
| Selesai, final | H4 (D-63) |
