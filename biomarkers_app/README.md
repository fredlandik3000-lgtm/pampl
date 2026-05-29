# Biomarkers Pipeline Visualization & Debug Tool

A comprehensive Windows desktop application for CAR-T therapy outcome prediction with full pipeline visualization and debugging capabilities.

## Features

- **Academic Review Mode**: Default mode for reviewing results and visualizations
- **Research Mode**: Full pipeline access for model training and analysis
- **Clinical Prediction Mode**: Enter patient data and receive outcome predictions
- **5 Model Families**: Neural Network, Logistic Regression, XGBoost, Random Forest, CatBoost
- **Comprehensive Visualizations**: ROC curves, heatmaps, confusion matrices, feature importance
- **Real-time Debug Console**: Monitor all pipeline operations
- **Export & Reporting**: Generate professional PDF reports

## Installation

### Prerequisites

- Python 3.11 or higher
- Windows 10/11 (64-bit)

### Install Dependencies

```bash
# Navigate to project directory
cd biomarkers_app

# Install application dependencies
pip install -r requirements_app.txt

# Existing pipeline dependencies should already be installed
```

## Documentation

- **`../AGENTS.md`** (repository root) — orientation for humans and AI agents: paths, `repo_paths`, results/logs layout, batch CLI.
- **`docs/DOCUMENTATION.md`** — map of specs, roadmaps, and links (`../results/README.md` for run artifacts).

## Quick Start

### Run the Application

```bash
python main.py
```

### Application Modes

The application starts in **Academic Review Mode** by default. Switch modes via the **Mode** menu:
- **Academic Review Mode**: Default mode for reviewing results and presentations
- **Research Mode**: For pipeline development and training
- **Clinical Mode**: For patient predictions

## Development

### Project Structure

```
biomarkers_app/
├── main.py                  # Application entry point
├── app/                     # Application code
│   ├── main_window.py      # Main Qt window
│   ├── core/               # Core logic (config, logger, orchestrator)
│   ├── ui/                 # UI components
│   ├── pipeline/           # Pipeline wrappers
│   ├── visualization/      # Plot generation
│   └── utils/              # Utilities
├── config/                 # Configuration files
├── tests/                  # Test suite
└── docs/                   # Documentation
```

### Run Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/unit/test_config_manager.py
```

### Configuration

Default configuration is in `config/default_params.json`. User modifications are saved to `config/user_params.json`.

To reset configuration:
```python
from app.core.config_manager import ConfigManager
config = ConfigManager()
config.reset_to_defaults()
```

## Phase 1 Complete ✓

**Completed Components:**
- [x] Project structure and all directories
- [x] ConfigManager with validation and presets
- [x] LoggerManager with file and console output
- [x] Main Window with Qt (tabs, menu, status bar)
- [x] Mode selection dialog
- [x] Unit tests (27 tests, all passing)
- [x] Requirements file with all dependencies
- [x] Application runs successfully with GUI

**Phase 1 Deliverables:**
- Runnable application with mode selection
- Configuration management system
- Logging system
- Basic UI framework (3 modes)
- Comprehensive test suite

**Test Results:** ✅ 27 passed (ConfigManager: 14 tests, Logger: 13 tests)

## 🎯 NEXT STEPS: Phase 2 - Pipeline Integration

**GOAL:** Connect the existing biomarkers pipeline to the GUI application.

### Phase 2.1: Pipeline Orchestrator (Week 2)

**Priority 1: Create Core Orchestrator**

File to create: `app/core/pipeline_orchestrator.py`

This orchestrator will:
- Manage pipeline step execution (sequential/parallel)
- Track progress and emit callbacks for UI updates
- Handle cancellation tokens
- Cache results in SQLite database
- Provide structured error handling

Reference: `docs/API_SPECIFICATIONS.md` (PipelineOrchestrator section)

**Priority 2: Data Loader Wrapper**

File to create: `app/pipeline/wrappers/data_loader_wrapper.py`

This wrapper will:
- Load data from CSV using existing pipeline code
- Add progress callbacks (0-100%)
- Add cancellation support
- Return structured `StepResult` with metadata
- Handle errors gracefully

Wraps: `current_state/pipeline.py` data loading logic

**Priority 3: Basic Integration Test**

Create: `tests/integration/test_pipeline_basic.py`

Test that:
- Orchestrator can load data
- Progress callbacks work
- Results are cached
- UI receives updates

### Phase 2.2: Model Training Wrappers (Week 3)

Create wrappers for each model family:
- `app/pipeline/wrappers/nn_trainer_wrapper.py`
- `app/pipeline/wrappers/lr_trainer_wrapper.py`
- `app/pipeline/wrappers/xgb_trainer_wrapper.py`
- `app/pipeline/wrappers/rf_trainer_wrapper.py`
- `app/pipeline/wrappers/catboost_trainer_wrapper.py`

Each wraps existing model training from `current_state/pipeline.py`

### Quick Start for Phase 2

1. Read `docs/API_SPECIFICATIONS.md` - contains detailed wrapper specifications
2. Read `docs/DATA_FLOW.md` - understand the data flow architecture
3. Start with `PipelineOrchestrator` in `app/core/pipeline_orchestrator.py`
4. Use existing pipeline code from `current_state/pipeline.py` as reference

### Success Criteria for Phase 2

- [ ] Can load data through GUI and see progress bar
- [ ] Can train one model (NN) through GUI
- [ ] Results are cached in SQLite
- [ ] Debug console shows all pipeline steps
- [ ] At least 10 integration tests passing

## Documentation

See `docs/` folder for:
- SPECIFICATIONS.md - Complete functional requirements
- IMPLEMENTATION_ROADMAP.md - Development plan
- UI_MOCKUPS.md - UI designs
- API_SPECIFICATIONS.md - Technical API details

## Important Notice

**⚠ RESEARCH USE ONLY - NOT FOR CLINICAL DIAGNOSIS ⚠**

This software provides probabilistic predictions for research purposes. It is NOT an FDA-approved medical device and should NOT be used as the sole basis for clinical decisions.

## License

Copyright © 2026 - Research Use Only

## Contact

For questions or issues, contact the development team.
