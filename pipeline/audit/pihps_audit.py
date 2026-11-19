"""Audit completeness harga PIHPS: sumber x provinsi x bulan, tanpa mengubah data.

Output (pipeline/audit/reports/):
  pihps_monthly_coverage.csv   hari terisi per tipe harga x komoditas x provinsi x bulan
  pihps_series_summary.csv     profil gap per seri (dipakai merancang treatment di fase transform)
  pihps_year_coverage.csv      persen bulan valid per provinsi x tahun
  pihps_weekly_coverage.csv    persen minggu terisi per provinsi x tahun
  pihps_audit.md               laporan: ringkasan, tabel tahunan, heatmap missing, profil gap
"""
import numpy as np
import pandas as pd

from pipeline.rules import MAX_FILL_GAP, TIER_DESCRIPTIVE_MIN_SHARE, TIER_MAIN_MIN_SHARE, assign_tier, gap_profile
from pipeline.audit.loaders import (
    COMMODITY_LABELS,
    CORE_START,
    FIRST_MONTH,
    LAST_MONTH,
    MIN_VALID_DAYS,
    MODEL_END,
    PRICE_TYPE_LABELS,
    RAW,
    REPORTS,
    load_pihps_grid,
    load_pihps_provinces,
    months,
    to_markdown,
    weekdays_per_month,
    write_report,
)

NATIONAL = "Semua Provinsi"
HEATMAP_COMMODITIES = ["cat_7", "cat_8"]


def monthly_coverage(daily, province_names):
    """Hari terisi per bulan untuk semua kombinasi seri, termasuk seri yang tidak ada di respons (nol hari)."""
    observed = (
        daily.assign(month=pd.PeriodIndex(pd.to_datetime(daily["date"]), freq="M"))
        .groupby(["price_type_id", "commodity_id", "province", "month"])["price"]
        .count()
    )
    full_index = pd.MultiIndex.from_product(
        [sorted(PRICE_TYPE_LABELS), list(COMMODITY_LABELS), [NATIONAL] + province_names, months()],
        names=["price_type_id", "commodity_id", "province", "month"],
    )
    coverage = observed.reindex(full_index, fill_value=0).rename("n_days_observed").reset_index()
    coverage["n_weekdays"] = coverage["month"].map(weekdays_per_month())
    coverage["is_valid"] = coverage["n_days_observed"] >= MIN_VALID_DAYS
    return coverage


def series_summary(coverage):
    core = coverage[(coverage["month"] >= CORE_START) & (coverage["month"] <= MODEL_END)]
    rows = []
    for (price_type, commodity, province), group in core.groupby(["price_type_id", "commodity_id", "province"]):
        group = group.sort_values("month")
        everything = coverage[(coverage["price_type_id"] == price_type) & (coverage["commodity_id"] == commodity) & (coverage["province"] == province)]
        valid_months = everything[everything["is_valid"]]["month"]
        profile = gap_profile(group["is_valid"])
        rows.append(
            {
                "price_type": PRICE_TYPE_LABELS[price_type],
                "commodity": COMMODITY_LABELS[commodity],
                "province": province,
                "core_months": len(group),
                "valid_months": int(group["is_valid"].sum()),
                "valid_share": group["is_valid"].mean(),
                "first_valid_month": str(valid_months.min()) if len(valid_months) else "",
                "last_valid_month": str(valid_months.max()) if len(valid_months) else "",
                "nov_2026_days": int(everything[everything["month"] == LAST_MONTH]["n_days_observed"].iloc[0]),
                **profile,
                "tier": assign_tier(group["is_valid"].mean(), profile["longest_interior_gap"]),
            }
        )
    return pd.DataFrame(rows)


def year_coverage(coverage):
    core = coverage[(coverage["month"] >= CORE_START) & (coverage["month"] <= MODEL_END)].copy()
    core["year"] = core["month"].dt.year
    table = core.groupby(["price_type_id", "commodity_id", "province", "year"])["is_valid"].mean().mul(100).round(0).reset_index()
    table["price_type"] = table["price_type_id"].map(PRICE_TYPE_LABELS)
    table["commodity"] = table["commodity_id"].map(COMMODITY_LABELS)
    return table[["price_type", "commodity", "province", "year", "is_valid"]].rename(columns={"is_valid": "pct_valid_months"})


