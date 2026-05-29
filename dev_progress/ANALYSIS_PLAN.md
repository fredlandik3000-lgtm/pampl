# Analysis Plan (Block A3 — Pre-specification)

**Purpose:** Pre-specify primary metric and primary targets for the CAR-T outcome prediction paper. No post hoc target or phase selection for main claims.

---

## Primary metric

- **Model selection and main reporting:** **Balanced accuracy (BA)**
- Rationale: Outcomes are class-imbalanced; BA gives equal weight to each class and is the standard for imbalanced classification in clinical prediction.

---

## Primary targets

Pre-specified outcome variables for the main results (all others are exploratory/supplementary):

1. **D30_response_3class** — Day 30 response (3-class: CR / PR / NR or similar)
2. **D90_is_cr** — Day 90 complete response (binary)
3. **crs_grade_ge2** — CRS grade ≥ 2 (binary)
4. **icans_grade_ge2** — ICANS grade ≥ 2 (binary)
5. **relapse_or_progression** — Relapse or progression (binary)
6. **survival_status_lfu** — Survival status at last follow-up (binary)

*(List may be shortened after evaluable-gate filtering and power considerations; any change must be documented and justified before viewing test results.)*

---

## Phases for main results

- **Primary phases:** phase_-6, phase_0, phase_15 (baseline, day 0, day 15).
- phase_30 may be included or reported separately; same pre-specification applies.

---

## No post hoc selection

- Main claims (abstract and primary results) use only the primary metric and primary targets above.
- No data-driven addition or removal of targets or phases for the main narrative after viewing model performance.
- Exploratory analyses (other targets, subgroups) must be clearly labeled as such.

---

**Document version:** 1.0  
**Last updated:** 2026-02-26  
**Reference:** Publication Readiness Roadmap (ROADMAP.md), Block A.
