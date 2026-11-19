"""Extract produksi dan luas panen cabai dari BDSP Kementan (subsektor Hortikultura).

Cara endpoint ditemukan: form di https://bdsp2.pertanian.go.id/bdsp/id/lokasi diisi lewat
Playwright dan request yang keluar saat tombol Cari ditekan ditangkap. Hasilnya, halaman
hanya perlu satu POST ke /bdsp/id/lokasi/result dengan body form-encoded; HTML tabel
dikembalikan langsung, jadi script ini memanggil endpoint itu tanpa browser.

Yang ditarik ke data/raw/bdsp/ (respons HTML apa adanya, 2018-2025, Angka Tetap):
  provinsi/    satu file per komoditas x indikator (semua provinsi, termasuk pemekaran)
  kabupaten/   satu file per komoditas x indikator x provinsi; dipakai memilih sentra
  ref/         daftar komoditas dan provinsi dari dropdown form

Angka berformat koma desimal ("62167,10"); parsing dilakukan di fase transform.
Jalankan:  python -m pipeline.extract.bdsp [--refresh]
"""
import argparse
import json
import time

from pipeline.extract.common import (
    RAW_DIR,
    new_session,
    request_with_retry,
    save_raw,
    target_path,
)

ROOT = "https://bdsp2.pertanian.go.id/bdsp/id/"
OUT = RAW_DIR / "bdsp"
PAUSE_SECONDS = 1.0

SUBSEKTOR = ("04", "Hortikultura")
YEAR_FROM, YEAR_TO = 2018, 2025
STATUS_ANGKA = ("6", "Angka Tetap")

# kode komoditas BDSP -> nama untuk file
COMMODITIES = {"01133": "cabe_besar", "01194": "cabe_keriting", "01132": "cabe_rawit"}
INDICATORS = ("PRODUKSI", "LUAS PANEN")
LEVELS = {"02": "Provinsi", "03": "Kabupaten"}


def post_json(session, endpoint, data):
    response = request_with_retry(session, "POST", ROOT + endpoint, data=data)
    return response.json()


def indicator_codes(session, commodity_code):
    """Cari kode indikator (PRODUKSI, LUAS PANEN) dan satuannya untuk satu komoditas."""
    listed = post_json(session, "indikator/getIndiByKomSubsek", {"subsektorcd": SUBSEKTOR[0], "komcd": commodity_code})
    found = {}
    for item in listed:
        name = item["findinm"].strip().upper()
        if name in INDICATORS:
            unit = post_json(
                session,
                "satuan/getSatuan",
                {"indikatorcd": item["findicd"], "subsektorcd": SUBSEKTOR[0], "komcd": commodity_code},
            )[0]["fsatuan"]
            found[name] = (item["findicd"], unit)
        time.sleep(PAUSE_SECONDS)
    return found


def result_body(commodity_code, commodity_name, indicator_code, indicator_name, unit, level_code, prov_code, prov_name):
    """Body yang sama dengan yang dikirim form saat tombol Cari ditekan."""
    return {
        "subsektor": SUBSEKTOR[0],
        "subsektorcd": SUBSEKTOR[0],
        "subsektornm": SUBSEKTOR[1],
        "level": level_code,
        "levelnm": LEVELS[level_code],
        "prov": prov_code,
        "provnm": prov_name,
        "sts_angka": STATUS_ANGKA[0],
        "sts_angkanm": STATUS_ANGKA[1],
        "sumb_data": "00",
        "sumb_datanm": "-- Pilih Sumber Data --",
        "tahunAwal": YEAR_FROM,
        "tahunAkhir": YEAR_TO,
        "satuannm": unit,
        "komoditas": commodity_code,
        "komoditasnm": commodity_name,
        "indikator": indicator_code,
        "indikatornm": indicator_name,
    }


def fetch_result(session, path, body, refresh):
    path = target_path(path, refresh)
    if path is None:
        return False
    response = request_with_retry(session, "POST", ROOT + "lokasi/result", data=body, timeout=180)
    n_rows = response.text.count("<tr")
    save_raw(path, response.content, "bdsp", {"url": ROOT + "lokasi/result", "method": "POST", "body": body}, n_rows=n_rows)
    time.sleep(PAUSE_SECONDS)
    return True


def main():
    parser = argparse.ArgumentParser(description="Extract BDSP ke data/raw/bdsp")
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()

    session = new_session()
    session.get(ROOT + "lokasi", timeout=60)  # ambil cookie sesi seperti browser

    provinces = request_with_retry(session, "GET", ROOT + "lokasi/getProv").json()
    commodity_list = post_json(session, "komoditas/getKomBySubsektor", {"subsektorcd": SUBSEKTOR[0]})
    for name, payload in (("getProv", provinces), ("komoditas_hortikultura", commodity_list)):
        path = target_path(OUT / "ref" / f"{name}.json", args.refresh)
        if path is not None:
            save_raw(path, json.dumps(payload, ensure_ascii=False), "bdsp", {"url": ROOT, "name": name}, n_rows=len(payload))

    commodity_names = {item["fkomcd"]: item["fkomnm"] for item in commodity_list}
    fetched = 0
    for commodity_code, file_name in COMMODITIES.items():
        commodity_name = commodity_names[commodity_code]
        for indicator_name, (indicator_code, unit) in indicator_codes(session, commodity_code).items():
            tag = f"{file_name}_{indicator_name.lower().replace(' ', '_')}"
            # level provinsi: satu request untuk semua provinsi
            body = result_body(commodity_code, commodity_name, indicator_code, indicator_name, unit, "02", "00", "--- Pilih Provinsi ---")
            fetched += fetch_result(session, OUT / "provinsi" / f"{tag}.html", body, args.refresh)
            # level kabupaten: harus per provinsi
            for province in provinces:
                body = result_body(
                    commodity_code, commodity_name, indicator_code, indicator_name, unit,
                    "03", province["fkode_prop"], province["nama_prop"],
                )
                fetched += fetch_result(
                    session, OUT / "kabupaten" / f"{tag}_prov{province['fkode_prop']}.html", body, args.refresh
                )
            print(f"{tag}: selesai")
    print(f"selesai: {fetched} file baru")


if __name__ == "__main__":
    main()
