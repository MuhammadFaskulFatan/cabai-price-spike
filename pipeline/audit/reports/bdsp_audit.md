# Audit BDSP (produksi dan luas panen tahunan)

Sumber: BDSP Kementan, level provinsi (38 provinsi BDSP) dan kabupaten, 2018-2025, status Angka Tetap. Produksi dalam ton (cabe keriting dikonversi dari kuintal); luas panen dalam hektare. Angka 2025 belum bisa diverifikasi ke rilis BPS, jadi ditandai preliminary (D-29).

Satuan asli di BDSP: cabe besar produksi = Ton; cabe besar luas panen = Ha; cabe keriting produksi = Kuintal; cabe keriting luas panen = Ha; cabe rawit produksi = Ton; cabe rawit luas panen = Ha

## 1. Konsistensi baris TOTAL vs jumlah provinsi

| komoditas | indikator | selisih_terbesar_pct |
| --- | --- | --- |
| cabe besar | produksi | 0.0000 |
| cabe besar | luas panen | 0.0000 |
| cabe keriting | produksi | 0.0000 |
| cabe keriting | luas panen | 0.0000 |
| cabe rawit | produksi | 0.0000 |
| cabe rawit | luas panen | 0.0000 |

## 2. Nilai nol per provinsi x tahun

Nol di BDSP berarti tidak ada produksi atau tidak dilaporkan; keduanya tidak bisa dibedakan dari data. Dihitung pada 38 provinsi BDSP.

Jumlah provinsi bernilai nol per tahun:

| komoditas | indikator | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | nol_semua_tahun |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cabe besar | luas panen | 5 | 5 | 5 | 5 | 5 | 4 | 1 | 0 | 0 |
| cabe besar | produksi | 5 | 5 | 5 | 5 | 5 | 4 | 1 | 0 | 0 |
| cabe keriting | luas panen | 38 | 38 | 38 | 6 | 6 | 5 | 1 | 0 | 0 |
| cabe keriting | produksi | 38 | 38 | 38 | 6 | 6 | 5 | 1 | 0 | 0 |
| cabe rawit | luas panen | 4 | 5 | 5 | 4 | 4 | 4 | 1 | 0 | 0 |
| cabe rawit | produksi | 4 | 5 | 5 | 4 | 4 | 4 | 1 | 0 | 0 |

Provinsi yang nol di semua tahun:

- cabe besar / luas panen: tidak ada
- cabe besar / produksi: tidak ada
- cabe keriting / luas panen: tidak ada
- cabe keriting / produksi: tidak ada
- cabe rawit / luas panen: tidak ada
- cabe rawit / produksi: tidak ada

Provinsi pemekaran Papua (dipetakan ke induk, D-17): tahun pertama bernilai non-nol.

| komoditas | indikator | provinsi | tahun_pertama_nonnol |
| --- | --- | --- | --- |
| cabe besar | luas panen | Papua Barat Daya | 2024 |
| cabe besar | luas panen | Papua Pegunungan | 2025 |
| cabe besar | luas panen | Papua Selatan | 2024 |
| cabe besar | luas panen | Papua Tengah | 2024 |
| cabe besar | produksi | Papua Barat Daya | 2024 |
| cabe besar | produksi | Papua Pegunungan | 2025 |
| cabe besar | produksi | Papua Selatan | 2024 |
| cabe besar | produksi | Papua Tengah | 2024 |
| cabe keriting | luas panen | Papua Barat Daya | 2024 |
| cabe keriting | luas panen | Papua Pegunungan | 2025 |
| cabe keriting | luas panen | Papua Selatan | tidak pernah |
| cabe keriting | luas panen | Papua Tengah | 2024 |
| cabe keriting | produksi | Papua Barat Daya | 2024 |
| cabe keriting | produksi | Papua Pegunungan | 2025 |
| cabe keriting | produksi | Papua Selatan | tidak pernah |
| cabe keriting | produksi | Papua Tengah | 2024 |
| cabe rawit | luas panen | Papua Barat Daya | 2024 |
| cabe rawit | luas panen | Papua Pegunungan | 2025 |
| cabe rawit | luas panen | Papua Selatan | 2024 |
| cabe rawit | luas panen | Papua Tengah | 2024 |
| cabe rawit | produksi | Papua Barat Daya | 2024 |
| cabe rawit | produksi | Papua Pegunungan | 2025 |
| cabe rawit | produksi | Papua Selatan | 2024 |
| cabe rawit | produksi | Papua Tengah | 2024 |

