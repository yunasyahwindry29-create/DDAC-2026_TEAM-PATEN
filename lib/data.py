"""Data access + analytics layer.

Small aggregate tables are read straight from Parquet into pandas (cached) -
they are only a few hundred rows each. The 1.14M-row satker fact is queried
lazily through DuckDB (predicate pushdown) and is only present locally, so the
at-risk watchlist degrades gracefully on the aggregate-only public deploy.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from lib.config import (
    DATA, YEARS, FINAL_PERIODE, EXCELLENT_THRESHOLD, HEALTHY_THRESHOLD,
    COMPONENT_FLOOR, REGION_ORDER, component_label,
    REORG_FAMILIES, REORG_PREDECESSOR_YEAR, REORG_SUCCESSOR_YEAR,
    REORG_HEATMAP_COMPONENTS,
)

UNMAPPED = "00"

QUADRANT_LABELS = {
    "leaders": "Unggul & Menguat",
    "coasting": "Tinggi tetapi Melemah",
    "rising": "Rendah tetapi Membaik",
    "atrisk": "Rawan (Rendah & Melemah)",
}
QUADRANT_COLORS = {
    "leaders": "#1E8449", "coasting": "#D68910",
    "rising": "#5DADE2", "atrisk": "#C0392B",
}


# --- raw table access --------------------------------------------------------
@st.cache_data(show_spinner=False)
def load(name: str) -> pd.DataFrame:
    return pd.read_parquet(DATA / f"{name}.parquet")


@st.cache_resource(show_spinner=False)
def get_con():
    import duckdb
    return duckdb.connect(database=":memory:")


def has_satker_fact() -> bool:
    return (DATA / "fact_ikpa_satker.parquet").exists()


# --- dimensions --------------------------------------------------------------
@st.cache_data(show_spinner=False)
def dim_province() -> pd.DataFrame:
    return load("dim_province")


@st.cache_data(show_spinner=False)
def dim_ministry() -> pd.DataFrame:
    return load("dim_ministry")


def ministry_name_map() -> dict:
    d = dim_ministry()
    return dict(zip(d["kdba"], d["ministry_name"]))


def province_name_map() -> dict:
    d = dim_province()
    return dict(zip(d["kdkanwil"], d["province_name"]))


# --- joined convenience views ------------------------------------------------
@st.cache_data(show_spinner=False)
def province_year() -> pd.DataFrame:
    df = load("agg_province_year")
    df = df[df["kdkanwil"] != UNMAPPED]
    return df.merge(dim_province(), on="kdkanwil", how="left")


@st.cache_data(show_spinner=False)
def ministry_year() -> pd.DataFrame:
    df = load("agg_ministry_year")
    d = dim_ministry()
    df = df.merge(d, on="kdba", how="left")
    df["ministry_name"] = df["ministry_name"].fillna("BA " + df["kdba"].astype(str))
    df["ministry_short"] = df["ministry_short"].fillna("BA " + df["kdba"].astype(str))
    return df


@st.cache_data(show_spinner=False)
def national_year() -> pd.DataFrame:
    return load("agg_national_year")


@st.cache_data(show_spinner=False)
def national_monthly() -> pd.DataFrame:
    return load("agg_national_monthly")


@st.cache_data(show_spinner=False)
def matrix_ministry_province(year: int, min_satker: int = 1) -> pd.DataFrame:
    df = load("agg_ministry_province_year")
    df = df[(df["year"] == year) & (df["kdkanwil"] != UNMAPPED) & (df["n_satker"] >= min_satker)]
    df = df.merge(dim_province()[["kdkanwil", "province_name", "province_short", "region_island"]],
                  on="kdkanwil", how="left")
    df = df.merge(dim_ministry()[["kdba", "ministry_name", "ministry_short"]],
                  on="kdba", how="left")
    df["ministry_short"] = df["ministry_short"].fillna("BA " + df["kdba"].astype(str))
    df["ministry_name"] = df["ministry_name"].fillna("BA " + df["kdba"].astype(str))
    return df


# --- F2: trend slope + performance/improvement quadrant ----------------------
def _slope(years: np.ndarray, vals: np.ndarray) -> float:
    m = ~np.isnan(vals)
    if m.sum() < 2:
        return np.nan
    return float(np.polyfit(years[m], vals[m], 1)[0])


def quadrant(level: str, latest_year: int = 2025,
             slope_from: int = 2022) -> pd.DataFrame:
    """level = 'province' | 'ministry'. Returns one row per entity with its
    latest level, multi-year trend slope, and quadrant classification."""
    if level == "province":
        df = province_year()
        key, name = "kdkanwil", "province_name"
        extra = ["region_island"]
    else:
        df = ministry_year()
        key, name = "kdba", "ministry_name"
        extra = ["kategori"] if "kategori" in df.columns else []

    slopes = (
        df[df["year"] >= slope_from]
        .groupby(key)
        .apply(lambda g: _slope(g["year"].to_numpy(float), g["avg_nilai_akhir"].to_numpy(float)),
               include_groups=False)
        .reset_index(name="slope")
    )
    latest = df[df["year"] == latest_year][[key, name, "avg_nilai_akhir", "n_satker"] + extra]
    out = latest.merge(slopes, on=key, how="left").dropna(subset=["avg_nilai_akhir"])
    out = out.rename(columns={"avg_nilai_akhir": "level"})

    div_level = out["level"].median()
    high = out["level"] >= div_level
    improving = out["slope"] >= 0
    out["quadrant"] = np.select(
        [high & improving, high & ~improving, ~high & improving, ~high & ~improving],
        ["leaders", "coasting", "rising", "atrisk"], default="atrisk",
    )
    out["quadrant_label"] = out["quadrant"].map(QUADRANT_LABELS)
    out["divider_level"] = div_level
    return out


# --- F3: component contribution-to-gap decomposition -------------------------
def _national_components(year: int) -> pd.DataFrame:
    nat = load("agg_component_year")
    nat = nat[nat["year"] == year]
    return nat[["component", "avg_nilai"]].rename(columns={"avg_nilai": "national_nilai"})


def gap_decomposition(level: str, code: str, year: int = 2025) -> pd.DataFrame:
    """Per-component weighted gap vs the national average for one entity.
    weighted_gap > 0 means the component drags the entity below national."""
    table = "agg_component_province_year" if level == "province" else "agg_component_ministry_year"
    key = "kdkanwil" if level == "province" else "kdba"
    ent = load(table)
    ent = ent[(ent["year"] == year) & (ent[key] == code)][["component", "avg_nilai", "avg_bobot"]]
    ent = ent.rename(columns={"avg_nilai": "entity_nilai", "avg_bobot": "bobot"})

    out = ent.merge(_national_components(year), on="component", how="left")
    out["weighted_gap"] = (out["national_nilai"] - out["entity_nilai"]) * (out["bobot"] / 100.0)
    out["label"] = out["component"].map(component_label)
    out["is_floor_breach"] = out["entity_nilai"] < COMPONENT_FLOOR
    return out.sort_values("weighted_gap", ascending=False).reset_index(drop=True)


def primary_drag(level: str, code: str, year: int = 2025) -> str | None:
    d = gap_decomposition(level, code, year)
    d = d[d["weighted_gap"] > 0]
    return d.iloc[0]["label"] if len(d) else None


# --- F6: new-cohort vs incumbent (needs satker fact, local only) -------------
@st.cache_data(show_spinner=False)
def cohort_comparison(year: int = 2025) -> pd.DataFrame | None:
    if not has_satker_fact():
        return None
    con = get_con()
    fact = (DATA / "fact_ikpa_satker.parquet").as_posix()
    comp = (DATA / "fact_ikpa_component.parquet").as_posix()
    # first appearance year per satker
    sql = f"""
    WITH first_seen AS (
        SELECT kdsatker, MIN(year) AS first_year
        FROM read_parquet('{fact}') GROUP BY kdsatker
    ),
    comp AS (
        SELECT c.component, c.nilai, fs.first_year
        FROM read_parquet('{comp}') c
        JOIN first_seen fs USING (kdsatker)
        WHERE c.year = {year} AND c.periode = {FINAL_PERIODE}
    )
    SELECT component,
           CASE WHEN first_year >= 2024 THEN 'Satker Baru (2024+)' ELSE 'Satker Lama (pra-2024)' END AS kohort,
           AVG(nilai) AS avg_nilai, COUNT(*) AS n
    FROM comp GROUP BY 1, 2
    """
    df = con.execute(sql).df()
    df["label"] = df["component"].map(component_label)
    return df


# --- Reorganization before/after (predecessor 2024 vs successors 2025) -------
@st.cache_data(show_spinner=False)
def reorg_before_after_matrix():
    """Heatmap source for the 2024 reorganization. Returns (vals, ns):
    both indexed by an ordered list of ministry rows (predecessor at 2024, its
    successors at 2025, a blank spacer between families), columns = component
    labels. `vals` holds avg_nilai, `ns` holds n_satker (for hover)."""
    acm = load("agg_component_ministry_year")
    shorts = dict(zip(dim_ministry()["kdba"], dim_ministry()["ministry_short"]))
    comp_labels = [component_label(c) for c in REORG_HEATMAP_COMPONENTS]
    val_rows, n_rows, order = {}, {}, []

    def _add(kdba, year, label):
        sub = acm[(acm["kdba"] == kdba) & (acm["year"] == year)]
        if sub.empty:
            return False
        vmap = dict(zip(sub["component"], sub["avg_nilai"]))
        nmap = dict(zip(sub["component"], sub["n_satker"]))
        val_rows[label] = {cl: vmap.get(c) for c, cl in zip(REORG_HEATMAP_COMPONENTS, comp_labels)}
        n_rows[label] = {cl: nmap.get(c) for c, cl in zip(REORG_HEATMAP_COMPONENTS, comp_labels)}
        order.append(label)
        return True

    py = str(REORG_PREDECESSOR_YEAR)[2:]
    sy = str(REORG_SUCCESSOR_YEAR)[2:]
    spacer = 0
    for _fam, pred, succs in REORG_FAMILIES:
        added = _add(pred, REORG_PREDECESSOR_YEAR, f"{shorts.get(pred, 'BA ' + pred)} · '{py}")
        for s in succs:
            added = _add(s, REORG_SUCCESSOR_YEAR, f"   ↳ {shorts.get(s, 'BA ' + s)} · '{sy}") or added
        if added:
            spacer += 1
            blank = " " * spacer
            val_rows[blank] = {cl: None for cl in comp_labels}
            n_rows[blank] = {cl: None for cl in comp_labels}
            order.append(blank)
    if order and not order[-1].strip():
        order.pop()

    vals = pd.DataFrame(val_rows).T.reindex(order)[comp_labels]
    ns = pd.DataFrame(n_rows).T.reindex(order)[comp_labels]
    return vals, ns


@st.cache_data(show_spinner=False)
def reorg_biggest_drop(min_satker: int = 20):
    """Largest predecessor(2024) -> successor(2025) component drop, restricted to
    successors with enough satker to be reliable. Returns a dict or None."""
    acm = load("agg_component_ministry_year")
    shorts = dict(zip(dim_ministry()["kdba"], dim_ministry()["ministry_short"]))
    best = None
    for fam, pred, succs in REORG_FAMILIES:
        p = acm[(acm["kdba"] == pred) & (acm["year"] == REORG_PREDECESSOR_YEAR)]
        if p.empty:
            continue
        pmap = dict(zip(p["component"], p["avg_nilai"]))
        for s in succs:
            q = acm[(acm["kdba"] == s) & (acm["year"] == REORG_SUCCESSOR_YEAR)]
            if q.empty or q["n_satker"].max() < min_satker:
                continue
            qv = dict(zip(q["component"], q["avg_nilai"]))
            for c in REORG_HEATMAP_COMPONENTS:
                if c in pmap and c in qv:
                    drop = pmap[c] - qv[c]
                    if best is None or drop > best["drop"]:
                        best = {"family": fam, "succ": shorts.get(s, "BA " + s),
                                "component": component_label(c),
                                "before": pmap[c], "after": qv[c], "drop": drop}
    return best


# --- F4: at-risk watchlist (needs satker fact, local only) -------------------
@st.cache_data(show_spinner=False)
def watchlist(year: int = 2025, kdkanwil: str | None = None,
              kdba: str | None = None, limit: int = 500) -> pd.DataFrame | None:
    if not has_satker_fact():
        return None
    con = get_con()
    fact = (DATA / "fact_ikpa_satker.parquet").as_posix()
    where = [f"year = {year}", f"periode = {FINAL_PERIODE}", "kdkanwil <> '00'"]
    if kdkanwil:
        where.append(f"kdkanwil = '{kdkanwil}'")
    if kdba:
        where.append(f"kdba = '{kdba}'")
    clause = " AND ".join(where)
    sql = f"""
    SELECT kdsatker, nmsatker, kdba, kdkanwil, kdkppn, nilai_akhir
    FROM read_parquet('{fact}')
    WHERE {clause} AND nilai_akhir < {HEALTHY_THRESHOLD}
    ORDER BY nilai_akhir ASC
    LIMIT {limit}
    """
    df = con.execute(sql).df()
    if df.empty:
        return df
    df["province"] = df["kdkanwil"].map(province_name_map())
    df["ministry"] = df["kdba"].map(ministry_name_map()).fillna("BA " + df["kdba"])
    return df


# --- small helpers -----------------------------------------------------------
def region_order(values) -> list[str]:
    present = [r for r in REGION_ORDER if r in set(values)]
    return present + [v for v in pd.unique(values) if v not in REGION_ORDER]
