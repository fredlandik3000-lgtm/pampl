"""Build Supplement S1 (table + fig S1), cohort stats, and Results figures 7–10 from data + results/latest/training_results.pkl."""
from __future__ import annotations

import argparse
import pickle
import sys
from pathlib import Path

# Repo root (Biomarkers): papers/arxiv/tools -> parents[3]
REPO_ROOT = Path(__file__).resolve().parents[3]
BIOMARKERS_APP = REPO_ROOT / "biomarkers_app"
if str(BIOMARKERS_APP) not in sys.path:
    sys.path.insert(0, str(BIOMARKERS_APP))


MODEL_DISPLAY: dict[str, str] = {
    "NN": "Neural Network",
    "LR": "Logistic Regression",
    "RF": "Random Forest",
    "XGB": "XGBoost",
    "ET": "Extra Trees",
    "CB": "CatBoost",
    "SVM": "Support Vector Machine",
    "LGB": "LightGBM",
}


TARGET_LABELS: dict[str, tuple[str, str]] = {
    "icans_grade_ge2": ("ICANS grade ≥2", "Bin"),
    "D90_is_cr": ("Day-90 complete response", "Bin"),
    "survival_status_lfu": ("Survival status at last follow-up", "Bin"),
    "crs_grade_ge2": ("CRS grade ≥2", "Bin"),
    "relapse_or_progression": ("Relapse or progression", "Bin"),
    "cat_cause_death": ("Cause of death (categorical)", "MC"),
    "cart_response_1_yr": ("CART response at 1 year", "Bin"),
    "infection_100days": ("Infection within 100 days", "Bin"),
    "cart_response_6_mos": ("CART response at 6 months", "Bin"),
    "cart_response_90_days": ("CART response at 90 days", "Bin"),
    "D30_response_3class": ("Day-30 response (3-class)", "MC"),
    "max_crs_grade": ("Maximum CRS grade", "ORD"),
    "best_response": ("Best overall response", "MC"),
    "cart_response_category_D30": ("Day-30 response category", "MC"),
    "icans_max_grade": ("Maximum ICANS grade", "ORD"),
}


def auc_is_reportable(auc: float) -> bool:
    if auc is None:
        return False
    try:
        v = float(auc)
    except (TypeError, ValueError):
        return False
    if v <= 0.0 or v >= 1.0:
        return False
    if abs(v - 0.5) < 1e-9:
        return False
    return True


def load_run(path: Path) -> tuple[list, dict]:
    with open(path, "rb") as f:
        payload = pickle.load(f)
    return payload.get("data", []), payload.get("metadata", {})


def champions_table(rows: list) -> list[dict]:
    ml = [r for r in rows if r.model_family not in ("Baseline-Majority", "Baseline-Random")]
    best: dict[tuple[str, str], object] = {}
    for r in ml:
        k = (r.target, r.phase)
        if k not in best or r.balanced_accuracy > best[k].balanced_accuracy:
            best[k] = r

    targets = sorted(set(r.target for r in rows))
    out = []
    for t in targets:
        candidates = [best[(t, ph)] for ph in ("phase_-6", "phase_0", "phase_15", "phase_30") if (t, ph) in best]
        if not candidates:
            continue
        champ = max(candidates, key=lambda x: x.balanced_accuracy)
        maj = next(
            (
                x
                for x in rows
                if x.target == champ.target and x.phase == champ.phase and x.model_family == "Baseline-Majority"
            ),
            None,
        )
        if maj is None:
            continue
        delta = champ.balanced_accuracy - maj.balanced_accuracy
        out.append(
            {
                "target": t,
                "label": TARGET_LABELS.get(t, (t, "?"))[0],
                "task": TARGET_LABELS.get(t, (t, "?"))[1],
                "phase": champ.phase,
                "model": champ.model_family,
                "ba": champ.balanced_accuracy,
                "ci_lo": champ.balanced_accuracy_ci_low,
                "ci_hi": champ.balanced_accuracy_ci_high,
                "maj": maj.balanced_accuracy,
                "delta": delta,
                "n": champ.sample_size,
                "auc": champ.auc,
            }
        )
    return out


def fmt_ci(ci_lo: float, ci_hi: float) -> str:
    if (ci_lo and ci_lo > 0) or (ci_hi and ci_hi > 0):
        return f"({ci_lo:.4f}, {ci_hi:.4f})"
    return "—"


