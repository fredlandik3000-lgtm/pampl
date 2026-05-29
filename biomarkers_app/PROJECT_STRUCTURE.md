# Project Structure
## Biomarkers Pipeline Visualization & Debug Tool

This document shows the complete folder and file structure for the application.

---

## Directory Tree

```
biomarkers_app/
│
├── README.md                           # Project overview and quick start
├── PROJECT_STRUCTURE.md               # This file
├── requirements_app.txt               # Application-specific dependencies
├── .gitignore                         # Git ignore rules
│
├── docs/                              # 📚 DOCUMENTATION (CURRENT)
│   ├── README.md                      # Documentation index and navigation
│   ├── SPECIFICATIONS.md              # Complete functional & technical specs
│   ├── UI_MOCKUPS.md                  # UI wireframes and design
│   ├── DATA_FLOW.md                   # Architecture and data flow diagrams
│   ├── API_SPECIFICATIONS.md          # Wrapper API specifications
│   └── IMPLEMENTATION_ROADMAP.md      # Phased development plan
│
├── main.py                            # 🚀 APPLICATION ENTRY POINT
│
├── app/                               # 🎨 APPLICATION CODE
│   ├── __init__.py
│   │
│   ├── main_window.py                 # Main Qt application window
│   │
│   ├── ui/                            # UI Components (Views)
│   │   ├── __init__.py
│   │   ├── pipeline_view.py           # Pipeline flow visualization
│   │   ├── model_comparison.py        # Model comparison table view
│   │   ├── results_dashboard.py       # Results & metrics dashboard
│   │   ├── parameter_panel.py         # Parameter configuration panel
│   │   ├── feature_analysis.py        # Feature analysis view
│   │   ├── data_inspector.py          # Data preview and inspection
│   │   ├── validation_results.py      # Validation methods results
│   │   ├── registry_viewer.py         # Model registry viewer
│   │   ├── debug_console.py           # Debug console widget
│   │   │
│   │   ├── dialogs/                   # Modal Dialogs
│   │   │   ├── __init__.py
│   │   │   ├── parameter_dialog.py    # Main parameter editor
│   │   │   ├── nn_config_dialog.py    # Neural network configuration
│   │   │   ├── model_config_dialog.py # Generic model configuration
│   │   │   ├── export_dialog.py       # Export/report generation
│   │   │   ├── preset_dialog.py       # Preset management
│   │   │   └── about_dialog.py        # About/help dialog
│   │   │
│   │   └── widgets/                   # Reusable UI Widgets
│   │       ├── __init__.py
│   │       ├── step_node.py           # Pipeline step node widget
│   │       ├── plot_widget.py         # Matplotlib/Plotly embedding
│   │       ├── metric_card.py         # Metric display card
│   │       ├── progress_widget.py     # Enhanced progress bar
│   │       ├── log_viewer.py          # Scrollable log viewer
│   │       └── table_widget.py        # Enhanced table with filters
│   │
│   ├── core/                          # 🧠 APPLICATION LOGIC
│   │   ├── __init__.py
│   │   ├── orchestrator.py            # Pipeline orchestration controller
│   │   ├── step_runner.py             # Individual step execution
│   │   ├── config_manager.py          # Configuration management
│   │   ├── results_cache.py           # Results caching (memory + SQLite)
│   │   ├── model_registry.py          # Model registry manager
│   │   ├── export_manager.py          # Export and report generation
│   │   ├── logger_manager.py          # Logging system
│   │   └── threading_utils.py         # Threading helpers (workers, signals)
│   │
│   ├── pipeline/                      # 🔗 PIPELINE WRAPPERS
│   │   ├── __init__.py
│   │   ├── wrappers/                  # Wrapper classes for existing code
│   │   │   ├── __init__.py
│   │   │   ├── data_loader.py         # Data loading wrapper
│   │   │   ├── target_derivation.py   # Target derivation wrapper
│   │   │   ├── feature_engineering.py # Feature preparation wrapper
│   │   │   ├── model_trainer.py       # Model training wrapper
│   │   │   ├── model_evaluator.py     # Evaluation wrapper
│   │   │   └── validator.py           # Validation methods wrapper
│   │   │
│   │   ├── steps.py                   # Pipeline step definitions
│   │   └── validators.py              # Data and config validators
│   │
│   ├── visualization/                 # 📊 VISUALIZATION ENGINE
│   │   ├── __init__.py
│   │   ├── generator.py               # Main visualization generator
│   │   ├── plots.py                   # ROC, scatter, line plots
│   │   ├── heatmaps.py                # Heatmap generation
│   │   ├── confusion_matrix.py        # Confusion matrix plots
│   │   ├── feature_plots.py           # Feature importance plots
│   │   ├── training_curves.py         # Training history plots
│   │   └── flow_diagram.py            # Pipeline flow diagram
│   │
│   └── utils/                         # 🛠 UTILITIES
│       ├── __init__.py
│       ├── logger.py                  # Logging utilities
│       ├── validators.py              # Input validation helpers
│       ├── themes.py                  # UI themes and styling
│       ├── constants.py               # Application constants
│       └── helpers.py                 # General helper functions
│
├── config/                            # ⚙ CONFIGURATION FILES
│   ├── default_params.json            # Factory default parameters
│   ├── user_params.json               # User-modified parameters (created at runtime)
│   ├── pipeline_definition.json       # Pipeline step definitions
│   ├── ui_layout.json                 # UI layout state (saved/restored)
│   │
│   └── presets/                       # Parameter Presets
│       ├── quick_test.json            # Quick test preset (minimal)
│       ├── full_run.json              # Full run preset (all phases/targets)
│       └── demo_mode.json             # Demo preset (for presentations)
│
├── assets/                            # 🎨 ASSETS (Icons, Images, etc.)
│   ├── icons/
│   │   ├── app_icon.ico               # Application icon
│   │   ├── run.png
│   │   ├── stop.png
│   │   ├── export.png
│   │   └── ...
│   │
│   ├── images/
│   │   └── logo.png                   # Application logo
│   │
│   └── styles/
│       ├── light_theme.qss            # Light theme stylesheet
│       └── dark_theme.qss             # Dark theme stylesheet (optional)
│
├── cache/                             # 💾 RUNTIME CACHE (Created at runtime)
│   ├── .gitignore                     # Ignore cache contents
│   ├── results_cache.db               # SQLite cache database
│   └── plots/                         # Cached plot images
│       └── .gitignore
│
├── exports/                           # 📤 EXPORTED FILES (Created by user)
│   ├── .gitignore                     # Ignore exports
│   └── run_YYYYMMDD_HHMMSS/           # Per-run export directory
│       ├── report.html
│       ├── report.pdf
│       ├── metrics.csv
│       ├── results.json
│       └── figures/
│           ├── roc_*.png
│           ├── confusion_matrix_*.png
│           └── heatmap_*.png
│
├── logs/                              # 📝 APPLICATION LOGS (Created at runtime)
│   ├── .gitignore                     # Ignore logs
│   ├── app_YYYYMMDD.log               # Daily log files
│   └── error.log                      # Error-only log
│
├── tests/                             # 🧪 TESTS
│   ├── __init__.py
│   │
│   ├── unit/                          # Unit tests
│   │   ├── __init__.py
│   │   ├── test_config_manager.py
│   │   ├── test_data_loader.py
│   │   ├── test_wrappers.py
│   │   └── ...
│   │
│   ├── integration/                   # Integration tests
│   │   ├── __init__.py
│   │   ├── test_pipeline_flow.py
│   │   ├── test_orchestrator.py
│   │   └── ...
│   │
│   ├── ui/                            # UI tests
│   │   ├── __init__.py
│   │   ├── test_main_window.py
│   │   ├── test_dialogs.py
│   │   └── ...
│   │
│   └── fixtures/                      # Test fixtures
│       ├── sample_data.csv
│       ├── sample_config.json
│       └── expected_results.json
│
└── build/                             # 📦 BUILD ARTIFACTS (Created during packaging)
    ├── .gitignore                     # Ignore build artifacts
    ├── build_exe.py                   # PyInstaller build script
    ├── BiomarkersPipelineTool.spec    # PyInstaller spec file
    │
    └── dist/                          # Distribution output
        └── BiomarkersPipelineTool.exe # Final executable
```

