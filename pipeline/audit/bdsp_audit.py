"""Audit data BDSP (produksi dan luas panen tahunan, 2018-2025).

Output (pipeline/audit/reports/): bdsp_province_year.csv dan bdsp_audit.md.
Yang diperiksa: nol vs terisi per provinsi x tahun, konsistensi total, konsistensi kabupaten vs provinsi,
produktivitas (ton/ha), cek apakah cabe keriting subset dari cabe besar (D-28), dan perubahan tahunan nasional.
"""
import json
import re

import numpy as np
import pandas as pd
from bs4 import BeautifulSoup

from pipeline.audit.loaders import RAW, REPORTS, parse_bdsp_number, to_markdown, write_report
from pipeline.provinces import BPS_TO_PIHPS

YEARS = list(range(2018, 2026))
COMMODITIES = {"cabe_besar": "cabe besar", "cabe_keriting": "cabe keriting", "cabe_rawit": "cabe rawit"}
INDICATORS = {"produksi": "produksi", "luas_panen": "luas panen"}
TO_BASE_UNIT = {"Ton": 1.0, "Kuintal": 0.1, "Ha": 1.0}  # produksi dalam ton


def read_table(path):
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "lxml")
    rows = {}
    for tr in soup.find_all("tr"):
        cells = [cell.get_text(strip=True) for cell in tr.find_all(["th", "td"])]
        if len(cells) >= 10 and re.match(r"^\d{2,4} - ", cells[1]):
            rows[cells[1]] = [parse_bdsp_number(value) for value in cells[2:10]]
        elif cells and cells[0] == "TOTAL":
            rows["TOTAL"] = [parse_bdsp_number(value) for value in cells[1:9]]
    return rows


def unit_of(path):
    meta = json.loads(path.with_name(path.name + ".meta.json").read_text(encoding="utf-8"))
    return meta["request"]["body"]["satuannm"]


def load_province_tables():
    """Tabel panjang: commodity, indicator, bps_code, bdsp_name, parent_id, year, value (ton atau ha)."""
    records, units = [], {}
    for commodity in COMMODITIES:
        for indicator in INDICATORS:
            path = RAW / "bdsp" / "provinsi" / f"{commodity}_{indicator}.html"
            unit = unit_of(path)
            units[(commodity, indicator)] = unit
            for label, values in read_table(path).items():
                if label == "TOTAL":
                    continue
                code, name = label.split(" - ", 1)
                for year, value in zip(YEARS, values):
                    records.append((commodity, indicator, code, name, BPS_TO_PIHPS[code][0], year, value * TO_BASE_UNIT[unit]))
    return pd.DataFrame(records, columns=["commodity", "indicator", "bps_code", "bdsp_name", "province_id", "year", "value"]), units


def total_row_check():
    rows = []
    for commodity in COMMODITIES:
        for indicator in INDICATORS:
            table = read_table(RAW / "bdsp" / "provinsi" / f"{commodity}_{indicator}.html")
            total = np.array(table.pop("TOTAL"))
            summed = np.sum(list(table.values()), axis=0)
            rows.append({"komoditas": COMMODITIES[commodity], "indikator": INDICATORS[indicator],
                         "selisih_terbesar_pct": float(np.max(np.abs(summed - total) / np.where(total == 0, 1, total)) * 100)})
    return pd.DataFrame(rows)


def regency_vs_province(frame):
    """Jumlah kabupaten (baris TOTAL berkas kabupaten) dibanding nilai provinsi, per provinsi x tahun."""
    rows = []
    for commodity in COMMODITIES:
        for indicator in INDICATORS:
            for path in sorted((RAW / "bdsp" / "kabupaten").glob(f"{commodity}_{indicator}_prov*.html")):
                code = path.stem.rsplit("prov", 1)[1]
                table = read_table(path)
                total = table.get("TOTAL")
                if total is None:
                    continue
                factor = TO_BASE_UNIT[unit_of(path)]
                n_regencies = len([k for k in table if k != "TOTAL"])
                province_values = frame[(frame["commodity"] == commodity) & (frame["indicator"] == indicator) & (frame["bps_code"] == code)].set_index("year")["value"]
                for year, value in zip(YEARS, total):
                    reference = province_values.get(year, np.nan)
                    rows.append((COMMODITIES[commodity], INDICATORS[indicator], code, year, value * factor, reference, n_regencies))
    result = pd.DataFrame(rows, columns=["komoditas", "indikator", "bps_code", "year", "jumlah_kabupaten", "nilai_provinsi", "n_kabupaten"])
    result["selisih_pct"] = (result["jumlah_kabupaten"] - result["nilai_provinsi"]).abs() / result["nilai_provinsi"].replace(0, np.nan) * 100
    return result


