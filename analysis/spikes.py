"""Definisi price spike yang dipakai EDA dan uji hipotesis.

Price spike: harga eceran bulanan >= ambang x median 12 bulan sebelumnya (t-12 sampai t-1, trailing, tanpa
look-ahead). Ambang utama 1,25; sensitivity 1,15 dan 1,35. Bulan spike yang berurutan digabung menjadi satu episode.
"""
import numpy as np
import pandas as pd

MAIN_THRESHOLD = 1.25
SENSITIVITY_THRESHOLDS = (1.15, 1.35)
WINDOW = 12


def flag_spikes(prices, threshold=MAIN_THRESHOLD):
    """prices: Series harga bulanan berindeks bulan, terurut. Kembalikan DataFrame price, baseline, ratio, is_spike.

    Baseline butuh 12 bulan sebelumnya yang lengkap; kalau ada yang kosong, bulan itu tidak dinilai (NaN)."""
    baseline = prices.shift(1).rolling(WINDOW, min_periods=WINDOW).median()
    ratio = prices / baseline
    is_spike = (ratio >= threshold).where(ratio.notna())
    return pd.DataFrame({"price": prices, "baseline": baseline, "ratio": ratio, "is_spike": is_spike})


def episodes(flags):
    """Gabungkan bulan spike berurutan menjadi episode: awal, akhir, durasi, rasio puncak, bulan puncak, harga puncak."""
    spike = flags["is_spike"].fillna(False).astype(bool).to_numpy()
    rows, start = [], None
    index = flags.index
    for i, value in enumerate(list(spike) + [False]):
        if value and start is None:
            start = i
        elif not value and start is not None:
            part = flags.iloc[start:i]
            peak = part["ratio"].idxmax()
            rows.append({"start": index[start], "end": index[i - 1], "months": i - start,
                         "peak_month": peak, "peak_ratio": part["ratio"].max(), "peak_price": part.loc[peak, "price"]})
            start = None
    return pd.DataFrame(rows, columns=["start", "end", "months", "peak_month", "peak_ratio", "peak_price"])
