"""ETL orchestrator. Run from the project root:

    python -m etl.build       (or)   .venv/bin/python etl/build.py

Reads data_raw/*.csv -> writes data/*.parquet:
  - fact_ikpa_satker.parquet, fact_ikpa_component.parquet   (local only / gitignored)
  - dim_ministry, dim_province, dim_kppn
  - agg_* summary tables
  - meta_* data-quality tables
"""
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lib.config import DATA, REFERENCE  # noqa: E402
from etl.normalize import load_all  # noqa: E402
from etl.backfill import build_kppn_kanwil_map, apply_backfill  # noqa: E402
from etl.aggregate import derive_dim_kppn, build_aggregates, build_meta  # noqa: E402


def _write(df: pd.DataFrame, name: str, compression: str = "snappy") -> None:
    path = DATA / f"{name}.parquet"
    df.to_parquet(path, index=False, compression=compression)
    print(f"  -> {name:32s} {len(df):>9,} rows  ({path.stat().st_size/1024:,.0f} KB)")


def main() -> None:
    t0 = time.time()
    DATA.mkdir(exist_ok=True)

    print("[1/5] Normalising 5 raw CSVs ...")
    satker, comp = load_all()
    satker["is_final_period"] = satker["periode"] == 12

    print("[2/5] Building KPPN -> Kanwil map and backfilling province ...")
    kppn_map, kppn_report = build_kppn_kanwil_map(satker)
    print(f"  map: {kppn_report}")
    satker, comp, cov = apply_backfill(satker, comp, kppn_map)
    print(cov.to_string(index=False))

    print("[3/5] Loading dimensions ...")
    dim_ministry = pd.read_csv(REFERENCE / "dim_ministry.csv", dtype={"kdba": str})
    dim_province = pd.read_csv(REFERENCE / "dim_province.csv",
                               dtype={"kdkanwil": str, "geojson_state": str})
    dim_kppn = derive_dim_kppn(satker, kppn_map)

    print("[4/5] Building aggregates + metadata ...")
    aggs = build_aggregates(satker, comp)
    meta = build_meta(satker, comp, cov, kppn_report, dim_kppn)

    print("[5/5] Writing parquet outputs ...")
    # full-grain facts -> local only (gitignored)
    _write(satker, "fact_ikpa_satker", compression="zstd")
    _write(comp, "fact_ikpa_component", compression="zstd")
    # dimensions
    _write(dim_ministry, "dim_ministry")
    _write(dim_province, "dim_province")
    _write(dim_kppn, "dim_kppn")
    # aggregates + meta (public)
    for name, df in aggs.items():
        _write(df, name)
    for name, df in meta.items():
        _write(df, name)

    print(f"\nDone in {time.time()-t0:,.1f}s. Outputs in {DATA}/")


if __name__ == "__main__":
    main()
