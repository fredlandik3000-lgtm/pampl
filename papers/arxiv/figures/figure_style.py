"""
Canonical visual style for manuscript figures under papers/arxiv/figures/.

Use for Matplotlib (e.g. manuscript_from_run.py). Hand-authored SVGs should
match the same palette and typography (see README.md in this directory).

Manuscript numbering: do not duplicate "Figure N." as a banner inside SVGs;
captions live in markdown below the image (README Captions section).
"""

from __future__ import annotations

# --- SVG / conceptual diagram palette (aligned with papers/arxiv/figures/README.md inventory) ---
CANVAS_FILL = "#fafafa"
TEXT_PRIMARY = "#212121"
TEXT_SECONDARY = "#555555"
TEXT_MUTED = "#616161"
ARROW_STROKE = "#666666"

ACCENT_BLUE = "#1976d2"  # primary UI / timeline accent
ACCENT_BLUE_FILL = "#e3f2fd"
ACCENT_ORANGE = "#f57c00"
ACCENT_ORANGE_FILL = "#fff3e0"
ACCENT_PURPLE = "#7b1fa2"
ACCENT_PURPLE_FILL = "#f3e5f5"
ACCENT_GREEN = "#388e3c"
ACCENT_GREEN_FILL = "#e8f5e9"
ACCENT_SLATE = "#455a64"
ACCENT_SLATE_FILL = "#eceff1"

# Clinical event marker (infusion axis)
MARKER_INFUSION = "#c62828"

# Training / supervision emphasis (dashed annotations)
ANNOTATION_ORANGE = "#ef6c00"

# Primary data series (bars, highlights) — single green for quantitative plots
SERIES_PRIMARY = "#388e3c"

# --- Typography (SVG string; Matplotlib sans-serif stack) ---
FONT_STACK_SVG = "Segoe UI, Arial, sans-serif"
TITLE_FONT_SIZE = 14
TITLE_FONT_WEIGHT = "600"
BODY_FONT_SIZE = 11
CAPTION_FONT_SIZE = 10


def mpl_rc_params() -> dict:
    """Return matplotlib rc_params dict; caller should do plt.rcParams.update(...)."""
    return {
        "font.family": "sans-serif",
        "font.sans-serif": ["Segoe UI", "Arial", "DejaVu Sans", "Helvetica"],
        "figure.facecolor": CANVAS_FILL,
        "axes.facecolor": CANVAS_FILL,
        "axes.edgecolor": TEXT_SECONDARY,
        "axes.labelcolor": TEXT_PRIMARY,
        "text.color": TEXT_PRIMARY,
        "xtick.color": TEXT_MUTED,
        "ytick.color": TEXT_MUTED,
        "grid.color": "#cccccc",
        "grid.alpha": 0.35,
        "axes.grid": True,
    }


def apply_mpl_style() -> None:
    import matplotlib.pyplot as plt

    plt.rcParams.update(mpl_rc_params())
