# Rekomendasi akhir: harga cabai melonjak di tengah surplus produksi

Disusun dari `analysis/notes_recommendations.md` dan hasil skenario what-if (langkah 4.8). Keterlacakan lengkap ada di [RTM](../docs/06_requirements_traceability_matrix.md) bagian 4.

Setiap rekomendasi menyebut:
- hipotesis atau skenario yang mendukungnya;
- kekuatan bukti:
  - terbukti: temuan yang lolos uji di proyek ini;
  - implikasi: langkah yang masuk akal dari temuan terbukti, tetapi efeknya belum diuji;
  - dugaan: perlu verifikasi.

Tidak ada angka efektivitas intervensi yang diklaim. Semua angka redaman di skenario adalah asumsi (D-64).

## 1. Jawaban atas pertanyaan inti

**Kalau produksi cabai nasional cukup, kenapa harga tetap melonjak di banyak daerah?**

| Jawaban | Bukti | Kekuatan |
| --- | --- | --- |
| Lonjakan terjadi serentak secara nasional, bukan karena satu-dua daerah kekurangan. Saat guncangan, disparitas antarprovinsi justru menyempit. | H3: CV antarprovinsi turun 8,1 poin (merah) dan 4,0 poin (rawit) di bulan guncangan | Terbukti |
| Cuaca kering di sentra adalah pendorong yang terukur, bukan Lebaran. Kemarau yang lebih kering dari normal menaikkan harga produsen rawit sekitar 13% tiga bulan kemudian, dan harga eceran sekitar 6% di provinsi sentra (merah dan rawit). Bulan Idulfitri tidak lebih mahal setelah kontrol. | H1 (rawit, lag 3), H6 final (D-62), lampiran H1 (indeks hujan nasional merah, eksploratif) | Terbukti untuk rawit dan harga eceran; merah di tingkat harga produsen tidak terdeteksi |
| Angka produksi tahunan yang "cukup" bisa menutupi kekurangan bulanan saat kemarau. Produksi bulanan per provinsi tidak tersedia, sehingga jalur hujan → produksi → harga tidak bisa diuji bulanan. | H1 jalur produksi tahunan tidak terdeteksi; D-42 | Dugaan |
| Lonjakan bukan siklus "harga tinggi → tanam lebih banyak → harga jatuh" di grain tahunan. | H5: elastisitas luas panen terhadap harga tahun lalu tidak signifikan | Terbukti untuk data tahunan |
| Sinyal pertama terlihat di harga eceran dan pedagang besar. Peran petani belum terbaca karena harga produsen PIHPS jarang diperbarui. | H2: eceran mendahului pedagang besar sekitar 1 minggu, transmisi simetris; harga produsen berubah di sekitar 22% minggu | Terbukti untuk eceran-pedagang besar; bagian produsen tertahan data |

**Skala masalah.** Jan 2023 - Okt 2026, rumah tangga membayar sekitar Rp 5,5 triliun (merah) dan Rp 10,3 triliun (rawit) di atas harga normal selama bulan-bulan lonjakan. Angka ini hanya konsumsi rumah tangga dengan harga nominal, sehingga understate (skenario, bagian 2).

## 2. Rekomendasi

