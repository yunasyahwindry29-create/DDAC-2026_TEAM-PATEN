"""Halaman 2 - Kementerian/Lembaga: kuadran kinerja vs tren (F2), lalu telusuri
sebaran satu K/L antarprovinsi (peta) dan komponen pembebani (F3)."""
import streamlit as st

from lib import data, charts, geo, text

st.set_page_config(page_title="Kementerian (K/L)", page_icon="🏛️", layout="wide")
st.title("Kementerian / Lembaga")
st.caption(text.PAGE_INTRO["kementerian"])

nat = data.national_year()
nat25 = nat[nat.year == 2025]["avg_nilai_akhir"].iloc[0]

# --- F2 quadrant ---
st.subheader("Peta Kinerja vs Tren (2025)")
min_satker = st.slider("Saring K/L dengan jumlah satker minimum", 0, 200, 20, step=10)
q = data.quadrant("ministry", latest_year=2025, slope_from=2022)
q = q[q["n_satker"] >= min_satker]
st.plotly_chart(charts.quadrant_scatter(q, "ministry_name"), width="stretch")
st.caption("Sumbu-X = IKPA terkini, sumbu-Y = tren rata-rata per tahun (2022-2025). "
           "Kuadran kiri-bawah (**Rawan**) = prioritas pembinaan; kanan-bawah (**Melemah**) = "
           "perlu diwaspadai meski masih tinggi.")

counts = q["quadrant_label"].value_counts()
cc = st.columns(len(counts))
for i, (lab, n) in enumerate(counts.items()):
    cc[i].metric(lab, f"{n} K/L")

st.divider()

# --- Drill-down satu K/L ---
st.subheader("Telusuri satu Kementerian/Lembaga")
my = data.ministry_year()
my25 = my[my.year == 2025].sort_values("ministry_name")
options = my25["kdba"].tolist()
labels = dict(zip(my25["kdba"], my25["ministry_name"] + " (" + my25["n_satker"].astype(str) + " satker)"))
# default to the lowest-scoring K/L that is large enough to be representative
sizable = my25[my25["n_satker"] >= 50]
default_kdba = (sizable if len(sizable) else my25).loc[
    (sizable if len(sizable) else my25)["avg_nilai_akhir"].idxmin(), "kdba"]
pick = st.selectbox("Pilih K/L", options, format_func=lambda k: labels.get(k, k),
                    index=options.index(default_kdba))

row = my25[my25.kdba == pick].iloc[0]
drag = data.primary_drag("ministry", pick, 2025)
st.markdown(text.callout_ministry(row["ministry_name"], row["avg_nilai_akhir"], nat25, drag))

left, right = st.columns(2)
with left:
    st.markdown("**Sebaran antarprovinsi** (peta IKPA K/L ini per provinsi)")
    mp = data.matrix_ministry_province(2025)
    mp = mp[mp.kdba == pick]
    dp = data.dim_province()
    mp = mp.merge(dp[["kdkanwil", "geojson_state", "lat", "lon"]], on="kdkanwil", how="left")
    if len(mp):
        st.plotly_chart(
            geo.province_map(mp, "avg_nilai_akhir", "IKPA",
                             color_range=(80, 100),
                             hover_cols=["avg_nilai_akhir", "n_satker"]),
            width="stretch")
    else:
        st.info("Tidak ada data provinsi untuk K/L ini.")
with right:
    st.markdown("**Komponen pembebani** (kontribusi terhadap selisih vs nasional)")
    gap = data.gap_decomposition("ministry", pick, 2025)
    st.plotly_chart(charts.diverging_gap(gap), width="stretch")
    st.caption("Batang merah ke kanan = komponen yang menarik K/L ini di bawah rata-rata nasional.")
