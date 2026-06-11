"""Halaman 7 - Daftar Satker Rawan (F4). Deliverable yang dapat diadopsi DJPb:
roster pembinaan beserta alasan dan komponen pembebani.

CATATAN: halaman ini memakai data tingkat satker dan hanya aktif pada build
lokal/penyajian. Pada tampilan agregat publik halaman ini menampilkan pemberitahuan.
"""
import streamlit as st

from lib import data, text
from lib.config import HEALTHY_THRESHOLD

st.set_page_config(page_title="Watchlist Satker", page_icon="🚨", layout="wide")
st.title("Daftar Satker Prioritas Pembinaan")
st.caption(text.PAGE_INTRO["watchlist"])

if not data.has_satker_fact():
    st.warning(
        "Daftar tingkat satker tidak tersedia pada tampilan agregat publik (sesuai ketentuan "
        "penggunaan data lomba: data satker tidak diredistribusikan). Daftar ini ditunjukkan "
        "secara langsung pada sesi presentasi/demo dari build lokal.", icon="🔒")
    st.stop()

prov = data.province_year()
prov25 = prov[prov.year == 2025].sort_values("avg_nilai_akhir")
my = data.ministry_year()
my25 = my[my.year == 2025].sort_values("ministry_name")

c0, c1, c2 = st.columns(3)
year = c0.selectbox("Tahun", [2025, 2024, 2023, 2022, 2021], index=0)
prov_opt = ["(semua)"] + prov25["kdkanwil"].tolist()
pname = dict(zip(prov25["kdkanwil"], prov25["province_name"]))
prov_pick = c1.selectbox("Provinsi", prov_opt, format_func=lambda k: pname.get(k, k))
min_opt = ["(semua)"] + my25["kdba"].tolist()
mname = dict(zip(my25["kdba"], my25["ministry_name"]))
min_pick = c2.selectbox("K/L", min_opt, format_func=lambda k: mname.get(k, k))

wl = data.watchlist(year=year,
                    kdkanwil=None if prov_pick == "(semua)" else prov_pick,
                    kdba=None if min_pick == "(semua)" else min_pick,
                    limit=1000)
st.markdown(f"Kriteria: IKPA akhir **< {HEALTHY_THRESHOLD:.0f}** (di bawah batas sehat), "
            "diurutkan dari paling rendah.")
if wl is None or wl.empty:
    st.info("Tidak ada satker yang memenuhi kriteria pada filter ini.")
    st.stop()

st.metric("Satker rawan ditemukan", f"{len(wl):,}")
show = wl[["nmsatker", "ministry", "province", "nilai_akhir"]].rename(
    columns={"nmsatker": "Satuan Kerja", "ministry": "K/L", "province": "Provinsi",
             "nilai_akhir": "IKPA"})
st.dataframe(show, width="stretch", hide_index=True, height=460)
st.download_button("⬇️ Unduh daftar (CSV)", show.to_csv(index=False).encode("utf-8"),
                   file_name=f"watchlist_satker_{year}.csv", mime="text/csv")
st.caption("Untuk komponen pembebani spesifik tiap satker, padukan dengan halaman Diagnostik "
           "Komponen dan halaman Provinsi/Kementerian.")
