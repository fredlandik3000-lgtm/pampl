# Biomarkers Pipeline Visualization & Debug Tool
## Documentation Index

**Start here:** [DOCUMENTATION.md](DOCUMENTATION.md) — map of specs, roadmaps, and where outputs live (`../../results/README.md`).

Welcome to the comprehensive documentation for the Biomarkers Pipeline Tool project.

---

## Quick Navigation

### 📋 Core Documents
1. **[SPECIFICATIONS.md](SPECIFICATIONS.md)** - Complete functional and technical specifications
2. **[IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md)** - Phased development plan with timelines

### 🎨 Design Documents
3. **[UI_MOCKUPS.md](UI_MOCKUPS.md)** - User interface wireframes and visual design
4. **[DATA_FLOW.md](DATA_FLOW.md)** - System architecture and data flow diagrams

### 💻 Technical References
5. **[API_SPECIFICATIONS.md](API_SPECIFICATIONS.md)** - Wrapper API for pipeline integration

---

## Document Overview

### SPECIFICATIONS.md
**Purpose**: Master specification document covering all aspects of the application  
**Audience**: All team members, stakeholders  
**Key Sections**:
- Functional requirements (FR-001 through FR-095)
- **§2.1.2b + Tab 3:** Visualizations metadata contract (`roc_curves`, `cv_curve_source`, etc.) and UI behavior—required reading before changing `model_training_wrapper.py` or `visualizations_widget.py`
- Pipeline integration details
- UI specifications
- Technical architecture
- Performance requirements
- Export & reporting
- Testing strategy
- Security & privacy
- Distribution & deployment
- Open questions for decision

**When to Use**: 
- Before starting any implementation
- When making architectural decisions
- When clarifying feature requirements
- As reference during development

---

### UI_MOCKUPS.md
**Purpose**: Visual representation of all UI components  
**Audience**: Developers, UX reviewers  
**Key Sections**:
- Main window layouts (12 different views)
- Dialog mockups (parameter editor, NN config, export)
- Tab structures and navigation
- Color scheme and styling
- Keyboard shortcuts
- Interactive elements

**When to Use**:
- During UI implementation
- When reviewing user flows
- When making design decisions
- For stakeholder demos

---

### DATA_FLOW.md
**Purpose**: Technical details of system architecture and data movement  
**Audience**: Developers  
**Key Sections**:
- High-level architecture diagram
- Step-by-step pipeline execution flow (all 9 steps)
- Visualization data flow
- Configuration management flow
- Results caching strategy
- Threading & concurrency model
- Error propagation
- Export data flow

**When to Use**:
- When implementing pipeline orchestration
- When debugging data flow issues
- When optimizing performance
- When adding new pipeline steps

---

### API_SPECIFICATIONS.md
**Purpose**: Detailed API for wrapping existing pipeline code  
**Audience**: Developers  
**Key Sections**:
- Core principles and type definitions
- DataLoaderWrapper API
- TargetDerivationWrapper API
- FeatureEngineeringWrapper API
- ModelTrainerWrapper API (all 5 model families)
- ModelEvaluatorWrapper API
- VisualizationGenerator API
- PipelineOrchestrator API

**When to Use**:
- When implementing wrapper classes
- When integrating existing pipeline code
- When adding new model types
- When extending functionality

---

### IMPLEMENTATION_ROADMAP.md
**Purpose**: Phased development plan with task breakdowns  
**Audience**: Project managers, developers  
**Key Sections**:
- 7 development phases (Weeks 1-8)
- Task checklists for each phase
- Deliverables and acceptance criteria
- Risk management
- Success metrics
- Post-launch enhancements
- Development guidelines

**When to Use**:
- For project planning
- When tracking progress
- When estimating timelines
- When prioritizing features

---

## How to Use This Documentation

### For Initial Planning
1. Read SPECIFICATIONS.md (sections 1-2) for overview
2. Review UI_MOCKUPS.md for visual understanding
3. Study IMPLEMENTATION_ROADMAP.md for timeline

### For Development
1. Start with IMPLEMENTATION_ROADMAP.md for your current phase
2. Reference SPECIFICATIONS.md for detailed requirements
3. Use API_SPECIFICATIONS.md for implementation details
4. Consult DATA_FLOW.md for architecture clarity
5. Check UI_MOCKUPS.md for UI implementation

### For Code Review
1. Check implementation against SPECIFICATIONS.md requirements
2. Verify data flow matches DATA_FLOW.md
3. Ensure API contracts follow API_SPECIFICATIONS.md
4. Compare UI to UI_MOCKUPS.md

