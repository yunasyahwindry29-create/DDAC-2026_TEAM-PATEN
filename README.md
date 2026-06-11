# IKPA Insight — DDAC 2026 (Data Story Telling)

Dashboard Streamlit untuk **memetakan disiplin pelaksanaan anggaran (IKPA)** satuan kerja
se-Indonesia, 2021–2025. Tujuannya bukan sekadar menampilkan data, melainkan menjadi **alat
diagnosis & penargetan**: di **mana** (provinsi/K-L) dan pada **komponen apa** pembinaan DJPb
paling dibutuhkan.

Sumber data: Katalog Dataset DDAC 2026 — IKPA Satker 2021–2025 (DJPb, Kementerian Keuangan RI).

## Cerita (5 babak)
1. Rata-rata nasional yang menenangkan — IKPA naik 91.9 → 94.8.
2. Sebaran yang tersembunyi — median naik & jarak menyempit, tetapi ekor bawah (P10) tertinggal.
3. Guncangan 2024 — reorganisasi menambah ribuan satker baru; kohort baru lemah di komponen *onboarding*.
4. Di mana titik lemahnya — matriks K/L × Provinsi memisahkan masalah **wilayah** vs **sistemik K/L**.
5. Mesin penargetan — kuadran kinerja-perbaikan + daftar satker rawan → rencana pembinaan.

## Arsitektur

```
data_raw/ (5 CSV mentah, gitignored)
   │  etl/  (normalize → backfill provinsi → aggregate)
   ▼
data/ *.parquet
   ├─ fact_ikpa_satker / fact_ikpa_component   (tingkat satker — LOKAL saja, gitignored)
   ├─ dim_ministry / dim_province / dim_kppn    (dimensi)
   └─ agg_* + meta_*                            (agregat publik — yang dirender dashboard)
   │  lib/ (data+analitik, charts, geo, text, config)
   ▼
app.py + pages/ (Streamlit multipage, Bahasa Indonesia)
```

- **Agregat** (ringan, beberapa ratus baris) dibaca langsung dari Parquet dan di-cache.
- **Fakta satker** (1,14 juta baris) dikueri *lazy* via DuckDB hanya untuk halaman Watchlist.
- Peta: choropleth 34 provinsi (`assets/indonesia_kanwil.geojson`, di-join lewat
  `dim_province.geojson_state`), dengan fallback peta gelembung berbasis sentroid.

## Menjalankan lokal

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 1) bangun data (butuh data_raw/IKPA_SATKER_2021..2025.csv)
python -m etl.build

# 2) jalankan dashboard
streamlit run app.py
```

## Deploy (Streamlit Community Cloud) — kepatuhan data

`.gitignore` mengecualikan `data_raw/` dan kedua `fact_*.parquet` (data tingkat satker).
**Repo publik hanya berisi agregat** (`agg_*`, `dim_*`, `meta_*`) + GeoJSON, sehingga tautan
publik memenuhi kewajiban "data tidak diredistribusikan". Halaman **Watchlist Satker** otomatis
menampilkan pemberitahuan bila berkas fakta satker tidak ada (mode publik); daftar satker
ditunjukkan langsung dari build lokal saat presentasi/demo.

Langkah: build ETL secara lokal → commit isi `data/` (kecuali `fact_*`) → push ke GitHub →
sambungkan repo ke Streamlit Community Cloud (entrypoint `app.py`).

## Catatan metodologi
- **Era formula:** 2021 memakai formula lama 13-komponen; 2022–2025 memakai 8-komponen. Tren
  lintas-era hanya pada `NILAI_AKHIR`.
- **Rekonstruksi provinsi:** `KDKANWIL` hanya ada native di 2024/2025; peta KPPN→Kanwil (1:1)
  dipakai mem-*backfill* 2021–2023 (cakupan > 99,8%).
- **Penamaan K/L baru (2024–2025):** diturunkan dari nama satker di dalam dataset, dipadankan
  dengan struktur Kabinet Merah Putih. Lihat halaman **Data & Metodologi** untuk transparansi penuh.
# DDAC-2026_TEAM-PATEN
# DDAC-2026_TEAM-PATEN
