# Categorical Data Standardization Mappings

This document tracks all categorical variable standardizations applied during data unification.

**Last Updated:** 2026-01-18  
**Applied in:** `data/uni_standardize.py`

---

## 1. Response Assessment Variables

### Columns Affected:
- `best_response`
- `cart_response_category_D30` (Day 30)
- `cart_response_90_days` (Day 90)
- `cart_response_6_mos` (6 months)
- `cart_response_1_yr` (1 year)

### Standardized Categories (5):

#### Complete Response
**Consolidates:** All complete response variants including MM-specific stringent/MRD-negative responses
- `Complete Response`, `complete response`, `COMPLETE RESPONSE`
- `Complete`, `complete`, `COMPLETE`
- `CR`, `cr`
- `1`, `1.0`, `1. Complete Response`, `1, Complete Response`
- `MRD Negative Stringent Complete Response`
- `Minimal Residual Disease Negative Stringent Complete Response`
- `Minimal Residual Disease Negative`
- `Stringent Complete Response`
- `sCR`, `scr`
- `MRD Negative`, `mrd negative`

#### Partial Response
**Consolidates:** All partial response variants including MM-specific VGPR
- `Partial Response`, `partial response`, `PARTIAL RESPONSE`
- `Partial`, `partial`, `PARTIAL`
- `PR`, `pr`
- `2`, `2.0`, `2. Partial Response`, `2, Partial Response`
- `Very Good Partial Response`
- `VGPR`, `vgpr`

#### Stable Disease
**Consolidates:** All stable disease variants
- `Stable Disease`, `stable disease`, `STABLE DISEASE`
- `Stable`, `stable`, `STABLE`
- `SD`, `sd`
- `3`, `3.0`, `3. Stable Disease`, `3, Stable Disease`

#### Progressive Disease
**Consolidates:** All progressive disease variants
- `Progressive Disease`, `progressive disease`, `PROGRESSIVE DISEASE`
- `Progressive`, `progressive`, `PROGRESSIVE`
- `PD`, `pd`
- `4`, `4.0`, `4. Progressive Disease`, `4, Progressive Disease`

#### Inevaluable
**Consolidates:** All non-evaluable, indeterminate, and early death responses
- `Inevaluable`, `inevaluable`, `INEVALUABLE`
- `Indeterminate`, `indeterminate`, `INDETERMINATE`
- `died early without response assessment`
- `Died early without response assessment`
- `died early`, `Died early`
- `Not evaluable`, `not evaluable`
- `NE`, `ne`
- `5`, `5.0`, `5. Inevaluable`, `5, Inevaluable`

---

## 2. Performance Status (ECOG Scale)

### Column: `performance_status`

### Standardized Categories (4):

- **0** → `ECOG 0: Fully active`
- **1** → `ECOG 1: Restricted in strenuous activity`
- **2** → `ECOG 2: Ambulatory, self-care capable`
- **3** → `ECOG 3: Limited self-care`

**Input variants handled:** `0`, `0.0`, `0. 0`, `1`, `1.0`, `2`, `2.0`, `3`, `3.0`

---

## 3. Cause of Death

### Column: `cat_cause_death`

### Standardized Categories (2):

- **1** → `Disease progression`
- **2** → `NRM` (Non-Relapse Mortality)

**Input variants handled:**
- `1`, `1.0`, `1. Disease progression`, `1, Disease progression` → `Disease progression`
- `2`, `2.0`, `2. NRM`, `2, NRM` → `NRM`

---

## 4. CNS Involvement Variables

### Column: `cns_involvement`

- **0** → `No`
- **1** → `Yes`

**Case-insensitive:** `no`, `No`, `NO`, `yes`, `Yes`, `YES`

### Column: `cns_status`

- **0** → `Prior`
- **1** → `Active`

**Case-insensitive:** `prior`, `Prior`, `PRIOR`, `active`, `Active`, `ACTIVE`

### Column: `cns_involvement_level`

- **1** → `CNS-1`
- **2** → `CNS-2`
- **3** → `CNS-3`

**Input variants:** `1`, `1.0`, `1. CNS-1`, `1, CNS-1` → `CNS-1` (same for 2 and 3)

---

## 5. Bridging Therapy Variables

### Column: `bridging_tx`

- `Yes`, `yes`, `YES` → `Yes`
- `No`, `no`, `NO` → `No`

### Column: `bridging_type`

### Standardized Categories (4):

#### Steroids
- `Steroids`, `steroids`, `STEROIDS`
- `1`, `1.0`, `1. Steroids`, `1, Steroids`

#### Chemo-based regimen
- `Chemo-based regimen`, `chemo-based regimen`
- `Chemo-based`, `chemo-based`
- `Chemo based`, `chemo based`
- `Chemo`, `chemo`, `CHEMO`
- `2`, `2.0`, `2. Chemo-based regimen`, `2, Chemo-based regimen`

#### Radiation therapy
- `Radiation therapy`, `radiation therapy`
- `Radiation`, `radiation`, `RADIATION`
- `3`, `3.0`, `3. Radiation therapy`, `3, Radiation therapy`

#### Other
- `Other`, `other`, `OTHER`
- `4`, `4.0`, `4. Other`, `4, Other`

---

## 6. Tumor Burden

