"""All user-facing narrative copy, in Bahasa Indonesia.

Centralised so the storytelling reads consistently and auto-generated callouts
(templated from the selected entity's data) stay uniform across pages.
"""

APP_TITLE = "IKPA Insight: Memetakan Disiplin Pelaksanaan Anggaran 2021-2025"
APP_TAGLINE = ("Alat diagnosis kinerja pelaksanaan anggaran (IKPA) tingkat satuan kerja, "
               "untuk membantu DJPb menentukan **di mana** dan **pada komponen apa** "
               "pembinaan paling dibutuhkan.")

DATA_NOTICE = (
    "Tampilan publik ini menyajikan **data agregat** (tingkat provinsi/Kanwil, "
    "kementerian/lembaga, KPPN, dan komponen). Data tingkat satuan kerja tidak "
    "diredistribusikan, sesuai ketentuan penggunaan data lomba."
)

GLOSSARY = {
    "IKPA": "Indikator Kinerja Pelaksanaan Anggaran: skor 0-100 yang mengukur kualitas "
            "dan disiplin satuan kerja dalam mengeksekusi anggaran (dihitung kumulatif tiap bulan).",
    "Satker": "Satuan Kerja, unit pemerintah pengelola anggaran (DIPA).",
    "KDBA / K-L": "Kode Bagian Anggaran = Kementerian/Lembaga pengelola anggaran.",
    "Kanwil / Provinsi": "Kantor Wilayah DJPb yang mewakili wilayah provinsi (34 Kanwil).",
    "KPPN": "Kantor Pelayanan Perbendaharaan Negara, unit layanan DJPb di daerah.",
    "Komponen IKPA": "8 sub-indikator pembentuk IKPA (sejak 2022): Revisi DIPA, Deviasi Hal. III, "
                     "Penyerapan, Belanja Kontraktual, Penyelesaian Tagihan, UP/TUP, Dispensasi SPM, "
                     "dan Capaian Output.",
}

# --- The 5-act narrative spine ----------------------------------------------
ACTS = {
    1: ("Rata-rata yang Menenangkan",
        "Secara nasional IKPA terus membaik dan terlihat 'sehat'. Tetapi rata-rata "
        "menyembunyikan siapa yang sebenarnya tertinggal."),
    2: ("Sebaran yang Tersembunyi",
        "Di balik rata-rata yang naik, masih ada ekor satker berkinerja rendah. "
        "Kita perlu melihat sebaran, bukan hanya nilai tengah."),
    3: ("Pembentukan Kabinet Merah Putih 2024",
        "Reorganisasi pemerintahan akhir 2024 menambah ribuan satker baru dan "
        "kementerian baru. Kohort baru cenderung tertinggal pada komponen 'onboarding' "
        "(perencanaan & administrasi), bukan penyerapan."),
    4: ("Di Mana Titik Lemahnya",
        "Matriks K/L x Provinsi memisahkan dua jenis masalah: provinsi yang lemah di "
        "hampir semua K/L (masalah kapasitas wilayah) versus K/L yang lemah di hampir "
        "semua provinsi (masalah sistemik kementerian)."),
    5: ("Mesin Penargetan",
        "Kuadran kinerja-perbaikan plus daftar satker rawan mengubah temuan menjadi "
        "rencana pembinaan yang dapat ditindaklanjuti."),
}

PAGE_INTRO = {
    "ikhtisar": "Mulai dari gambaran nasional, lalu temukan kejutan di balik rata-rata.",
    "kementerian": "Posisikan setiap K/L pada kuadran kinerja vs tren, lalu telusuri "
                   "sebarannya antarprovinsi dan komponen yang membebani.",
    "provinsi": "Diagnosis sebuah provinsi: komponen apa yang menariknya di bawah "
                "rata-rata nasional, dan unit layanan (KPPN) mana yang tertinggal.",
    "matriks": "Baca baris untuk masalah sistemik K/L, baca kolom untuk masalah wilayah.",
    "komponen": "Lihat ke-8 komponen IKPA dari waktu ke waktu dan temukan akar pelemahan.",
    "metodologi": "Bagaimana 5 berkas mentah dibersihkan, disatukan, dan provinsinya "
                  "direkonstruksi - secara transparan dan dapat diverifikasi.",
    "watchlist": "Daftar satker prioritas pembinaan beserta alasan dan komponen pembebannya.",
}


def callout_province(name: str, score: float, national: float,
                     drag: str | None, pct_below: float) -> str:
    delta = score - national
    arah = "di atas" if delta >= 0 else "di bawah"
    s = (f"**{name}** mencatat IKPA **{score:.1f}** ({abs(delta):.1f} poin {arah} "
         f"rata-rata nasional {national:.1f}). Sekitar **{pct_below:.0f}%** satker-nya "
         f"masih di bawah batas sehat.")
    if drag:
        s += f" Komponen pembebani terbesar: **{drag}**."
    return s


def callout_ministry(name: str, score: float, national: float, drag: str | None) -> str:
    delta = score - national
    arah = "di atas" if delta >= 0 else "di bawah"
    s = (f"**{name}** mencatat IKPA **{score:.1f}** ({abs(delta):.1f} poin {arah} "
         f"rata-rata nasional {national:.1f}).")
    if drag:
        s += f" Komponen pembebani terbesar: **{drag}**."
    return s