### For Testing
1. Use SPECIFICATIONS.md functional requirements as test cases
2. Follow acceptance criteria from IMPLEMENTATION_ROADMAP.md
3. Test data flows described in DATA_FLOW.md
4. Verify UI matches UI_MOCKUPS.md

---

## Open Questions & Decisions

The following questions from SPECIFICATIONS.md require decisions:

### Data Loading
- **Q**: Should the app package sample/demo data for colleagues without access to full dataset?
- **Decision**: [ ] Yes, include anonymized sample  [ ] No, require full data  [ ] TBD

### Model Persistence
- **Q**: Should trained models be saved to disk for later inspection/deployment?
- **Decision**: [ ] Yes, save all models  [ ] Yes, save champions only  [ ] No  [ ] TBD

### Comparison Baseline
- **Q**: Should we always compare against the July 2025 baseline results?
- **Decision**: [ ] Yes, always  [ ] Make it optional  [ ] No  [ ] TBD

### Validation Methods
- **Q**: Which validation method should be default (nested CV, holdout, or k-fold)?
- **Decision**: [ ] Nested CV  [ ] Holdout  [ ] K-fold  [ ] TBD

### Feature Selection
- **Q**: Should the app support interactive feature selection (enable/disable features)?
- **Decision**: [ ] Yes, v1.0  [ ] Yes, later version  [ ] No  [ ] TBD

### Ensemble Models
- **Q**: Should the app support custom ensemble creation (average of selected models)?
- **Decision**: [ ] Yes, v1.0  [ ] Yes, later version  [ ] No  [ ] TBD

### Branding
- **Q**: Application name, logo, color scheme preferences?
- **Decision**: 
  - Name: [ ] "Biomarkers Pipeline Tool"  [ ] Other: _____________
  - Logo: [ ] Custom design  [ ] Simple icon  [ ] None
  - Colors: [ ] Use Microsoft blue scheme  [ ] Custom: _____________

---

## Document Status

| Document | Version | Last Updated | Status | Reviewer |
|----------|---------|--------------|--------|----------|
| SPECIFICATIONS.md | 1.0 | 2026-01-18 | Draft for Review | - |
| UI_MOCKUPS.md | 1.0 | 2026-01-18 | Draft for Review | - |
| DATA_FLOW.md | 1.0 | 2026-01-18 | Draft for Review | - |
| API_SPECIFICATIONS.md | 1.0 | 2026-01-18 | Draft for Review | - |
| IMPLEMENTATION_ROADMAP.md | 1.0 | 2026-01-18 | Draft for Review | - |

### Review Process
1. **Technical Review**: Verify accuracy, completeness, feasibility
2. **Stakeholder Review**: Confirm requirements match needs
3. **Final Approval**: Sign off on specifications before implementation

---

## Next Steps

### Before Starting Implementation
1. [ ] Review all documentation
2. [ ] Answer open questions above
3. [ ] Approve or request changes
4. [ ] Finalize specifications (move to "Approved" status)
5. [ ] Set up development environment
6. [ ] Create project repository (if separate from main pipeline)

### After Approval
1. Begin Phase 1 of IMPLEMENTATION_ROADMAP.md
2. Update README.md with project status
3. Track progress against roadmap
4. Update documentation as needed during development

---

## Contact & Support

For questions or clarifications about this documentation:
- **Technical Questions**: [Your technical lead]
- **Requirement Questions**: [Your product owner]
- **Design Questions**: [Your UX lead]

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2026-01-18 | Initial comprehensive documentation | AI Assistant |

---

## Appendix: Key Terminology

- **BA**: Balanced Accuracy
- **Champion-Challenger**: Pattern where new models (challengers) compete against current best (champion)
- **Gate**: Evaluable_gate target indicating if a response assessment is valid/evaluable
- **Phase**: Time point relative to CAR-T infusion (day -6, 0, 15, 30)
- **Target**: Outcome variable being predicted
- **Model Family**: Type of model (NN, LR, RF, XGB, CB, ET, LGB, SVM)
- **NN**: Neural Network (MLP)
- **LR**: Logistic Regression
- **RF**: Random Forest
- **XGB**: XGBoost (gradient boosting)
- **CB**: CatBoost (gradient boosting)
- **ET**: Extra Trees (sklearn)
- **LGB**: LightGBM (gradient boosting, optional)
- **SVM**: Support Vector Machine (RBF kernel)
- **ROC**: Receiver Operating Characteristic
- **AUC**: Area Under the Curve
- **CM**: Confusion Matrix

---

**This documentation package is comprehensive and ready for review. Please provide feedback on any sections that need clarification or modification.**
