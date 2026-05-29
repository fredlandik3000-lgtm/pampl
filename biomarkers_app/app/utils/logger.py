"""Logging utilities for Biomarkers Pipeline Tool"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable
from enum import Enum


class LogLevel(Enum):
    """Log level enum."""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class LoggerManager:
    """Centralized logging manager for the application."""
    
    def __init__(
        self, 
        log_dir: Optional[str] = None,
        level: str = "INFO",
        save_to_file: bool = True,
        callback: Optional[Callable[[str, str, str], None]] = None
    ):
        """
        Initialize logger manager.
        
        Args:
            log_dir: Directory for log files
            level: Logging level (DEBUG, INFO, WARNING, ERROR)
            save_to_file: Whether to save logs to file
            callback: Optional callback function(level, source, message) for UI updates
        """
        self.log_dir = Path(log_dir) if log_dir else Path("logs")
        self.level = getattr(logging, level.upper())
        self.save_to_file = save_to_file
        self.callback = callback
        
        # Create logs directory if it doesn't exist
        if self.save_to_file:
            self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up logger
        self.logger = logging.getLogger("BiomarkersPipeline")
        self.logger.setLevel(self.level)
        self.logger.handlers = []  # Clear any existing handlers
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.level)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler
        if self.save_to_file:
            today = datetime.now().strftime('%Y%m%d')
            log_file = self.log_dir / f"app_{today}.log"
            
            file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
            file_handler.setLevel(self.level)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
            
            # Also create error-only log
            error_file = self.log_dir / "error.log"
            error_handler = logging.FileHandler(error_file, mode='a', encoding='utf-8')
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(file_formatter)
            self.logger.addHandler(error_handler)
    
    def debug(self, message: str, source: str = "System") -> None:
        """Log debug message."""
        self.logger.debug(f"[{source}] {message}")
        if self.callback and self.logger.isEnabledFor(logging.DEBUG):
            self.callback("DEBUG", source, message)
    
    def info(self, message: str, source: str = "System") -> None:
        """Log info message."""
        self.logger.info(f"[{source}] {message}")
        if self.callback and self.logger.isEnabledFor(logging.INFO):
            self.callback("INFO", source, message)
    
    def warning(self, message: str, source: str = "System") -> None:
        """Log warning message."""
        self.logger.warning(f"[{source}] {message}")
        if self.callback and self.logger.isEnabledFor(logging.WARNING):
            self.callback("WARNING", source, message)
    
    def error(self, message: str, source: str = "System", exc_info: bool = False) -> None:
        """Log error message."""
        self.logger.error(f"[{source}] {message}", exc_info=exc_info)
        if self.callback and self.logger.isEnabledFor(logging.ERROR):
            self.callback("ERROR", source, message)
    
    def critical(self, message: str, source: str = "System", exc_info: bool = True) -> None:
        """Log critical message."""
        self.logger.critical(f"[{source}] {message}", exc_info=exc_info)
        if self.callback and self.logger.isEnabledFor(logging.CRITICAL):
            self.callback("CRITICAL", source, message)
    
    def set_level(self, level: str) -> None:
        """Change logging level at runtime."""
        new_level = getattr(logging, level.upper())
        self.logger.setLevel(new_level)
        for handler in self.logger.handlers:
            handler.setLevel(new_level)
    
    def set_callback(self, callback: Callable[[str, str, str], None]) -> None:
        """Set callback for UI updates."""
        self.callback = callback
    
    def close(self) -> None:
        """Close all handlers and release file handles."""
        handlers = self.logger.handlers[:]
        for handler in handlers:
            handler.close()
            self.logger.removeHandler(handler)
