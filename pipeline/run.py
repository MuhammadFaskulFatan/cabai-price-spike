"""Jalankan pipeline dari awal. Tahap: extract, audit, transform, validate.

    python -m pipeline.run                 # semua tahap yang sudah ada
    python -m pipeline.run --stage extract
    python -m pipeline.run --refresh       # tarik ulang; file raw lama tidak ditimpa

Urutan extract penting: BDSP harus selesai sebelum Open-Meteo karena titik sentra dipilih
dari data produksi kabupaten.
"""
import argparse
import sys

from pipeline.audit import completeness
from pipeline.extract import (
    bdsp,
    buletin_pusdatin,
    buletin_tables,
    calendar_holidays,
    noaa_oni,
    open_meteo,
    pihps,
)
from pipeline.transform import (
    aggregate_monthly,
    aggregate_weekly,
    calendar_features,
    geography,
    weather_features,
    impute_price,
    integrate,
    production,
    report,
)
from pipeline.validate import holdout_imputation
from pipeline.validate import report as validation_report

EXTRACT_STEPS = [
    ("pihps", pihps),
    ("bdsp", bdsp),
    ("noaa_oni", noaa_oni),
    ("calendar_holidays", calendar_holidays),
    ("buletin_pusdatin", buletin_pusdatin),
    ("buletin_tables", buletin_tables),
    ("open_meteo", open_meteo),
]

# hold-out harga dijalankan sebelum imputation karena memilih metode (D-09). Hold-out produksi (Denton) hanya
# dokumentasi keputusan D-42: jalankan manual dengan python -m pipeline.validate.holdout_production
TRANSFORM_STEPS = [
    ("aggregate_monthly", aggregate_monthly),
    ("aggregate_weekly", aggregate_weekly),
    ("holdout_imputation", holdout_imputation),
    ("impute_price", impute_price),
    ("production", production),
    ("calendar_features", calendar_features),
    ("geography", geography),
    ("weather_features", weather_features),
    ("integrate", integrate),
    ("report", report),
]

STAGES = {"extract": EXTRACT_STEPS, "audit": [("completeness", completeness)], "transform": TRANSFORM_STEPS,
          "validate": [("validation_report", validation_report)]}


def run_stage(name, refresh):
    for step_name, module in STAGES[name]:
        print(f"\n=== {name}: {step_name} ===")
        sys.argv = [step_name] + (["--refresh"] if refresh and name == "extract" else [])
        # modul extract dan audit punya main() dengan argparse; modul transform cukup run()
        (module.main if hasattr(module, "main") else module.run)()


def main():
    parser = argparse.ArgumentParser(description="Jalankan pipeline cabai-price-spike")
    parser.add_argument("--stage", choices=list(STAGES))
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    for stage in [args.stage] if args.stage else STAGES:
        run_stage(stage, args.refresh)


if __name__ == "__main__":
    main()