def markdown_table(champs: list[dict]) -> str:
    champs = sorted(champs, key=lambda x: -x["ba"])
    lines = [
        "| Outcome (internal ID) | Label | Task | Best phase | Best model | BA | 95% CI | Majority BA | BA gain (vs modal) | n |",
        "|---|---|---|---|---|---:|---:|---:|---:|---:|",
    ]
    for c in champs:
        mname = MODEL_DISPLAY.get(c["model"], c["model"])
        lines.append(
            f"| {c['target']} | {c['label']} | {c['task']} | {c['phase']} | {mname} | "
            f"{c['ba']:.4f} | {fmt_ci(c['ci_lo'], c['ci_hi'])} | {c['maj']:.4f} | {c['delta']:.4f} | {c['n']} |"
        )
    return "\n".join(lines)


def cohort_paragraph(csv_path: Path) -> str:
    import pandas as pd

    df = pd.read_csv(csv_path)
    n = len(df)
    age = df["age_cart"]
    age_mean = float(age.mean())
    age_std = float(age.std(ddof=0))
    med = float(age.median())
    amin = int(age.min())
    amax = int(age.max())
    male = int((df["gender"] == "Male").sum())
    female = int((df["gender"] == "Female").sum())
    dx = df["dx_cart"].dropna()
    dx_counts = dx.value_counts()
    lymph = int(dx_counts.get("Lymphoma", 0))
    mm = int(dx_counts.get("MM", 0))
    all_ = int(dx_counts.get("ALL", 0))
    dx_n = int(dx.notna().sum())
    prior = df["number_of_prior_treatments"]
    prior_n = int(prior.notna().sum())
    prior_mean = float(prior.mean()) if prior_n else float("nan")
    prior_sd = float(prior.std(ddof=0)) if prior_n > 1 else float("nan")
    bridge = df["bridging_tx"].dropna()
    bridge_yes = int((bridge == "Yes").sum())
    bridge_no = int((bridge == "No").sum())
    bridge_miss = int(df["bridging_tx"].isna().sum())
    prod = df["cart_product"].value_counts().head(5)
    prod_bits = ", ".join(f"{k} (n = {int(v)})" for k, v in prod.items())
    crs = df["crs_yes_no"].dropna()
    crs_yes = int((crs == "Yes").sum())
    crs_doc = len(crs)
    icans = df["icans"].dropna()
    icans_yes = int((icans == "Yes").sum())
    icans_doc = len(icans)
    icu = df["icu_admission"].dropna()
    icu_yes = int((icu == "Yes").sum())
    icu_doc = len(icu)

    lines = [
        f"The development dataset is a unified clinical table combining retrospective CAR-T registry extracts from two academic medical centers "
        f"(not publicly redistributed with the code; see Software availability and reproducibility). "
        f"The analytic table contains **{n} patient records** used for modeling. "
        f"**Age at CAR-T infusion** (years): **{age_mean:.1f} ± {age_std:.1f}** (mean ± SD; median {med:.1f}; range {amin}–{amax}). "
        f"**Sex:** male n = {male}, female n = {female}. "
        f"**Disease category** (`dx_cart`) is documented for **{dx_n}** records: lymphoma (n = {lymph}), multiple myeloma (n = {mm}), acute lymphoblastic leukemia (n = {all_}); "
        f"remaining rows lack this field in the extract. "
        f"**Prior lines of therapy** (`number_of_prior_treatments`) are available for **{prior_n}** patients "
        f"({prior_mean:.2f} ± {prior_sd:.2f} mean ± SD among documented). "
        f"**Bridging therapy** (`bridging_tx`) is recorded as Yes/No for **{bridge_yes + bridge_no}** patients (Yes n = {bridge_yes}, No n = {bridge_no}; missing n = {bridge_miss}). "
        f"**CAR-T product** (top categories): {prod_bits}. "
        f"**CRS** (any) is documented for **{crs_doc}** patients (Yes n = {crs_yes}); **ICANS** (any) for **{icans_doc}** (Yes n = {icans_yes}); **ICU admission** post-infusion is sparsely populated (**{icu_doc}** non-missing; Yes n = {icu_yes}). "
        f"Effective **evaluable n** per outcome in Supplement S1 is often smaller than {n} because phase-specific gates require a valid assessment window."
    ]
    return "".join(lines)


