# DDAC 2026 — IKPA Data Storytelling Dashboard (Development Plan)

> Status: **DRAFT for review** · Track: *Data Story Telling* · Stack: Streamlit + DuckDB + Plotly
> Language: Bahasa Indonesia · Deploy: public aggregate-only on Streamlit Community Cloud

---

## 1. Context

We are entering **DDAC 2026, the "Data Story Telling" track** (DJPb / Kemenkeu). The mandatory
deliverable is a **live dashboard/web-app link**, plus a short use-case description and a
presentation. Judging rewards:

- **Data Quality** — volume/type of data + *visible, defensible* processing technique.
- **Visualization Quality** — information composition + visualization technique + **storytelling**.
- **Analysis Output** — usefulness of the output + adoptability by DJPb.

We have 5 raw files in `data_raw/`: satker-level **IKPA** scores 2021–2025
(*Indikator Kinerja Pelaksanaan Anggaran* = a 0–100 budget-execution discipline score computed
monthly and cumulatively for every government work unit / "satker").

**Goal:** a Streamlit dashboard that lets a treasury audience see which ministries (KDBA) perform
well year-over-year, how a ministry's performance is distributed across provinces, which provinces
are weak across all ministries, and which ministries are weak across all provinces — i.e. a
**targeting tool** for where DJPb should intervene.

**Decisions locked with the user:**

| Decision | Choice |
|---|---|
| Language | **Bahasa Indonesia** (UI + narrative) |
| Live deploy data policy | **Public app shows aggregated data only**; raw satker rows stay local/private (honors the no-redistribution clause) |
| External enrichment | **BPS regional framing only** (province names + 6-region island grouping); no budget-value (Rp) join in this phase |

---

## 2. Data facts (verified from the CSVs — these drive the whole design)

- Semicolon-delimited (`;`), UTF-8, ~220k–235k rows each, **~1.14M rows total**.
- **Grain:** one row per `(satker × month)`. `PERIODE` = `'01'..'12'`, **cumulative month-to-date**,
  so `PERIODE='12'` is the full-year IKPA. `NILAI_AKHIR` is the final score (0–100, rare bonus
  ≤ 107.5). No missing values observed.
- **Dimensions:**
  - `KDBA` — ministry/agency code (84 → 100 distinct; grows in 2025).
  - `KDKANWIL` — province / Kanwil-DJPb code (`'01'..'34'`), **present only in 2024 & 2025**.
  - `KDKPPN` — treasury service office (179–182 distinct).
  - `KDSATKER` — work unit (15k–19k), with `NMSATKER` (the only human-readable label in raw data).
- **Two methodology eras:**
  - 2021 → **old 13-component** formula (extra `PAGU_MINUS, LPJ, RETUR, RENKAS, SALAH_SPM`; different
    column order).
  - 2022–2025 → **8-component** formula (`REV_DIPA, HAL3_DIPA, REALISASI, KONTRAKTUAL, TAGIHAN,
    UP_TUP, DISPENSASI_SPM, CAPUT`).
  - Clean cross-year trend = 2022–2025; 2021 comparable only on `NILAI_AKHIR` (we annotate the break).
- **Province backfill is feasible:** `KDKPPN → KDKANWIL` is a clean **1:1** mapping (179 KPPN → 179
  pairs in 2025). We build the map from 2024/2025 and **backfill province onto 2021–2023**, tagging
  `kanwil_source = native | backfilled`. A few KPPN drift across years (182 → 179); unmatched rows are
  handled gracefully and coverage is reported.
- **Real narrative hook:** satker count jumps **~14,700 (2023) → ~19,000 (2024)** and ministries
  **84 → 100 (2025)** — Indonesia's late-2024 government reorganization. A once-in-a-decade natural
  experiment already sitting in the data.

This is greenfield: only the rules (`DDAC_2026_Data_Story_Telling.md`, `Ketentuan_Lomba_DDAC_2026.pdf`)
and `data_raw/` exist — no code yet.

---

## 3. Product thesis

Not "another dashboard" — a **diagnosis + targeting tool**: *given finite coaching capacity, which
ministries / regions / units should DJPb visit first, and on which IKPA component?* The
data-engineering work (province backfill, methodology normalization) is made **visible as a feature**
to win the Data Quality criterion.

