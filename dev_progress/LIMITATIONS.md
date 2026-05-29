# Limitations (for manuscript / reporting)

**Blocks E4 and F2**

## Study design and generalizability

- **Single center:** Data are from a single institution. Results may not generalize to other centers or populations.
- **Sample size:** The development cohort has approximately 252 patients. Many outcome targets have limited events, leading to underpowered or unstable estimates for some targets and phases.
- **No external validation:** To date, no external or temporal validation has been performed. **External validation on an independent cohort (or temporal holdout) is required before any claim of generalizability.** The current work should be framed as development and internal validation only.

## Model performance and baselines

- For several outcomes, the best model did **not** beat the majority-class baseline (reported per target in the Model vs baseline table and in the export). Those outcomes should not be presented as clinically useful predictions without further improvement or different data.
- Confidence intervals (bootstrap or from CV) are reported for primary metrics; when intervals are wide or include the majority baseline, interpretation should be cautious.

## Data and outcomes

- Evaluable gates were used so that response outcomes (e.g. D30, D90) are modeled only among evaluable patients; this reduces sample size further for some targets.
- Primary targets were pre-specified (ANALYSIS_PLAN.md); exploratory targets are reported separately and not used for main claims.

## Recommended framing (abstract and discussion)

- Frame as: *"We developed and internally validated prediction models for CAR-T outcomes using [n] patients from a single center. Performance was variable; for several outcomes models did not exceed a majority baseline. External validation is needed before clinical use."*
