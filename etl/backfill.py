"""Step 2 - reconstruct the province (KDKANWIL) dimension for 2021-2023.

KDKANWIL is present natively only in 2024 & 2025. We build a KPPN -> Kanwil
lookup from those two years (verified 1:1) and use it to backfill the earlier
years. Every row is tagged `kanwil_source` = native | backfilled | unmapped so
the data-quality page can show exactly what was reconstructed.
"""
import pandas as pd


def build_kppn_kanwil_map(satker: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    native = satker[satker["kdkanwil_raw"].notna() & (satker["kdkanwil_raw"] != "")].copy()
    native["kdkanwil_raw"] = native["kdkanwil_raw"].str.strip()

    pairs = native.groupby("kdkppn")["kdkanwil_raw"].agg(
        kdkanwil=lambda s: s.value_counts().index[0],     # dominant Kanwil
        n_distinct="nunique",
    ).reset_index()

    conflicts = int((pairs["n_distinct"] > 1).sum())
    report = {
        "kppn_in_map": int(len(pairs)),
        "kppn_conflicts": conflicts,
        "is_clean_1to1": conflicts == 0,
    }
    return pairs[["kdkppn", "kdkanwil"]], report


def apply_backfill(satker: pd.DataFrame, comp: pd.DataFrame, kppn_map: pd.DataFrame):
    lookup = dict(zip(kppn_map["kdkppn"], kppn_map["kdkanwil"]))

    def _resolve(df: pd.DataFrame) -> pd.DataFrame:
        raw = df["kdkanwil_raw"]
        has_native = raw.notna() & (raw.astype("string") != "")
        mapped = df["kdkppn"].map(lookup)
        df["kdkanwil"] = raw.where(has_native, mapped)
        df["kanwil_source"] = "backfilled"
        df.loc[has_native, "kanwil_source"] = "native"
        df.loc[df["kdkanwil"].isna(), "kanwil_source"] = "unmapped"
        df["kdkanwil"] = df["kdkanwil"].fillna("00")
        return df.drop(columns=["kdkanwil_raw"])

    satker = _resolve(satker)
    comp = _resolve(comp)

    cov = (
        satker.groupby("year")["kanwil_source"]
        .value_counts()
        .unstack(fill_value=0)
        .reset_index()
    )
    return satker, comp, cov