def heatmap(coverage, price_type, commodity, province_names):
    """Heatmap teks: satu karakter per bulan. # = valid (>=10 hari), + = parsial (1-9 hari), . = kosong."""
    sub = coverage[(coverage["price_type_id"] == price_type) & (coverage["commodity_id"] == commodity)]
    month_list = months()
    ruler = "".join(str(month.year)[-1] if month.month == 1 else " " for month in month_list)
    width = max(len(name) for name in province_names + [NATIONAL])
    lines = [f"{'':{width}}  {ruler}"]
    for province in [NATIONAL] + province_names:
        days = sub[sub["province"] == province].set_index("month")["n_days_observed"].reindex(month_list)
        cells = "".join("#" if d >= MIN_VALID_DAYS else ("+" if d > 0 else ".") for d in days)
        lines.append(f"{province:{width}}  {cells}")
    return "```\n" + "\n".join(lines) + "\n```"


def holiday_check(daily):
    """Apakah PIHPS mengisi hari kerja yang jatuh pada hari besar? (pertanyaan terbuka D-18)"""
    holidays = pd.read_csv(RAW / "calendar" / "holidays.csv", parse_dates=["date"])["date"].dt.date
    national = daily[(daily["province"] == NATIONAL) & (daily["commodity_id"] == "cat_7")].copy()
    national["is_festival_day"] = national["date"].isin(set(holidays))
    result = national.groupby(["price_type_id", "is_festival_day"])["price"].agg(hari="size", terisi="count").reset_index()
    result["pct_terisi"] = result["terisi"] / result["hari"] * 100
    result["price_type"] = result["price_type_id"].map(PRICE_TYPE_LABELS)
    return result[["price_type", "is_festival_day", "hari", "terisi", "pct_terisi"]]


def value_sanity(daily):
    provinces = daily[daily["level"] == 1]
    stats = provinces.groupby(["price_type_id", "commodity_id"])["price"].agg(
        min_price="min", median_price="median", max_price="max",
        zero_or_negative=lambda s: int((s <= 0).sum()),
    ).reset_index()
    stats["price_type"] = stats["price_type_id"].map(PRICE_TYPE_LABELS)
    stats["commodity"] = stats["commodity_id"].map(COMMODITY_LABELS)
    return stats[["price_type", "commodity", "min_price", "median_price", "max_price", "zero_or_negative"]]


def weekly_coverage(weekly, province_names):
    weekly = weekly.assign(year=pd.to_datetime(weekly["date"]).dt.year)
    grouped = weekly.groupby(["price_type_id", "commodity_id", "province", "year"])["price"].agg(minggu="size", terisi="count").reset_index()
    grouped["pct_terisi"] = (grouped["terisi"] / grouped["minggu"] * 100).round(0)
    grouped["price_type"] = grouped["price_type_id"].map(PRICE_TYPE_LABELS)
    grouped["commodity"] = grouped["commodity_id"].map(COMMODITY_LABELS)
    return grouped[["price_type", "commodity", "province", "year", "minggu", "terisi", "pct_terisi"]]