---

## 4. The winning narrative (guided scrollytelling, Bahasa Indonesia)

**Title:** *"Disiplin yang Tidak Merata: Memetakan Titik Lemah Pelaksanaan Anggaran Indonesia 2021–2025."*

Five acts; each closes with a bold one-line **"So What"** aimed at a treasury decision-maker:

1. **The reassuring average** — calm national IKPA trend. *So what:* averages hide who needs help.
2. **The hidden spread** — the distribution widens (P90–P10 gap, Gini) while the mean stays flat.
   *So what:* performance is becoming unequal; a one-size-fits-all policy is mis-targeted.
3. **The 2024 shock** — new-cohort satker score below incumbents on *onboarding* components
   (REV_DIPA, HAL3_DIPA, DISPENSASI_SPM). *So what:* a coachable onboarding gap, not incompetence.
4. **Where it hurts** — the ministry×province matrix separates **two failure modes**: provinces weak
   across all ministries (regional capacity → Kanwil owns it) vs ministries weak across all provinces
   (systemic → the K/L's central planning unit owns it).
5. **The targeting engine** — Performance×Improvement quadrant + at-risk list →
   *"coach these units on these components ≈ +X national IKPA points."*

---

## 5. Analytical features (defensible, reproducible methods)

**Must-have**

- **F1 — Dispersion / inequality:** per-year P10 / P50 / P90, the P90–P10 spread, and a Gini / CV of
  final IKPA, tracked 2021–2025.
- **F2 — Performance × Improvement quadrant:** X = latest-year level (or percentile), Y = OLS trend
  slope over 2022–2025. Quadrants: Leaders / Coasting / Rising / At-risk. Applied at ministry and
  province level — one view answers "good and improving year over year."
- **F3 — Component contribution-to-gap:** `(benchmark_score − entity_score) × weight` per component
  vs the national / peer median → names the **primary drag** component (turns "low score" into a
  to-do). Uses the official IKPA weights, cited on the methodology page.
- **F5 — Ministry × Province matrix with two-way decomposition:** heatmap + row means (systemic
  ministry weakness), column means (regional weakness), and residual `cell − row − col + grand`
  (specific bad pairing). This is the unique, winning insight.
- **F6 — New-cohort vs incumbent:** tag each satker by first-appearance year; compare the 2024 new
  cohort vs pre-2024 incumbents per component (quantifies Act 3).

**Local/demo build (satker-level — see deploy split in §8)**

- **F4 — At-risk watchlist:** a transparent, rule-based flag (≥ 2 of: bottom-decile vs KPPN peers,
  negative trend slope, any component below a hard floor, in-year monthly deterioration) + the
  primary-drag component + export. This is the adoptable deliverable.

**Nice-to-have:** F7 volatility, F8 KPPN-peer benchmarking, F10 methodology-bridge table.

---

## 6. Dashboard pages (Bahasa Indonesia) — each with a deliberate chart choice

| Page | Question it answers | Chart(s) |
|---|---|---|
| **Ikhtisar Nasional** | Are we doing well? then the twist | KPI tiles + national trend line, then a distribution ridgeline / strip plot by year (the reveal) |
| **Kementerian** (K/L deep-dive) | Which ministries are good/improving? how is one spread across provinces? | Performance×Improvement quadrant → drill to provincial choropleth + component small-multiples |
| **Provinsi** (deep-dive) | Why is this province low? which component drags it? | Diverging contribution-to-gap bars vs national median + ranked KPPN list |
| **Matriks K/L × Provinsi** | Provinces weak everywhere? ministries weak everywhere? | Clustered heatmap + marginal row/col mean bars + residual toggle |
| **Diagnostik Komponen** | Where are the pain points by component over time? | 8-component small-multiples + weighted contribution waterfall |
| **Data & Metodologi** | Can we trust this? | Pipeline/lineage diagram, row-count funnel, KPPN→Kanwil join-coverage bars, 2021↔2022 era-bridge table, cited data dictionary + IKPA weights |

**Storytelling techniques:** a fixed "insight → So What" rhythm; **auto-generated callouts** templated
from the selected entity's data; a before/after split on the 2024 cohort; annotated reference lines
(national median, healthy threshold, reorganization month); progressive drill-down with breadcrumbs;
one memorable headline number repeated at the open and the close.

**BPS regional framing (chosen enrichment):** `dim_province` carries `province_name` and a
`region_island` grouping aligned to the competition's own **6 RCE regions** (Sumatera, Jawa,
Kalimantan, Sulawesi, Bali–Nusa Tenggara, Maluku–Papua), enabling the eastern-Indonesia equity story
with a clean, official, low-risk join. No budget-value (Rp) join in this phase.

