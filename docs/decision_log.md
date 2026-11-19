# Decision Log

Setiap keputusan yang mengubah rencana dicatat di sini. Entri D-01 sampai D-08 dipindahkan dari decision log di Project Charter supaya riwayatnya satu tempat. Entri berikutnya ditambahkan di bawah.

Semua keputusan di bawah sudah dikonfirmasi Fatan pada 19 Nov 2026.

| ID | Tanggal | Keputusan | Alasan |
| --- | --- | --- | --- |
| D-01 | 19 Nov 2026 | Pertanyaan inti diganti menjadi paradoks surplus produksi vs harga melonjak | Lebih tajam dan actionable daripada "kenapa harga naik-turun" |
| D-02 | 19 Nov 2026 | Periode analisis dimulai Januari 2019 | Harga produsen di PIHPS baru tersedia sejak pertengahan 2018 |
| D-03 | 19 Nov 2026 | NTT dikeluarkan dari analisis harga produsen | Data kosong hampir terus sejak 2024; NTT bukan sentra cabai |
| D-04 | 19 Nov 2026 | Pasokan Pasar Induk Kramat Jati tidak masuk core dataset | Tidak ada seri publik; angka di berita hanya potongan tanggal tertentu |
| D-05 | 19 Nov 2026 | Cabai rawit masuk scope bersama cabai merah | Dampak dan keluhan sama; kelengkapan datanya setara |
| D-06 | 19 Nov 2026 | Premis "price spike menjelang Lebaran" ditinggalkan | Data PIHPS 2018-2026 menunjukkan puncak harga cabai tidak jatuh di bulan Lebaran |
| D-07 | 19 Nov 2026 | Fokus bergeser dari satu jenis usaha (warung) ke causal chain | Cerita warung terlalu sempit; pertanyaan yang lebih berguna adalah mekanisme penyebabnya |
| D-08 | 19 Nov 2026 | Studi kasus Citi Bike (New York) tidak dipakai | Masalahnya tidak relevan untuk pembaca di Indonesia |
| D-09 | 19 Nov 2026 | Harness hold-out validation dibangun di `pipeline/validate/` tetapi dipanggil dari fase transform untuk memilih metode imputation. Fase 5 menjalankannya lagi pada dataset final dan melaporkan hasilnya | Urutan fase asli menaruh hold-out di fase 5, padahal metode harus sudah dipilih di fase 4 |
| D-10 | 19 Nov 2026 | Core dataset memakai dua grup komoditas (`cabai_merah` = `cat_7`, `cabai_rawit` = `cat_8`) supaya bisa dipasangkan dengan data produksi. Di Extract, empat varian tetap ditarik ke `data/raw`: merah besar, merah keriting, rawit merah, rawit hijau. Varian dipakai untuk analisis deskriptif per jenis cabai (US3), di luar core | Produksi BDSP tersedia per grup, sedangkan US3 meminta durasi dan magnitude per jenis cabai. Produksi BDSP besar + keriting dijumlahkan ke `cabai_merah` |
| D-11 | 19 Nov 2026 | Harga pasar modern (`price_type_id = 2`) tidak ditarik | Tidak ada hipotesis yang memakainya |
| D-12 | 19 Nov 2026 | Data harga mingguan disimpan di tabel terpisah dan tidak di-impute | Dipakai khusus untuk lead-lag; mengisi minggu kosong akan melemahkan estimasi lead-lag |
| D-13 | 19 Nov 2026 | Semua produksi bulanan provinsi diberi `is_imputed = TRUE` dengan `impute_method = chow_lin`; hasil Denton disimpan di kolom pembanding | Tidak ada angka bulanan provinsi yang diamati, jadi semuanya estimasi |
| D-14 | 19 Nov 2026 | Setiap file di `data/raw/` punya sidecar `<nama>.meta.json` berisi `extraction_date`, parameter request, jumlah baris, dan hash. Re-extract membuat file baru, tidak menimpa | Memenuhi aturan tanggal extraction dan melindungi dari revisi PIHPS yang diam-diam |
| D-15 | 19 Nov 2026 | Tabel fakta menyimpan tipe harga di baris; tabel akhir `core_province_month` dibuat lebar dengan pasangan `<variabel>_is_imputed` dan `<variabel>_impute_method` | Flag melekat per nilai di tabel fakta, sementara analisis tetap mendapat tabel lebar |
| D-16 | 19 Nov 2026 | November 2026 ditandai `is_partial_month`, dan ONI Oktober-November 2026 dibiarkan `NULL`. Model dan uji hipotesis hanya memakai data sampai Oktober 2026; November 2026 hanya untuk deskriptif | Extraction dilakukan 19 Nov 2026 sehingga bulan belum penuh, dan ONI baru tersedia sampai ASO 2026 (September) |
| D-17 | 19 Nov 2026 | Provinsi dibakukan ke 34 provinsi sesuai PIHPS. Sumber yang sudah 38 provinsi dipetakan ke provinsi induk: Papua Selatan, Papua Tengah, Papua Pegunungan menjadi Papua; Papua Barat Daya menjadi Papua Barat | PIHPS menjadi sumber utama dan tetap memakai 34 provinsi. Pemetaan dicatat di tabel terpisah supaya bisa diaudit |
| D-18 | 19 Nov 2026 | Survei pasar tradisional PIHPS dilakukan Senin-Jumat, jadi aturan minimal 10 hari kerja tetap. Rata-rata bulanan dihitung sendiri dari data harian; angka bulanan PIHPS (`tipe_laporan=3`) dipakai sebagai cross-check, bukan sumber | Rata-rata dari harian memungkinkan aturan minimal hari dan kolom `n_days_observed` ditegakkan |
| D-19 | 19 Nov 2026 | Baseline kondisi normal cuaca memakai periode 1991-2020 (WMO climate normal). Open-Meteo ditarik sejak 1991-01-01, bukan 2010 | Periode normal standar internasional, dan berakhir 2020 sehingga episode 2022-2026 yang diuji tidak ikut membentuk baseline |
| D-20 | 19 Nov 2026 | Alur git: satu branch per fase, merge ke `main` dan push di akhir fase yang sudah disetujui. Identitas git diset di level repo. Keputusan yang disetujui di decision log langsung disinkronkan ke panduan kerja proyek | Riwayat per fase rapi, dan panduan kerja proyek tidak tertinggal dari keputusan terbaru |

## Catatan dampak

- D-16 menambah batas periode model. `dim_month` mendapat kolom `in_model_period` (sampai Oktober 2026).
- D-19 mengganti titik awal Open-Meteo di panduan kerja (2010) menjadi 1991. Volume data naik sekitar 1,7 kali, masih kecil untuk request harian per titik.
- D-17 mengubah daftar TBD di data dictionary: pertanyaan 34 vs 38 provinsi sudah terjawab, tinggal membuat tabel pemetaan di fase extract.
