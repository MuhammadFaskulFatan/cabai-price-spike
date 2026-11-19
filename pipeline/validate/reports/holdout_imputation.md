# Hold-out validation: metode imputation harga (D-09)

Seri tier main cabai_merah dan cabai_rawit, tipe harga eceran, pedagang besar, produsen (baris provinsi dan nasional). Gap buatan 1-6 bulan, 203 seri, sampai 3 posisi acak per panjang gap (seed 42), 3,654 gap buatan, 12,789 nilai diprediksi per metode. Metrik: MAPE pada skala harga (Rp/kg). `locf` (nilai terakhir diteruskan) hanya pembanding.

## 1. Apakah aturan gap cocok dengan hasil hold-out?

Aturan (panduan kerja): gap 1-2 bulan linear interpolation pada log price, 3-6 bulan Kalman. Success criterion charter: setiap metode lebih akurat dari linear interpolation.

| bucket | metode_aturan | metode_mape_terendah | sesuai_aturan | mape_linear_pct | mape_kalman_pct | mape_locf_pct |
| --- | --- | --- | --- | --- | --- | --- |
| 1-2 bulan | linear_log | linear_log | True | 17.01 | 17.20 | 24.47 |
| 3-6 bulan | kalman | linear_log | False | 24.55 | 24.80 | 32.25 |

## 2. MAPE per panjang gap

| gap_length | kalman | linear_log | locf |
| --- | --- | --- | --- |
| 1.00 | 15.19 | 14.66 | 21.65 |
| 2.00 | 18.21 | 18.18 | 25.88 |
| 3.00 | 20.57 | 19.74 | 27.65 |
| 4.00 | 23.46 | 23.43 | 31.52 |
| 5.00 | 26.03 | 25.74 | 32.85 |
| 6.00 | 26.77 | 26.71 | 34.53 |

(MAPE dalam persen.)

## 3. MAPE per bucket dan tipe harga

| bucket | price_type | kalman | linear_log | locf |
| --- | --- | --- | --- | --- |
| 1-2 bulan | eceran | 13.06 | 13.64 | 20.44 |
| 1-2 bulan | pedagang_besar | 17.33 | 17.41 | 23.93 |
| 1-2 bulan | produsen | 21.60 | 20.26 | 29.45 |
| 3-6 bulan | eceran | 20.52 | 20.45 | 27.35 |
| 3-6 bulan | pedagang_besar | 25.06 | 25.29 | 32.96 |
| 3-6 bulan | produsen | 29.19 | 28.24 | 36.84 |

## 4. Kalman vs linear pada gap yang sama (berpasangan)

Porsi nilai prediksi yang lebih akurat dengan Kalman daripada dengan linear:

| bucket | kalman_lebih_baik | n |
| --- | --- | --- |
| 1-2 bulan | 50.6 | 1827 |
| 3-6 bulan | 49.6 | 10962 |
