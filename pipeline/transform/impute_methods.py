"""Metode imputation harga bulanan. Semua metode bekerja pada satu series (PeriodIndex bulanan, NaN = missing)
dan hanya mengembalikan nilai untuk posisi di antara observasi pertama dan terakhir: gap di awal dan akhir
tidak pernah diisi (tanpa ekstrapolasi).

impute_price.py hanya memakai linear_log (D-43). kalman dan locf tetap di sini sebagai kandidat dan pembanding
di harness hold-out (pipeline/validate/holdout_imputation.py), supaya keputusan membatalkan Kalman bisa diulang.
"""
import warnings

import numpy as np
import pandas as pd
from statsmodels.tsa.statespace.structural import UnobservedComponents

SEASONAL_PERIOD = 12
MIN_OBS_FOR_SEASONAL = 2 * SEASONAL_PERIOD


def _interior(values):
    valid = values.dropna()
    return valid.index.min(), valid.index.max()


def linear_log(values):
    """Linear interpolation pada log price, antar observasi terdekat."""
    first, last = _interior(values)
    logged = np.log(values.loc[first:last])
    filled = logged.interpolate(method="linear", limit_area="inside")
    return np.exp(filled)


def kalman(values):
    """Kalman smoothing, state-space trend + seasonal (local linear trend + seasonal 12) pada log price.

    Parameter diestimasi dari seluruh observasi series; nilai pada bulan missing berasal dari smoothed state.
    Series yang terlalu pendek untuk musiman 12 bulan memakai trend saja.
    """
    first, last = _interior(values)
    logged = np.log(values.loc[first:last])
    seasonal = SEASONAL_PERIOD if logged.notna().sum() >= MIN_OBS_FOR_SEASONAL else None
    model = UnobservedComponents(logged.to_numpy(), level="lltrend", seasonal=seasonal)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = model.fit(disp=False, maxiter=200)
    signal = np.asarray(result.level.smoothed)
    if seasonal:
        signal = signal + np.asarray(result.seasonal.smoothed)
    return pd.Series(np.exp(signal), index=logged.index)


def locf(values):
    """Pembanding sederhana untuk hold-out: nilai observasi terakhir diteruskan."""
    first, last = _interior(values)
    return values.loc[first:last].ffill()


METHODS = {"linear_log": linear_log, "kalman": kalman, "locf": locf}