def write_cohort_figure(csv_path: Path, out_dir: Path) -> tuple[Path, Path]:
    """Case-study cohort mix (Figure 7): indication and sex counts from unified table."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd

    _fig_style_dir = REPO_ROOT / "papers" / "arxiv" / "figures"
    if str(_fig_style_dir) not in sys.path:
        sys.path.insert(0, str(_fig_style_dir))
    import figure_style  # noqa: E402

    figure_style.apply_mpl_style()
    df = pd.read_csv(csv_path)
    out_dir.mkdir(parents=True, exist_ok=True)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.2), layout="constrained")
    dx = df["dx_cart"]
    dx_known = dx.dropna()
    miss = int(dx.isna().sum())
    lymph = int((dx_known == "Lymphoma").sum())
    mm = int((dx_known == "MM").sum())
    all_ = int((dx_known == "ALL").sum())
    labels_dx = ["Lymphoma", "MM", "ALL", "dx missing"]
    vals_dx = np.array([lymph, mm, all_, miss], dtype=float)
    y1 = np.arange(len(labels_dx))
    ax1.barh(y1, vals_dx, color=figure_style.ACCENT_BLUE_FILL, edgecolor=figure_style.ACCENT_BLUE, linewidth=0.7)
    ax1.set_yticks(y1, labels=labels_dx, fontsize=10)
    ax1.set_xlabel("Patients (n)", fontsize=10)
    ax1.set_title("Disease indication (dx_cart)", fontsize=11)
    ax1.grid(axis="x", alpha=0.3)

    male = int((df["gender"] == "Male").sum())
    female = int((df["gender"] == "Female").sum())
    labels_s = ["Male", "Female"]
    vals_s = np.array([male, female], dtype=float)
    y2 = np.arange(2)
    ax2.barh(y2, vals_s, color=figure_style.ACCENT_ORANGE_FILL, edgecolor=figure_style.ACCENT_ORANGE, linewidth=0.7)
    ax2.set_yticks(y2, labels=labels_s, fontsize=10)
    ax2.set_xlabel("Patients (n)", fontsize=10)
    ax2.set_title("Sex", fontsize=11)
    ax2.grid(axis="x", alpha=0.3)
    fig.suptitle(f"Analytic cohort (n = {len(df)} records)", fontsize=12, fontweight="600")

    png = out_dir / "fig7_cohort_demographics.png"
    svg = out_dir / "fig7_cohort_demographics.svg"
    fig.savefig(png, dpi=200, bbox_inches="tight")
    fig.savefig(svg, bbox_inches="tight")
    plt.close(fig)
    return png, svg


def write_ba_figures(champs: list[dict], out_dir: Path) -> tuple[Path, Path]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.patches import Patch

    _fig_style_dir = REPO_ROOT / "papers" / "arxiv" / "figures"
    if str(_fig_style_dir) not in sys.path:
        sys.path.insert(0, str(_fig_style_dir))
    import figure_style  # noqa: E402

    figure_style.apply_mpl_style()
    champ_color = figure_style.SERIES_PRIMARY
    maj_fill = figure_style.ACCENT_SLATE_FILL
    maj_edge = figure_style.ACCENT_SLATE

    out_dir.mkdir(parents=True, exist_ok=True)
    by_task: dict[str, list[dict]] = {"Bin": [], "MC": [], "ORD": []}
    for c in champs:
        by_task[c["task"]].append(c)
    for k in by_task:
        by_task[k].sort(key=lambda x: -x["ba"])

    fig, axes = plt.subplots(3, 1, figsize=(9.5, 10), sharex=True, layout="constrained")
    titles = [
        "Binary classification targets (balanced accuracy)",
        "Multiclass targets (balanced accuracy)",
        "Ordinal / grade targets (balanced accuracy)",
    ]
    keys = ["Bin", "MC", "ORD"]
    bar_h = 0.58
    for ax, title, key in zip(axes, titles, keys):
        rows = by_task[key]
        if not rows:
            ax.set_visible(False)
            continue
        y = np.arange(len(rows))
        labels = [r["target"] for r in rows]
        vals = [float(r["ba"]) for r in rows]
        majs = [float(r["maj"]) for r in rows]
        err_lo = [
            float(r["ba"]) - float(r["ci_lo"]) if r["ci_lo"] and float(r["ci_lo"]) > 0 else 0.0 for r in rows
        ]
        err_hi = [
            float(r["ci_hi"]) - float(r["ba"]) if r["ci_hi"] and float(r["ci_hi"]) > 0 else 0.0 for r in rows
        ]
        has_ci = any(x > 0 for x in err_lo) or any(x > 0 for x in err_hi)
        # Majority-class BA (same partitions as champion; Drive comment: show baseline on chart)
        ax.barh(
            y,
            majs,
            height=bar_h,
            color=maj_fill,
            edgecolor=maj_edge,
            linewidth=0.6,
            alpha=0.9,
            zorder=1,
            label="Majority-class BA",
        )
        if has_ci:
            xerr = np.array([err_lo, err_hi])
            ax.barh(
                y,
                vals,
                xerr=xerr,
                capsize=2,
                color=champ_color,
                alpha=0.92,
                height=bar_h,
                zorder=2,
                label="Champion BA (95% bootstrap CI)",
            )
        else:
            ax.barh(
                y,
                vals,
                color=champ_color,
                alpha=0.92,
                height=bar_h,
                zorder=2,
                label="Champion BA",
            )
        ax.set_yticks(y, labels=labels, fontsize=8)
        ax.set_title(title, fontsize=11)
        ax.set_xlim(0, 1.0)
        ax.axvline(0.5, color="#888", linestyle="--", linewidth=0.8, zorder=0)
        ax.grid(axis="x", alpha=0.3)
    handles = [
        Patch(facecolor=maj_fill, edgecolor=maj_edge, linewidth=0.6, label="Majority-class BA"),
        Patch(facecolor=champ_color, label="Champion BA (best model, best phase)"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=2, bbox_to_anchor=(0.5, -0.02), fontsize=9)
    fig.supxlabel("Balanced accuracy (best model, best phase per target; nested CV)", fontsize=10)
    fig.get_layout_engine().set(rect=(0, 0.04, 1, 1))
    png = out_dir / "fig8_ba_by_task_type.png"
    svg = out_dir / "fig8_ba_by_task_type.svg"
    fig.savefig(png, dpi=200, bbox_inches="tight")
    fig.savefig(svg, bbox_inches="tight")
    plt.close(fig)
    return png, svg


def write_delta_figures(champs: list[dict], out_dir: Path) -> tuple[Path, Path]:
    """Improvement of champion BA over majority (Figure 9), faceted by task type."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    _fig_style_dir = REPO_ROOT / "papers" / "arxiv" / "figures"
    if str(_fig_style_dir) not in sys.path:
        sys.path.insert(0, str(_fig_style_dir))
    import figure_style  # noqa: E402

    figure_style.apply_mpl_style()
    bar_color = figure_style.SERIES_PRIMARY
    out_dir.mkdir(parents=True, exist_ok=True)
    by_task: dict[str, list[dict]] = {"Bin": [], "MC": [], "ORD": []}
    for c in champs:
        by_task[c["task"]].append(c)
    for k in by_task:
        by_task[k].sort(key=lambda x: -float(x["delta"]))

    fig, axes = plt.subplots(3, 1, figsize=(9.5, 10), sharex=True, layout="constrained")
    titles = [
        "Binary targets: BA improvement over majority",
        "Multiclass targets: BA improvement over majority",
        "Ordinal targets: BA improvement over majority",
    ]
    keys = ["Bin", "MC", "ORD"]
    xmax = max((float(c["delta"]) for c in champs), default=0.1) * 1.12 + 0.02
    xmax = min(max(xmax, 0.12), 0.45)
    bar_h = 0.58
    for ax, title, key in zip(axes, titles, keys):
        rows = by_task[key]
        if not rows:
            ax.set_visible(False)
            continue
        y = np.arange(len(rows))
        labels = [r["target"] for r in rows]
        deltas = [float(r["delta"]) for r in rows]
        ax.barh(y, deltas, height=bar_h, color=bar_color, alpha=0.9, edgecolor="#2e7d32", linewidth=0.5)
        ax.set_yticks(y, labels=labels, fontsize=8)
        ax.set_title(title, fontsize=11)
        ax.set_xlim(0, xmax)
        ax.axvline(0, color="#888", linestyle="-", linewidth=0.6, zorder=0)
        ax.grid(axis="x", alpha=0.3)
    fig.supxlabel("Champion BA minus majority-class BA (same evaluable cohort; nested CV)", fontsize=10)
    fig.get_layout_engine().set(rect=(0, 0.02, 1, 1))
    png = out_dir / "fig9_ba_delta_vs_majority.png"
    svg = out_dir / "fig9_ba_delta_vs_majority.svg"
    fig.savefig(png, dpi=200, bbox_inches="tight")
    fig.savefig(svg, bbox_inches="tight")
    plt.close(fig)
    return png, svg


