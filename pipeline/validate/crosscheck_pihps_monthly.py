"""Cross-check harga bulanan hasil hitung sendiri vs angka bulanan PIHPS (tipe_laporan=3), D-18.

Angka PIHPS bulanan hanya pembanding, tidak pernah dipakai mengisi nilai. Yang dibandingkan adalah rata-rata
dari hari terisi (sebelum imputation) untuk cabai_merah dan cabai_rawit, tiga tipe harga, 34 provinsi + nasional.
"""
import json
import re

import numpy as np
import pandas as pd

from pipeline.readers import COMMODITY_LABELS, PRICE_TYPE_LABELS, RAW, ROOT, load_pihps_provinces, parse_price

MONTH_COLUMN = re.compile(r"^[A-Z][a-z]{2} \d{4}$")
FILE_NAME = re.compile(r"pt(\d)_(cat_\d)_")


def load_pihps_monthly():
    provinces = load_pihps_provinces()
    records = []
    for path in sorted((RAW / "pihps" / "monthly").glob("pt*.json")):
        if path.name.endswith(".meta.json"):
            continue
        price_type, commodity = FILE_NAME.match(path.name).groups()
        for row in json.loads(path.read_text(encoding="utf-8"))["data"]:
            province_id = 0 if row["level"] == 0 else provinces.get(row["name"])
            if province_id is None:
                continue
            for key, value in row.items():
                if MONTH_COLUMN.match(key):
                    records.append((int(price_type), commodity, province_id, str(pd.Period(pd.to_datetime(key, format="%b %Y"), "M")), parse_price(value)))
    return pd.DataFrame(records, columns=["price_type_id", "commodity_id", "province_id", "month", "price_pihps"])


def run():
    ours = pd.read_parquet(ROOT / "data" / "interim" / "price_monthly_observed.parquet")
    ours = ours[ours["commodity_id"].isin(["cat_7", "cat_8"])]
    merged = ours.merge(load_pihps_monthly(), on=["price_type_id", "commodity_id", "province_id", "month"], how="inner")
    merged = merged[merged["month"] != merged["month"].max()]  # November 2026 parsial di kedua sumber
    both = merged.dropna(subset=["price_observed", "price_pihps"]).copy()
    both["selisih_pct"] = (both["price_observed"] - both["price_pihps"]).abs() / both["price_pihps"] * 100

    summary = both.groupby("price_type_id")["selisih_pct"].agg(
        n="size", median="median", p95=lambda s: s.quantile(0.95), maks="max",
        dalam_1pct=lambda s: (s <= 1).mean() * 100, dalam_5pct=lambda s: (s <= 5).mean() * 100,
    ).reset_index()
    summary.insert(0, "tipe_harga", summary.pop("price_type_id").map(PRICE_TYPE_LABELS))

    only_pihps = merged[merged["price_observed"].isna() & merged["price_pihps"].notna()]
    only_ours = merged[merged["price_observed"].notna() & merged["price_pihps"].isna()]
    worst = both.sort_values("selisih_pct", ascending=False).head(10).copy()
    worst["tipe_harga"] = worst["price_type_id"].map(PRICE_TYPE_LABELS)
    worst["komoditas"] = worst["commodity_id"].map(COMMODITY_LABELS)
    return {
        "summary": summary,
        "n_compared": len(both),
        "only_pihps": len(only_pihps),
        "only_pihps_days": only_pihps["n_days_observed"].describe()[["min", "max"]].tolist() if len(only_pihps) else [],
        "only_ours": len(only_ours),
        "worst": worst[["tipe_harga", "komoditas", "province_id", "month", "n_days_observed", "price_observed", "price_pihps", "selisih_pct"]],
    }


if __name__ == "__main__":
    result = run()
    print(result["summary"].round(2).to_string(index=False))
    print("hanya PIHPS:", result["only_pihps"], result["only_pihps_days"], "| hanya kita:", result["only_ours"])
    print(result["worst"].round(1).to_string(index=False))
