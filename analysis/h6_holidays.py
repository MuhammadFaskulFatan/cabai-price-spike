"""H6: seberapa besar Idulfitri menambah harga eceran, setelah kontrol musiman dan pasokan?

Rencana: docs/05_analysis_plan.md bagian 6 (D-48). Panel provinsi x bulan:
    log(harga eceran) = b1 * bulan Idulfitri + b2 * bulan sebelum Idulfitri + FE provinsi + FE month-of-year + trend
                        + log(1 + produksi tahunan provinsi) + ONI + jumlah hari cuti bersama + e
SE cluster per tahun-bulan (perlakuan hanya bervariasi menurut waktu, jadi provinsi di bulan yang sama tidak independen).
Idulfitri bergeser sekitar 11 hari per tahun sehingga efeknya bisa dipisah dari FE month-of-year.
Sampel utama Jan 2019 - Des 2025 (produksi 2026 belum ada); sensitivity tanpa kontrol produksi sampai Okt 2026.
Kesimpulan akhir (hari besar lebih kecil dari efek cuaca) menunggu H1.

    python -m analysis.h6_holidays
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm

from analysis.style import FIGURES, GROUP_COLOR, GROUP_LABEL, INK_2, SURFACE, TABLES, load_core, plt, setup

ALPHA = 0.05


def prepare():
    core = load_core()
    data = core[core["in_model_period"]].copy()
    data["log_price"] = np.log(data["price_retail"])
    data["idul"] = (data["months_to_idulfitri"] == 0).astype(float)
    data["pre_idul"] = (data["months_to_idulfitri"] == -1).astype(float)
    data["log_production"] = np.log1p(data["production_annual_ton"])
    data["trend"] = (data["month"] - pd.Period("2019-01", "M")).apply(lambda d: d.n) / 12
    data["moy"] = data["month"].dt.month
    data["year"] = data["month"].dt.year
    data["cluster"] = data["month"].astype(str)
    return data


def fit(data, terms, controls=("log_production", "oni_anomaly", "n_cuti_bersama_days"), year_fe=False):
    sample = data.dropna(subset=["log_price", *controls]).copy()
    X = pd.concat([
        sample[list(terms) + ["trend", *controls]],
        pd.get_dummies(sample["province_id"], prefix="p", drop_first=True, dtype=float),
        pd.get_dummies(sample["moy"], prefix="m", drop_first=True, dtype=float),
    ] + ([pd.get_dummies(sample["year"], prefix="y", drop_first=True, dtype=float)] if year_fe else []), axis=1)
    fitted = sm.OLS(sample["log_price"], sm.add_constant(X)).fit(cov_type="cluster", cov_kwds={"groups": sample["cluster"]})
    return fitted, sample


def effects(fitted, sample, terms):
    out = {"n": len(sample), "periode": f"{sample['month'].min()} s/d {sample['month'].max()}", "idulfitri_dalam_sampel": int(sample.loc[sample["idul"] == 1, "month"].nunique())}
    for term in terms:
        beta = fitted.params[term]
        low, high = fitted.conf_int().loc[term]
        out[f"{term}_efek_pct"] = (np.exp(beta) - 1) * 100
        out[f"{term}_ci_bawah"] = (np.exp(low) - 1) * 100
        out[f"{term}_ci_atas"] = (np.exp(high) - 1) * 100
        out[f"{term}_p"] = fitted.pvalues[term]
    return out


def run_specs(data):
    terms = ("idul", "pre_idul")
    specs = {
        "utama (2019-2025, kontrol produksi + ONI + cuti)": (data[data["year"] <= 2025], {}),
        "tanpa kontrol produksi, sampai Okt 2026": (data, {"controls": ("oni_anomaly", "n_cuti_bersama_days")}),
        "hanya bulan cuti_bersama_verified": (data[(data["year"] <= 2025) & data["cuti_bersama_verified"]], {}),
        "tanpa 2020": (data[(data["year"] <= 2025) & (data["year"] != 2020)], {}),
        "tanpa kontrol cuti bersama": (data[data["year"] <= 2025], {"controls": ("log_production", "oni_anomaly")}),
        "tambah FE tahun": (data[data["year"] <= 2025], {"year_fe": True}),
    }
    rows = []
    for group in GROUP_LABEL:
        for label, (subset, kwargs) in specs.items():
            fitted, sample = fit(subset[subset["commodity_group"] == group], terms, **kwargs)
            rows.append({"grup": group, "spesifikasi": label, **effects(fitted, sample, terms)})
    return pd.DataFrame(rows)


def event_study(data, year_fe=False):
    """Koefisien bulan -3 s/d +3 relatif terhadap Idulfitri (pembanding: bulan lain), spesifikasi utama."""
    data = data[data["year"] <= 2025].copy()
    terms = []
    for k in range(-3, 4):
        name = f"k{'m' if k < 0 else 'p'}{abs(k)}"
        data[name] = (data["months_to_idulfitri"] == k).astype(float)
        terms.append((k, name))
    rows = []
    for group in GROUP_LABEL:
        fitted, _ = fit(data[data["commodity_group"] == group], [n for _, n in terms], year_fe=year_fe)
        for k, name in terms:
            low, high = fitted.conf_int().loc[name]
            rows.append({"grup": group, "bulan_relatif": k, "efek_pct": (np.exp(fitted.params[name]) - 1) * 100,
                         "ci_bawah": (np.exp(low) - 1) * 100, "ci_atas": (np.exp(high) - 1) * 100, "p": fitted.pvalues[name]})
    return pd.DataFrame(rows)


def chart(event, path):
    fig, ax = plt.subplots(figsize=(8, 3.8))
    for offset, group in zip((-0.1, 0.1), GROUP_LABEL):
        part = event[event["grup"] == group]
        x = part["bulan_relatif"] + offset
        ax.errorbar(x, part["efek_pct"], yerr=[part["efek_pct"] - part["ci_bawah"], part["ci_atas"] - part["efek_pct"]], fmt="o", color=GROUP_COLOR[group],
                    elinewidth=1.2, capsize=0, markersize=6, markeredgecolor=SURFACE, label=GROUP_LABEL[group])
    ax.axhline(0, color=INK_2, linewidth=0.8)
    ax.axvline(0, color=INK_2, linewidth=0.6, linestyle=(0, (3, 3)))
    ax.set_xticks(range(-3, 4), ["-3", "-2", "-1", "bulan\nIdulfitri", "+1", "+2", "+3"])
    ax.set_ylabel("selisih harga eceran (%)")
    ax.set_title("H6: harga eceran di sekitar Idulfitri vs bulan lain, setelah kontrol (2019-2025)", loc="left", fontweight="bold", pad=16)
    ax.text(0, 1.01, "Titik = estimasi, garis = 95% CI; kontrol FE provinsi, FE bulan kalender, trend, produksi, ONI, cuti bersama", transform=ax.transAxes, fontsize=7.5, color=INK_2, va="bottom")
    ax.legend(loc="upper left", fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def run():
    setup()
    data = prepare()
    results = run_specs(data)
    event = event_study(data)
    event_year = event_study(data, year_fe=True).assign(spesifikasi="tambah FE tahun")
    event_year.to_csv(TABLES / "h6_event_study_year_fe.csv", index=False)
    chart(event, FIGURES / "h6_idulfitri_event.png")
    results.to_csv(TABLES / "h6_results.csv", index=False)
    event.to_csv(TABLES / "h6_event_study.csv", index=False)
    pd.to_pickle({"results": results, "event": event, "event_year": event_year}, TABLES / "h6_results.pkl")
    columns = ["grup", "spesifikasi", "n", "idulfitri_dalam_sampel", "idul_efek_pct", "idul_ci_bawah", "idul_ci_atas", "idul_p", "pre_idul_efek_pct", "pre_idul_ci_bawah", "pre_idul_ci_atas", "pre_idul_p"]
    print(results[columns].round(3).to_string(index=False))
    print(event.round(2).to_string(index=False))
    print(event_year.round(2).to_string(index=False))


if __name__ == "__main__":
    run()
