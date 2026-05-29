# Zenodo archive (DOI for preprint)

GitHub is live; a **Zenodo DOI** is still required for citable, persistent archiving (manuscript §6).

## Recommended workflow

1. Sign in at [zenodo.org](https://zenodo.org) with your GitHub account.
2. **Account → GitHub** → enable sync for **`fredlandik3000-lgtm/pampl`**.
3. Create a release from tag **`v0.1.0-manuscript`** (or newer manuscript tag).
4. Zenodo builds an archive and assigns a DOI (e.g. `10.5281/zenodo.XXXXXXX`).
5. Update these files with the DOI:
   - `CITATION.cff` — add under `identifiers:` with `type: doi`
   - `README.md` — Citation section
   - `papers/arxiv/manuscript_sections/06_Software_Availability_and_reproducibility.md`

## Example `CITATION.cff` snippet (after Zenodo)

```yaml
identifiers:
  - type: doi
    value: 10.5281/zenodo.XXXXXXX
```

## Manuscript tag policy

Record the **git tag** and **commit SHA** used for Supplement S1 and Figures 7–10 in §6 whenever you regenerate results. Tag naming: `v0.1.0-manuscript`, `v0.1.1-manuscript`, etc.
