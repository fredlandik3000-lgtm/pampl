# Implementation Roadmap
## Biomarkers Pipeline Tool v1.0

This document provides a phased approach to implementing the application.

---

## Overview

**Total Estimated Development Time**: 6-8 weeks (full-time)
**Phases**: 6 major phases
**Approach**: Incremental, with working prototype at end of each phase

---

## Current State (as of last update)

- **Pipeline–CLI alignment**: App feature set matches command-line NN trainer (NN_FEATURE_GROUPS); all trainable targets (no 20-target cap); NN binary loss uses float targets (BCEWithLogitsLoss).
- **Feature Analysis**: Correlations tab shows top pairwise correlations (numeric features) after feature engineering; Feature Importance tab shows variability (std/variance) table. Both refresh when engineered features are loaded. **Optional feature selection** in Settings (Pipeline Flow): enable/disable, method (mutual_info | variance), Top K; applied during feature engineering before training.
- **Model Comparison**: "Best only (champion per cell)" display option — compact table (rows=phases, columns=targets) with best metric + model name per cell. **Eight model families** trained and compared: NN, LR, RF, XGB, CB, Extra Trees (ET), LightGBM (LGB), SVM (RBF).
- **Evaluation modes (Settings)**: **Single split** (bootstrap 95% CI), **5-fold CV** (default, mean ± std and 95% CI), **3× repeated holdout** (configurable repeats, multiple 70/30 splits for stability), **Nested CV** (5-fold outer, 3-fold inner hyperparameter tuning for LR/RF/XGB). Same ModelResult/Validation Results format for all modes.
- **Specifications**: SPECIFICATIONS.md updated with FR-050/FR-051/FR-029b, evaluation modes, feature selection, and implementation notes.

---

## Phase 1: Foundation & Basic UI (Week 1)

### Goals
- Set up project structure
- Create basic Qt application shell
- Implement configuration management
- Create main window with placeholder tabs

### Tasks

#### 1.1 Project Setup
- [ ] Create folder structure as per specifications
- [ ] Set up virtual environment
- [ ] Install dependencies (PyQt6, existing pipeline deps)
- [ ] Create `requirements_app.txt`
- [ ] Initialize git (if not already in same repo)

#### 1.2 Configuration System
- [ ] Implement `ConfigManager` class
- [ ] Create `default_params.json` template
- [ ] Add config validation logic
- [ ] Add config save/load methods
- [ ] Write unit tests for ConfigManager

#### 1.3 Basic Main Window
- [ ] Create `MainWindow` class (PyQt6)
- [ ] Add menu bar (File, Edit, View, Run, Tools, Help)
- [ ] Create status bar with placeholders
- [ ] Add tab widget for main content area
- [ ] Create 7 placeholder tabs
- [ ] Add basic window styling

#### 1.4 Logger System
- [ ] Implement `LoggerManager` class
- [ ] Create log formatting utilities
- [ ] Add file logging support
- [ ] Create in-memory log buffer
- [ ] Write tests for logger

### Deliverables
- Runnable application that opens main window
- Configuration can be loaded/saved
- Tabs are visible (empty)
- Basic logging works

### Acceptance Criteria
- Application launches without errors
- Main window displays correctly
- Configuration saves and loads
- Logger writes to file and buffer

---

## Phase 2: Pipeline Integration & Orchestration (Week 2)

### Goals
- Wrap existing pipeline code
- Implement step-by-step execution
- Add progress tracking
- Create results cache

### Tasks

#### 2.1 Wrapper Classes
- [ ] Implement `DataLoaderWrapper`
- [ ] Implement `TargetDerivationWrapper`
- [ ] Implement `FeatureEngineeringWrapper`
- [ ] Implement `ModelTrainerWrapper`
- [ ] Implement `ModelEvaluatorWrapper`
- [ ] Write unit tests for each wrapper

#### 2.2 Pipeline Orchestrator
- [ ] Implement `PipelineOrchestrator` class
- [ ] Add step registration system
- [ ] Implement progress calculation
- [ ] Add cancellation support
- [ ] Implement error handling and recovery
- [ ] Write integration tests

#### 2.3 Threading Support
- [ ] Create `PipelineWorker` (QThread subclass)
- [ ] Implement signal/slot communication
- [ ] Add thread-safe result passing
- [ ] Test concurrent execution

#### 2.4 Results Cache
- [ ] Implement in-memory cache (dict-based)
- [ ] Create SQLite schema
- [ ] Implement `ResultsCacheManager`
- [ ] Add cache invalidation logic
- [ ] Write tests for cache operations

### Deliverables
- Pipeline can execute end-to-end (headless)
- Progress updates emit correctly
- Results cached properly
- Cancellation works

