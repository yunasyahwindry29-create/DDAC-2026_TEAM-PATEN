"""Step 1 - read the 5 raw IKPA CSVs and normalize their differing schemas
into two tidy tables:

  - satker fact      : one row per (satker x month), the scalar scores
  - component long   : one row per (satker x month x IKPA component)

The 2021 file uses the OLD 13-component formula (and has no KDKANWIL column);
2022-2025 use the NEW 8-component formula; 2024-2025 additionally carry KDKANWIL.
Because we select columns BY NAME, the differing column order is handled
automatically. Each year is tagged with its methodology `era`.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lib.config import DATA_RAW, YEARS  # noqa: E402

CODE_COLS = ["KDBA", "KDKANWIL", "KDKPPN", "KDSATKER"]
SCALAR_COLS = ["NILAI_TOTAL", "KONV_BOBOT", "NILAI_AKHIR"]


def _era(year: int) -> str:
    return "2021_old" if year == 2021 else "2022_new"


def _detect_components(columns) -> list[str]:
    """A component is any suffix with BOTH a NILAI_<suffix> and BOBOT_<suffix>
    column (this naturally excludes NILAI_TOTAL / NILAI_AKHIR / KONV_BOBOT)."""
    cols = set(columns)
    comps = []
    for c in columns:
        if c.startswith("NILAI_"):
            suffix = c[len("NILAI_"):]
            if f"BOBOT_{suffix}" in cols:
                comps.append(suffix)
    return comps


def load_year(year: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    path = DATA_RAW / f"IKPA_SATKER_{year}.csv"
    raw = pd.read_csv(path, sep=";", dtype=str, keep_default_na=False)
    raw.columns = [c.strip() for c in raw.columns]

    # zero-padded code columns stay as strings; KDKANWIL may be absent.
    if "KDKANWIL" not in raw.columns:
        raw["KDKANWIL"] = pd.NA

    components = _detect_components(raw.columns)

    # numeric casts
    num_cols = SCALAR_COLS + [f"NILAI_{c}" for c in components] + [f"BOBOT_{c}" for c in components]
    for col in num_cols:
        raw[col] = pd.to_numeric(raw[col], errors="coerce")
    raw["periode"] = pd.to_numeric(raw["PERIODE"], errors="coerce").astype("Int16")

    base = pd.DataFrame({
        "year": year,
        "periode": raw["periode"],
        "era": _era(year),
        "kdba": raw["KDBA"].str.strip(),
        "kdkanwil_raw": raw["KDKANWIL"],
        "kdkppn": raw["KDKPPN"].str.strip(),
        "kdsatker": raw["KDSATKER"].str.strip(),
    })

    # --- satker-grain fact ---
    satker = base.copy()
    satker["nmsatker"] = raw["NMSATKER"].str.strip()
    satker["nilai_total"] = raw["NILAI_TOTAL"].astype("float32")
    satker["konv_bobot"] = raw["KONV_BOBOT"].astype("float32")
    satker["nilai_akhir"] = raw["NILAI_AKHIR"].astype("float32")

    # --- component-grain long ---
    frames = []
    for c in components:
        f = base.copy()
        f["component"] = c
        f["nilai"] = raw[f"NILAI_{c}"].astype("float32")
        f["bobot"] = raw[f"BOBOT_{c}"].astype("float32")
        frames.append(f)
    comp = pd.concat(frames, ignore_index=True)

    return satker, comp


def load_all() -> tuple[pd.DataFrame, pd.DataFrame]:
    sat_frames, comp_frames = [], []
    for y in YEARS:
        s, c = load_year(y)
        sat_frames.append(s)
        comp_frames.append(c)
        print(f"  [normalize] {y}: {len(s):>7,} satker-rows, "
              f"{c['component'].nunique()} components, era={_era(y)}")
    satker = pd.concat(sat_frames, ignore_index=True)
    comp = pd.concat(comp_frames, ignore_index=True)
    return satker, comp
