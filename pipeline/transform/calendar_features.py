"""Variabel kalender dan ENSO per bulan: dim_month dan fact_oni_monthly.

dim_month: periode inti dan model, bulan parsial, hari kerja, jumlah hari libur nasional (Idulfitri, Iduladha, Natal,
Tahun Baru), cuti bersama (D-38), dan jarak bulan ke Idulfitri.
months_to_idulfitri: selisih bulan terhadap bulan 1 Syawal terdekat; negatif = sebelum Idulfitri, positif = sesudah,
0 = bulan Idulfitri. Kalau dua Idulfitri berjarak sama (6 bulan), dipilih Idulfitri yang akan datang (negatif).
fact_oni_monthly: season NOAA dipetakan ke bulan tengahnya (DJF -> Januari); bulan tanpa nilai tetap NULL (D-16).
"""
import numpy as np
import pandas as pd

from pipeline.audit.oni_audit import load_oni
from pipeline.extract.calendar_holidays import holiday_source_level
from pipeline.readers import CORE_START, FIRST_MONTH, LAST_MONTH, MODEL_END, RAW, ROOT, months, weekdays_per_month

OUT = ROOT / "data" / "interim"

# Idulfitri 2027 menurut SKB 3 Menteri 2027 (ditandatangani 15 Sep 2026; tanggal pasti menunggu sidang isbat). Hanya dipakai
# supaya bulan akhir 2026 menghitung jarak ke Idulfitri yang akan datang; tidak masuk kalender raw.
IDULFITRI_2027_MONTH = pd.Period("2027-03", "M")

# bulan yang cuti bersamanya belum terverifikasi (D-38): seluruh 2020, cuti Natal 2018/2019/2022, dan cuti Iduladha 2018-2019, 2021-2022
CUTI_UNVERIFIED_MONTHS = {pd.Period(m, "M") for m in ["2018-08", "2018-12", "2019-08", "2019-12", "2021-07", "2022-07", "2022-12"]} | {
    pd.Period(f"2020-{m:02d}", "M") for m in range(1, 13)
}


def months_to_idulfitri(holidays, month_list):
    first_syawal = holidays[holidays["holiday"] == "idulfitri"].groupby(holidays["date"].dt.year)["date"].min()
    idulfitri_months = [pd.Period(d, "M") for d in first_syawal] + [IDULFITRI_2027_MONTH]
    result = []
    for month in month_list:
        offsets = [(month - m).n for m in idulfitri_months]  # positif = sesudah Idulfitri
        best = min(offsets, key=lambda o: (abs(o), o))  # seri: pilih yang negatif (akan datang)
        result.append(best)
    return result


def build_dim_month():
    holidays = pd.read_csv(RAW / "calendar" / "holidays.csv", parse_dates=["date"])
    cuti = pd.read_csv(RAW / "calendar" / "cuti_bersama.csv", parse_dates=["date"])
    month_list = months()

    holidays["month"] = holidays["date"].dt.to_period("M")
    holidays["is_weekday"] = holidays["date"].dt.dayofweek < 5
    cuti["month"] = cuti["date"].dt.to_period("M")

    frame = pd.DataFrame({"month": month_list})
    frame["month_start"] = [m.to_timestamp().date() for m in month_list]
    frame["year"] = [m.year for m in month_list]
    frame["month_number"] = [m.month for m in month_list]
    frame["in_core_period"] = frame["month"] >= CORE_START
    frame["is_partial_month"] = frame["month"] == LAST_MONTH
    frame["in_model_period"] = (frame["month"] >= CORE_START) & (frame["month"] <= MODEL_END)
    frame["n_weekdays"] = frame["month"].map(weekdays_per_month()).astype(int)
    frame["n_holiday_days"] = frame["month"].map(holidays.groupby("month").size()).fillna(0).astype(int)
    frame["n_holiday_weekdays"] = frame["month"].map(holidays[holidays["is_weekday"]].groupby("month").size()).fillna(0).astype(int)
    frame["n_cuti_bersama_days"] = frame["month"].map(cuti.groupby("month").size()).fillna(0).astype(int)
    cuti_secondary = cuti[cuti["verification"] != "official"].groupby("month").size()
    frame["cuti_bersama_verified"] = [
        (m not in CUTI_UNVERIFIED_MONTHS) and (m not in cuti_secondary.index) for m in frame["month"]
    ]
    frame["months_to_idulfitri"] = months_to_idulfitri(holidays, month_list)
    return frame


def build_dim_holiday():
    """Tabel libur: libur nasional dan cuti bersama, dengan source_level official/secondary (D-46).

    Cuti bersama yang belum terverifikasi tidak ada di tabel (dibiarkan kosong, D-38)."""
    holidays = pd.read_csv(RAW / "calendar" / "holidays.csv", parse_dates=["date"])
    holidays["is_cuti_bersama"] = False
    holidays["source_level"] = [holiday_source_level(h, d.year) for h, d in zip(holidays["holiday"], holidays["date"])]
    cuti = pd.read_csv(RAW / "calendar" / "cuti_bersama.csv", parse_dates=["date"])
    cuti = cuti.assign(is_cuti_bersama=True, source_level=cuti["verification"])[["date", "holiday", "is_cuti_bersama", "source_level"]]
    table = pd.concat([holidays, cuti], ignore_index=True).sort_values(["date", "is_cuti_bersama"]).reset_index(drop=True)
    table["date"] = table["date"].dt.date
    return table


def build_oni():
    oni = load_oni().set_index("month")
    frame = pd.DataFrame({"month": months()})
    frame["month_start"] = [m.to_timestamp().date() for m in frame["month"]]
    frame["season_label"] = frame["month"].map(oni["SEAS"])
    frame["oni_anomaly"] = frame["month"].map(oni["ANOM"])
    frame["enso_phase"] = np.select(
        [frame["oni_anomaly"] >= 0.5, frame["oni_anomaly"] <= -0.5, frame["oni_anomaly"].notna()],
        ["el_nino", "la_nina", "neutral"],
        default=None,
    )
    return frame


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    dim_month = build_dim_month()
    oni = build_oni()
    dim_holiday = build_dim_holiday()
    dim_holiday.to_parquet(OUT / "dim_holiday.parquet", index=False)
    dim_month.assign(month=dim_month["month"].astype(str)).to_parquet(OUT / "dim_month.parquet", index=False)
    oni.assign(month=oni["month"].astype(str)).to_parquet(OUT / "fact_oni_monthly.parquet", index=False)
    print(f"dim_holiday {len(dim_holiday)} hari (official {int((dim_holiday['source_level'] == 'official').sum())}) | dim_month {len(dim_month)} bulan | ONI terisi {int(oni['oni_anomaly'].notna().sum())} dari {len(oni)} bulan")
    return dim_month, oni


if __name__ == "__main__":
    run()
