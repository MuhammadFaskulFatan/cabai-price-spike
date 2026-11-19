# H6: seberapa besar hari besar menambah kenaikan harga?

Script: `analysis/h6_holidays.py`. Tabel: `analysis/tables/h6_*.csv`. Rencana: `docs/05_analysis_plan.md` bagian 6 (D-48). Data: harga eceran 34 provinsi, Jan 2019 - Des 2025 untuk spesifikasi utama, karena kontrol produksi 2026 belum ada. Ada 7 Idulfitri dalam sampel: Juni 2019, Mei 2020, Mei 2021, Mei 2022, April 2023, April 2024, Maret 2025.

**Keputusan sementara: tidak didukung untuk bagian "menambah kenaikan" pada uji yang direncanakan.** Bulan Idulfitri tidak berbeda signifikan dari bulan lain. Bagian "bukan pemicu utama" baru bisa diputuskan setelah H1 (efek cuaca) selesai.

## 1. Hasil utama dan effect size

Panel FE provinsi x bulan: log harga eceran pada dummy bulan Idulfitri dan bulan sebelum Idulfitri, dengan:
- FE provinsi, FE month-of-year, dan trend;
- log produksi tahunan provinsi, ONI, dan jumlah hari cuti bersama sebagai kontrol;
- SE cluster per tahun-bulan.

| Komoditas | Bulan Idulfitri: efek (95% CI) | p | Bulan sebelum Idulfitri: efek (95% CI) | p |
| --- | --- | --- | --- | --- |
| Cabai merah | -4,6% (-20,7 s/d 14,8) | 0,62 | +12,5% (0,0 s/d 26,6) | 0,05 |
| Cabai rawit | +3,6% (-16,7 s/d 28,9) | 0,75 | +7,9% (-4,7 s/d 22,2) | 0,23 |

**Pemeriksaan pendukung (event study, di luar rencana):** dummy untuk bulan -3 sampai +3 dari Idulfitri, dengan kontrol yang sama dan pembanding semua bulan lain.

![Event study Idulfitri](figures/h6_idulfitri_event.png)

Harga di jendela -2 sampai +2 bulan rata-rata 15-46% lebih tinggi daripada bulan di luar jendela. Pola ini tetap ada setelah FE tahun ditambahkan. Karena pembanding uji utama ikut memuat bulan -2, +1, dan +2 yang juga tinggi, uji utama tidak menangkap kenaikan di jendela yang lebih lebar ini. Cara membaca angka ini ada di bagian 5.

## 2. Keputusan terhadap aturan di rencana

| Kriteria | Cabai merah | Cabai rawit |
| --- | --- | --- |
| Efek bulan Idulfitri positif dan signifikan | Tidak (-4,6%; p 0,62) | Tidak (+3,6%; p 0,75) |
| Efek hari besar lebih kecil dari efek cuaca (H1) | Menunggu H1 | Menunggu H1 |
| **Keputusan sementara** | **Tidak didukung untuk "menambah kenaikan"; final menunggu H1** | **Sama** |

## 3. Sensitivity check

| Spesifikasi | Merah: bulan Idulfitri (p) | Merah: bulan sebelum (p) | Rawit: bulan Idulfitri (p) | Rawit: bulan sebelum (p) |
| --- | --- | --- | --- | --- |
| Utama (2019-2025, kontrol produksi + ONI + cuti) | -4,6% (0,62) | +12,5% (0,05) | +3,6% (0,75) | +7,9% (0,23) |
| Tanpa kontrol produksi, sampai Okt 2026 (8 Idulfitri) | -8,8% (0,36) | +7,3% (0,28) | +2,7% (0,80) | +6,0% (0,33) |
| Hanya bulan `cuti_bersama_verified` | +17,6% (0,09) | +15,9% (0,02) | +34,9% (0,001) | +11,2% (0,17) |
| Tanpa 2020 | +3,4% (0,72) | +14,0% (0,03) | +8,1% (0,55) | +7,0% (0,38) |
| Tanpa kontrol cuti bersama | +6,1% (0,48) | +8,5% (0,22) | +3,7% (0,61) | +7,9% (0,27) |
| Tambah FE tahun | -3,9% (0,63) | +12,9% (0,04) | +5,3% (0,61) | +8,0% (0,22) |

- Hasil tidak stabil. Efek bulan Idulfitri hanya signifikan di subsampel bulan dengan cuti bersama terverifikasi. Subsampel itu membuang 2020 dan beberapa bulan Idulfitri, sehingga hanya tersisa 6 kejadian.
- Bulan sebelum Idulfitri untuk cabai merah positif dan signifikan atau hampir signifikan di 5 dari 6 spesifikasi (+7 sampai +16%).
- **Tidak dijalankan:** dummy Natal-Tahun Baru terpisah, yang ada di rencana. Natal dan Tahun Baru selalu jatuh di Desember-Januari, sehingga efeknya sepenuhnya terserap FE month-of-year dan tidak bisa diestimasi terpisah (dicatat di D-54).
- **D-44:** harga eceran tidak punya bulan imputasi, sehingga tidak ada yang perlu dikeluarkan.

## 4. Temuan yang terbukti

1. Pada uji yang direncanakan, harga eceran di bulan Idulfitri tidak berbeda signifikan dari bulan lain, untuk kedua komoditas.
2. Untuk cabai merah, bulan sebelum Idulfitri cenderung lebih mahal sekitar 12-13% (p 0,04-0,05 di spesifikasi utama dan dengan FE tahun).
3. Efek hari besar sangat bergantung pada spesifikasi. Dengan hanya 7-8 kejadian Idulfitri, estimasi efeknya tidak presisi (interval kepercayaan sekitar +-20 poin persen).

## 5. Dugaan yang perlu verifikasi

1. **Jendela sekitar Idulfitri yang mahal (event study).** Kenaikan 15-46% di bulan -2 sampai +2 kemungkinan bercampur dengan episode spike besar yang kebetulan jatuh dekat Idulfitri: Juni-Oktober 2019, Januari-Mei 2021 (rawit), Mei-September 2022, Januari-April 2025 (rawit). Dengan 7 kejadian, efek hari besar dan kebetulan waktu tidak bisa dipisahkan. EDA juga menunjukkan puncak harga tidak jatuh di bulan Lebaran (D-06). Verifikasi: ulangi setelah H1, dengan kontrol cuaca yang menjelaskan episode spike tersebut.
2. **Efek di subsampel cuti bersama terverifikasi** (+35% rawit) kemungkinan efek komposisi sampel, karena tahun dan bulan yang dibuang tidak acak. Verifikasi: lengkapi data cuti bersama 2020 dan Natal 2018, 2019, 2022 dari dokumen SKB.

## 6. So what

Kepercayaan umum bahwa harga cabai melonjak karena Lebaran tidak didukung uji utama: bulan Lebaran sendiri tidak lebih mahal setelah musim, tren, dan pasokan dikontrol. Ada tanda bahwa cabai merah lebih mahal sekitar sebulan sebelum Lebaran, saat orang mulai berbelanja.

Harga di periode sekitar Lebaran memang sering tinggi, tetapi dengan data yang ada belum bisa dipastikan apakah itu karena Lebaran atau karena guncangan pasokan yang kebetulan jatuh di periode yang sama. Jawaban yang lebih pasti menunggu analisis cuaca (H1).
