# Hold-out validation: metode imputation harga (D-09, D-43)

Seri tier main cabai_merah dan cabai_rawit, tipe harga eceran, pedagang besar, produsen (baris provinsi dan nasional). Gap buatan 1-6 bulan, 203 seri, sampai 3 posisi acak per panjang gap (seed 42), 3,654 gap buatan, 12,789 nilai diprediksi per metode. Metrik: MAPE pada skala harga (Rp/kg). `locf` (nilai terakhir diteruskan) hanya pembanding.

## 1. Keputusan

Success criterion: metode imputasi dipilih lewat hold-out; jika tidak lebih akurat dari baseline linear, baseline yang dipakai. Kandidat `kalman` tidak lebih akurat di bucket mana pun, jadi semua gap 1-6 bulan memakai `linear_log` (D-43).

| bucket | mape_linear_pct | mape_kalman_pct | mape_locf_pct | kalman_lebih_akurat | metode_dipakai |
| --- | --- | --- | --- | --- | --- |
| 1-2 bulan | 17.01 | 17.20 | 24.47 | False | linear_log |
| 3-6 bulan | 24.55 | 24.80 | 32.25 | False | linear_log |
| 1-6 bulan | 23.47 | 23.71 | 31.14 | False | linear_log |

## 2. MAPE per panjang gap (persen)

| gap_length | kalman | linear_log | locf |
| --- | --- | --- | --- |
| 1 | 15.19 | 14.66 | 21.65 |
| 2 | 18.21 | 18.18 | 25.88 |
| 3 | 20.57 | 19.74 | 27.65 |
| 4 | 23.46 | 23.43 | 31.52 |
| 5 | 26.03 | 25.74 | 32.85 |
| 6 | 26.77 | 26.71 | 34.53 |

## 3. MAPE per bucket dan tipe harga (persen)

| bucket | price_type | kalman | linear_log | locf |
| --- | --- | --- | --- | --- |
| 1-2 bulan | eceran | 13.06 | 13.64 | 20.44 |
| 1-2 bulan | pedagang_besar | 17.33 | 17.41 | 23.93 |
| 1-2 bulan | produsen | 21.60 | 20.26 | 29.45 |
| 3-6 bulan | eceran | 20.52 | 20.45 | 27.35 |
| 3-6 bulan | pedagang_besar | 25.06 | 25.29 | 32.96 |
| 3-6 bulan | produsen | 29.19 | 28.24 | 36.84 |

## 4. Kalman vs linear pada gap yang sama (berpasangan)

Porsi nilai prediksi yang lebih akurat dengan Kalman daripada dengan linear (persen):

| bucket | kalman_lebih_baik | n |
| --- | --- | --- |
| 1-2 bulan | 50.6 | 1827 |
| 3-6 bulan | 49.6 | 10962 |

MAPE 15-27% mencerminkan gejolak harga cabai: satu bulan saja bisa bergeser puluhan persen, sehingga setiap uji H2/H4 wajib punya sensitivity check yang mengecualikan bulan imputasi (D-44).