### Acceptance Criteria
- Full pipeline runs without UI
- Progress callbacks fire
- Results stored in cache
- Can cancel mid-execution
- Cache persists across runs

---

## Phase 3: Pipeline Flow View & Execution Control (Week 3)

### Goals
- Implement visual pipeline flow diagram
- Add step-by-step execution controls
- Show real-time progress
- Display debug console

### Tasks

#### 3.1 Pipeline Flow Widget
- [ ] Design step node widget (`StepNodeWidget`)
- [ ] Implement flow layout algorithm
- [ ] Add status indicators (pending, running, complete, error)
- [ ] Add click handlers for step details
- [ ] Implement animated transitions

#### 3.2 Execution Controls
- [ ] Add "Run All" button functionality
- [ ] Add "Run Step" button functionality
- [ ] Add "Pause" functionality (if feasible)
- [ ] Add "Stop" functionality
- [ ] Add step navigation (previous/next)

#### 3.3 Progress Display
- [ ] Implement overall progress bar
- [ ] Implement per-step progress bar
- [ ] Add elapsed time counter
- [ ] Add ETA estimation (if possible)
- [ ] Create animated spinner for running state

#### 3.4 Debug Console
- [ ] Implement `DebugConsoleWidget`
- [ ] Add log level filtering
- [ ] Add search functionality
- [ ] Add color coding for log levels
- [ ] Add auto-scroll toggle
- [ ] Add export logs button

#### 3.5 Integration
- [ ] Connect orchestrator signals to UI
- [ ] Wire up all buttons
- [ ] Test full execution flow with UI feedback
- [ ] Polish animations and transitions

### Deliverables
- Pipeline tab shows visual flow
- Can run pipeline from UI
- Real-time progress updates
- Debug console shows logs

### Acceptance Criteria
- Pipeline flow diagram renders correctly
- Status updates in real-time
- Console shows all log messages
- Can stop pipeline at any time
- UI remains responsive during execution

---

## Phase 4: Visualizations & Data Display (Week 4-5)

### Goals
- Implement all visualization types
- Create data inspector
- Add model comparison view
- Generate plots dynamically

### Tasks

#### 4.1 Visualization Engine
- [ ] Implement `VisualizationGenerator` class
- [ ] Create matplotlib embedding helper
- [ ] Implement plot caching
- [ ] Add export plot functionality
- [ ] Write tests for visualization generation

#### 4.2 ROC Curve Tab
- [ ] Create ROC curve widget
- [ ] Add parameter selection controls
- [ ] Implement multi-model overlay
- [ ] Add legend and AUC display
- [ ] Add export button

#### 4.3 Confusion Matrix Tab
- [ ] Create confusion matrix widget
- [ ] Add heatmap rendering
- [ ] Add class label annotations
- [ ] Add threshold slider (for binary)
- [ ] Add export button

#### 4.4 Heatmap Tab
- [ ] Create heatmap widget (phase × target)
- [ ] Add model selection dropdown
- [ ] Add metric selection dropdown
- [ ] Implement color scale customization
- [ ] Add insights panel (best/worst cells)
- [ ] Add export button

#### 4.5 Feature Importance Tab
- [x] Feature Analysis: variability (std/variance) table after feature engineering
- [x] Feature Analysis: correlations table (top pairwise correlations)
- [ ] Add bar chart rendering (optional)
- [ ] Add model comparison mode (model-based importance from training)
- [ ] Add top-N filter
- [ ] Add export button

#### 4.6 Training Curves Tab (NN only)
- [ ] Create training curves widget
- [ ] Plot loss and accuracy over epochs
- [ ] Add train/val curves
- [ ] Highlight early stopping point
- [ ] Add export button

#### 4.7 Data Inspector Tab
- [ ] Create data preview table widget
- [ ] Implement pagination
- [ ] Add column statistics panel
- [ ] Add missing value visualization
- [ ] Add distribution histograms
- [ ] Add data validation report button

#### 4.8 Model Comparison Tab
- [x] Create comparison table widget
- [x] Filtering controls (phase, target, model, metric)
- [x] Color coding (best/worst)
- [x] Highlight champion models (asterisk)
- [x] "Best only (champion per cell)" display mode — compact view
- [x] Add detail panel for selected cell
- [x] Add export button (CSV)
- [ ] Sortable columns (optional)

### Deliverables
- All visualization tabs functional
- Plots render correctly
- Data inspector shows data
- Model comparison table works

### Acceptance Criteria
- All plot types generate correctly
- Plots can be exported (PNG, PDF, SVG)
- Data table displays and paginates
- Model comparison table is interactive
- All visualizations update when new results available

---

## Phase 5: Parameter Tuning & Advanced Features (Week 6)

### Goals
- Implement parameter editor dialogs
- Add preset management
- Add validation methods
- Implement registry viewer

