"""IKPA Insight - DDAC 2026 Data Story Telling.
Landing page: thesis, national KPIs, and the 5-act narrative map.
"""
import streamlit as st

from lib import data, text
from lib.config import HEALTHY_THRESHOLD

st.set_page_config(page_title="IKPA Insight - DDAC 2026", page_icon="📊",
                   layout="wide", initial_sidebar_state="expanded")

st.title("📊 " + text.APP_TITLE)
st.markdown(text.APP_TAGLINE)
st.info(text.DATA_NOTICE, icon="🔒")

nat = data.national_year().sort_values("year")
cur = nat[nat["year"] == 2025].iloc[0]
prev = nat[nat["year"] == 2024].iloc[0]
prov = data.province_year()
prov25 = prov[prov["year"] == 2025]

st.subheader("Potret Nasional 2025")
c1, c2, c3, c4 = st.columns(4)
c1.metric("IKPA Nasional (rata-rata)", f"{cur['avg_nilai_akhir']:.1f}",
          f"{cur['avg_nilai_akhir'] - prev['avg_nilai_akhir']:+.1f} vs 2024")
c2.metric("Satker dievaluasi", f"{int(cur['n_satker']):,}")
c3.metric("Satker 'Sangat Baik' (>=95)", f"{cur['pct_excellent']:.0f}%",
          f"{cur['pct_excellent'] - prev['pct_excellent']:+.0f} poin")
c4.metric(f"Satker di bawah sehat (<{HEALTHY_THRESHOLD:.0f})", f"{cur['pct_below_healthy']:.0f}%",
          f"{cur['pct_below_healthy'] - prev['pct_below_healthy']:+.0f} poin", delta_color="inverse")

best = prov25.loc[prov25["avg_nilai_akhir"].idxmax()]
worst = prov25.loc[prov25["avg_nilai_akhir"].idxmin()]
st.caption(f"Provinsi tertinggi: **{best['province_name']}** ({best['avg_nilai_akhir']:.1f}) · "
           f"terendah: **{worst['province_name']}** ({worst['avg_nilai_akhir']:.1f}). "
           f"Selisih { best['avg_nilai_akhir'] - worst['avg_nilai_akhir']:.1f} poin - "
           "kesenjangan wilayah inilah inti cerita kita.")

st.divider()
st.subheader("Alur Cerita: 5 Babak")
cols = st.columns(5)
for i, (act, (title_, body)) in enumerate(text.ACTS.items()):
    with cols[i]:
        st.markdown(f"**Babak {act}**")
        st.markdown(f"**{title_}**")
        st.caption(body)

st.divider()
st.markdown("#### Navigasi")
st.markdown(
    "- **Ikhtisar Nasional** - rata-rata yang menenangkan, lalu sebaran yang tersembunyi\n"
    "- **Kementerian (K/L)** - kuadran kinerja vs tren, telusuri per K/L\n"
    "- **Provinsi** - diagnosis komponen pembebani sebuah provinsi\n"
    "- **Matriks K/L x Provinsi** - dua jenis masalah: wilayah vs sistemik\n"
    "- **Diagnostik Komponen** - 8 komponen IKPA & kohort satker baru 2024\n"
    "- **Data & Metodologi** - pembersihan, penyatuan, & rekonstruksi provinsi"
)
st.caption("Gunakan menu di sisi kiri untuk berpindah halaman. Sumber data: Katalog Dataset DDAC 2026 "
           "(IKPA Satker 2021-2025, DJPb Kementerian Keuangan).")