def run():
    province_ids = load_pihps_provinces()
    province_names = sorted(province_ids)
    daily = load_pihps_grid("daily")
    weekly = load_pihps_grid("weekly")

    names_in_data = set(daily[daily["level"] == 1]["province"])
    unmatched = sorted(names_in_data - set(province_names))
    coverage = monthly_coverage(daily, province_names)
    summary = series_summary(coverage)
    years = year_coverage(coverage)
    weekly_table = weekly_coverage(weekly, province_names)

    REPORTS.mkdir(parents=True, exist_ok=True)
    coverage_out = coverage.assign(price_type=coverage["price_type_id"].map(PRICE_TYPE_LABELS), commodity=coverage["commodity_id"].map(COMMODITY_LABELS), month=coverage["month"].astype(str))
    coverage_out[["price_type", "commodity", "province", "month", "n_days_observed", "n_weekdays", "is_valid"]].to_csv(REPORTS / "pihps_monthly_coverage.csv", index=False)
    summary.to_csv(REPORTS / "pihps_series_summary.csv", index=False)
    years.to_csv(REPORTS / "pihps_year_coverage.csv", index=False)
    weekly_table.to_csv(REPORTS / "pihps_weekly_coverage.csv", index=False)

    lines = ["# Audit PIHPS (harga harian, bulanan hasil hitung sendiri)", ""]
    lines += [
        f"Periode data {FIRST_MONTH} sampai {LAST_MONTH} (November 2026 parsial). Periode inti {CORE_START} sampai {MODEL_END} ({len(months(CORE_START, MODEL_END))} bulan). "
        f"Bulan dianggap valid kalau minimal {MIN_VALID_DAYS} hari kerja terisi. Survei PIHPS hanya Senin-Jumat, sehingga file harian berisi kolom hari kerja saja.",
        "",
        f"- File harian: {daily[['price_type_id','commodity_id']].drop_duplicates().shape[0]} kombinasi tipe harga x komoditas; {len(daily):,} sel harian.",
        f"- Baris provinsi di data yang tidak ada di referensi 34 provinsi: {unmatched or 'tidak ada'}. Baris ini dikeluarkan dari tabel di bawah dan dicatat sebagai anomali sumber (bagian 8).",
        "- Baris yang tidak muncul di respons (misalnya provinsi tanpa data harga produsen) diperlakukan sebagai seri kosong (nol hari).",
        "",
        "## 1. Ringkasan profil gap per tipe harga dan komoditas",
        "",
        "Hanya periode inti (Jan 2019 - Okt 2026). Gap tengah 1-6 bulan linear interpolation pada log price (D-43), lebih dari 6 bulan tetap NULL (D-35). "
        "Gap di awal dan akhir seri tidak pernah di-impute.",
        "",
    ]
    overview = (
        summary.groupby(["price_type", "commodity"])
        .agg(seri=("province", "size"), lengkap=("valid_share", lambda s: int((s == 1).sum())), valid_rata2_pct=("valid_share", lambda s: s.mean() * 100),
             leading=("leading_gap", lambda s: int((s > 0).sum())), trailing=("trailing_gap", lambda s: int((s > 0).sum())),
             gap_diisi=("filled_gaps", "sum"), gap_tetap_null=("null_gaps", "sum"),
             bulan_linear=("months_linear_log", "sum"), bulan_null=("months_left_null", "sum"))
        .reset_index()
    )
    lines += [to_markdown(overview), ""]
    tiers = summary.pivot_table(index=["price_type", "commodity"], columns="tier", values="province", aggfunc="count", fill_value=0).reset_index()
    for tier_name in ("main", "descriptive", "excluded"):
        if tier_name not in tiers.columns:
            tiers[tier_name] = 0
    tiers = tiers[["price_type", "commodity", "main", "descriptive", "excluded"]]
    lines += [f"### Seri per tier (D-35)", "",
              f"`main`: bulan valid >= {TIER_MAIN_MIN_SHARE:.0%} dan gap tengah terpanjang <= {MAX_FILL_GAP} bulan. `descriptive`: bulan valid {TIER_DESCRIPTIVE_MIN_SHARE:.0%}-{TIER_MAIN_MIN_SHARE:.0%} "
              f"(atau >= {TIER_MAIN_MIN_SHARE:.0%} tetapi gap tengah > {MAX_FILL_GAP} bulan); di-impute dengan aturan sama, hanya untuk deskriptif dan sensitivity check. "
              f"`excluded`: < {TIER_DESCRIPTIVE_MIN_SHARE:.0%}, tidak di-impute dan tidak dipakai di model. Satu baris nasional ikut dihitung per kombinasi.", "",
              to_markdown(tiers), ""]

    lines += ["## 2. Seri bermasalah (bulan valid < 80% pada periode inti)", ""]
    weak = summary[summary["valid_share"] < 0.8].sort_values(["price_type", "commodity", "valid_share"])
    weak_view = weak[["price_type", "commodity", "province", "tier", "valid_months", "core_months", "first_valid_month", "last_valid_month", "leading_gap", "trailing_gap", "longest_interior_gap"]].copy()
    lines += [f"{len(weak)} seri dari {len(summary)}.", "", to_markdown(weak_view) if len(weak) else "Tidak ada.", ""]

    lines += ["## 3. Persen bulan valid per provinsi x tahun (periode inti)", "", "Tabel lengkap semua komoditas ada di `pihps_year_coverage.csv`; di sini cabai_merah dan cabai_rawit.", ""]
    for price_type in sorted(PRICE_TYPE_LABELS):
        for commodity in HEATMAP_COMMODITIES:
            part = years[(years["price_type"] == PRICE_TYPE_LABELS[price_type]) & (years["commodity"] == COMMODITY_LABELS[commodity])]
            pivot = part.pivot(index="province", columns="year", values="pct_valid_months").reindex([NATIONAL] + province_names)
            lines += [f"### {PRICE_TYPE_LABELS[price_type]} - {COMMODITY_LABELS[commodity]}", "", to_markdown(pivot, index=True, floatfmt="{:.0f}"), ""]

    lines += ["## 4. Heatmap missing value", "",
              "Satu karakter per bulan mulai Januari 2018 (angka di penggaris = digit terakhir tahun, ditaruh di bulan Januari). `#` valid (>=10 hari), `+` parsial (1-9 hari, dianggap missing), `.` kosong. Kolom terakhir = November 2026 (parsial).", ""]
    for price_type in sorted(PRICE_TYPE_LABELS):
        for commodity in HEATMAP_COMMODITIES:
            lines += [f"### {PRICE_TYPE_LABELS[price_type]} - {COMMODITY_LABELS[commodity]}", "", heatmap(coverage, price_type, commodity, province_names), ""]

    lines += ["## 5. Hari besar dan hari kerja", "",
              "Pertanyaan terbuka D-18: apakah hari kerja yang jatuh pada hari besar (libur nasional empat perayaan di kalender raw) terisi? Dihitung pada baris nasional cabai_merah.", "",
              to_markdown(holiday_check(daily)), ""]

    lines += ["## 6. Sanity check nilai harian (baris provinsi)", "", to_markdown(value_sanity(daily)), ""]

    lines += ["## 7. Data mingguan (untuk lead-lag)", "",
              "Persen minggu terisi per tahun untuk baris nasional; semua provinsi ada di `pihps_weekly_coverage.csv`. Data mingguan tidak di-impute (D-12).", ""]
    national_weekly = weekly_table[weekly_table["province"] == NATIONAL].pivot_table(index=["price_type", "commodity"], columns="year", values="pct_terisi").reset_index()
    lines += [to_markdown(national_weekly, floatfmt="{:.0f}"), ""]
    weekly_low = weekly_table[(weekly_table["year"] >= 2019) & (weekly_table["province"] != NATIONAL)].groupby(["price_type", "commodity"])["pct_terisi"].agg(rata2="mean", minimum="min").reset_index()
    lines += ["Rata-rata dan minimum persen minggu terisi pada baris provinsi, 2019-2026:", "", to_markdown(weekly_low), ""]

    stray = daily[(daily["level"] == 1) & (daily["province"].isin(unmatched)) & daily["price"].notna()]
    lines += ["## 8. Anomali sumber: baris provinsi tidak dikenal", "",
              "Nilai yang terisi pada baris yang namanya tidak ada di `GetRefProvince`:", "",
              to_markdown(stray[["province", "price_type_id", "commodity_id", "date", "price"]].astype(str)) if len(stray) else "Tidak ada.", ""]

    write_report("pihps_audit.md", "\n".join(lines))
    return summary
