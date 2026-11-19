"""Integrasi ke core dataset (tanpa cuaca; cuaca menyusul setelah data Open-Meteo lengkap).

Output di data/final/:
  core_province_month.csv   provinsi x bulan x grup komoditas (cabai_merah, cabai_rawit), 2018-01 sampai 2026-11
  core_province_year.csv    provinsi x tahun x grup komoditas, untuk uji H5 (D-27)
  price_monthly_variants.csv  empat varian (merah besar, merah keriting, rawit merah, rawit hijau), deskriptif (US3)
  price_monthly_national.csv  baris nasional ("Semua Provinsi") semua komoditas
  dim_province.csv, dim_commodity.csv, dim_price_type.csv, dim_month.csv, dim_holiday.csv (libur + cuti bersama, source_level)
Tiap nilai yang di-impute atau diestimasi punya pasangan flag is_imputed dan impute_method; sel kosong hanya
sah dengan alasan yang tercatat (di luar periode, seri excluded, gap tengah > 6 bulan, NTT produsen, produksi 2026).
Produksi di core_province_month = angka tahunan BDSP (`production_annual_ton`), bukan estimasi bulanan (D-42).
"""
import numpy as np
import pandas as pd

from pipeline.readers import COMMODITY_LABELS, PRICE_TYPE_LABELS, ROOT, load_pihps_provinces

INTERIM = ROOT / "data" / "interim"
FINAL = ROOT / "data" / "final"

PRICE_COLUMNS = {1: "price_retail", 3: "price_wholesale", 4: "price_producer"}
CORE_COMMODITY = {"cat_7": "cabai_merah", "cat_8": "cabai_rawit"}
VARIANTS = ["com_13", "com_14", "com_16", "com_15"]
NO_PRODUCER_ANALYSIS = {19}  # NTT keluar dari analisis harga produsen (D-03)

ISLAND_GROUP = {
    **{i: "Sumatera" for i in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)},
    **{i: "Jawa" for i in (11, 12, 13, 14, 15, 16)},
    **{i: "Bali dan Nusa Tenggara" for i in (17, 18, 19)},
    **{i: "Kalimantan" for i in (20, 21, 22, 23, 24)},
    **{i: "Sulawesi" for i in (25, 26, 27, 28, 29, 30)},
    **{i: "Maluku" for i in (31, 32)},
    **{i: "Papua" for i in (33, 34)},
}


def build_dim_province():
    provinces = load_pihps_provinces()
    frame = pd.DataFrame({"province_id": sorted(provinces.values())})
    names = {v: k for k, v in provinces.items()}
    frame["province_name"] = frame["province_id"].map(names)
    frame["island_group"] = frame["province_id"].map(ISLAND_GROUP)
    frame["in_producer_price_analysis"] = ~frame["province_id"].isin(NO_PRODUCER_ANALYSIS)
    return frame


def load_prices():
    prices = pd.read_parquet(INTERIM / "fact_price_monthly.parquet")
    prices["month_start"] = pd.to_datetime(prices["month"] + "-01").dt.date
    return prices


def price_wide(prices):
    """Satu baris per provinsi x bulan x grup; kolom harga per tipe dengan flag-nya."""
    core = prices[prices["commodity_id"].isin(CORE_COMMODITY) & (prices["province_id"] > 0)].copy()
    core["commodity_group"] = core["commodity_id"].map(CORE_COMMODITY)
    pieces = []
    for price_type, name in PRICE_COLUMNS.items():
        part = core[core["price_type_id"] == price_type].set_index(["province_id", "month_start", "commodity_group"])
        pieces.append(
            pd.DataFrame(
                {
                    name: part["price_idr_per_kg"],
                    f"{name}_is_imputed": part["is_imputed"],
                    f"{name}_impute_method": part["impute_method"],
                    f"{name}_tier": part["tier"],
                    f"{name}_n_days": part["n_days_observed"],
                }
            )
        )
    return pd.concat(pieces, axis=1).reset_index()


