"""Halaman 1 - Ikhtisar Nasional: rata-rata yang menenangkan (Babak 1),
lalu sebaran yang tersembunyi (Babak 2)."""
import plotly.graph_objects as go
import streamlit as st

from lib import data, charts, text
from lib.config import COLOR_PRIMARY, HEALTHY_THRESHOLD

st.set_page_config(page_title="Ikhtisar Nasional", page_icon="🇮🇩", layout="wide")
st.title("Ikhtisar Nasional")
st.caption(text.PAGE_INTRO["ikhtisar"])

nat = data.national_year().sort_values("year")

# --- Babak 1: rata-rata yang menenangkan ---
st.subheader("Babak 1 - " + text.ACTS[1][0])
col1, col2 = st.columns([3, 2])
with col1:
    st.plotly_chart(charts.national_trend(nat), width="stretch")
with col2:
    st.markdown(text.ACTS[1][1])
    st.success("**So what:** Jika berhenti di sini, kita menyimpulkan semua baik-baik saja. "
               "Padahal rata-rata menyembunyikan satker yang butuh pembinaan.")

st.divider()

# --- Babak 2: sebaran yang tersembunyi ---
st.subheader("Babak 2 - " + text.ACTS[2][0])
gap25 = nat[nat.year == 2025].iloc[0]
gap21 = nat[nat.year == 2021].iloc[0]
m1, m2, m3 = st.columns(3)
m1.metric("Jarak P90-P10 (2025)", f"{gap25['p90'] - gap25['p10']:.1f} poin",
          f"{(gap25['p90'] - gap25['p10']) - (gap21['p90'] - gap21['p10']):+.1f} vs 2021",
          delta_color="inverse")
m2.metric("Gini IKPA (2025)", f"{gap25['gini']:.3f}",
          f"{gap25['gini'] - gap21['gini']:+.3f} vs 2021", delta_color="inverse")
m3.metric("Satker di bawah sehat (2025)", f"{gap25['pct_below_healthy']:.0f}%",
          f"{gap25['pct_below_healthy'] - gap21['pct_below_healthy']:+.0f} poin vs 2021",
          delta_color="inverse")

# percentile band (P10-P90) over years
fig = go.Figure()
fig.add_trace(go.Scatter(x=nat["year"], y=nat["p90"], line=dict(width=0), showlegend=False,
                         hoverinfo="skip"))
fig.add_trace(go.Scatter(x=nat["year"], y=nat["p10"], fill="tonexty",
                         fillcolor="rgba(26,82,118,0.15)", line=dict(width=0),
                         name="Rentang P10-P90"))
fig.add_trace(go.Scatter(x=nat["year"], y=nat["median_nilai_akhir"], mode="lines+markers",
                         line=dict(color=COLOR_PRIMARY, width=3), name="Median"))
fig.add_trace(go.Scatter(x=nat["year"], y=nat["p10"], mode="lines+markers",
                         line=dict(color="#C0392B", width=2, dash="dot"), name="P10 (ekor bawah)"))
fig.add_hline(y=HEALTHY_THRESHOLD, line_dash="dot", line_color="#D68910")
fig.update_layout(height=420, margin=dict(l=10, r=10, t=30, b=10), plot_bgcolor="white",
                  yaxis_title="IKPA", xaxis_title="Tahun",
                  legend=dict(orientation="h", yanchor="bottom", y=1.02))
fig.update_xaxes(dtick=1)

c1, c2 = st.columns([3, 2])
with c1:
    st.plotly_chart(fig, width="stretch")
with c2:
    st.markdown(text.ACTS[2][1])
    st.success("**So what:** Median naik dan jarak menyempit secara nasional - kabar baik - "
               "namun **ekor bawah (P10) tetap jauh tertinggal**. Kebijakan seragam salah sasaran; "
               "pembinaan harus diarahkan ke ekor itu (lihat halaman Provinsi & Matriks).")

with st.expander("📈 Pola kumulatif bulanan (mengapa Desember = IKPA tahunan)"):
    st.plotly_chart(charts.monthly_buildup(data.national_monthly()), width="stretch")
    st.caption("IKPA dihitung kumulatif. Nilai naik sepanjang tahun dan mengunci di Desember; "
               "seluruh analisis tahunan memakai posisi Desember (periode 12).")
