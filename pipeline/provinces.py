"""Pemetaan kode provinsi BPS/BDSP ke 34 provinsi PIHPS (D-17).

PIHPS memakai 34 provinsi. BDSP sudah memuat provinsi pemekaran di Papua; semuanya
dipetakan ke provinsi induk supaya grain provinsi seragam di seluruh sumber.
"""

# kode BPS -> (province_id PIHPS, nama PIHPS)
BPS_TO_PIHPS = {
    "11": (1, "Aceh"),
    "12": (2, "Sumatera Utara"),
    "13": (3, "Sumatera Barat"),
    "14": (4, "Riau"),
    "15": (6, "Jambi"),
    "16": (8, "Sumatera Selatan"),
    "17": (7, "Bengkulu"),
    "18": (10, "Lampung"),
    "19": (9, "Kepulauan Bangka Belitung"),
    "21": (5, "Kepulauan Riau"),
    "31": (13, "DKI Jakarta"),
    "32": (12, "Jawa Barat"),
    "33": (14, "Jawa Tengah"),
    "34": (15, "DI Yogyakarta"),
    "35": (16, "Jawa Timur"),
    "36": (11, "Banten"),
    "51": (17, "Bali"),
    "52": (18, "Nusa Tenggara Barat"),
    "53": (19, "Nusa Tenggara Timur"),
    "61": (20, "Kalimantan Barat"),
    "62": (22, "Kalimantan Tengah"),
    "63": (21, "Kalimantan Selatan"),
    "64": (23, "Kalimantan Timur"),
    "65": (24, "Kalimantan Utara"),
    "71": (29, "Sulawesi Utara"),
    "72": (28, "Sulawesi Tengah"),
    "73": (26, "Sulawesi Selatan"),
    "74": (27, "Sulawesi Tenggara"),
    "75": (25, "Gorontalo"),
    "76": (30, "Sulawesi Barat"),
    "81": (31, "Maluku"),
    "82": (32, "Maluku Utara"),
    "91": (34, "Papua Barat"),
    "92": (34, "Papua Barat"),  # Papua Barat Daya -> induk Papua Barat
    "94": (33, "Papua"),
    "95": (33, "Papua"),  # Papua Selatan -> induk Papua
    "96": (33, "Papua"),  # Papua Tengah -> induk Papua
    "97": (33, "Papua"),  # Papua Pegunungan -> induk Papua
}
