"""Aturan data quality yang dipakai bersama oleh audit, transform, dan validate (D-35).

Satu tempat untuk semua ambang supaya angka di laporan audit dan di imputation tidak bisa berbeda.
"""

import numpy as np

MIN_VALID_DAYS = 10  # hari kerja terisi minimal agar rata-rata bulanan dianggap valid

# gap di tengah series (dalam bulan)
LINEAR_MAX_GAP = 2  # 1-2 bulan: linear interpolation pada log price
MAX_FILL_GAP = 6  # 3-6 bulan: Kalman smoothing; lebih dari 6 tetap NULL tanpa pengecualian

# tier seri harga, dihitung pada Jan 2019 - Okt 2026
TIER_MAIN_MIN_SHARE = 0.80  # bulan valid minimal, dan gap tengah terpanjang <= MAX_FILL_GAP
TIER_DESCRIPTIVE_MIN_SHARE = 0.50  # di bawah ini: excluded (tidak di-impute, tidak dipakai)

# produktivitas BDSP (ton per hektare) di luar rentang ini diberi flag is_outlier, nilai tidak diubah
YIELD_MIN, YIELD_MAX = 1.0, 30.0


def assign_tier(valid_share, longest_interior_gap):
    """main | descriptive | excluded sesuai D-35."""
    if valid_share >= TIER_MAIN_MIN_SHARE and longest_interior_gap <= MAX_FILL_GAP:
        return "main"
    if valid_share >= TIER_DESCRIPTIVE_MIN_SHARE:
        return "descriptive"
    return "excluded"


def gap_profile(valid):
    """Profil gap satu seri (array boolean bulan valid pada periode inti).

    leading/trailing tidak pernah di-impute. Gap tengah: 1-2 bulan linear, 3-6 Kalman, lebih dari 6 tetap NULL.
    """
    valid = np.asarray(valid, dtype=bool)
    size = len(valid)
    positions = np.flatnonzero(valid)
    if positions.size == 0:
        return {"leading_gap": size, "trailing_gap": 0, "linear_gaps": 0, "kalman_gaps": 0, "null_gaps": 0,
                "longest_interior_gap": 0, "months_linear_log": 0, "months_kalman": 0, "months_left_null": 0}
    interior = [int(after - before - 1) for before, after in zip(positions[:-1], positions[1:]) if after - before > 1]
    return {
        "leading_gap": int(positions[0]),
        "trailing_gap": int(size - 1 - positions[-1]),
        "linear_gaps": sum(1 for gap in interior if gap <= LINEAR_MAX_GAP),
        "kalman_gaps": sum(1 for gap in interior if LINEAR_MAX_GAP < gap <= MAX_FILL_GAP),
        "null_gaps": sum(1 for gap in interior if gap > MAX_FILL_GAP),
        "longest_interior_gap": max(interior, default=0),
        "months_linear_log": sum(gap for gap in interior if gap <= LINEAR_MAX_GAP),
        "months_kalman": sum(gap for gap in interior if LINEAR_MAX_GAP < gap <= MAX_FILL_GAP),
        "months_left_null": sum(gap for gap in interior if gap > MAX_FILL_GAP),
    }