---

## File Descriptions

### Root Level

- **main.py**: Application entry point. Initializes Qt application and shows main window.
- **requirements_app.txt**: Python dependencies specific to the application (PyQt6, etc.). Separate from existing pipeline requirements.txt.
- **PROJECT_STRUCTURE.md**: This file.

### app/ (Application Code)

#### app/main_window.py
Main Qt window class. Manages:
- Menu bar
- Tab widget
- Status bar
- Overall window layout
- Signal/slot connections

#### app/ui/ (User Interface Components)
Each file contains a QWidget subclass for a specific view:
- **pipeline_view.py**: Visual pipeline flow with step nodes
- **model_comparison.py**: Interactive comparison table
- **results_dashboard.py**: Metrics and visualizations overview
- **parameter_panel.py**: Parameter display and quick edit
- **feature_analysis.py**: Feature importance and correlation
- **data_inspector.py**: Data table and statistics
- **validation_results.py**: Cross-validation results
- **registry_viewer.py**: Model registry and champion tracking
- **debug_console.py**: Real-time log display

#### app/ui/dialogs/ (Modal Dialogs)
- **parameter_dialog.py**: Comprehensive parameter editor (tabbed)
- **nn_config_dialog.py**: Neural network hyperparameter configuration
- **model_config_dialog.py**: Generic model configuration template
- **export_dialog.py**: Export options and report generation
- **preset_dialog.py**: Manage parameter presets
- **about_dialog.py**: Application info and help

