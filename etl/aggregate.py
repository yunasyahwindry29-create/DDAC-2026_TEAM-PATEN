"""Step 3 - build the small, analytics-ready aggregate tables the app renders,
plus the derived KPPN dimension and the data-quality metadata.

Everything here is aggregated to province / ministry / KPPN / component level
(never satker-level), so these outputs are safe to commit to the public repo.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lib.config import (  # noqa: E402
    EXCELLENT_THRESHOLD, HEALTHY_THRESHOLD, FINAL_PERIODE,
)

KPPN_OFFICE_PREFIX = "KANTOR PELAYANAN PERBENDAHARAAN NEGARA"


def _gini(values: np.ndarray) -> float:
    x = np.sort(np.asarray(values, dtype=float))
    x = x[~np.isnan(x)]
    n = x.size
    if n == 0 or x.sum() == 0:
        return float("nan")
    cum = np.cumsum(x)
    return float((n + 1 - 2 * np.sum(cum) / cum[-1]) / n)


def _summarize(df: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    g = df.groupby(keys, observed=True)["nilai_akhir"]
    base = g.agg(
        n_satker="count",
        avg_nilai_akhir="mean",
        median_nilai_akhir="median",
        std_nilai_akhir="std",
    ).reset_index()
    extra = g.agg(
        p10=lambda s: float(np.nanpercentile(s, 10)),
        p90=lambda s: float(np.nanpercentile(s, 90)),
        pct_excellent=lambda s: float((s >= EXCELLENT_THRESHOLD).mean() * 100),
        pct_below_healthy=lambda s: float((s < HEALTHY_THRESHOLD).mean() * 100),
    ).reset_index()
    out = base.merge(extra, on=keys)
    return out.round(2)


def derive_dim_kppn(satker: pd.DataFrame, kppn_map: pd.DataFrame) -> pd.DataFrame:
    offices = satker[satker["nmsatker"].str.startswith(KPPN_OFFICE_PREFIX, na=False)].copy()
    # prefer the most recent year's name for each KPPN
    offices = offices.sort_values("year").drop_duplicates("kdkppn", keep="last")
    offices["city"] = (
        offices["nmsatker"].str.replace(KPPN_OFFICE_PREFIX, "", regex=False).str.strip().str.title()
    )
    names = offices[["kdkppn", "city"]].copy()

    dim = kppn_map.merge(names, on="kdkppn", how="left")
    dim["name_source"] = np.where(dim["city"].notna(), "derived", "fallback")
    dim["kppn_name"] = np.where(
        dim["city"].notna(), "KPPN " + dim["city"].fillna(""), "KPPN " + dim["kdkppn"]
    )
    return dim[["kdkppn", "kppn_name", "kdkanwil", "name_source"]]


def build_aggregates(satker: pd.DataFrame, comp: pd.DataFrame) -> dict[str, pd.DataFrame]:
    fin = satker[satker["periode"] == FINAL_PERIODE].copy()
    cfin = comp[comp["periode"] == FINAL_PERIODE].copy()
    out = {}

    # National per-year (with Gini) -- F1 dispersion
    nat = _summarize(fin, ["year"])
    gini = fin.groupby("year")["nilai_akhir"].apply(lambda s: _gini(s.values)).reset_index(
        name="gini")
    out["agg_national_year"] = nat.merge(gini, on="year").round(4)

    # National monthly cumulative build-up
    out["agg_national_monthly"] = (
        satker.groupby(["year", "periode"], observed=True)["nilai_akhir"]
        .mean().reset_index(name="avg_nilai_akhir").round(2)
    )

    # Province / ministry / KPPN per-year
    out["agg_province_year"] = _summarize(fin, ["year", "kdkanwil"])
    out["agg_ministry_year"] = _summarize(fin, ["year", "kdba"])
    out["agg_kppn_year"] = _summarize(fin, ["year", "kdkppn"])

    # Ministry x Province matrix -- F5
    out["agg_ministry_province_year"] = (
        fin.groupby(["year", "kdba", "kdkanwil"], observed=True)
        .agg(n_satker=("nilai_akhir", "count"),
             avg_nilai_akhir=("nilai_akhir", "mean")).reset_index().round(2)
    )

    # Component aggregates -- F3 diagnosis
    def comp_agg(keys):
        return (cfin.groupby(keys, observed=True)
                .agg(avg_nilai=("nilai", "mean"), avg_bobot=("bobot", "mean"),
                     n_satker=("nilai", "count")).reset_index().round(2))

    out["agg_component_year"] = comp_agg(["year", "era", "component"])
    out["agg_component_province_year"] = comp_agg(["year", "kdkanwil", "component"])
    out["agg_component_ministry_year"] = comp_agg(["year", "kdba", "component"])
    return out


def build_meta(satker: pd.DataFrame, comp: pd.DataFrame, cov: pd.DataFrame,
               kppn_report: dict, dim_kppn: pd.DataFrame) -> dict[str, pd.DataFrame]:
    per_year = (
        satker.groupby("year", observed=True)
        .agg(era=("era", "first"),
             n_rows=("kdsatker", "size"),
             n_satker=("kdsatker", "nunique"),
             n_kppn=("kdkppn", "nunique"),
             n_kdba=("kdba", "nunique"),
             avg_nilai_akhir=("nilai_akhir", "mean")).reset_index()
    )
    ncomp = comp.groupby("year", observed=True)["component"].nunique().reset_index(
        name="n_components")
    per_year = per_year.merge(ncomp, on="year")

    cov = cov.copy()
    for c in ["native", "backfilled", "unmapped"]:
        if c not in cov.columns:
            cov[c] = 0
    per_year = per_year.merge(
        cov[["year", "native", "backfilled", "unmapped"]], on="year", how="left"
    ).rename(columns={"native": "kanwil_native",
                      "backfilled": "kanwil_backfilled",
                      "unmapped": "kanwil_unmapped"})
    per_year["avg_nilai_akhir"] = per_year["avg_nilai_akhir"].round(2)

    summary = pd.DataFrame([
        {"item": "KPPN dalam peta KPPN->Kanwil", "value": str(kppn_report["kppn_in_map"])},
        {"item": "Konflik pemetaan (KPPN -> >1 Kanwil)", "value": str(kppn_report["kppn_conflicts"])},
        {"item": "Pemetaan bersih 1:1?", "value": "Ya" if kppn_report["is_clean_1to1"] else "Tidak"},
        {"item": "Nama KPPN berhasil diturunkan dari data",
         "value": f"{int((dim_kppn['name_source'] == 'derived').sum())} / {len(dim_kppn)}"},
        {"item": "Total baris (semua tahun)", "value": f"{len(satker):,}"},
    ])
    return {"meta_per_year": per_year, "meta_summary": summary}
