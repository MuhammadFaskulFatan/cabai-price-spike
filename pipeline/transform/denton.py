"""Disagregasi temporal dengan metode Denton (proportional first-difference, D-26).

Diberikan indikator bulanan i_t (pola musiman) dan total tahunan A_y (benchmark), cari x_t yang menjumlah ke A_y
di tiap tahun dan paling kecil mengubah rasio x_t / i_t dari bulan ke bulan:

    minimalkan  sum_t ( x_t / i_t - x_(t-1) / i_(t-1) )^2   dengan   sum_(t di tahun y) x_t = A_y

Diselesaikan langsung lewat sistem KKT; kalau hasilnya ada nilai negatif, diulang sebagai QP dengan batas x >= 0. Skala indikator tidak memengaruhi hasil, jadi indikator boleh
berupa angka nasional dalam ton atau sekadar pola relatif.
"""
import numpy as np
from scipy.optimize import minimize


def denton_pfd(indicator, annual_totals, months_per_year=12, nonnegative=True):
    indicator = np.asarray(indicator, dtype=float)
    annual_totals = np.asarray(annual_totals, dtype=float)
    n_months, n_years = len(indicator), len(annual_totals)
    if n_months != n_years * months_per_year:
        raise ValueError("indikator harus berisi tepat 12 bulan per tahun benchmark")
    if (indicator <= 0).any():
        raise ValueError("indikator harus positif")

    difference = np.zeros((n_months - 1, n_months))
    rows = np.arange(n_months - 1)
    difference[rows, rows] = -1.0
    difference[rows, rows + 1] = 1.0

    annual_sum = np.zeros((n_years, n_months))
    for year in range(n_years):
        annual_sum[year, year * months_per_year : (year + 1) * months_per_year] = 1.0
    constraint = annual_sum * indicator  # sum_t i_t * z_t = A_y, dengan z_t = x_t / i_t

    size = n_months + n_years
    system = np.zeros((size, size))
    system[:n_months, :n_months] = 2 * difference.T @ difference
    system[:n_months, n_months:] = constraint.T
    system[n_months:, :n_months] = constraint
    rhs = np.concatenate([np.zeros(n_months), annual_totals])
    solution = np.linalg.solve(system, rhs)
    z = solution[:n_months]
    if nonnegative and (z < 0).any():
        z = _solve_nonnegative(difference, constraint, annual_totals, start=np.clip(z, 0, None))
    return indicator * z


def _solve_nonnegative(difference, constraint, annual_totals, start):
    """Versi dengan batas x >= 0 untuk provinsi kecil yang benchmark tahunannya melompat tajam (jarang terjadi)."""
    quadratic = difference.T @ difference
    result = minimize(
        lambda z: z @ quadratic @ z,
        start,
        jac=lambda z: 2 * quadratic @ z,
        bounds=[(0, None)] * len(start),
        constraints=[{"type": "eq", "fun": lambda z: constraint @ z - annual_totals, "jac": lambda z: constraint}],
        method="SLSQP",
        options={"maxiter": 500, "ftol": 1e-12},
    )
    return result.x