#### app/ui/widgets/ (Reusable Widgets)
Small, reusable UI components:
- **step_node.py**: Visual representation of a pipeline step
- **plot_widget.py**: Matplotlib canvas for Qt embedding
- **metric_card.py**: Card-style metric display
- **progress_widget.py**: Enhanced progress bar with labels
- **log_viewer.py**: Scrollable, filterable log viewer
- **table_widget.py**: Enhanced QTableWidget with sorting/filtering

#### app/core/ (Application Logic)
Business logic, no UI code:
- **orchestrator.py**: Coordinates pipeline execution, manages workers
- **step_runner.py**: Executes individual pipeline steps
- **config_manager.py**: Load, save, validate configurations
- **results_cache.py**: Memory and SQLite caching
- **model_registry.py**: Champion-challenger registry management
- **export_manager.py**: Generate exports and reports
- **logger_manager.py**: Centralized logging
- **threading_utils.py**: QThread workers, cancellation tokens

#### app/pipeline/wrappers/ (Pipeline Integration)
Wrapper classes that make existing pipeline code UI-friendly:
- **data_loader.py**: Wraps data loading with progress callbacks
- **target_derivation.py**: Wraps derive_targets() function
- **feature_engineering.py**: Wraps prepare_features()
- **model_trainer.py**: Wraps model training for all families
- **model_evaluator.py**: Wraps evaluation and metrics
- **validator.py**: Wraps validation methods (nested CV, etc.)

#### app/visualization/ (Visualization Engine)
Plot generation (returns matplotlib Figure objects):
- **generator.py**: Main generator class, coordinates plotting
- **plots.py**: ROC curves, scatter plots, line plots
- **heatmaps.py**: Heatmap generation (seaborn-based)
- **confusion_matrix.py**: Confusion matrix heatmaps
- **feature_plots.py**: Feature importance bar charts
- **training_curves.py**: NN training history plots
- **flow_diagram.py**: Pipeline flow diagram generation

#### app/utils/ (Utilities)
Helper functions and constants:
- **logger.py**: Logging setup and formatters
- **validators.py**: Input validation functions
- **themes.py**: Qt stylesheet definitions
- **constants.py**: Application-wide constants (colors, sizes, etc.)
- **helpers.py**: Miscellaneous helper functions

### config/ (Configuration)
JSON files for configuration:
- **default_params.json**: Factory defaults, never modified
- **user_params.json**: User modifications, created at runtime
- **pipeline_definition.json**: Step definitions (order, names, etc.)
- **ui_layout.json**: Saved window state (sizes, positions)
- **presets/**: Named parameter presets

### assets/ (Static Assets)
Icons, images, stylesheets:
- **icons/**: PNG/ICO icons for buttons, tabs, etc.
- **images/**: Logo and branding images
- **styles/**: Qt stylesheet files (.qss)

### cache/ (Runtime Cache)
Created automatically at runtime:
- **results_cache.db**: SQLite database with run results
- **plots/**: Cached plot images for fast re-display

### exports/ (User Exports)
Created when user exports results:
- Timestamped subdirectories per export
- HTML/PDF reports
- CSV/Excel/JSON data files
- PNG/PDF/SVG figure files

### logs/ (Application Logs)
Created automatically:
- Daily log files with all messages
- Separate error log

### tests/ (Test Suite)
- **unit/**: Test individual classes/functions
- **integration/**: Test complete workflows
- **ui/**: Test UI components and interactions
- **fixtures/**: Sample data for tests

### build/ (Packaging)
Created during build process:
- **build_exe.py**: Script to build .exe with PyInstaller
- **BiomarkersPipelineTool.spec**: PyInstaller configuration
- **dist/**: Output directory with final .exe

---

## Key Integration Points

### With Existing Pipeline Code

The application wraps your existing pipeline code (in `c:\Projects\Biomarkers\`):

```
biomarkers_app/app/pipeline/wrappers/
    ↓ wraps ↓
c:\Projects\Biomarkers\current_state\
    - pipeline.py
    - report_phase_minus6_balacc.py
    - nested_cv_phase_minus6_balacc.py
    - holdout_phase_minus6_balacc.py

c:\Projects\Biomarkers\versions\
    - nn_module_enhanced_fixed_v6.py
```

The wrapper classes add:
- Progress callbacks for UI updates
- Cancellation support
- Structured result returns
- Error handling
- Logging

---

## File Count Summary

- **Python files**: ~60
- **JSON config files**: ~7
- **Documentation files**: 6
- **Test files**: ~15
- **Asset files**: ~10
- **Total**: ~100 files

---

## Next Steps

1. Review this structure with your team
2. Confirm any modifications needed
3. Proceed with Phase 1 implementation (Foundation)
4. Create initial folder structure
5. Implement core components

---

**This structure is designed for scalability, maintainability, and clear separation of concerns.**
