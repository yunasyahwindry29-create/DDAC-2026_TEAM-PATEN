"""Halaman 4 - Matriks K/L x Provinsi (F5). Baris = masalah sistemik K/L,
kolom = masalah wilayah. Toggle residual menyorot pasangan K/L-provinsi yang
buruk secara spesifik (lebih buruk dari yang diperkirakan baris+kolom)."""
import plotly.express as px
import streamlit as st

from lib import data, charts, text
from lib.config import REGION_ORDER

st.set_page_config(page_title="Matriks K/L x Provinsi", page_icon="🔢", layout="wide")
st.title("Matriks Kementerian × Provinsi")
st.caption(text.PAGE_INTRO["matriks"])

c0, c1, c2 = st.columns([1, 1, 2])
year = c0.selectbox("Tahun", [2025, 2024, 2023, 2022, 2021], index=0)
topn = c1.slider("Jumlah K/L terbesar (per satker)", 10, 40, 25, step=5)
regions = c2.multiselect("Wilayah", REGION_ORDER, default=REGION_ORDER)

m = data.matrix_ministry_province(year, min_satker=1)
m = m[m["region_island"].isin(regions)]

# top-N ministries by total satker in scope
top = (m.groupby(["kdba", "ministry_short"])["n_satker"].sum()
       .sort_values(ascending=False).head(topn).reset_index())
m = m[m["kdba"].isin(top["kdba"])]

piv = m.pivot_table(index="ministry_short", columns="province_short",
                    values="avg_nilai_akhir", aggfunc="mean")
# order columns by region then province
col_order = (data.dim_province().assign(
    region_rank=lambda d: d["region_island"].map({r: i for i, r in enumerate(REGION_ORDER)}))
    .sort_values(["region_rank", "province_name"])["province_short"])
piv = piv.reindex(columns=[c for c in col_order if c in piv.columns])

mode = st.radio("Tampilan", ["Nilai IKPA", "Residual (pasangan spesifik)"], horizontal=True)
if mode.startswith("Residual"):
    grand = piv.stack().mean()
    row_m = piv.mean(axis=1)
    col_m = piv.mean(axis=0)
    resid = piv.sub(row_m, axis=0).sub(col_m, axis=1) + grand
    fig = px.imshow(resid, color_continuous_scale="RdBu", zmin=-8, zmax=8, aspect="auto",
                    labels=dict(x="Provinsi", y="K/L", color="Residual"))
    fig.update_xaxes(side="top", tickangle=45, title_text="")
    fig.update_yaxes(title_text="")
    fig.update_layout(margin=dict(l=10, r=10, t=60, b=10), height=620)
    st.plotly_chart(fig, width="stretch")
    st.caption("Biru tua = pasangan K/L-provinsi yang **jauh lebih buruk** daripada yang "
               "dijelaskan oleh rata-rata baris (K/L) dan kolom (provinsi) - titik intervensi spesifik.")
else:
    st.plotly_chart(charts.matrix_heatmap(piv, zmin=80, zmax=100), width="stretch")

st.divider()
st.subheader("Dua jenis masalah")
left, right = st.columns(2)
with left:
    st.markdown("**Masalah wilayah** - provinsi terlemah lintas K/L (rata-rata kolom)")
    col_rank = piv.mean(axis=0).sort_values().head(10).reset_index()
    col_rank.columns = ["Provinsi", "IKPA rata-rata"]
    fig = px.bar(col_rank, x="IKPA rata-rata", y="Provinsi", orientation="h",
                 color="IKPA rata-rata", color_continuous_scale="RdYlGn", range_color=(85, 97))
    fig.update_layout(height=380, margin=dict(l=10, r=10, t=10, b=10), yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig, width="stretch")
with right:
    st.markdown("**Masalah sistemik** - K/L terlemah lintas provinsi (rata-rata baris)")
    row_rank = piv.mean(axis=1).sort_values().head(10).reset_index()
    row_rank.columns = ["K/L", "IKPA rata-rata"]
    fig = px.bar(row_rank, x="IKPA rata-rata", y="K/L", orientation="h",
                 color="IKPA rata-rata", color_continuous_scale="RdYlGn", range_color=(85, 97))
    fig.update_layout(height=380, margin=dict(l=10, r=10, t=10, b=10), yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig, width="stretch")
st.success("**So what:** provinsi di kiri butuh penguatan kapasitas wilayah (Kanwil/KPPN); "
           "K/L di kanan butuh koordinasi dengan unit perencana pusat K/L tersebut. "
           "Dua masalah, dua pemilik tindakan.")
