# Manuscript figures (`papers/arxiv/figures/`)

Canonical style for **all** publication-bound figures in this work (SVG hand-drawn and PNG/SVG exported from code). **Future figures should follow this spec** so Methods, Results, and supplements look like one series.

## Current inventory (order of first appearance in the manuscript)

| Figure | Files | Where used |
|--------|--------|--------------|
| **1** | `fig1_scope_overview.svg` | **Introduction**, reporting gaps vs design commitments (contrast schematic) |
| **2** | `fig2_pipeline_architecture.svg` | **Methods**, *Software overview* (end-to-end pipeline flow) |
| **3** | `fig3_software_modules.svg` | **Methods**, *Software overview* (application vs training core) |
| **4** | `fig4_phase_landmarks.svg` | **Methods**, *Clinical phase windows and terminology* |
| **5** | `fig5_target_derivation_evaluable_gates.svg` | **Methods**, *Target derivation and evaluable gates* |
| **6** | `fig6_nested_cv.svg` | **Methods**, *Evaluation protocol* (nested cross-validation) |
| **7** | `fig7_cohort_demographics.svg` (+ `.png` from `manuscript_from_run.py`) | **Results**, *Case study cohort*: indication and sex counts (`data/unified_clinical_data.csv`) |
| **8** | `fig8_ba_by_task_type.svg` (+ `.png`) | **Results**, champion vs **majority-class** BA by task type (nested CV) |
| **9** | `fig9_ba_delta_vs_majority.svg` (+ `.png`) | **Results**, BA improvement over majority by task type |
| **10** | `fig10_roc_by_target.svg` (+ `.png`) | **Results**, ROC AUC by target (NR = not reportable in export) |

Regenerate **Figures 7–10** together: `python papers/arxiv/tools/manuscript_from_run.py --figures` (repo root).

## Supplement figures (not renumbered with main text)

| ID | Files | Where used |
|----|--------|------------|
| **S1** | `figS1_champion_vs_majority_scatter.svg` (+ `.png`) | [`manuscript_sections/supplement_S01_table1_and_overview.md`](../manuscript_sections/supplement_S01_table1_and_overview.md) — champion vs majority BA, marker size ~ **n** |

Written by the same `manuscript_from_run.py --figures` run as Figures 7–10.

Filenames `figK_*` are legacy basenames; **manuscript figure numbers** follow first appearance in `manuscript_sections/*.md` (not necessarily `K`).

## Renumbering rule (mandatory for this repo)

Whenever you **add or remove** a manuscript figure:

1. **Rename** assets under `papers/arxiv/figures/` so `fig{N}_…` matches the new **global** figure order (first mention in **Abstract → Methods → Results → Discussion** as applicable).
2. **Edit SVG metadata only:** keep `<title>` / `<desc>` for accessibility (short description **without** duplicating the manuscript “Figure N.” line). **Do not** draw **Figure N.** as a banner inside the artwork; the numbered caption lives in markdown **below** the image (see **Captions**).
3. **Search the repo** for `Figure `, `fig`, and old basenames (`rg -i "figure|fig[0-9]" papers/arxiv biomarkers_app/docs` from repo root) and update **`manuscript_sections/*.md`**, **`papers/arxiv/tools/manuscript_from_run.py`**, this **README** inventory, **`AGENTS.md`**, **`.cursor/rules/biomarkers.mdc`**, **`manuscript_todo.md`**, and any **`papers/arxiv/*.md`** that cite figures.
4. **Regenerate** Matplotlib exports: `python papers/arxiv/tools/manuscript_from_run.py --figures` so PNG/SVG basenames match the new number.
5. **Refresh** the inventory table above.

## Canvas

| Use | Width | Height | `viewBox` |
|-----|-------|--------|-----------|
| Default schematic | 720 | 200 | `0 0 720 200` |
| Taller schematic (modules, timelines, target/gate flow) | 720 | 220–230 | `0 0 720 220` or `0 0 720 230` |