---

## 7. Technical architecture

**Thesis:** never load 1.14M rows into pandas in the app. Offline ETL → columnar **Parquet**; the app
queries lazily with **DuckDB** (projection + predicate pushdown); charts read tiny pre-aggregated
tables. Steady-state RAM stays comfortably under ~300 MB on the Streamlit Community Cloud free tier.

### ETL (`etl/`, run locally; outputs committed selectively)

1. Read each year with explicit `sep=';'`, **code columns as zero-padded strings** (`'001'`, `'01'`),
   `NILAI_*` / `BOBOT_*` as numeric.
2. Normalize wide → long per component into one controlled vocabulary; tag `era`
   (`2021_old` / `2022_new`).
3. Build and **assert 1:1** the `KPPN → Kanwil` map from 2024/2025; **backfill** 2021–2023; set
   `kanwil_source`; record coverage in `meta_quality`.
4. Join small **dimension** lookups at query time (keep facts star-shaped).
5. Write Parquet (Zstd for facts, Snappy for aggregates) + a `meta_quality` lineage sidecar.

### Tidy schema (star)

- `fact_ikpa_satker.parquet` — `year, periode, era, kdba, kdkanwil, kanwil_source, kdkppn, kdsatker,
  nmsatker, nilai_total, konv_bobot, nilai_akhir, is_final_period` (~1.14M rows; **local/private**).
- `fact_ikpa_component.parquet` — long component grain `(…, component, nilai, bobot)` (~9M rows;
  **local/private**; only the Component page touches it).
- Dimensions (committed): `dim_ministry(kdba, ministry_name, ministry_short)`,
  `dim_province(kdkanwil, province_name, region_island, prov_id)`,
  `dim_kppn(kdkppn, kppn_name, kdkanwil)`.
- **Pre-aggregated, committed to the public repo:** `agg_province_year`, `agg_ministry_year`,
  `agg_kppn_year`, `agg_national_monthly`, `agg_component_year`, plus `meta_quality`. All ≤ a few
  hundred rows.

### App (`app.py` + native `pages/`, modules in `lib/`)

- `@st.cache_resource`: one DuckDB connection + the simplified province GeoJSON.
- `@st.cache_data(max_entries=…)`: every query/aggregation result, keyed by filters (data is static).
- Default `periode=12` everywhere except the explicit monthly-trend chart.
- **Plotly** for all charts incl. `choropleth_mapbox` over a **simplified 34-Kanwil GeoJSON**
  (`assets/`); join via an explicit `kdkanwil → prov_id` crosswalk in `dim_province` (KDKANWIL is the
  DJPb Kanwil code, **not** the BPS code — do not name-match).

### Reference data to author (cited; authenticity provable from official sources)

- `reference/dim_ministry.csv` — BA code → K/L name.
- `reference/dim_province.csv` — Kanwil code → province name + 6-region island group + `prov_id`.
- `reference/dim_kppn.csv` — KPPN code → name + parent Kanwil (seeded from the 2024/2025 KPPN→Kanwil
  map; names from the DJPb list).

---

## 8. Deployment + the redistribution constraint

- **Streamlit Community Cloud.** The **public repo contains ONLY** `agg_*` + `dim_*` + `meta_quality`
  + the GeoJSON. `data_raw/` and both `fact_*` Parquets are **`.gitignore`d** (local-only).
- Public pages render from aggregates (province / ministry / KPPN level), not the committee's
  row-level data, satisfying *tidak disebarluaskan*.
