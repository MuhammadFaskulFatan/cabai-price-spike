"""Jalankan pipeline dari awal. Saat ini baru tahap extract; audit sampai validate menyusul.

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

EXTRACT_STEPS = [
    ("pihps", pihps),
    ("bdsp", bdsp),
    ("noaa_oni", noaa_oni),
    ("calendar_holidays", calendar_holidays),
    ("buletin_pusdatin", buletin_pusdatin),
    ("buletin_tables", buletin_tables),
    ("open_meteo", open_meteo),
]

STAGES = {"extract": EXTRACT_STEPS, "audit": [("completeness", completeness)]}


def run_stage(name, refresh):
    for step_name, module in STAGES[name]:
        print(f"\n=== {name}: {step_name} ===")
        sys.argv = [step_name] + (["--refresh"] if refresh and name == "extract" else [])
        module.main()


def main():
    parser = argparse.ArgumentParser(description="Jalankan pipeline cabai-price-spike")
    parser.add_argument("--stage", choices=list(STAGES))
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    for stage in [args.stage] if args.stage else STAGES:
        run_stage(stage, args.refresh)


if __name__ == "__main__":
    main()