## 3. Jumlah kabupaten vs nilai provinsi

1,824 kombinasi komoditas x indikator x provinsi x tahun diperiksa; selisih terbesar 0.0000%. Kombinasi dengan selisih > 1%: 0.

## 4. Produktivitas (ton per hektare)

Cabai umumnya sekitar 5-15 ton/ha; nilai di luar 1-30 ton/ha ditandai untuk dicek.

| komoditas | n | min_ton_per_ha | median | max_ton_per_ha | di_bawah_1 | di_atas_30 | produksi_ada_luas_nol |
| --- | --- | --- | --- | --- | --- | --- | --- |
| cabe besar | 274 | 0.26 | 7.46 | 33.89 | 9 | 1 | 0 |
| cabe keriting | 172 | 0.20 | 7.64 | 34.54 | 7 | 1 | 0 |
| cabe rawit | 277 | 0.20 | 6.43 | 30.94 | 8 | 2 | 0 |

## 5. Cek subset: cabe keriting vs cabe besar (D-28)

- **produksi**: 172 provinsi-tahun dengan keriting > 0; keriting > besar: 0; nilai identik dengan besar: 8 ['Sumatera Barat 2022', 'Sumatera Barat 2025', 'Kepulauan Bangka Belitung 2024', 'Kepulauan Bangka Belitung 2025', 'Gorontalo 2023', 'Gorontalo 2024', 'Gorontalo 2025', 'Maluku Utara 2023']; besar > 0 tetapi keriting = 0: 102.
- **luas panen**: 172 provinsi-tahun dengan keriting > 0; keriting > besar: 0; nilai identik dengan besar: 8 ['Sumatera Barat 2022', 'Sumatera Barat 2025', 'Kepulauan Bangka Belitung 2024', 'Kepulauan Bangka Belitung 2025', 'Gorontalo 2023', 'Gorontalo 2024', 'Gorontalo 2025', 'Maluku Utara 2023']; besar > 0 tetapi keriting = 0: 102.

Total nasional dan rasio:

| tahun | besar_ton | keriting_ton | rasio_keriting_besar | rawit_ton |
| --- | --- | --- | --- | --- |
| 2018 | 1,206,737.30 | 0.00 | 0.00 | 1,335,595.30 |
| 2019 | 1,214,417.59 | 0.00 | 0.00 | 1,374,214.97 |
| 2020 | 1,264,189.61 | 0.00 | 0.00 | 1,508,404.18 |
| 2021 | 1,360,571.14 | 860,185.07 | 0.63 | 1,386,446.94 |
| 2022 | 1,475,821.26 | 1,017,381.84 | 0.69 | 1,544,440.87 |
| 2023 | 1,554,498.35 | 1,159,457.55 | 0.75 | 1,506,762.14 |
| 2024 | 1,469,325.13 | 1,085,321.06 | 0.74 | 1,568,757.02 |
| 2025 | 1,715,029.22 | 1,327,912.73 | 0.77 | 1,743,125.45 |

## 6. Total nasional per tahun dan perubahan tahunan

Perubahan tahunan yang lebih dari 20% (naik atau turun):

| komoditas | indikator | tahun | total | perubahan_pct |
| --- | --- | --- | --- | --- |
| cabe keriting | produksi | 2025 | 1,327,912.7 | 22.4 |

Total nasional (ton atau ha):