### Tasks

#### 5.1 Parameter Editor Dialog
- [ ] Create main parameter dialog
- [ ] Implement tabbed interface
- [ ] Add General tab (data path, phases, etc.)
- [ ] Add Models tab (enable/disable, configure)
- [ ] Add Data Splitting tab
- [ ] Add Targets tab (selection)
- [ ] Add Evaluation tab (metrics)
- [ ] Add validation for all inputs
- [ ] Wire up Save/Cancel buttons

#### 5.2 Model-Specific Configuration Dialogs
- [ ] Create NN configuration dialog
- [ ] Create XGBoost configuration dialog
- [ ] Create RF configuration dialog
- [ ] Create LR configuration dialog
- [ ] Create CatBoost configuration dialog
- [ ] Create Extra Trees configuration dialog
- [ ] Create LightGBM configuration dialog
- [ ] Create SVM configuration dialog
- [ ] Add "Test Configuration" button

#### 5.3 Preset Management
- [ ] Implement preset save dialog
- [ ] Implement preset load dropdown
- [ ] Create default presets (Quick, Full, Demo)
- [ ] Add preset delete functionality
- [ ] Add preset export/import

#### 5.4 Validation Methods
- [ ] Implement nested CV wrapper
- [ ] Implement holdout validation wrapper
- [ ] Implement K-fold CV wrapper
- [ ] Create validation results tab
- [ ] Add comparison of validation methods

#### 5.5 Registry Viewer Tab
- [ ] Create registry table widget
- [ ] Show current champions
- [ ] Add champion vs challenger comparison
- [ ] Add historical trend chart
- [ ] Add registry export button
- [ ] Add manual registry edit (optional)

### Deliverables
- Parameter editor fully functional
- All model configs customizable
- Presets work
- Validation methods implemented
- Registry viewer operational

### Acceptance Criteria
- Parameters can be modified and saved
- Invalid parameters are rejected
- Presets save and load correctly
- Validation methods produce results
- Registry displays correct champion models

---

## Phase 6: Export, Reporting & Polish (Week 7)

### Goals
- Implement comprehensive reporting
- Add export functionality
- Polish UI/UX
- Prepare for distribution

### Tasks

#### 6.1 Export Manager
- [ ] Implement `ExportManager` class
- [ ] Add CSV export for tables
- [ ] Add Excel export with formatting
- [ ] Add JSON export for structured data
- [ ] Add PNG/PDF/SVG export for plots
- [ ] Test all export formats

#### 6.2 Report Generator
- [ ] Create Jinja2 HTML templates
- [ ] Implement comprehensive report generation
- [ ] Add executive summary section
- [ ] Add all visualizations
- [ ] Add detailed tables
- [ ] Add configuration appendix
- [ ] Implement PDF conversion (if feasible)
- [ ] Add Markdown export option

#### 6.3 Export Dialog
- [ ] Create export/report dialog UI
- [ ] Add component selection
- [ ] Add format selection
- [ ] Add report metadata fields
- [ ] Wire up generation logic
- [ ] Add progress bar for long exports

#### 6.4 UI/UX Polish
- [ ] Review all layouts for consistency
- [ ] Add tooltips to all buttons
- [ ] Add keyboard shortcuts
- [ ] Implement dark/light theme toggle (optional)
- [ ] Add icons to buttons and tabs
- [ ] Smooth all animations
- [ ] Test on different screen resolutions
- [ ] Improve error messages

#### 6.5 Help & Documentation
- [ ] Add Help menu items
- [ ] Create user guide (PDF)
- [ ] Add tooltips with explanations
- [ ] Add "About" dialog
- [ ] Add "What's New" for version
- [ ] Include sample data (if permissible)

#### 6.6 Testing & Bug Fixes
- [ ] Run full integration tests
- [ ] Test all user workflows
- [ ] Fix any discovered bugs
- [ ] Test on clean Windows machine
- [ ] Verify resource usage
- [ ] Stress test with large datasets

### Deliverables
- Export functionality complete
- Report generation works
- UI polished and consistent
- User guide available

### Acceptance Criteria
- All export formats work correctly
- Comprehensive reports generated
- UI is intuitive and responsive
- No critical bugs
- Application feels professional

---

## Phase 7: Packaging & Distribution (Week 8)

### Goals
- Package as standalone .exe
- Test distribution
- Create installation instructions
- Prepare for colleague distribution

### Tasks

#### 7.1 PyInstaller Configuration
- [ ] Create `build_exe.py` script
- [ ] Configure PyInstaller spec file
- [ ] Include all dependencies
- [ ] Include data files (config, assets)
- [ ] Test build process
- [ ] Optimize executable size

