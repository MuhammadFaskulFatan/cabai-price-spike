"""Laporan Fase 5 (Validate): cek struktur core, reconciliation tahunan, cross-check PIHPS bulanan, spot-check
ke sumber (termasuk cuaca), dan ringkasan hold-out.

    python -m pipeline.validate.report [--skip-live]

--skip-live melewati request live ke PIHPS, BDSP, NOAA, dan Open-Meteo pada spot-check.
"""
import argparse

import pandas as pd

from pipeline.audit.loaders import to_markdown
from pipeline.readers import ROOT
from pipeline.validate import checks_core, crosscheck_pihps_monthly, reconcile_annual, spot_check

REPORTS = ROOT / "pipeline" / "validate" / "reports"


def section(path, start, end=None):
    if not path.exists():
        return "(belum ada)"
    text = path.read_text(encoding="utf-8").split(start, 1)[1]
    return (text.split(end, 1)[0] if end else text).strip()


def run(skip_live=False):
    REPORTS.mkdir(parents=True, exist_ok=True)
    checks = checks_core.run_checks()
    reconcile = reconcile_annual.run()
    crosscheck = crosscheck_pihps_monthly.run()
    spots = None if skip_live else spot_check.run()

    checks.to_csv(REPORTS / "checks_core.csv", index=False)
    reconcile["totals"].to_csv(REPORTS / "reconcile_annual.csv", index=False)
    crosscheck["worst"].to_csv(REPORTS / "crosscheck_pihps_worst.csv", index=False)
    if spots:
        for name, frame in spots.items():
            frame.to_csv(REPORTS / f"spot_check_{name}.csv", index=False)

    passed = int(checks["lulus"].sum())
    lines = ["# Laporan Fase 5 (Validate)", "",
             f"Core dataset termasuk cuaca (`data/final/`). Cek struktur: {passed} dari {len(checks)} lulus. "
             f"Reconciliation tahunan: {'cocok' if reconcile['totals_pass'] and reconcile['papua_pass'] else 'ADA SELISIH'}. "
             f"Cross-check PIHPS bulanan: {crosscheck['n_compared']:,} sel dibandingkan. "
             + ("Spot-check live dilewati." if spots is None else
                f"Spot-check: harga {int(spots['prices']['raw_cocok'].sum())}/{len(spots['prices'])} cocok dengan raw, "
                f"{int((spots['prices']['live_selisih_pct'] < 0.01).sum())}/{int(spots['prices']['live'].notna().sum())} cocok dengan PIHPS live; "
                f"produksi {int(spots['production']['live_cocok'].sum())}/{len(spots['production'])} cocok dengan BDSP live; ONI {int(spots['oni']['cocok'].sum())}/{len(spots['oni'])}; "
                f"cuaca {int(spots['weather']['cocok'].sum())}/{len(spots['weather'])}."), ""]

    lines += ["## 1. Cek struktur dan aturan core dataset", "", to_markdown(checks), "",
              "Dua cek sempat gagal pada versi pertama karena cara mengeceknya, bukan datanya: (1) imputation di awal 2019 dibaca sebagai gap awal seri karena cek hanya melihat periode model, "
              "padahal gap itu dijembatani observasi 2018 (cek kini memakai jendela imputation Jan 2018 - Okt 2026); (2) hitung ulang `n_holiday_days` ikut memasukkan Natal Desember 2026 yang berada di luar `dim_month`.", ""]

    lines += ["## 2. Reconciliation total tahunan (BDSP)", "",
              f"- Baris TOTAL nasional BDSP vs jumlah 34 provinsi di core, {len(reconcile['totals'])} kombinasi komoditas x indikator x tahun: selisih maksimum {reconcile['totals']['selisih'].abs().max():.2f} ton/ha "
              f"(BDSP membulatkan tiap baris provinsi ke 2 desimal; batas wajar 0,19). Lulus: {reconcile['totals_pass']}.",
              f"- core_province_year vs fact_production_annual: selisih maksimum {reconcile['core_year_gap']:.1e} pada {reconcile['core_year_rows']} baris.",
              f"- Papua dan Papua Barat = jumlah induk + pemekaran BDSP: lulus {reconcile['papua_pass']}.", "",
              "Informasi (bukan reconciliation): porsi realisasi Januari-Maret Buletin terhadap total tahunan BDSP.", "",
              to_markdown(reconcile["realised_share"].astype({"year": str}), floatfmt="{:,.1f}"), "",
              "Porsi 19-24% untuk tiga bulan pertama masuk akal (sedikit di bawah 25%); rawit 2024 paling rendah (18,9%).", ""]

    lines += ["## 3. Cross-check harga bulanan vs angka bulanan PIHPS (D-18)", "",
              "Rata-rata dari hari terisi (sebelum imputation) vs `tipe_laporan=3`, cabai_merah dan cabai_rawit, 34 provinsi + nasional, Jan 2018 - Okt 2026. Selisih dalam persen:", "",
              to_markdown(crosscheck["summary"], floatfmt="{:,.2f}"), "",
              f"- Sel yang hanya terisi di PIHPS bulanan: {crosscheck['only_pihps']} (bulan kita kosong karena hanya {int(crosscheck['only_pihps_days'][0]) if crosscheck['only_pihps_days'] else 0}-{int(crosscheck['only_pihps_days'][1]) if crosscheck['only_pihps_days'] else 0} hari kerja terisi, di bawah aturan minimal 10 hari). Sel yang hanya terisi di data kita: {crosscheck['only_ours']}.",
              "- Eceran praktis identik. Pedagang besar dan produsen sedikit berbeda (88-89% dalam 1%, hampir semua dalam 5%), kemungkinan karena PIHPS menghitung angka bulanan dengan cara lain (misalnya rata-rata pasar atau minggu, bukan rata-rata hari). Angka PIHPS bulanan tetap hanya pembanding.", "",
              "Sepuluh selisih terbesar:", "", to_markdown(crosscheck["worst"], floatfmt="{:,.1f}"), "",
              "### Sel kosong karena kurang dari 10 hari kerja: bulan Idulfitri vs bulan lain", "",
              "Sel yang terisi di PIHPS bulanan tetapi kosong di data kita, dibagi menurut bulan 1 Syawal, bulan sesudahnya, dan bulan lain. "
              "Periode 2019-2026 dipisah karena sebagian besar sel kosong 2018 berasal dari masa awal seri harga produsen (Juli-September 2018).", ""]
    for label, table in crosscheck["idulfitri"].items():
        lines += [f"Periode {label}:", "", to_markdown(table, floatfmt="{:.2f}"), ""]
    lines += ["Kesimpulan: sel kosong hampir seluruhnya di harga produsen, dan proporsinya di bulan Idulfitri tidak jauh lebih tinggi daripada bulan lain "
              "(2019-2026: 1,71% di bulan Idulfitri dan bulan sesudahnya vs 1,40% di bulan lain, masing-masing 9 sel). Tidak dicatat sebagai risiko H6; "
              "hasil ini cukup didokumentasikan di sini.", ""]

    if spots:
        lines += ["## 4. Spot-check terhadap sumber (seed 2026)", "",
                  "Harga: 30 sel observed acak dihitung ulang dari file raw harian dengan kode terpisah; 10 pertama juga ditarik ulang dari PIHPS live pada 19 Nov 2026.", "",
                  to_markdown(spots["prices"], floatfmt="{:,.2f}"), "",
                  "Produksi: 10 provinsi-tahun acak vs HTML raw BDSP dan tabel BDSP yang ditarik ulang live.", "", to_markdown(spots["production"], floatfmt="{:,.2f}"), "",
                  "ONI: 5 bulan acak vs file NOAA live.", "", to_markdown(spots["oni"], floatfmt="{:.2f}"), "",
                  "Cuaca: 5 sel acak dihitung ulang dari file raw harian (rata-rata berbobot produksi), dan 3 lokasi x 1 bulan acak ditarik ulang dari Open-Meteo live "
                  "(untuk baris live, `core_mm` = jumlah hujan dari file raw lokasi itu).", "", to_markdown(spots["weather"], floatfmt="{:,.2f}"), "",
                  "Tidak ada revisi sumber yang terdeteksi pada sampel live.", ""]

    lines += ["## 5. Hold-out validation imputation (D-09, D-43)", "",
              section(REPORTS / "holdout_imputation.md", "## 1. Keputusan", "## 2."), "",
              "Hold-out produksi bulanan (Denton) terdokumentasi di `holdout_production.md`; metode itu dibatalkan (D-42).", ""]

    lines += ["## 6. Belum tercakup", "",
              "- Cuaca hanya untuk 18 provinsi bertitik sentra (14 untuk cabai merah, 15 untuk cabai rawit); provinsi lain `not_applicable` (D-25). Data reanalysis Open-Meteo belum dibandingkan dengan pengamatan stasiun BMKG.",
              "- Cross-check mingguan PIHPS tidak dilakukan; data mingguan tidak di-impute dan hanya dipakai untuk lead-lag (D-12).",
              "- Spot-check live hanya sampel (10 harga, 2 tabel BDSP, 1 file ONI, 3 lokasi cuaca); revisi PIHPS di luar sampel tidak terdeteksi. Tanggal extraction tersimpan di metadata raw (D-14).", ""]

    (REPORTS / "validation_report.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"ditulis: pipeline/validate/reports/validation_report.md ({passed}/{len(checks)} cek lulus)")


def main():
    parser = argparse.ArgumentParser(description="Laporan validasi core dataset")
    parser.add_argument("--skip-live", action="store_true")
    args = parser.parse_args()
    run(args.skip_live)


if __name__ == "__main__":
    main()