def write_roc_figure(champs: list[dict], out_dir: Path) -> tuple[Path, Path]:
    """ROC AUC for champion at best phase (Figure 10); NR when not reportable in export."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    _fig_style_dir = REPO_ROOT / "papers" / "arxiv" / "figures"
    if str(_fig_style_dir) not in sys.path:
        sys.path.insert(0, str(_fig_style_dir))
    import figure_style  # noqa: E402

    figure_style.apply_mpl_style()
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = sorted(champs, key=lambda x: x["target"])
    y = np.arange(len(rows))
    labels = [r["target"] for r in rows]
    fig, ax = plt.subplots(figsize=(9, 7), layout="constrained")
    bar_color = figure_style.ACCENT_BLUE
    nr_color = "#bdbdbd"
    for i, r in enumerate(rows):
        auc = r.get("auc")
        if auc_is_reportable(auc):
            v = float(auc)
            ax.barh(i, v - 0.5, left=0.5, height=0.65, color=bar_color, alpha=0.85, edgecolor=figure_style.ACCENT_BLUE, linewidth=0.5)
        else:
            ax.barh(i, 0.04, left=0.48, height=0.35, color=nr_color, edgecolor="#757575", linewidth=0.5)
            ax.text(0.52, i, "NR", va="center", fontsize=8, color=figure_style.TEXT_PRIMARY)
    ax.set_yticks(y, labels=labels, fontsize=8)
    ax.set_xlim(0.45, 1.02)
    ax.axvline(0.5, color="#888", linestyle="--", linewidth=0.8)
    ax.set_xlabel("ROC AUC (champion, best phase; NR = not reportable in export)", fontsize=10)
    ax.set_title("Secondary discrimination metric by target", fontsize=11)
    ax.grid(axis="x", alpha=0.3)
    png = out_dir / "fig10_roc_by_target.png"
    svg = out_dir / "fig10_roc_by_target.svg"
    fig.savefig(png, dpi=200, bbox_inches="tight")
    fig.savefig(svg, bbox_inches="tight")
    plt.close(fig)
    return png, svg


def write_supplement_scatter_figure(champs: list[dict], out_dir: Path) -> tuple[Path, Path]:
    """Supplement Figure S1: champion vs majority BA (one panel), marker size ~ evaluable n, color = task."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    _fig_style_dir = REPO_ROOT / "papers" / "arxiv" / "figures"
    if str(_fig_style_dir) not in sys.path:
        sys.path.insert(0, str(_fig_style_dir))
    import figure_style  # noqa: E402

    figure_style.apply_mpl_style()
    out_dir.mkdir(parents=True, exist_ok=True)
    task_color = {
        "Bin": figure_style.ACCENT_BLUE,
        "MC": figure_style.ACCENT_ORANGE,
        "ORD": figure_style.ACCENT_PURPLE,
    }
    fig, ax = plt.subplots(figsize=(7.2, 6.8), layout="constrained")
    for r in champs:
        t = r["task"]
        c = task_color.get(t, "#455a64")
        n = max(float(r["n"]), 1.0)
        size = 28.0 + 2.2 * np.sqrt(n)
        ax.scatter(
            float(r["maj"]),
            float(r["ba"]),
            c=c,
            s=size,
            alpha=0.88,
            edgecolors=figure_style.TEXT_SECONDARY,
            linewidths=0.45,
            zorder=2,
        )
    ax.plot([0, 1], [0, 1], color="#888888", linestyle="--", linewidth=1.0, zorder=1, label="No lift (y = x)")
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.0)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("Majority-class balanced accuracy", fontsize=11)
    ax.set_ylabel("Champion balanced accuracy (best phase)", fontsize=11)
    ax.set_title("Supplement S1 — all targets: champion vs majority", fontsize=12, fontweight="600")
    ax.grid(alpha=0.3)
    from matplotlib.lines import Line2D

    leg = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor=task_color["Bin"], markersize=9, label="Binary"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor=task_color["MC"], markersize=9, label="Multiclass"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor=task_color["ORD"], markersize=9, label="Ordinal"),
        Line2D([0], [0], color="#888888", linestyle="--", linewidth=1.0, label="y = x"),
    ]
    ax.legend(handles=leg, loc="lower right", fontsize=9)
    ax.text(
        0.02,
        0.98,
        "Marker area scales with evaluable n; see Supplement Table 1 for exact values.",
        transform=ax.transAxes,
        fontsize=8,
        color=figure_style.TEXT_MUTED,
        va="top",
    )
    png = out_dir / "figS1_champion_vs_majority_scatter.png"
    svg = out_dir / "figS1_champion_vs_majority_scatter.svg"
    fig.savefig(png, dpi=200, bbox_inches="tight")
    fig.savefig(svg, bbox_inches="tight")
    plt.close(fig)
    return png, svg


