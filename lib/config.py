"""Shared configuration: paths, component vocabulary, labels, thresholds, colors.

Used by both the ETL pipeline (etl/) and the Streamlit app (app.py, pages/).
All user-facing copy is in Bahasa Indonesia.
"""
from pathlib import Path

# --- Paths -------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = ROOT / "data_raw"
DATA = ROOT / "data"
REFERENCE = ROOT / "reference"
ASSETS = ROOT / "assets"

GEOJSON_PATH = ASSETS / "indonesia_kanwil.geojson"
GEOJSON_FEATURE_KEY = "properties.state"  # join key inside the GeoJSON

YEARS = [2021, 2022, 2023, 2024, 2025]

# --- IKPA component vocabulary ----------------------------------------------
# 8-component formula used 2022-2025 ("new" era).
COMPONENTS_NEW = [
    "REV_DIPA", "HAL3_DIPA", "REALISASI", "KONTRAKTUAL",
    "TAGIHAN", "UP_TUP", "DISPENSASI_SPM", "CAPUT",
]
# Extra components that only exist in the 2021 ("old") 13-component formula.
COMPONENTS_OLD_EXTRA = ["PAGU_MINUS", "LPJ", "RETUR", "RENKAS", "SALAH_SPM"]

# Human-readable Bahasa Indonesia labels for every component code.
COMPONENT_LABELS = {
    "REV_DIPA": "Revisi DIPA",
    "HAL3_DIPA": "Deviasi Halaman III DIPA",
    "REALISASI": "Penyerapan Anggaran",
    "KONTRAKTUAL": "Belanja Kontraktual",
    "TAGIHAN": "Penyelesaian Tagihan",
    "UP_TUP": "Pengelolaan UP dan TUP",
    "DISPENSASI_SPM": "Dispensasi SPM",
    "CAPUT": "Capaian Output",
    "PAGU_MINUS": "Pagu Minus",
    "LPJ": "Penyampaian LPJ Bendahara",
    "RETUR": "Retur SP2D",
    "RENKAS": "Renkas / RPD Harian",
    "SALAH_SPM": "Kesalahan SPM",
}

ERA_LABELS = {
    "2021_old": "Formula lama (13 komponen, 2021)",
    "2022_new": "Formula baru (8 komponen, 2022-2025)",
}

# --- Thresholds / business rules --------------------------------------------
EXCELLENT_THRESHOLD = 95.0    # nilai_akhir >= 95 dianggap "Sangat Baik"
HEALTHY_THRESHOLD = 89.0      # batas sehat nasional (acuan)
COMPONENT_FLOOR = 70.0        # komponen di bawah ini = lampu merah
FINAL_PERIODE = 12            # IKPA tahunan = posisi bulan Desember (kumulatif)

# 6 regional groupings = the DDAC 2026 RCE regions.
REGION_ORDER = [
    "Sumatera", "Jawa", "Kalimantan",
    "Bali dan Nusa Tenggara", "Sulawesi", "Maluku dan Papua",
]

# --- 2024 Kabinet Merah Putih reorganization (Perpres 139/2024) -------------
# 9 predecessor ministries split into 21 successors. Predecessors have satker
# only through 2024; successors only from 2025. Used for the before/after
# component heatmap on the Diagnostik Komponen page.
# Each entry: (family_label, predecessor_kdba, [successor_kdba, ...]).
REORG_FAMILIES = [
    ("Hukum, HAM & Pemasyarakatan (eks Kemenkumham)", "013", ["135", "136", "137"]),
    ("Pendidikan & Kebudayaan (eks Kemendikbudristek)", "023", ["138", "139", "140"]),
    ("Lingkungan Hidup & Kehutanan (eks KLHK)", "029", ["143", "144"]),
    ("Infrastruktur & Perumahan (eks PUPR)", "033", ["145", "146", "132"]),
    ("Pariwisata & Ekonomi Kreatif (eks Kemenparekraf)", "040", ["148", "147"]),
    ("Koperasi & UMKM (eks Kemenkop UKM)", "044", ["149", "150"]),
    ("Desa & Transmigrasi (eks Kemendes PDTT)", "067", ["151", "152"]),
    ("Koordinator Polhukam (eks Kemenko Polhukam)", "034", ["129", "130"]),
    ("Koordinator PMK (eks Kemenko PMK)", "036", ["134"]),
]
REORG_PREDECESSOR_YEAR = 2024
REORG_SUCCESSOR_YEAR = 2025
# Components shown in the reorg heatmap (Dispensasi SPM excluded: ~0 / zero-weight for all).
REORG_HEATMAP_COMPONENTS = [
    "REV_DIPA", "HAL3_DIPA", "REALISASI", "KONTRAKTUAL", "TAGIHAN", "UP_TUP", "CAPUT",
]

# --- Color palette -----------------------------------------------------------
COLOR_PRIMARY = "#1A5276"
COLOR_GOOD = "#1E8449"
COLOR_WARN = "#D68910"
COLOR_BAD = "#C0392B"
# Diverging scale for "below / above benchmark" used consistently across charts.
DIVERGING_SCALE = "RdYlGn"
SEQUENTIAL_SCALE = "Blues"


def component_label(code: str) -> str:
    return COMPONENT_LABELS.get(code, code)
