"""Gaya figure statis (matplotlib) untuk dokumen riset & jurnal.

Palet mengikuti reference palette skill dataviz: slot kategorikal urutan tetap (tidak
di-cycle), sequential satu hue (biru), diverging biru<->merah dengan titik tengah abu-abu.
Scatter/bubble dibatasi <= 3 kategori; lebih dari itu -> small multiples.
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

SURFACE = "#fcfcfb"
TEXT = "#0b0b0b"
TEXT_2 = "#52514e"
GRID = "#e4e3df"
NEUTRAL = "#b9b8b3"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
SEQ = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
DIVERGING = LinearSegmentedColormap.from_list(
    "woos_div", ["#1c5cab", "#6da7ec", "#f0efec", "#ef8a89", "#b62f2f"])
SEQUENTIAL = LinearSegmentedColormap.from_list("woos_seq", SEQ)


def apply():
    plt.rcParams.update({
        "figure.dpi": 130, "savefig.dpi": 160, "savefig.bbox": "tight",
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "font.size": 8.5, "axes.titlesize": 9.5, "axes.titleweight": "semibold", "axes.labelsize": 8.5,
        "axes.edgecolor": NEUTRAL, "axes.labelcolor": TEXT_2, "text.color": TEXT,
        "xtick.color": TEXT_2, "ytick.color": TEXT_2, "axes.grid": True, "grid.color": GRID,
        "grid.linewidth": 0.6, "axes.axisbelow": True, "axes.spines.top": False, "axes.spines.right": False,
        "legend.frameon": False, "lines.linewidth": 2, "patch.linewidth": 0,
        "axes.prop_cycle": matplotlib.cycler(color=SERIES),
    })


def bar_kw(color=SERIES[0]):
    """Bar tipis dengan celah 2px (edge warna surface)."""
    return {"color": color, "edgecolor": SURFACE, "linewidth": 1.0}
