# AS-IS Process Map: Rantai Pasok Cabai

Dokumen ini menggambarkan bagaimana cabai bergerak dari petani sampai konsumen **saat ini**, beserta faktor yang memengaruhi volume dan harga di tiap tahap. Tujuannya satu: menunjukkan di titik mana data publik bisa mengamati rantai ini, dan di titik mana tidak.

> **Catatan sumber.** Gambaran ini disusun dari secondary research (pernyataan pejabat, pedagang, petani, dan penelitian yang dikutip media; lihat daftar sumber di Project Charter), bukan dari wawancara atau survei lapangan. Detail tiap tahap (misalnya peran pengepul) perlu dibaca sebagai generalisasi, dan bisa berbeda antar sentra.

## 1. Peta proses

```mermaid
flowchart LR
    subgraph EXT["Faktor eksternal"]
        direction TB
        CUACA["Cuaca dan iklim<br/>curah hujan, kelembapan, ENSO"]
        HAMA["Hama dan penyakit tanaman"]
        HARIBESAR["Hari besar dan libur<br/>Idulfitri, Iduladha, Natal-Tahun Baru"]
        KEBIJAKAN["Kebijakan dan intervensi<br/>Harga Acuan, operasi pasar, TPID"]
    end

    subgraph HULU["Hulu: sentra produksi"]
        direction LR
        INPUT["Input usaha tani<br/>benih, pupuk, pestisida"] --> TANAM["Petani menanam"]
        TANAM --> PANEN["Petani panen"]
        PANEN --> JUAL["Jual hasil panen<br/>harga produsen"]
    end

    subgraph TENGAH["Tengah: pengumpulan dan distribusi"]
        direction LR
        KUMPUL["Pengepul dan pedagang desa"] --> PBS["Pedagang besar sentra"]
        PBS --> ANTAR["Distribusi antardaerah<br/>darat dan laut"]
        ANTAR --> PBD["Pedagang besar<br/>daerah tujuan"]
    end

    subgraph HILIR["Hilir: pasar konsumen"]
        direction LR
        ECER["Pasar tradisional<br/>harga eceran"]
        MODERN["Pasar modern"]
        KONS["Konsumen<br/>rumah tangga, warung, resto, katering"]
        ECER --> KONS
        MODERN --> KONS
    end

    JUAL --> KUMPUL
    PBD --> ECER
    PBD --> MODERN

    CUACA -. "memengaruhi hasil panen" .-> TANAM
    CUACA -. "memengaruhi hasil panen" .-> PANEN
    HAMA -. "gagal panen" .-> PANEN
    HARIBESAR -. "lonjakan permintaan" .-> KONS
    KEBIJAKAN -. "intervensi pasokan dan harga" .-> PBD
    KEBIJAKAN -. "intervensi pasokan dan harga" .-> ECER
```

## 2. Titik pengamatan data

Peta berikut menandai tahap mana yang punya data publik, dan sumbernya.

```mermaid
flowchart LR
    PANEN["Panen dan produksi"] --- D1["BDSP: produksi tahunan per provinsi<br/>Buletin Pusdatin: produksi bulanan nasional"]
    JUAL["Harga produsen"] --- D2["PIHPS price_type_id = 4"]
    PBS["Pedagang besar"] --- D3["PIHPS price_type_id = 3"]
    ECER["Pasar tradisional"] --- D4["PIHPS price_type_id = 1"]
    MODERN["Pasar modern"] --- D5["PIHPS price_type_id = 2<br/>tidak dipakai di core dataset"]
    CUACA["Cuaca di sentra"] --- D6["Open-Meteo Historical API"]
    ENSO["El Nino dan La Nina"] --- D7["NOAA ONI"]
    HB["Hari besar"] --- D8["Kalender disusun sendiri"]
    ANTAR["Arus distribusi antardaerah"] --- X1["TIDAK ADA data publik<br/>proxy: price disparity antarprovinsi"]
    PASOK["Pasokan harian Pasar Induk Kramat Jati"] --- X2["TIDAK ADA data publik<br/>tidak masuk core dataset"]
    TANAMAN["Luas tanam bulanan"] --- X3["TIDAK dipublikasikan<br/>tidak masuk core dataset"]

    classDef ada fill:#e8f3ea,stroke:#3b7a4b,color:#1d3a26
    classDef kosong fill:#fbeaea,stroke:#b04545,color:#4a1d1d
    class D1,D2,D3,D4,D5,D6,D7,D8 ada
    class X1,X2,X3 kosong
```

## 3. Tahap, masalah yang diketahui, dan kaitannya dengan hipotesis

| Tahap | Apa yang terjadi | Titik rawan (dari secondary research) | Hipotesis terkait | Data yang mengamati |
| --- | --- | --- | --- | --- |
| Input dan tanam | Petani memutuskan kapan dan seberapa luas menanam | Keputusan tanam mengikuti harga musim sebelumnya, sehingga ramai-ramai menanam lalu panen berlimpah (cobweb cycle) | H5 | Produksi bulanan (hasil disagregasi); luas tanam tidak tersedia |
| Panen | Hasil panen ditentukan cuaca dan hama | Curah hujan ekstrem dan serangan penyakit menurunkan volume | H1 | Curah hujan Open-Meteo, ONI, produksi |
| Harga produsen | Petani menjual ke pengepul | Harga anjlok saat panen ramai, naik cepat saat gagal panen | H1, H2 | PIHPS tipe 4 |
| Pengumpulan | Pengepul dan pedagang besar sentra mengumpulkan volume | Tidak ada data publik di level ini selain harga pedagang besar | H2 | PIHPS tipe 3 |
| Distribusi antardaerah | Cabai dikirim dari sentra ke daerah konsumsi dan daerah defisit | Daerah jauh dari sentra menanggung biaya dan waktu angkut; nasional surplus tapi daerah tertentu defisit | H3 | Tidak ada data arus; proxy price disparity antarprovinsi |
| Harga eceran | Pedagang pasar menjual ke konsumen | Kenaikan diteruskan cepat, penurunan lambat (asymmetric price transmission) | H2 | PIHPS tipe 1 |
| Konsumsi | Rumah tangga dan usaha makanan membeli | Permintaan naik di sekitar hari besar | H6 | Kalender hari besar |
| Intervensi | Pemerintah dan TPID menekan harga | Data intervensi tidak lengkap, sehingga policy evaluation tidak masuk scope | di luar scope | Tidak tersedia |

## 4. Batasan peta ini

- Rantai digambar linear supaya mudah dibaca. Di lapangan satu pedagang bisa melewati beberapa tahap, dan sebagian petani menjual langsung ke pasar.
- Tahap "distribusi antardaerah" adalah kotak hitam. H3 hanya bisa diuji lewat proxy (price disparity), jadi kesimpulannya akan berbentuk asosiasi, bukan bukti mekanisme.
- Peta ini akan diperbarui kalau hasil analisis menunjukkan tahap lain yang ikut berperan. Perubahan dicatat di `decision_log.md`.
