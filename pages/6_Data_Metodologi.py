"""Halaman 6 - Data & Metodologi: membuat pembersihan, penyatuan skema, dan
rekonstruksi provinsi terlihat & dapat diverifikasi (kriteria Kualitas Data)."""
import pandas as pd
import plotly.express as px
import streamlit as st

from lib import data, text
from lib.config import COMPONENTS_NEW, COMPONENTS_OLD_EXTRA, ERA_LABELS, component_label

st.set_page_config(page_title="Data & Metodologi", page_icon="🔎", layout="wide")
st.title("Data & Metodologi")
st.caption(text.PAGE_INTRO["metodologi"])

st.subheader("Alur pengolahan data (lineage)")
st.markdown(
    "```\n"
    "5 berkas CSV mentah (2021-2025, ~1,14 juta baris)\n"
    "      │  baca dengan pemisah ';', kode disimpan sebagai teks ber-nol-depan\n"
    "      ▼\n"
    "Penyatuan skema  →  tag 'era' metodologi (2021 lama 13-komponen vs 2022+ baru 8-komponen)\n"
    "      ▼\n"
    "Rekonstruksi provinsi  →  peta KPPN→Kanwil (dibangun dari 2024/2025, 1:1) di-backfill ke 2021-2023\n"
    "      ▼\n"
    "Agregasi (provinsi / K-L / KPPN / komponen)  →  Parquet siap-analitik (publik, non-satker)\n"
    "```"
)

st.subheader("Ringkasan per tahun")
meta = data.load("meta_per_year").copy()
meta["era"] = meta["era"].map(ERA_LABELS)
show = meta.rename(columns={
    "year": "Tahun", "era": "Era metodologi", "n_rows": "Baris", "n_satker": "Satker",
    "n_kppn": "KPPN", "n_kdba": "K/L", "n_components": "Komponen",
    "kanwil_native": "Kanwil asli", "kanwil_backfilled": "Kanwil backfill",
    "kanwil_unmapped": "Kanwil tak terpetakan", "avg_nilai_akhir": "IKPA rata-rata (semua periode)"})
st.dataframe(show, width="stretch", hide_index=True)

c1, c2 = st.columns(2)
with c1:
    st.markdown("**Cakupan rekonstruksi provinsi (KPPN→Kanwil)**")
    cov = meta.melt(id_vars="year",
                    value_vars=["kanwil_native", "kanwil_backfilled", "kanwil_unmapped"],
                    var_name="sumber", value_name="baris")
    cov["sumber"] = cov["sumber"].map({"kanwil_native": "Asli (2024-2025)",
                                       "kanwil_backfilled": "Backfill (2021-2023)",
                                       "kanwil_unmapped": "Tak terpetakan"})
    fig = px.bar(cov, x="year", y="baris", color="sumber", barmode="stack",
                 color_discrete_map={"Asli (2024-2025)": "#1E8449",
                                     "Backfill (2021-2023)": "#2E86C1",
                                     "Tak terpetakan": "#C0392B"},
                 labels={"year": "Tahun", "baris": "Baris", "sumber": ""})
    fig.update_layout(height=340, margin=dict(l=10, r=10, t=10, b=10),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02))
    fig.update_xaxes(dtick=1)
    st.plotly_chart(fig, width="stretch")
    tot_bf = int(meta["kanwil_backfilled"].sum())
    tot_un = int(meta["kanwil_unmapped"].sum())
    pct_un = tot_un / (tot_bf + tot_un) * 100 if (tot_bf + tot_un) else 0
    st.caption(f"{tot_bf:,} baris (2021-2023) berhasil direkonstruksi provinsinya; "
               f"hanya {tot_un:,} baris ({pct_un:.2f}% dari yang direkonstruksi) tak terpetakan "
               "(KPPN yang sudah tidak aktif di 2024/2025).")
with c2:
    st.markdown("**Verifikasi pemetaan & penamaan**")
    st.dataframe(data.load("meta_summary").rename(columns={"item": "Pemeriksaan", "value": "Hasil"}),
                 width="stretch", hide_index=True)

st.divider()
st.subheader("Jembatan metodologi: 2021 (lama) vs 2022+ (baru)")
rows = []
for c in COMPONENTS_NEW:
    rows.append({"Komponen": component_label(c), "2021 (13-komponen)": "✔", "2022-2025 (8-komponen)": "✔"})
for c in COMPONENTS_OLD_EXTRA:
    rows.append({"Komponen": component_label(c), "2021 (13-komponen)": "✔", "2022-2025 (8-komponen)": "—"})
st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
st.caption("Karena formula berubah pada 2022, perbandingan lintas-era hanya dilakukan pada "
           "**NILAI_AKHIR** (yang setara), dan setiap grafik runtun waktu menandai patahan 2021 ini.")

st.divider()
st.subheader("Catatan keterbukaan")
st.markdown(
    "- **Penamaan K/L baru (reorganisasi 2024-2025).** Kode Bagian Anggaran baru "
    "(mis. Kementerian hasil pemisahan) ditelusuri dari **nama satuan kerja di dalam dataset** "
    "(mis. unit 'Kantor Wilayah Kementerian Hukum ...' → Kementerian Hukum), lalu dipadankan dengan "
    "struktur Kabinet Merah Putih. Sebagian kecil kode dengan unit generik ditandai dengan kode BA.\n"
    "- **Provinsi = Kanwil DJPb (34).** Kode KDKANWIL adalah kode Kanwil DJPb, bukan kode BPS; "
    "pemetaan ke nama provinsi diturunkan dari nama kantor 'Kanwil Ditjen Perbendaharaan Provinsi ...' "
    "di dalam dataset.\n"
    "- **Data agregat.** Tampilan publik hanya menyajikan agregat (non-satker), sesuai ketentuan "
    "penggunaan data lomba."
)

st.subheader("Glosarium")
for k, v in text.GLOSSARY.items():
    st.markdown(f"- **{k}** — {v}")

st.caption("Sumber data: Katalog Dataset DDAC 2026 — IKPA Satker 2021-2025, Direktorat Jenderal "
           "Perbendaharaan, Kementerian Keuangan RI. Geometri peta: GeoJSON provinsi Indonesia (publik).")