| commodity | indicator | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cabe besar | luas panen | 137,596 | 133,434 | 133,729 | 142,618 | 145,277 | 145,212 | 138,334 | 136,836 |
| cabe besar | produksi | 1,206,737 | 1,214,418 | 1,264,190 | 1,360,571 | 1,475,821 | 1,554,498 | 1,469,325 | 1,715,029 |
| cabe keriting | luas panen | 0 | 0 | 0 | 82,804 | 95,564 | 100,671 | 94,391 | 98,651 |
| cabe keriting | produksi | 0 | 0 | 0 | 860,185 | 1,017,382 | 1,159,458 | 1,085,321 | 1,327,913 |
| cabe rawit | luas panen | 172,847 | 166,943 | 181,043 | 179,306 | 189,267 | 193,423 | 191,884 | 202,470 |
| cabe rawit | produksi | 1,335,595 | 1,374,215 | 1,508,404 | 1,386,447 | 1,544,441 | 1,506,762 | 1,568,757 | 1,743,125 |

## 7. Provinsi produsen per tahun (34 provinsi PIHPS, setelah pemetaan induk)

Jumlah provinsi (dari 34) dengan produksi > 0:

| komoditas | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cabe besar | 33 | 33 | 33 | 33 | 33 | 34 | 34 | 34 |
| cabe keriting | 0 | 0 | 0 | 32 | 32 | 33 | 34 | 34 |
| cabe rawit | 34 | 33 | 33 | 34 | 34 | 34 | 34 | 34 |

## 8. Provinsi pemekaran Papua: sebelum dan sesudah agregasi ke induk (D-17)

`sebelum` = hanya baris provinsi induk di BDSP; `sesudah` = induk + pemekaran (Papua: + Papua Selatan, Papua Tengah, Papua Pegunungan; Papua Barat: + Papua Barat Daya).

### Papua

| komoditas | indikator | versi | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cabe besar | produksi | sebelum | 3,412 | 3,033 | 1,993 | 3,016 | 2,198 | 2,811 | 463 | 103 |
| cabe besar | produksi | sesudah | 3,412 | 3,033 | 1,993 | 3,016 | 2,198 | 2,811 | 2,887 | 1,943 |
| cabe besar | luas panen | sebelum | 529 | 510 | 299 | 333 | 263 | 392 | 225 | 106 |
| cabe besar | luas panen | sesudah | 529 | 510 | 299 | 333 | 263 | 392 | 513 | 488 |
| cabe keriting | produksi | sebelum | 0 | 0 | 0 | 23 | 44 | 417 | 51 | 54 |
| cabe keriting | produksi | sesudah | 0 | 0 | 0 | 23 | 44 | 417 | 644 | 128 |
| cabe keriting | luas panen | sebelum | 0 | 0 | 0 | 4 | 6 | 54 | 45 | 52 |
| cabe keriting | luas panen | sesudah | 0 | 0 | 0 | 4 | 6 | 54 | 96 | 96 |
| cabe rawit | produksi | sebelum | 6,943 | 4,388 | 3,436 | 5,054 | 4,335 | 4,556 | 1,418 | 144 |
| cabe rawit | produksi | sesudah | 6,943 | 4,388 | 3,436 | 5,054 | 4,335 | 4,556 | 7,003 | 4,339 |
| cabe rawit | luas panen | sebelum | 1,025 | 821 | 586 | 639 | 544 | 936 | 434 | 92 |
| cabe rawit | luas panen | sesudah | 1,025 | 821 | 586 | 639 | 544 | 936 | 1,070 | 774 |

### Papua Barat

| komoditas | indikator | versi | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cabe besar | produksi | sebelum | 251 | 1,168 | 812 | 911 | 1,567 | 1,316 | 149 | 81 |
| cabe besar | produksi | sesudah | 251 | 1,168 | 812 | 911 | 1,567 | 1,316 | 621 | 620 |
| cabe besar | luas panen | sebelum | 228 | 326 | 269 | 217 | 195 | 195 | 52 | 243 |
| cabe besar | luas panen | sesudah | 228 | 326 | 269 | 217 | 195 | 195 | 147 | 310 |
| cabe keriting | produksi | sebelum | 0 | 0 | 0 | 344 | 497 | 831 | 31 | 33 |
| cabe keriting | produksi | sesudah | 0 | 0 | 0 | 344 | 497 | 831 | 379 | 429 |
| cabe keriting | luas panen | sebelum | 0 | 0 | 0 | 55 | 91 | 119 | 11 | 109 |
| cabe keriting | luas panen | sesudah | 0 | 0 | 0 | 55 | 91 | 119 | 88 | 157 |
| cabe rawit | produksi | sebelum | 625 | 3,276 | 2,351 | 3,808 | 4,106 | 3,010 | 1,293 | 393 |
| cabe rawit | produksi | sesudah | 625 | 3,276 | 2,351 | 3,808 | 4,106 | 3,010 | 4,618 | 3,415 |
| cabe rawit | luas panen | sebelum | 588 | 885 | 677 | 721 | 675 | 578 | 329 | 258 |
| cabe rawit | luas panen | sesudah | 588 | 885 | 677 | 721 | 675 | 578 | 643 | 535 |