| ID | Rekomendasi | Untuk | Dasar | Kekuatan bukti |
| --- | --- | --- | --- | --- |
| **R1** | Pakai model peringatan dini cabai merah sebagai **daftar pantau bulanan**: provinsi yang beralarm diprioritaskan untuk pengecekan pasokan dan koordinasi. Bukan pemicu otomatis operasi pasar. | TPID, Bapanas | H4 merah: 59% episode besar terdeteksi minimal 1 bulan sebelumnya; lift 1,81; false alarm 27% vs 42% baseline pada recall setara. Skenario: episode Nov 2023 (Rp 4,28 T) terdeteksi; alarm palsu 616 vs 947 provinsi-bulan | Terbukti (kinerja backtest); manfaat = implikasi, bergantung redaman yang belum diukur |
| **R2** | Masukkan **anomali hujan di sentra rawit** (kekeringan) ke pemantauan sebagai tanda awal 2-3 bulan. Dibaca analis sebagai informasi pendukung, belum sebagai model otomatis. | TPID, Kementan (Ditjen Hortikultura), BMKG sebagai sumber data | H1 rawit: anomali -1 selama 4 bulan → harga produsen +12,9%, lag 3; H6 final: +6,0% harga eceran; H4: cuaca memperbaiki model rawit | Terbukti (asosiasi); pemakaian untuk pemantauan = implikasi |
| **R3** | **Perbaiki frekuensi pencatatan harga produsen PIHPS** (atau sediakan seri harga produsen bulanan lain yang diperbarui teratur). Ini prasyarat untuk membaca peran petani dan untuk model peringatan dini rawit. | Bank Indonesia (PIHPS), BPS | H2: harga produsen berubah di median 22% minggu vs 90% pedagang besar; H1 dugaan 2; H4 rawit tidak didukung; skenario bagian 4 | Terbukti (masalah data); manfaatnya = implikasi |
| **R4** | Untuk pemantauan harian/mingguan, bertumpu pada **harga eceran dan pedagang besar PIHPS**. Kenaikan eceran adalah sinyal paling cepat. | TPID, Bapanas | H2: eceran dan pedagang besar diperbarui hampir setiap minggu; eceran mendahului pedagang besar sekitar 1 minggu | Terbukti |
| **R5** | Tangani lonjakan sebagai **masalah nasional**: kesiapan pasokan dari sentra secara nasional saat sinyal kemarau dan alarm muncul, bukan terutama memindahkan stok antardaerah saat lonjakan sudah terjadi. | Bapanas, Kementan | H3: disparitas menyempit saat guncangan; daerah surplus ikut mahal. H4 dan skenario: alarm cenderung serentak | Terbukti (pola serentak); bentuk kebijakan = implikasi |
| **R6** | Untuk daerah yang **mahal secara struktural** (Maluku, Maluku Utara, Papua/Papua Barat, Kalimantan Utara/Tengah, Kep. Bangka Belitung, Kep. Riau, DKI Jakarta), prioritaskan perbaikan rantai pasok jangka panjang daripada operasi pasar saat lonjakan. | Pemda, Kemendag, Bapanas | H3: daerah ini konsisten paling mahal, dan premiumnya tidak naik saat guncangan | Terbukti (pola harga); kebijakan = implikasi |
| **R7** | Menjelang Lebaran, cukup **kesiapan stok sekitar sebulan sebelumnya** (cabai merah), bukan operasi besar khusus di bulan Lebaran. | TPID, Bapanas | H6 final: bulan Idulfitri tidak lebih mahal setelah kontrol; bulan sebelum Idulfitri merah sekitar +12-13% (p 0,04-0,05); cuaca kering terukur lebih konsisten | Terbukti (uji utama); kebijakan = implikasi |
| **R8** | **Catat data intervensi** (operasi pasar/SPHP per provinsi-bulan: waktu, volume, harga) supaya efektivitas (redaman) bisa diukur sebelum memperbesar program berbasis peringatan dini. | Bapanas, TPID | Skenario: manfaat bergantung sepenuhnya pada redaman yang diasumsikan; break-even untuk merah: redaman minimum 1,4-14,4% untuk biaya tindak lanjut Rp 100 juta - 1 miliar per alarm palsu (rentang asumsi, tanpa patokan resmi; D-65) | Terbukti (kesenjangan data); dampak = implikasi |
| **R9** | Sediakan **data luas tanam dan panen bulanan per kabupaten** sebelum membuat kebijakan pola tanam atau jadwal tanam. | Kementan, BPS (SPH) | H5: tidak ada respons cobweb di data tahunan; H1: jalur produksi tidak bisa diuji bulanan | Terbukti (keterbatasan data); kebutuhan = implikasi |

## 3. Yang tidak direkomendasikan (ditahan)

| Usulan | Alasan ditahan | Dasar |
| --- | --- | --- |
| Model peringatan dini otomatis untuk cabai rawit | Alarm rawit belum jelas lebih tepat dari menebak acak (lift 1,18; interval 0,92-1,50) | H4 final (D-63); ambang lebih ketat = future work (D-64) |
| Pengaturan pola tanam untuk meredam siklus harga ("cobweb") | Tidak ada respons luas panen terhadap harga tahun lalu | H5 |
| Operasi pasar besar khusus di bulan Lebaran | Bulan Idulfitri tidak lebih mahal setelah kontrol musim, pasokan, dan cuaca | H6 final |
| Intervensi khusus di tingkat pedagang besar karena "margin melebar" | Margin melebar tidak didukung data; peran pedagang besar vs produsen tertahan oleh kualitas harga produsen | H2 bagian 5 |
| Bantuan berbasis harga saat musim hujan berlebih | Hujan di atas normal tidak diikuti kenaikan harga produsen (rawit justru turun). Kerugian petani mungkin ada tetapi tidak terlihat di harga | H1 |
| Klaim besaran penghematan dari peringatan dini | Redaman belum pernah diukur; semua angka penghematan di skenario adalah asumsi | Skenario (D-64) |

## 4. Future work

1. Ambang alarm rawit yang lebih ketat, ditetapkan sebelum backtest baru (D-64).
2. Model khusus spike nasional, karena lonjakan serentak (H3, H4 dugaan 3).
3. Ulangi H1 dan H4 rawit dengan harga produsen yang lebih sering diperbarui (R3).
4. Ukur redaman dari data intervensi (R8), lalu hitung ulang skenario dengan redaman terukur.
5. Validasi cuaca reanalysis terhadap stasiun BMKG di beberapa sentra (H1 keterbatasan).
6. Verifikasi cuti bersama 2020 dan Natal 2018, 2019, 2022 ke dokumen SKB (D-56).
7. Event study Idulfitri per tahun, untuk menguji apakah jendela mahal sekitar Lebaran berasal dari satu-dua tahun (H6 dugaan 1).

## 5. So what

Lonjakan harga cabai adalah guncangan pasokan yang serentak secara nasional, dengan kemarau di sentra sebagai pendorong yang paling konsisten terukur. Lebaran dan siklus tanam bukan pendorong yang terlihat di data. Biayanya bagi rumah tangga belasan triliun rupiah dalam empat tahun.

Langkah yang paling bisa dibenarkan oleh data sekarang:
- memakai peringatan dini cabai merah sebagai daftar pantau;
- memantau kekeringan di sentra rawit;
- memperbaiki data yang membuat sisa pertanyaan belum terjawab: harga produsen yang lebih sering diperbarui, produksi bulanan, dan catatan intervensi.

Investasi besar dalam intervensi berbasis peringatan dini sebaiknya menunggu efektivitas intervensi terukur.
