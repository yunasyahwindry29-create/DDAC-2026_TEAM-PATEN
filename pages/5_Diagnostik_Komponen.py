"""Halaman 5 - Diagnostik Komponen: 8 komponen IKPA dari waktu ke waktu, dan
Babak 3 (Guncangan 2024): perbandingan kohort satker baru vs lama (F6)."""
import plotly.express as px
import streamlit as st

from lib import data, charts, text
from lib.config import COMPONENTS_NEW, component_label

st.set_page_config(page_title="Diagnostik Komponen", page_icon="🧩", layout="wide")
st.title("Diagnostik Komponen IKPA")
st.caption(text.PAGE_INTRO["komponen"])

cy = data.load("agg_component_year")
new = cy[(cy.era == "2022_new") & (cy.component.isin(COMPONENTS_NEW))].copy()
new["label"] = new["component"].map(component_label)

st.subheader("Tren 8 komponen (2022-2025)")
st.plotly_chart(charts.component_small_multiples(new.sort_values("year")), width="stretch")

st.markdown("**Komponen terlemah secara nasional (2025)**")
last = new[new.year == 2025].sort_values("avg_nilai")
fig = px.bar(last, x="avg_nilai", y="label", orientation="h", color="avg_nilai",
             color_continuous_scale="RdYlGn", range_color=(80, 100),
             labels={"avg_nilai": "Nilai komponen rata-rata", "label": ""})
fig.update_layout(height=360, margin=dict(l=10, r=10, t=10, b=10))
st.plotly_chart(fig, width="stretch")

st.divider()
st.subheader("Babak 3 - " + text.ACTS[3][0])
st.markdown(text.ACTS[3][1])

cohort = data.cohort_comparison(2025)
if cohort is None:
    st.warning("Perbandingan kohort membutuhkan data tingkat satker (hanya tersedia pada "
               "build lokal/penyajian, tidak pada tampilan agregat publik).", icon="🔒")
else:
    order = cohort.groupby("label")["avg_nilai"].min().sort_values().index.tolist()
    cohort["label"] = cohort["label"].astype("category").cat.set_categories(order, ordered=True)
    st.plotly_chart(charts.cohort_bars(cohort.sort_values("label")), width="stretch")
    piv = cohort.pivot_table(index="label", columns="kohort", values="avg_nilai")
    baru_col = next((c for c in piv.columns if "Baru" in c), None)
    lama_col = next((c for c in piv.columns if "Lama" in c), None)
    if baru_col and lama_col:
        lag = (piv[lama_col] - piv[baru_col]).sort_values(ascending=False)  # + = satker baru tertinggal
        worst, worst_val = lag.index[0], lag.iloc[0]
        ahead, ahead_val = lag.index[-1], -lag.iloc[-1]
        st.success(
            f"**So what:** kohort satker baru paling tertinggal pada **{worst}** "
            f"(-{worst_val:.1f} poin vs satker lama) - khas unit yang baru terbentuk di "
            f"pertengahan tahun: anggaran turun belakangan dan rencana kas belum matang. "
            f"Sebaliknya, kohort baru justru lebih unggul pada **{ahead}** (+{ahead_val:.1f} poin). "
            "Selisih ini menyusut seiring unit matang - sasaran pembinaan yang jelas, "
            "bukan indikasi ketidakmampuan.")