## 9. Flag `is_outlier` (produktivitas di luar 1-30 ton/ha, dihitung setelah agregasi ke 34 provinsi)

21 provinsi-tahun ditandai; nilai tidak diubah. H5 dijalankan dengan dan tanpa outlier (D-37).

| komoditas | province_id | tahun | produksi | luas_panen | yield_ton_per_ha |
| --- | --- | --- | --- | --- | --- |
| cabe besar | 6 | 2025 | 214,628.83 | 6,333.40 | 33.89 |
| cabe besar | 13 | 2023 | 0.19 | 0.66 | 0.29 |
| cabe besar | 13 | 2025 | 0.10 | 0.25 | 0.40 |
| cabe besar | 30 | 2021 | 2,465.82 | 4,246.23 | 0.58 |
| cabe besar | 30 | 2022 | 3,602.45 | 4,653.55 | 0.77 |
| cabe besar | 30 | 2023 | 4,025.36 | 4,925.18 | 0.82 |
| cabe besar | 30 | 2024 | 3,159.41 | 4,440.98 | 0.71 |
| cabe keriting | 6 | 2025 | 213,975.33 | 6,195.30 | 34.54 |
| cabe keriting | 13 | 2023 | 0.15 | 0.46 | 0.33 |
| cabe keriting | 13 | 2025 | 0.07 | 0.23 | 0.29 |
| cabe keriting | 17 | 2024 | 1.70 | 5.00 | 0.34 |
| cabe keriting | 17 | 2025 | 0.14 | 0.21 | 0.65 |
| cabe rawit | 6 | 2024 | 43,578.48 | 1,447.56 | 30.10 |
| cabe rawit | 6 | 2025 | 42,173.88 | 1,363.24 | 30.94 |
| cabe rawit | 13 | 2018 | 0.40 | 2.00 | 0.20 |
| cabe rawit | 13 | 2022 | 0.06 | 0.12 | 0.50 |
| cabe rawit | 13 | 2023 | 1.48 | 2.16 | 0.69 |
| cabe rawit | 30 | 2021 | 3,335.74 | 4,304.50 | 0.77 |
| cabe rawit | 30 | 2022 | 3,495.87 | 4,654.75 | 0.75 |
| cabe rawit | 30 | 2023 | 3,709.93 | 4,902.90 | 0.76 |
| cabe rawit | 30 | 2024 | 3,275.34 | 4,312.26 | 0.76 |

## 10. Flag `suspect_copy` (nilai cabe keriting persis sama dengan cabe besar)

8 provinsi-tahun. Nilai tidak dikoreksi; flag disimpan sebagai anotasi di `data/raw/bdsp/flags/suspect_copy.csv` tanpa mengubah file raw (D-39).

| bdsp_name | year | indicators_identical |
| --- | --- | --- |
| Gorontalo | 2023 | produksi,luas_panen |
| Gorontalo | 2024 | produksi,luas_panen |
| Gorontalo | 2025 | produksi,luas_panen |
| Kepulauan Bangka Belitung | 2024 | produksi,luas_panen |
| Kepulauan Bangka Belitung | 2025 | produksi,luas_panen |
| Maluku Utara | 2023 | produksi,luas_panen |
| Sumatera Barat | 2022 | produksi,luas_panen |
| Sumatera Barat | 2025 | produksi,luas_panen |