#### 7.2 Installer Creation (Optional)
- [ ] Create installer using NSIS or Inno Setup
- [ ] Add start menu shortcuts
- [ ] Add desktop shortcut option
- [ ] Add uninstaller
- [ ] Test installer on clean machine

#### 7.3 Distribution Testing
- [ ] Test on Windows 10
- [ ] Test on Windows 11
- [ ] Test on machine without Python
- [ ] Verify all dependencies bundled
- [ ] Test file permissions
- [ ] Test with real data

#### 7.4 Documentation
- [ ] Write installation guide
- [ ] Write quick start guide
- [ ] Document known issues
- [ ] Create troubleshooting guide
- [ ] Add FAQ

#### 7.5 Versioning & Release
- [ ] Set version number (1.0.0)
- [ ] Create CHANGELOG
- [ ] Tag release in git
- [ ] Create release notes
- [ ] Package all deliverables

### Deliverables
- Standalone .exe (or installer)
- Installation instructions
- User documentation
- Release package

### Acceptance Criteria
- Executable runs on clean Windows machines
- No missing dependencies
- Installer works correctly
- Documentation is clear
- Ready for distribution to colleagues

---

## Development Guidelines

### Code Quality
- Use type hints for all functions
- Write docstrings for all public methods
- Follow PEP 8 style guide
- Use meaningful variable names
- Keep functions small and focused

### Testing Strategy
- Write unit tests for all wrappers
- Integration tests for pipeline flow
- UI tests for critical workflows
- Manual testing on each phase completion

### Version Control
- Commit frequently with clear messages
- Use feature branches for major work
- Tag each phase completion
- Keep main branch stable

### Documentation
- Update docs as features are implemented
- Document any deviations from specs
- Keep README up to date
- Document known issues

---

## Risk Management

### Identified Risks

#### Risk 1: Qt Performance with Large Datasets
**Mitigation**: Use pagination, lazy loading, and caching

#### Risk 2: Threading Complexity
**Mitigation**: Use Qt's signals/slots, test thoroughly

#### Risk 3: Memory Usage
**Mitigation**: Profile regularly, clear cache when needed

#### Risk 4: Matplotlib Embedding Issues
**Mitigation**: Use FigureCanvasQTAgg, test on different Qt versions

#### Risk 5: PyInstaller Packaging Problems
**Mitigation**: Test packaging early and often

#### Risk 6: Cross-Machine Compatibility
**Mitigation**: Test on multiple Windows machines

---

## Success Metrics

### Phase Completion Criteria
Each phase is considered complete when:
1. All tasks are checked off
2. Deliverables are verified
3. Acceptance criteria are met
4. No critical bugs remain
5. Code is reviewed and documented

### Overall Success Criteria
The project is successful when:
1. Application runs on clean Windows machines
2. Full pipeline can be executed
3. All visualizations render correctly
4. Parameters can be modified and saved
5. Results can be exported in multiple formats
6. Application is stable and responsive
7. Documentation is complete
8. Colleagues can use it independently

---

## Post-Launch (Future Enhancements)

### Version 1.1
- SHAP value integration
- Automated hyperparameter tuning
- Model persistence and deployment
- Custom dashboard builder

### Version 1.2
- Web-based version (Flask/Django)
- Multi-user support
- Cloud storage integration
- Real-time collaboration

### Version 2.0
- Support for additional data sources
- Integration with R scripts
- Survival analysis visualizations
- Automated report scheduling

---

## Notes & Decisions Log

### Decision 1: PyQt6 vs PySide6
**Decision**: Use PyQt6
**Rationale**: Better documentation, wider community support, easier packaging

### Decision 2: SQLite vs File-based Cache
**Decision**: Use SQLite for persistent cache
**Rationale**: Better query performance, easier to maintain

### Decision 3: Matplotlib vs Plotly for Plots
**Decision**: Use Matplotlib (with optional Plotly for interactive plots)
**Rationale**: Better Qt embedding support, lighter weight

### Decision 4: Threading Model
**Decision**: One worker thread per pipeline run, with sub-tasks serialized
**Rationale**: Simpler to manage, avoids race conditions

### Decision 5: Configuration Format
**Decision**: JSON for configuration files
**Rationale**: Human-readable, easy to edit, standard library support

---

## Appendix: Development Tools

### Recommended IDE
- PyCharm Professional (or VS Code with Python extensions)
- Qt Designer for UI prototyping (optional)

### Recommended Tools
- Git for version control
- pytest for unit testing
- black for code formatting
- pylint for linting
- Sphinx for documentation (optional)

### Recommended Workflow
1. Create feature branch
2. Implement feature with tests
3. Run tests locally
4. Update documentation
5. Commit and push
6. Merge to main after review

---

**Document Version**: 1.0  
**Last Updated**: 2026-01-18  
**Status**: Draft for Review