### Column: `burden_before_cart`

- **0** → `No burden`
- **bulky** → `Bulky`

**Input variants:**
- `0`, `0.0`, `None`, `none`, `NONE` → `No burden`
- `bulky`, `Bulky`, `BULKY`, `1`, `1.0` → `Bulky`

---

## 7. Ethnicity

### Column: `ethnicity`

- **0**, **0.0** → `Not Hispanic or Latino`
- **1**, **1.0** → `Hispanic or Latino`

**Input variants:** Numeric codes (0/1, 0.0/1.0) and text variants handled

---

## 8. Lymphodepleting Regimen

### Column: `lymphodep_regimen`

- **Flu/Cy** → `Fludarabine, Cyclophosphamide`
- **Fludarabine, Cyclophosphamide** → `Fludarabine, Cyclophosphamide`
- **Bendamustine** → `Bendamustine`
- **RICE** → `RICE`

**Note:** Standardizes abbreviated form "Flu/Cy" to full drug names

---

## 9. Binary Yes/No Clinical Variables

These columns had mixed numeric (0/1, 0.0/1.0) and text (Yes/No/yes/no) representations, now standardized to Yes/No:

- `icans` - Immune effector cell-associated neurotoxicity syndrome
- `iec-hs` - Immune effector cell-associated hemophagocytic lymphohistiocytosis-like syndrome
- `icu_admission` - Intensive care unit admission
- `prbc_infusion` - Packed red blood cell infusion
- `plt_transfusion` - Platelet transfusion
- `infection_30days` - Infection within 30 days
- `pt_transfusion` - Platelet transfusion

**Standardization:**
- `Yes`, `yes`, `YES`, `1`, `1.0` → `Yes`
- `No`, `no`, `NO`, `0`, `0.0` → `No`

---

## 10. Infection Type Classification

### Columns: `infection_type_30days`, `infection_type_100_days`

**Standardization:**
- Removes numeric prefixes (e.g., "1, Bacterial" → "Bacterial")
- Case-insensitive standardization: `bacterial`/`Bacterial`/`BACTERIAL` → `Bacterial`
- Case-insensitive standardization: `viral`/`Viral`/`VIRAL` → `Viral`
- Case-insensitive standardization: `fungal`/`Fungal`/`FUNGAL` → `Fungal`
- Preserves specific infection types (CMV, C diff, rhinovirus, etc.)

**Categories:**
- `Bacterial` - General bacterial infections
- `Viral` - General viral infections
- `Fungal` - General fungal infections
- Specific types (CMV, COVID, rhinovirus, etc.) preserved as-is

---

## 11. Previously Standardized Columns

These columns were standardized in earlier data cleaning phases:

### `gender`
- `1` → `Male`
- `2` → `Female`
- `3` → `Other`

### `race`
- `1` → `Race: White`
- `2` → `Race: Black or African American`
- `3` → `Race: American Indian or Alaska Native`
- `4` → `Race: Asian`
- `5` → `Race: Native Hawaiian or Other Pacific Islander`
- `6` → `Race: Other`

### `survival_status_lfu`
- `0` → `Alive`
- `1` → `Deceased`
- `2` → `Lost to FU`

### `dx_cart`
- `1` → `Lymphoma`
- `2` → `ALL`
- `3` → `MM`
- `4` → `Other`
- Numeric floats from JHU exports (`1.0`, `3.0`) are normalized in `normalize_dx_cart_value()`.

**Backfill (missing `dx_cart` only):** `backfill_dx_cart()` in `uni_standardize_helpers.py`, called from `uni_main.py` after standardization. Priority: `all_subtype` → ALL; `mm_risk_stratification` → MM; `lymphoma_subtype` == `MM` → MM; allowlisted lymphoma histology → Lymphoma. Conflicting signals leave `dx_cart` missing and set `dx_cart_source` to `backfill:conflict`. Audit column: `dx_cart_source` (`redcap` | `backfill:*`).

### `cart_product`
- `1` → `Tisa-cel`
- `2` → `Axi-cel`
- `3` → `Brexu-cel`
- `4` → `Liso-cel`
- `5` → `Ide-cel`
- `6` → `Cilta-cel`

---

## Technical Notes

### Implementation Location
All mappings are applied in `data/uni_standardize.py` within the `standardize_categorical_values()` function.

### Data Type Handling
Columns that need categorical mapping are explicitly loaded as `str` type in `data/uni_load.py` to prevent pandas from inferring them as numeric types.

### Exclusion from Generic Cleaning
All categorically-mapped columns are excluded from generic text cleaning in the `clean_column_values()` function to preserve their specific format before mapping.

### Missing Values
All mappings preserve `NaN`, `nan`, and empty string `''` as missing values.

---

## Usage

When adding new categorical mappings:

1. Add column to `categorical_cols` exclusion list in `clean_column_values()`
2. Create mapping dictionary with all observed variants
3. Apply mapping using: `df[col].map(lambda x: mapping.get(str(x).strip(), np.nan) if pd.notna(x) else np.nan)`
4. Document the mapping in this file
5. Regenerate `unified_clinical_data.csv` by running `python data/uni_main.py`
6. Verify standardization with value counts

---

**Maintained by:** Data Unification Pipeline  
**Version:** 2.0 (Jan 2026)
