"""Halaman 3 - Provinsi: diagnosis komponen pembebani sebuah provinsi (F3),
peringkat KPPN di dalamnya, dan tren multi-tahun vs nasional."""
import plotly.graph_objects as go
import streamlit as st

from lib import data, charts, text
from lib.config import COLOR_PRIMARY, COLOR_WARN, HEALTHY_THRESHOLD

st.set_page_config(page_title="Provinsi", page_icon="🗺️", layout="wide")
st.title("Diagnosis Provinsi")
st.caption(text.PAGE_INTRO["provinsi"])

prov = data.province_year()
nat = data.national_year()
nat25 = nat[nat.year == 2025]["avg_nilai_akhir"].iloc[0]
prov25 = prov[prov.year == 2025].sort_values("avg_nilai_akhir")

opts = prov25["kdkanwil"].tolist()
labels = dict(zip(prov25["kdkanwil"],
                  prov25["province_name"] + " — " + prov25["avg_nilai_akhir"].round(1).astype(str)))
pick = st.selectbox("Pilih provinsi (diurutkan dari IKPA terendah)", opts,
                    format_func=lambda k: labels.get(k, k))

row = prov25[prov25.kdkanwil == pick].iloc[0]
drag = data.primary_drag("province", pick, 2025)
st.markdown(text.callout_province(row["province_name"], row["avg_nilai_akhir"], nat25,
                                  drag, row["pct_below_healthy"]))

k1, k2, k3, k4 = st.columns(4)
k1.metric("IKPA 2025", f"{row['avg_nilai_akhir']:.1f}", f"{row['avg_nilai_akhir'] - nat25:+.1f} vs nasional")
k2.metric("Wilayah", row["region_island"])
k3.metric("Jumlah satker", f"{int(row['n_satker']):,}")
k4.metric("Satker di bawah sehat", f"{row['pct_below_healthy']:.0f}%", delta_color="inverse")

st.divider()
left, right = st.columns(2)
with left:
    st.markdown("**Komponen pembebani** (kontribusi terhadap selisih vs nasional)")
    gap = data.gap_decomposition("province", pick, 2025)
    st.plotly_chart(charts.diverging_gap(gap), width="stretch")
with right:
    st.markdown("**Tren multi-tahun vs nasional**")
    pv = prov[prov.kdkanwil == pick].sort_values("year")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=pv["year"], y=pv["avg_nilai_akhir"], mode="lines+markers",
                             name=row["province_name"], line=dict(color=COLOR_PRIMARY, width=3)))
    fig.add_trace(go.Scatter(x=nat["year"], y=nat["avg_nilai_akhir"], mode="lines+markers",
                             name="Nasional", line=dict(color="#888", width=2, dash="dash")))
    fig.add_hline(y=HEALTHY_THRESHOLD, line_dash="dot", line_color=COLOR_WARN)
    fig.update_layout(height=380, margin=dict(l=10, r=10, t=30, b=10), plot_bgcolor="white",
                      yaxis_title="IKPA", xaxis_title="Tahun",
                      legend=dict(orientation="h", yanchor="bottom", y=1.02))
    fig.update_xaxes(dtick=1)
    st.plotly_chart(fig, width="stretch")

st.divider()
st.markdown("**Peringkat KPPN di provinsi ini (2025, terendah dahulu)**")
kp = data.load("agg_kppn_year")
kp = kp[kp.year == 2025].merge(data.load("dim_kppn"), on="kdkppn", how="left")
kp = kp[kp.kdkanwil == pick].sort_values("avg_nilai_akhir")
if len(kp):
    show = kp[["kppn_name", "n_satker", "avg_nilai_akhir", "median_nilai_akhir"]].rename(
        columns={"kppn_name": "KPPN", "n_satker": "Jml satker",
                 "avg_nilai_akhir": "IKPA rata-rata", "median_nilai_akhir": "Median"})
    st.dataframe(show, width="stretch", hide_index=True)
else:
    st.info("Tidak ada data KPPN untuk provinsi ini.")