- The **satker-level F4 watchlist** (with names) lives in the **local/private build**, demoed in the
  presentation and optional video — not on the public link. A short on-page notice states the
  aggregate-level data policy.
- `requirements.txt`: `streamlit, duckdb, pandas, pyarrow, plotly`.

---

## 9. Project scaffold to create

```
app.py  requirements.txt  README.md  .gitignore  .streamlit/config.toml
pages/   1_Ikhtisar_Nasional.py  2_Kementerian.py  3_Provinsi.py
         4_Matriks_KL_Provinsi.py  5_Diagnostik_Komponen.py  6_Data_Metodologi.py
lib/     config.py  data.py (DuckDB + cached helpers)  charts.py  geo.py  text.py (ID copy)
etl/     build.py  normalize.py  backfill.py  aggregate.py
reference/  dim_ministry.csv  dim_province.csv  dim_kppn.csv
assets/  indonesia_kanwil.geojson (simplified)
data/    fact_*.parquet (gitignored)  dim_*.parquet  agg_*.parquet  meta_quality.parquet
data_raw/  (gitignored; the 5 source CSVs)
```

---

## 10. Build sequence

1. **Scaffold + reference data:** repo skeleton, author the 3 `dim_*.csv`, source & simplify the
   Kanwil GeoJSON, set the `kdkanwil → prov_id` crosswalk.
2. **ETL:** `normalize.py` (schema unify, era tag) → `backfill.py` (KPPN→Kanwil, province backfill) →
   `aggregate.py` / `build.py` (write facts, aggregates, `meta_quality`).
3. **App core:** `lib/data.py` cached DuckDB helpers, `lib/config.py`, `app.py` global filters; build
   F1 / F2 / F3 / F5 as reusable analytics functions.
4. **Highest-impact pages first:** `Ikhtisar Nasional` + `Matriks K/L × Provinsi` (validate the
   GeoJSON join early — the riskiest integration), then `Kementerian`, `Provinsi`,
   `Diagnostik Komponen`.
5. **`Data & Metodologi`** transparency page from `meta_quality` (cheap Data-Quality points).
6. **Local-only F4 watchlist + F6 cohort analysis** for the presentation/demo.
7. **Deploy:** finalize `.gitignore` (aggregate-only public repo), push, connect Streamlit Cloud,
   smoke-test cold-start RAM + chart latency.
8. **Submission assets:** Bahasa-Indonesia use-case description, a presentation deck mapping each page
   to the 3 judging criteria, and an optional demo video.

---

## 11. Verification

- **ETL integrity:** assert `KPPN→Kanwil` is 1:1; total rows reconcile to raw (`wc -l` minus headers,
  ~1.14M); 0 rows silently dropped (any drops reported in `meta_quality`); backfill coverage ≥
  expected % and logged; `NILAI_AKHIR` range sane (0 – ~107.5).
- **Spot-checks:** recompute a known satker's F3 contribution-to-gap by hand against the official IKPA
  weights; confirm 2021 is era-flagged and excluded from 8-component cross-year charts.
- **App run:** `streamlit run app.py`; click each page, exercise filters, confirm the choropleth colors
  all 34 Kanwil (no unmatched gray), charts render in < ~1s, cold-start RAM < ~300 MB.
- **Deploy:** load the live public URL in a clean session; confirm no `fact_*` / `data_raw` in the
  public repo; verify the data-policy notice shows.
- **Criteria check:** walk the 5-act story end-to-end and confirm each "So What" lands; verify the
  Data & Metodologi page makes the cleaning / joins / era-normalization visible.

---

## 12. How this maps to the judging criteria

| Criterion | How we score |
|---|---|
| **Data Quality** | 5 years × 1.14M rows; visible cleaning, schema harmonization, KPPN→Kanwil backfill, and 2021↔2022 era normalization on a dedicated transparency page |
| **Visualization Quality** | Deliberate chart-per-question, consistent diverging scale, guided scrollytelling with auto-generated callouts, all in Bahasa Indonesia |
| **Analysis Output** | Two-failure-mode diagnosis, Performance×Improvement targeting, component-level coaching recommendations, exportable watchlist — directly adoptable by DJPb |
