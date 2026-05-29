"""Unit tests for LoggerManager"""

import pytest
import tempfile
import logging
from pathlib import Path
from datetime import datetime

from app.utils.logger import LoggerManager, LogLevel


@pytest.fixture
def temp_log_dir():
    """Create temporary log directory. Closes logger file handles before cleanup so Windows can delete the dir."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir
        # Close file handlers before TemporaryDirectory.__exit__ runs (avoids WinError 32 on Windows)
        log = logging.getLogger("BiomarkersPipeline")
        for h in log.handlers[:]:
            h.close()
            log.removeHandler(h)


def test_logger_init(temp_log_dir):
    """Test LoggerManager initialization."""
    logger = LoggerManager(log_dir=temp_log_dir, level="INFO", save_to_file=True)
    
    assert logger.log_dir == Path(temp_log_dir)
    assert logger.save_to_file is True
    assert logger.logger is not None


def test_logger_create_log_files(temp_log_dir):
    """Test that log files are created."""
    logger = LoggerManager(log_dir=temp_log_dir, level="INFO", save_to_file=True)
    
    logger.info("Test message", "Test")
    
    # Check that log directory exists
    log_path = Path(temp_log_dir)
    assert log_path.exists()
    
    # Check that daily log file is created
    today = datetime.now().strftime('%Y%m%d')
    daily_log = log_path / f"app_{today}.log"
    assert daily_log.exists()
    
    # Check that error log file is created
    error_log = log_path / "error.log"
    assert error_log.exists()


def test_logger_info_message(temp_log_dir):
    """Test logging INFO message."""
    messages = []
    
    def callback(level, source, message):
        messages.append((level, source, message))
    
    logger = LoggerManager(log_dir=temp_log_dir, level="INFO", save_to_file=True, callback=callback)
    
    logger.info("Test info message", "TestSource")
    
    assert len(messages) == 1
    assert messages[0][0] == "INFO"
    assert messages[0][1] == "TestSource"
    assert messages[0][2] == "Test info message"


def test_logger_debug_message(temp_log_dir):
    """Test logging DEBUG message."""
    messages = []
    
    def callback(level, source, message):
        messages.append((level, source, message))
    
    logger = LoggerManager(log_dir=temp_log_dir, level="DEBUG", save_to_file=True, callback=callback)
    
    logger.debug("Test debug message", "TestSource")
    
    assert len(messages) == 1
    assert messages[0][0] == "DEBUG"


def test_logger_warning_message(temp_log_dir):
    """Test logging WARNING message."""
    messages = []
    
    def callback(level, source, message):
        messages.append((level, source, message))
    
    logger = LoggerManager(log_dir=temp_log_dir, level="WARNING", save_to_file=True, callback=callback)
    
    logger.warning("Test warning", "TestSource")
    
    assert len(messages) == 1
    assert messages[0][0] == "WARNING"


def test_logger_error_message(temp_log_dir):
    """Test logging ERROR message."""
    messages = []
    
    def callback(level, source, message):
        messages.append((level, source, message))
    
    logger = LoggerManager(log_dir=temp_log_dir, level="ERROR", save_to_file=True, callback=callback)
    
    logger.error("Test error", "TestSource")
    
    assert len(messages) == 1
    assert messages[0][0] == "ERROR"


def test_logger_error_in_error_log(temp_log_dir):
    """Test that errors are written to error.log."""
    logger = LoggerManager(log_dir=temp_log_dir, level="INFO", save_to_file=True)
    
    logger.error("Test error message", "TestSource")
    
    error_log = Path(temp_log_dir) / "error.log"
    assert error_log.exists()
    
    content = error_log.read_text()
    assert "Test error message" in content
    assert "ERROR" in content


def test_logger_set_level(temp_log_dir):
    """Test changing log level at runtime."""
    messages = []
    
    def callback(level, source, message):
        messages.append((level, source, message))
    
    logger = LoggerManager(log_dir=temp_log_dir, level="WARNING", save_to_file=False, callback=callback)
    
    # INFO should not be logged at WARNING level
    logger.info("This should not appear", "Test")
    assert len(messages) == 0
    
    # Change to INFO level
    logger.set_level("INFO")
    
    # Now INFO should be logged
    logger.info("This should appear", "Test")
    assert len(messages) == 1


def test_logger_callback(temp_log_dir):
    """Test callback functionality."""
    call_count = [0]
    
    def callback(level, source, message):
        call_count[0] += 1
    
    logger = LoggerManager(log_dir=temp_log_dir, level="INFO", save_to_file=False, callback=callback)
    
    logger.info("Message 1", "Test")
    logger.info("Message 2", "Test")
    logger.warning("Message 3", "Test")
    
    assert call_count[0] == 3


def test_logger_set_callback(temp_log_dir):
    """Test setting callback after initialization."""
    messages = []
    
    logger = LoggerManager(log_dir=temp_log_dir, level="INFO", save_to_file=False)
    
    # Log without callback
    logger.info("Before callback", "Test")
    assert len(messages) == 0
    
    # Set callback
    def callback(level, source, message):
        messages.append((level, source, message))
    
    logger.set_callback(callback)
    
    # Log with callback
    logger.info("After callback", "Test")
    assert len(messages) == 1
    assert messages[0][2] == "After callback"


def test_logger_no_file_output(temp_log_dir):
    """Test logger with file output disabled."""
    logger = LoggerManager(log_dir=temp_log_dir, level="INFO", save_to_file=False)
    
    logger.info("Test message", "Test")
    
    # No log files should be created
    log_path = Path(temp_log_dir)
    log_files = list(log_path.glob("*.log"))
    assert len(log_files) == 0


def test_logger_multiple_messages(temp_log_dir):
    """Test logging multiple messages."""
    messages = []
    
    def callback(level, source, message):
        messages.append((level, source, message))
    
    logger = LoggerManager(log_dir=temp_log_dir, level="DEBUG", save_to_file=True, callback=callback)
    
    logger.debug("Debug msg", "Source1")
    logger.info("Info msg", "Source2")
    logger.warning("Warning msg", "Source3")
    logger.error("Error msg", "Source4")
    
    assert len(messages) == 4
    assert messages[0][0] == "DEBUG"
    assert messages[1][0] == "INFO"
    assert messages[2][0] == "WARNING"
    assert messages[3][0] == "ERROR"


def test_logger_default_source(temp_log_dir):
    """Test logging with default source."""
    messages = []
    
    def callback(level, source, message):
        messages.append((level, source, message))
    
    logger = LoggerManager(log_dir=temp_log_dir, level="INFO", save_to_file=False, callback=callback)
    
    logger.info("Test message")  # No source specified
    
    assert len(messages) == 1
    assert messages[0][1] == "System"  # Default source
