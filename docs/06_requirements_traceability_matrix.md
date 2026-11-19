# Requirements Traceability Matrix

Menghubungkan setiap business requirement (BR) di Project Charter ke user story, hipotesis, data, metode, output, dan status. Metode rinci ada di [rencana analisis](05_analysis_plan.md). Status per 19 Nov 2026.

## 1. Matriks utama

| BR | User story | Hipotesis | Tabel / kolom data | Metode | Output | Status |
| --- | --- | --- | --- | --- | --- | --- |
| BR1: driver utama dan lag | US3 (durasi dan magnitude spike) | (deskriptif) | `price_monthly_national`, `core_province_month.price_retail`; `analysis/spikes.py` | Definisi spike 1,25 x median 12 bulan; episode | `analysis/01_eda_report.md`, `figures/01_national_retail_trend.png`, `figures/03_province_spike_months.png`, `tables/spike_episodes_*.csv` | Selesai (EDA) |
| BR1 | US3, US5 | H1: hujan ekstrem di sentra -> harga produsen, lag 1-4 | `rain_anomaly` (menunggu), `oni_anomaly`, `price_producer`, `production_annual_ton` | Panel FE provinsi x bulan, lag 1-4 + kuadrat (spesifikasi 1: FE month-of-year + ONI; spesifikasi 2: FE tahun-bulan); jalur produksi tahunan | Tabel efek marginal per lag; chart efek terhadap anomali hujan | Direncanakan, menunggu paket cuaca |
| BR1 | US5 | H5: cobweb (luas panen t vs harga produsen t-1) | `core_province_year`: `harvested_area_ha`, `producer_price_annual_mean`, `is_outlier`, `is_preliminary` | Panel FE provinsi x tahun; pembanding dengan year FE | Tabel elastisitas + sensitivity (tanpa outlier, tanpa 2025, year FE) | Direncanakan |
| BR1 | US3, US5 | H6: hari besar menambah, bukan pemicu utama | `price_retail`, `months_to_idulfitri`, `n_cuti_bersama_days`, `cuti_bersama_verified`, `production_annual_ton`, `oni_anomaly`; `dim_holiday` | Panel FE provinsi x bulan, dummy bulan Idulfitri dan sebelumnya | Tabel efek (persen) vs efek cuaca H1 | Direncanakan; kesimpulan akhir menunggu H1 |
| BR2: level rantai pasok tempat spike dimulai | US4 (lead-lag dalam minggu) | H2: produsen/pedagang besar mendahului eceran, transmisi asimetris | `fact_price_weekly` (nasional), `core_province_month`: `price_producer`, `price_wholesale`, `price_retail`, `_tier`, `_is_imputed` | Cross-correlation + Granger mingguan; kointegrasi lalu asymmetric ECM (atau first difference tanpa kointegrasi) per provinsi | `analysis/02_h2_report.md`, `figures/h2_weekly_ccf.png`, `figures/h2_asymmetry_provinces.png`, `tables/h2_*.csv` | Selesai, menunggu review: sebagian (hilir bergerak lebih dulu; asimetri hanya produsen -> pedagang besar) |
| BR3: daerah tetap mahal saat produksi cukup | US2 (provinsi paling rentan) | H3: disparitas melebar saat guncangan, terutama jauh dari sentra | `price_retail` 34 provinsi; spike harga produsen nasional; `distance_to_sentra_km`, `is_different_island` | CV antarprovinsi per bulan; regresi premium pada jarak | Chart CV dari waktu ke waktu dengan bulan guncangan; ranking provinsi rentan per episode | Direncanakan; kolom jarak sudah di core (D-50) |
| BR4: early warning dan lead time | US1 (lead time >= 1 bulan, false alarm lebih rendah) | H4: cuaca sentra dan harga produsen sebagai leading indicator | Onset episode besar (spike provinsi >= 2 bulan) t+1/t+2; fitur harga produsen dan pedagang besar, `rain_anomaly` (menunggu), `oni_anomaly`, `months_to_idulfitri` | Logistic + aturan sederhana, rolling-origin backtest 2023-2026; berhasil hanya jika mengalahkan baseline terkuat (musiman naif atau naik bulan lalu) | Tabel recall, precision, false alarm rate, lead time; timeline peringatan vs episode | Direncanakan, menunggu paket cuaca |
| Semua | US5 (penjelasan yang bisa dicek ulang) | H1-H6 | Seluruh core dataset, `docs/decision_log.md` | Pipeline reproducible (`python -m pipeline.run`), script di `analysis/` | Setiap temuan menunjuk ke script, tabel, dan commit | Berjalan |

## 2. Data pendukung per hipotesis

| Hipotesis | Kolom wajib | Keterbatasan yang sudah tercatat |
| --- | --- | --- |
| H1 | `rain_anomaly`, `rel_humidity_mean`, `weather_status`, `oni_anomaly`, `price_producer` | Cuaca hanya 18 provinsi bertitik sentra (D-25); produksi hanya tahunan (D-42); 23 lokasi cuaca belum terunduh |
| H2 | Tiga level harga + flag imputasi + tier | Harga produsen: 109 nilai imputasi linear, 108 di periode model (D-43), wajib sensitivity tanpa imputasi (D-44) |
| H3 | `price_retail`, penanda guncangan, jarak ke sentra | Arus distribusi antarprovinsi tidak tersedia; disparitas harga dipakai sebagai proxy (charter) |
| H4 | Fitur hulu + target spike | Hanya sekitar 6-10 episode nasional; metrik per episode bergejolak |
| H5 | `core_province_year` | Sekitar 34 x 6 observasi perubahan; 2025 preliminary; 16 provinsi-tahun outlier di core tahunan |
| H6 | Kalender, cuti bersama | Cuti bersama 2020 dan sebagian Natal belum terverifikasi (D-38, D-41) |

## 3. Status ringkas

| Status | Jumlah |
| --- | --- |
| Selesai | EDA deskriptif |
| Selesai, menunggu review | H2 |
| Siap dijalankan | H3, H5, H6 (tanpa perbandingan dengan H1) |
| Menunggu paket cuaca | H1, H4, bagian cuaca di H3 dan H6 |