Background: **`#fafafa`** (full-bleed `<rect>` or Matplotlib `figure.facecolor`).

## Layout (conceptual diagrams)

- **Data flow:** orient the main sequence **left to right** (earlier → later on timelines; pipeline order for flowcharts). Use explicit arrows where direction matters.
- **Inside the graphic:** keep **short** node and axis labels only (names of phases, modules, landmarks). Do **not** add second-line **subtitles** under boxes, narrative **footnotes**, or “legend paragraphs” in the SVG—those belong in the manuscript **Figure N.** caption only.

## Captions (manuscript — sole place for the figure legend)

**Do not** place a manuscript-style banner (**“Figure N. …”**) inside the artwork.

In **`manuscript_sections/*.md`**, use this pattern only:

1. Optional brief pointer in the running text if needed (do **not** duplicate the figure legend there).
2. `![Short alt for screen readers.](../figures/figN_….svg)` — `alt` is **not** the full legend.
3. **`Figure N.`** One or more **substantial** sentences that explain what appears in the figure: main layout, direction of flow, color or box roles if non-obvious, and how to read symbols (this is the **only** place for that explanation).

Do **not** insert separate subtitle lines such as “(conceptual schematic)” or “Legend: …” **above** the image; the **Figure N.** block carries the full caption.

## Typography

- **Font stack:** `Segoe UI, Arial, sans-serif` (SVG `font-family`; Matplotlib sans-serif with the same stack — see [`figure_style.py`](figure_style.py)).
- **Internal diagram text** (boxes, arrows, short axis words): **10–12** pt; default **11** pt for box titles. Avoid extra footer lines inside the SVG; use the markdown **Figure N.** caption for narrative.

## Color palette (conceptual diagrams)

Use these for fills and strokes so schematic figures (**Figures 1–6** in the current inventory) stay visually consistent:

| Role | Stroke | Fill |
|------|--------|------|
| Primary / UI / timeline accent | `#1976d2` | `#e3f2fd` |
| Phase / windows / warm accent | `#f57c00` | `#fff3e0` |
| Models / gates / purple accent | `#7b1fa2` | `#f3e5f5` |
| Success / evaluable / “go” path | `#388e3c` | `#e8f5e9` |
| Neutral / metrics | `#455a64` | `#eceff1` |

Shared neutrals:

- Arrows and connectors: **`#666666`**
- Secondary label text: **`#616161`**
- Infusion / hazard vertical (timeline): **`#c62828`**
- Dashed “training / supervision” annotation: **`#ef6c00`** (stroke); text **`#e65100`**

## Quantitative plots (Matplotlib)

- Primary series color: **`#388e3c`** (aligned with green accent stroke above; replaces ad hoc greens).
- Reference line (e.g. BA = 0.5): `#888888`, dashed.
- Before saving: `apply_mpl_style()` from [`figure_style.py`](figure_style.py).

## File naming

`fig{number}_{short_snake_name}.svg`  
Use a **single global N** per main figure; avoid ad hoc suffixes in filenames unless the journal uses lettered panels (e.g. `figS1_…` for supplement).

When a PNG is generated for Google Docs or print, keep the **same basename** as the SVG.

## Markdown usage in `manuscript_sections/`

Standard pattern (image then caption below):

```markdown
![Short alt for accessibility.](../figures/figN_….svg)

**Figure N.** Full caption text here.
```

For Google Doc paste without images, use the **`Figure N.`** line alone.

## Checklist before adding a new figure

- [ ] Canvas 720×200 or 720×220, background `#fafafa`
- [ ] **No** “Figure N.” banner inside the SVG; **no** subtitle/footnote paragraphs inside the SVG
- [ ] Main flow **left to right** (or time left → right on timelines)
- [ ] Colors from the table above (no one-off hex unless added here)
- [ ] **Figure N.** in markdown is a **substantial** legend (what is shown and how to read it)
- [ ] Filename matches `fig*_*.svg` convention