def build_core_month(dim_province, dim_month):
    skeleton = pd.MultiIndex.from_product(
        [dim_province["province_id"], dim_month["month_start"], list(CORE_COMMODITY.values())], names=["province_id", "month_start", "commodity_group"]
    ).to_frame(index=False)

    core = skeleton.merge(price_wide(load_prices()), on=["province_id", "month_start", "commodity_group"], how="left")

    # produksi: angka tahunan BDSP, sama untuk 12 bulan dalam tahunnya; 2026 NULL (D-42)
    annual = pd.read_parquet(INTERIM / "fact_production_annual.parquet")
    annual = annual[annual["commodity_group"].isin(CORE_COMMODITY.values())]
    annual = annual.rename(columns={"production_ton": "production_annual_ton", "is_preliminary": "production_annual_preliminary"})
    core["year"] = pd.to_datetime(core["month_start"]).dt.year
    core = core.merge(annual[["province_id", "year", "commodity_group", "production_annual_ton", "production_annual_preliminary"]],
                      on=["province_id", "year", "commodity_group"], how="left").drop(columns="year")

    oni = pd.read_parquet(INTERIM / "fact_oni_monthly.parquet")[["month_start", "oni_anomaly", "enso_phase"]]
    oni["month_start"] = pd.to_datetime(oni["month_start"]).dt.date
    core = core.merge(oni, on="month_start", how="left")

    calendar = dim_month[["month_start", "in_core_period", "in_model_period", "is_partial_month", "n_weekdays", "n_holiday_days", "n_holiday_weekdays",
                          "n_cuti_bersama_days", "cuti_bersama_verified", "months_to_idulfitri"]]
    core = core.merge(calendar, on="month_start", how="left")
    core = core.merge(dim_province[["province_id", "in_producer_price_analysis"]], on="province_id", how="left")
    return core.sort_values(["province_id", "commodity_group", "month_start"]).reset_index(drop=True)


def build_core_year(dim_province):
    annual = pd.read_parquet(INTERIM / "fact_production_annual.parquet")
    annual = annual[annual["commodity_group"].isin(CORE_COMMODITY.values())].copy()

    prices = load_prices()
    producer = prices[(prices["price_type_id"] == 4) & prices["commodity_id"].isin(CORE_COMMODITY) & (prices["province_id"] > 0)].copy()
    producer["commodity_group"] = producer["commodity_id"].map(CORE_COMMODITY)
    producer["year"] = pd.to_datetime(producer["month_start"]).dt.year
    producer = producer[~producer["is_partial_month"]]
    yearly = producer.groupby(["province_id", "year", "commodity_group"]).agg(
        producer_price_annual_mean=("price_idr_per_kg", "mean"),
        producer_price_n_months=("price_idr_per_kg", "count"),
        producer_price_n_imputed=("is_imputed", "sum"),
        producer_price_tier=("tier", "first"),
    ).reset_index()
    result = annual.merge(yearly, on=["province_id", "year", "commodity_group"], how="left")
    result["producer_price_n_months"] = result["producer_price_n_months"].fillna(0).astype(int)
    result = result.merge(dim_province[["province_id", "in_producer_price_analysis"]], on="province_id", how="left")
    return result.sort_values(["province_id", "commodity_group", "year"]).reset_index(drop=True)


def long_prices(prices, commodities, national):
    selected = prices[prices["commodity_id"].isin(commodities) & ((prices["province_id"] == 0) == national)].copy()
    selected["commodity"] = selected["commodity_id"].map(COMMODITY_LABELS)
    selected["price_type"] = selected["price_type_id"].map(PRICE_TYPE_LABELS)
    columns = ["price_type", "commodity", "province_id", "month_start", "price_idr_per_kg", "n_days_observed", "is_imputed", "impute_method", "tier", "is_partial_month"]
    return selected[columns].sort_values(["price_type", "commodity", "province_id", "month_start"])


def run():
    FINAL.mkdir(parents=True, exist_ok=True)
    dim_province = build_dim_province()
    dim_month = pd.read_parquet(INTERIM / "dim_month.parquet").drop(columns="month")
    dim_month["month_start"] = pd.to_datetime(dim_month["month_start"]).dt.date
    core_month = build_core_month(dim_province, dim_month)
    core_year = build_core_year(dim_province)
    prices = load_prices()

    dim_commodity = pd.DataFrame({"commodity_group": ["cabai_merah", "cabai_rawit"], "commodity_label": ["Cabai merah (cabe besar)", "Cabai rawit"], "pihps_category_id": ["cat_7", "cat_8"]})
    dim_price_type = pd.DataFrame(
        {"price_type_id": [1, 2, 3, 4], "level_name": ["Pasar Tradisional", "Pasar Modern", "Pedagang Besar", "Produsen"],
         "supply_chain_stage": ["eceran", "eceran modern", "pedagang besar", "produsen (farm-gate)"], "in_core": [True, False, True, True]}
    )

    outputs = {
        "core_province_month.csv": core_month,
        "core_province_year.csv": core_year,
        "price_monthly_variants.csv": long_prices(prices, VARIANTS, national=False),
        "price_monthly_national.csv": long_prices(prices, list(COMMODITY_LABELS), national=True),
        "dim_province.csv": dim_province,
        "dim_commodity.csv": dim_commodity,
        "dim_price_type.csv": dim_price_type,
        "dim_month.csv": dim_month,
        "dim_holiday.csv": pd.read_parquet(INTERIM / "dim_holiday.parquet"),
    }
    for name, frame in outputs.items():
        frame.round(4).to_csv(FINAL / name, index=False)
        print(f"{name}: {len(frame):,} baris, {frame.shape[1]} kolom")
    return outputs


if __name__ == "__main__":
    run()