def run():
    frame, units = load_province_tables()

    lines = ["# Audit BDSP (produksi dan luas panen tahunan)", "",
             "Sumber: BDSP Kementan, level provinsi (38 provinsi BDSP) dan kabupaten, 2018-2025, status Angka Tetap. "
             "Produksi dalam ton (cabe keriting dikonversi dari kuintal); luas panen dalam hektare. Angka 2025 belum bisa diverifikasi ke rilis BPS, jadi ditandai preliminary (D-29).", "",
             "Satuan asli di BDSP: " + "; ".join(f"{COMMODITIES[c]} {INDICATORS[i]} = {u}" for (c, i), u in units.items()), ""]

    lines += ["## 1. Konsistensi baris TOTAL vs jumlah provinsi", "", to_markdown(total_row_check(), floatfmt="{:.4f}"), ""]

    # 2. nol vs terisi
    lines += ["## 2. Nilai nol per provinsi x tahun", "",
              "Nol di BDSP berarti tidak ada produksi atau tidak dilaporkan; keduanya tidak bisa dibedakan dari data. Dihitung pada 38 provinsi BDSP.", ""]
    zero_rows = []
    for (commodity, indicator), group in frame.groupby(["commodity", "indicator"]):
        pivot = group.pivot(index="bdsp_name", columns="year", values="value")
        zero_rows.append({"komoditas": COMMODITIES[commodity], "indikator": INDICATORS[indicator],
                          **{str(y): int((pivot[y] == 0).sum()) for y in YEARS}, "nol_semua_tahun": int((pivot == 0).all(axis=1).sum())})
    lines += ["Jumlah provinsi bernilai nol per tahun:", "", to_markdown(pd.DataFrame(zero_rows)), ""]
    always_zero = {}
    for (commodity, indicator), group in frame.groupby(["commodity", "indicator"]):
        pivot = group.pivot(index="bdsp_name", columns="year", values="value")
        always_zero[(COMMODITIES[commodity], INDICATORS[indicator])] = sorted(pivot.index[(pivot == 0).all(axis=1)])
    lines += ["Provinsi yang nol di semua tahun:", ""]
    for (commodity, indicator), names in always_zero.items():
        lines.append(f"- {commodity} / {indicator}: {', '.join(names) or 'tidak ada'}")
    lines.append("")

    new_provinces = frame[frame["bps_code"].isin(["92", "95", "96", "97"])].pivot_table(index=["commodity", "indicator", "bdsp_name"], columns="year", values="value").round(0)
    first_nonzero = {}
    for key, row in new_provinces.iterrows():
        nonzero = [y for y in YEARS if row[y] > 0]
        first_nonzero[key] = nonzero[0] if nonzero else None
    lines += ["Provinsi pemekaran Papua (dipetakan ke induk, D-17): tahun pertama bernilai non-nol.", "",
              to_markdown(pd.DataFrame([{"komoditas": COMMODITIES[c], "indikator": INDICATORS[i], "provinsi": n, "tahun_pertama_nonnol": y or "tidak pernah"} for (c, i, n), y in first_nonzero.items()])), ""]

    # 3. kabupaten vs provinsi
    comparison = regency_vs_province(frame)
    big = comparison[comparison["selisih_pct"] > 1]
    lines += ["## 3. Jumlah kabupaten vs nilai provinsi", "",
              f"{len(comparison):,} kombinasi komoditas x indikator x provinsi x tahun diperiksa; selisih terbesar {comparison['selisih_pct'].max():.4f}%. Kombinasi dengan selisih > 1%: {len(big)}.", ""]
    if len(big):
        lines += [to_markdown(big.head(30)), ""]

    # 4. produktivitas
    yield_rows = []
    for commodity in COMMODITIES:
        production = frame[(frame["commodity"] == commodity) & (frame["indicator"] == "produksi")].set_index(["bdsp_name", "year"])["value"]
        area = frame[(frame["commodity"] == commodity) & (frame["indicator"] == "luas_panen")].set_index(["bdsp_name", "year"])["value"]
        productivity = (production / area.replace(0, np.nan)).dropna()
        productivity = productivity[production.reindex(productivity.index) > 0]
        yield_rows.append({"komoditas": COMMODITIES[commodity], "n": len(productivity), "min_ton_per_ha": productivity.min(), "median": productivity.median(),
                           "max_ton_per_ha": productivity.max(), "di_bawah_1": int((productivity < 1).sum()), "di_atas_30": int((productivity > 30).sum()),
                           "produksi_ada_luas_nol": int(((production > 0) & (area == 0)).sum())})
    lines += ["## 4. Produktivitas (ton per hektare)", "",
              "Cabai umumnya sekitar 5-15 ton/ha; nilai di luar 1-30 ton/ha ditandai untuk dicek.", "", to_markdown(pd.DataFrame(yield_rows), floatfmt="{:.2f}"), ""]

    # 5. keriting vs besar
    lines += ["## 5. Cek subset: cabe keriting vs cabe besar (D-28)", ""]
    def pair(indicator):
        besar = frame[(frame["commodity"] == "cabe_besar") & (frame["indicator"] == indicator)].set_index(["bdsp_name", "year"])["value"]
        keriting = frame[(frame["commodity"] == "cabe_keriting") & (frame["indicator"] == indicator)].set_index(["bdsp_name", "year"])["value"]
        return besar, keriting
    for indicator in INDICATORS:
        besar, keriting = pair(indicator)
        positive = keriting[keriting > 0].index
        greater = [(k, besar[k], keriting[k]) for k in positive if keriting[k] > besar[k] + max(0.02, 1e-6 * besar[k])]
        identical = [(k, round(besar[k], 2)) for k in positive if abs(keriting[k] - besar[k]) <= max(0.02, 1e-6 * besar[k])]
        lines += [f"- **{INDICATORS[indicator]}**: {len(positive)} provinsi-tahun dengan keriting > 0; keriting > besar: {len(greater)}; "
                  f"nilai identik dengan besar: {len(identical)} {[f'{n} {y}' for (n, y), _ in identical]}; besar > 0 tetapi keriting = 0: {int(((besar > 0) & (keriting == 0)).sum())}."]
    lines.append("")
    ratio_rows = []
    for year in YEARS:
        total = frame[(frame["year"] == year) & (frame["indicator"] == "produksi")].groupby("commodity")["value"].sum()
        ratio_rows.append({"tahun": str(year), "besar_ton": total["cabe_besar"], "keriting_ton": total["cabe_keriting"],
                           "rasio_keriting_besar": total["cabe_keriting"] / total["cabe_besar"], "rawit_ton": total["cabe_rawit"]})
    lines += ["Total nasional dan rasio:", "", to_markdown(pd.DataFrame(ratio_rows), floatfmt="{:,.2f}"), ""]

    # 6. perubahan tahunan nasional
    lines += ["## 6. Total nasional per tahun dan perubahan tahunan", ""]
    change_rows = []
    for (commodity, indicator), group in frame.groupby(["commodity", "indicator"]):
        totals = group.groupby("year")["value"].sum()
        for year in YEARS[1:]:
            if totals[year - 1] > 0:
                change_rows.append({"komoditas": COMMODITIES[commodity], "indikator": INDICATORS[indicator], "tahun": str(year), "total": totals[year], "perubahan_pct": (totals[year] / totals[year - 1] - 1) * 100})
    changes = pd.DataFrame(change_rows)
    lines += ["Perubahan tahunan yang lebih dari 20% (naik atau turun):", "", to_markdown(changes[changes["perubahan_pct"].abs() > 20], floatfmt="{:,.1f}"), ""]
    pivot_total = frame.groupby(["commodity", "indicator", "year"])["value"].sum().unstack("year").round(0).reset_index()
    pivot_total["commodity"] = pivot_total["commodity"].map(COMMODITIES)
    pivot_total["indicator"] = pivot_total["indicator"].map(INDICATORS)
    lines += ["Total nasional (ton atau ha):", "", to_markdown(pivot_total, floatfmt="{:,.0f}"), ""]

    # 7. Provinsi induk non-nol
    lines += ["## 7. Provinsi produsen per tahun (34 provinsi PIHPS, setelah pemetaan induk)", ""]
    parent = frame[frame["indicator"] == "produksi"].groupby(["commodity", "province_id", "year"])["value"].sum().reset_index()
    parent_rows = []
    for commodity in COMMODITIES:
        part = parent[parent["commodity"] == commodity]
        parent_rows.append({"komoditas": COMMODITIES[commodity], **{str(y): int((part[part["year"] == y]["value"] > 0).sum()) for y in YEARS}})
    lines += ["Jumlah provinsi (dari 34) dengan produksi > 0:", "", to_markdown(pd.DataFrame(parent_rows)), ""]

    write_report("bdsp_audit.md", "\n".join(lines))
    REPORTS.mkdir(parents=True, exist_ok=True)
    frame.to_csv(REPORTS / "bdsp_province_year.csv", index=False)