def write_supplement_s01_markdown(champs: list[dict], out_path: Path) -> None:
    """Write Supplement S1 markdown (Table 1 + Figure S1) for manuscript_sections."""
    cap = (
        "**Supplementary Table 1.** Best-model **balanced accuracy (BA)** and comparison to the **majority-class baseline** "
        "on the **same** evaluable cohort and phase (best phase per outcome; nested CV). "
        "Archived run: `training_results_2026-04-05_12-18-35.pkl`, mirrored as `results/latest/training_results.pkl`. "
        "*Task*: Bin = binary classification; MC = multiclass; ORD = ordinal / ordered grade. "
        "*Columns:* **Majority BA** = balanced accuracy from always predicting the modal class; "
        "**BA gain (vs modal)** = champion BA minus majority-class (always-modal) BA on the exported summary (not a separate re-fit).\n"
    )
    body = cap + "\n" + markdown_table(champs) + "\n\n"
    body += (
        "![Supplement S1: champion vs majority BA scatter.](../figures/figS1_champion_vs_majority_scatter.svg)\n\n"
        "**Supplementary Figure S1.** **Champion vs majority-class BA** for all **15** targets on one plane (nested CV export). "
        "**x-axis:** majority baseline BA; **y-axis:** champion BA at the best phase. Points **above** the dashed **y = x** line indicate "
        "lift over the trivial baseline. **Color:** task type (binary, multiclass, ordinal). **Marker size** scales with **evaluable n** "
        "(larger markers are not “better,” only more patients in that target–phase row). For **phase, model family, 95% CI**, and **ROC** context, "
        "use the table above. Regenerate this file and figure with `python papers/arxiv/tools/manuscript_from_run.py --figures`.\n"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        "## Supplement S1 — Full performance table and overview figure\n\n"
        + "This supplement holds the **numeric table** moved out of the main **Results** section, plus **Supplementary Figure S1**, "
        "a single-plane summary of champion vs majority performance.\n\n"
        + body,
        encoding="utf-8",
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pickle", type=Path, default=REPO_ROOT / "results" / "latest" / "training_results.pkl")
    ap.add_argument("--print-md", action="store_true")
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--write-md", type=Path, help="Write UTF-8 markdown table fragment")
    ap.add_argument(
        "--figures",
        action="store_true",
        help="Write fig7–10, figS1 scatter, and supplement/S01 markdown under papers/arxiv/",
    )
    ap.add_argument("--cohort-text", type=Path, help="Write cohort paragraph (UTF-8 text)")
    args = ap.parse_args()
    rows, meta = load_run(args.pickle)
    ch = champions_table(rows)
    if args.summary:
        bas = [c["ba"] for c in ch]
        dts = [c["delta"] for c in ch]
        auc_ok = sum(1 for c in ch if auc_is_reportable(c["auc"]))
        print(f"n_targets={len(ch)} BA min/max={min(bas):.4f}/{max(bas):.4f} mean={sum(bas)/len(bas):.4f}")
        print(f"Delta min/max={min(dts):.4f}/{max(dts):.4f}")
        print(f"AUC reportable={auc_ok}/{len(ch)}")
    if args.print_md:
        print(markdown_table(ch))
    if args.write_md:
        args.write_md.write_text(markdown_table(ch), encoding="utf-8")
    if args.cohort_text:
        args.cohort_text.write_text(cohort_paragraph(REPO_ROOT / "data" / "unified_clinical_data.csv"), encoding="utf-8")
    if args.figures:
        outd = REPO_ROOT / "papers" / "arxiv" / "figures"
        csv_path = REPO_ROOT / "data" / "unified_clinical_data.csv"
        for p1, p2 in (
            write_cohort_figure(csv_path, outd),
            write_ba_figures(ch, outd),
            write_delta_figures(ch, outd),
            write_roc_figure(ch, outd),
            write_supplement_scatter_figure(ch, outd),
        ):
            print(f"Wrote {p1.name} {p2.name}")
        s01 = REPO_ROOT / "papers" / "arxiv" / "manuscript_sections" / "supplement_S01_table1_and_overview.md"
        write_supplement_s01_markdown(ch, s01)
        print(f"Wrote {s01.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
