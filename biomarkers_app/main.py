"""Main entry point for Biomarkers Pipeline Tool"""

import os
import sys
import datetime
from pathlib import Path

# Avoid joblib/loky calling wmic on Windows (fails on Windows 11 / Store Python)
os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Force threading backend so joblib never uses loky (no wmic CPU count)
from joblib import parallel_backend
parallel_backend("threading", n_jobs=1)

from PyQt6.QtWidgets import QApplication, QDialog, QVBoxLayout, QPushButton, QLabel, QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from app.core.config_manager import ConfigManager
from app.core.logger_manager import LoggerManager
from app.core.repo_paths import repo_root
from app.main_window import MainWindow


def excepthook(exc_type, exc_value, exc_tb):
    """Global exception hook to catch and log all uncaught exceptions"""
    import traceback
    tb_lines = traceback.format_exception(exc_type, exc_value, exc_tb)
    tb_text = ''.join(tb_lines)
    
    # Print to console
    print("=" * 80)
    print("UNCAUGHT EXCEPTION:")
    print("=" * 80)
    print(tb_text)
    print("=" * 80)
    
    # Try to log to file (repository root logs/)
    try:
        log_file = repo_root() / "logs" / "crash.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"Crash at {datetime.datetime.now()}\n")
            f.write(f"{'='*80}\n")
            f.write(tb_text)
            f.write(f"{'='*80}\n\n")
    except:
        pass


class ModeSelectionDialog(QDialog):
    """Dialog for selecting application mode on startup."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_mode = None
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI."""
        self.setWindowTitle("Biomarkers CAR-T Prediction Tool")
        self.setFixedSize(700, 500)
        self.setModal(True)
        
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title = QLabel("🧬 Biomarkers CAR-T Prediction Tool")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Select Mode:")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_font = QFont()
        subtitle_font.setPointSize(12)
        subtitle.setFont(subtitle_font)
        layout.addWidget(subtitle)
        
        layout.addSpacing(10)
        
        # Clinical Mode Button
        clinical_btn = self._create_mode_button(
            "🏥 CLINICAL PREDICTION MODE",
            "Enter patient data and receive outcome predictions\n→ For clinicians making treatment decisions",
            "#E8F5E9",
            "#4CAF50",
            lambda: self._select_mode("clinical")
        )
        layout.addWidget(clinical_btn)
        
        # Research Mode Button
        research_btn = self._create_mode_button(
            "🔬 RESEARCH & DEVELOPMENT MODE",
            "Full pipeline access for model training & analysis\n→ For researchers and data scientists",
            "#E3F2FD",
            "#2196F3",
            lambda: self._select_mode("research")
        )
        layout.addWidget(research_btn)
        
        # Demo Mode Button
        demo_btn = self._create_mode_button(
            "📊 DEMO MODE",
            "View pre-computed results and visualizations\n→ For presentations and demonstrations",
            "#FFF3E0",
            "#FF9800",
            lambda: self._select_mode("demo")
        )
        layout.addWidget(demo_btn)
        
        layout.addSpacing(10)
        
        # Warning disclaimer
        warning = QLabel(
            "⚠ RESEARCH USE ONLY - NOT FOR CLINICAL DIAGNOSIS ⚠\n"
            "Predictions are for research purposes. Always consult complete clinical information."
        )
        warning.setAlignment(Qt.AlignmentFlag.AlignCenter)
        warning.setStyleSheet("""
            QLabel {
                background-color: #FFF9E6;
                border: 1px solid #FFC107;
                padding: 10px;
                border-radius: 5px;
                color: #F57C00;
                font-weight: bold;
            }
        """)
        warning_font = QFont()
        warning_font.setPointSize(9)
        warning.setFont(warning_font)
        layout.addWidget(warning)
        
        self.setLayout(layout)
    
    def _create_mode_button(self, title: str, description: str, 
                           bg_color: str, border_color: str, callback) -> QPushButton:
        """Create a mode selection button."""
        btn = QPushButton()
        btn.setMinimumHeight(100)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color};
                border: 3px solid {border_color};
                border-radius: 10px;
                padding: 15px;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: {border_color};
                border: 3px solid {border_color};
            }}
        """)
        
        # Create layout for button content
        button_layout = QVBoxLayout()
        button_layout.setSpacing(5)
        
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        button_layout.addWidget(title_label)
        
        desc_label = QLabel(description)
        desc_font = QFont()
        desc_font.setPointSize(9)
        desc_label.setFont(desc_font)
        button_layout.addWidget(desc_label)
        
        btn.setLayout(button_layout)
        btn.clicked.connect(callback)
        
        return btn
    
    def _select_mode(self, mode: str):
        """Handle mode selection."""
        self.selected_mode = mode
        self.accept()
    
    def get_selected_mode(self) -> str:
        """Get selected mode."""
        return self.selected_mode


def main():
    """Main application entry point."""
    sys.excepthook = excepthook
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Biomarkers Pipeline Tool")
    app.setOrganizationName("Biomarkers Research")
    
    try:
        # Initialize configuration
        config = ConfigManager()
        
        # Initialize logger
        log_rel = config.get("logging.log_dir", "logs")
        log_dir = str(repo_root() / log_rel)
        log_level = config.get("logging.level", "INFO")
        save_to_file = config.get("logging.save_to_file", True)
        
        logger = LoggerManager(
            log_dir=log_dir,
            level=log_level,
            save_to_file=save_to_file
        )
        
        logger.info("Application starting", "Main")
        
        # Start directly in academic_review mode
        mode = "academic_review"
        logger.info(f"Starting in {mode} mode", "Main")
        
        # Create and show main window
        window = MainWindow(config, logger, mode)
        window.show()
        window.showFullScreen()
        
        # Start event loop
        return app.exec()
        
    except Exception as e:
        error_msg = f"Fatal error during startup: {str(e)}"
        print(error_msg)
        if logger:
            logger.critical(error_msg, "Main")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
