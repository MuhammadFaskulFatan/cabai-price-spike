"""Jalankan semua audit completeness.

    python -m pipeline.audit.completeness [--only pihps|bdsp|buletin|oni|calendar|weather]
"""
import argparse

from pipeline.audit import bdsp_audit, buletin_audit, calendar_audit, oni_audit, pihps_audit, weather_audit

AUDITS = {
    "pihps": pihps_audit,
    "bdsp": bdsp_audit,
    "buletin": buletin_audit,
    "oni": oni_audit,
    "calendar": calendar_audit,
    "weather": weather_audit,
}


def main():
    parser = argparse.ArgumentParser(description="Audit completeness data raw")
    parser.add_argument("--only", choices=list(AUDITS))
    args = parser.parse_args()
    for name, module in AUDITS.items():
        if args.only in (None, name):
            print(f"=== audit {name} ===")
            module.run()


if __name__ == "__main__":
    main()
