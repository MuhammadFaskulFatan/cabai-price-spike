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
- **luas panen**: 172 provinsi-tahun dengan keriting > 0; keriting > besar: 0; nilai identik dengan besar: 9 ['Sumatera Barat 2022', 'Sumatera Barat 2025', 'Kepulauan Bangka Belitung 2024', 'Kepulauan Bangka Belitung 2025', 'Daerah Khusus Ibukota Jakarta 2025', 'Gorontalo 2023', 'Gorontalo 2024', 'Gorontalo 2025', 'Maluku Utara 2023']; besar > 0 tetapi keriting = 0: 102.

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
