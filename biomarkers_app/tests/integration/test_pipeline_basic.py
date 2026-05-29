"""Integration tests for basic pipeline operations"""

import pytest
import tempfile
import pandas as pd
from pathlib import Path

from app.pipeline.types import (
    PipelineStep, PipelineConfig, CancellationToken
)
from app.core.pipeline_orchestrator import PipelineOrchestrator
from app.pipeline.wrappers.data_loader_wrapper import DataLoaderWrapper
from app.core.logger_manager import LoggerManager


@pytest.fixture
def temp_data_file():
    """Create a temporary CSV file with sample data"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        # Write sample clinical data
        f.write("patient_id,age,disease,phase_-6_feature1,phase_-6_feature2\n")
        f.write("P001,45,DLBCL,1.2,3.4\n")
        f.write("P002,52,MCL,2.1,4.5\n")
        f.write("P003,38,FL,1.8,3.9\n")
        f.write("P004,61,DLBCL,2.5,5.1\n")
        f.write("P005,48,MCL,1.4,3.7\n")
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    Path(temp_path).unlink()


@pytest.fixture
def logger():
    """Create a logger instance for testing"""
    return LoggerManager(log_dir="logs", level="INFO", save_to_file=False)


@pytest.fixture
def pipeline_config(temp_data_file):
    """Create a pipeline configuration"""
    return PipelineConfig(
        data_path=temp_data_file,
        phases=['phase_-6', 'phase_0'],
        targets=['D30_response_3class', 'D90_is_cr'],
        random_seed=42,
        validate_data=True,
        enable_caching=True
    )


def test_data_loader_basic(temp_data_file):
    """Test basic data loading functionality"""
    loader = DataLoaderWrapper()
    
    result = loader.load_data(temp_data_file, validate=True)
    
    assert result.success
    assert result.data is not None
    assert isinstance(result.data, pd.DataFrame)
    assert result.metadata['rows'] == 5
    assert result.metadata['columns'] == 5
    assert result.metadata['completeness'] == 1.0  # No missing values
    assert 'load_time_sec' in result.metadata


def test_data_loader_nonexistent_file():
    """Test data loader with nonexistent file"""
    loader = DataLoaderWrapper()
    
    result = loader.load_data("nonexistent_file.csv")
    
    assert not result.success
    assert result.data is None
    assert len(result.errors) > 0
    assert "not found" in result.errors[0].lower()


def test_data_loader_with_progress_callback(temp_data_file):
    """Test data loader with progress callback"""
    loader = DataLoaderWrapper()
    
    progress_updates = []
    
    def progress_callback(percent, message):
        progress_updates.append((percent, message))
    
    result = loader.load_data(temp_data_file, progress_callback=progress_callback)
    
    assert result.success
    assert len(progress_updates) > 0
    # Should have progress at 0%, 10%, 50%, 80%, 100%
    assert any(p[0] == 100.0 for p in progress_updates)


def test_data_loader_with_cancellation(temp_data_file):
    """Test data loader with immediate cancellation"""
    loader = DataLoaderWrapper()
    cancellation_token = CancellationToken()
    
    # Cancel immediately
    cancellation_token.cancel()
    
    result = loader.load_data(
        temp_data_file,
        cancellation_token=cancellation_token
    )
    
    assert not result.success
    assert "cancel" in result.errors[0].lower()


def test_orchestrator_initialization(pipeline_config, logger):
    """Test pipeline orchestrator initialization"""
    orchestrator = PipelineOrchestrator(pipeline_config, logger)
    
    assert orchestrator.config == pipeline_config
    assert orchestrator.logger == logger
    assert orchestrator.current_step is None
    assert len(orchestrator.step_results) == 0


def test_orchestrator_execute_single_step(pipeline_config, logger, temp_data_file):
    """Test orchestrator executing a single step"""
    orchestrator = PipelineOrchestrator(pipeline_config, logger)
    loader = DataLoaderWrapper()
    
    # Execute data loading step
    result = orchestrator.execute_step(
        PipelineStep.LOAD_DATA,
        loader.load_data,
        temp_data_file
    )
    
    assert result.success
    assert orchestrator.current_step == PipelineStep.LOAD_DATA
    assert PipelineStep.LOAD_DATA in orchestrator.step_results
    assert 'execution_time_sec' in result.metadata
    assert 'timestamp' in result.metadata


def test_orchestrator_cancel_execution(pipeline_config, logger, temp_data_file):
    """Test orchestrator cancellation"""
    orchestrator = PipelineOrchestrator(pipeline_config, logger)
    loader = DataLoaderWrapper()
    
    # Cancel before execution
    orchestrator.cancel()
    
    result = orchestrator.execute_step(
        PipelineStep.LOAD_DATA,
        loader.load_data,
        temp_data_file
    )
    
    assert not result.success
    assert "cancelled" in result.errors[0].lower()


def test_orchestrator_step_progress_callback(pipeline_config, logger, temp_data_file):
    """Test orchestrator with progress callback"""
    orchestrator = PipelineOrchestrator(pipeline_config, logger)
    loader = DataLoaderWrapper()
    
    progress_updates = []
    
    def progress_callback(percent, message):
        progress_updates.append((percent, message))
    
    orchestrator.set_progress_callback(progress_callback)
    
    result = orchestrator.execute_step(
        PipelineStep.LOAD_DATA,
        loader.load_data,
        temp_data_file
    )
    
    assert result.success
    assert len(progress_updates) > 0
    # Check that step name is included in messages
    assert any("load_data" in str(msg).lower() for _, msg in progress_updates)


def test_orchestrator_get_execution_summary(pipeline_config, logger, temp_data_file):
    """Test execution summary generation"""
    orchestrator = PipelineOrchestrator(pipeline_config, logger)
    loader = DataLoaderWrapper()
    
    # Execute a step
    orchestrator.execute_step(
        PipelineStep.LOAD_DATA,
        loader.load_data,
        temp_data_file
    )
    
    summary = orchestrator.get_execution_summary()
    
    assert summary['total_steps'] == 1
    assert summary['successful_steps'] == 1
    assert summary['failed_steps'] == 0
    assert summary['total_execution_time_sec'] > 0
    assert not summary['cancelled']


def test_orchestrator_reset(pipeline_config, logger, temp_data_file):
    """Test orchestrator reset functionality"""
    orchestrator = PipelineOrchestrator(pipeline_config, logger)
    loader = DataLoaderWrapper()
    
    # Execute a step
    orchestrator.execute_step(
        PipelineStep.LOAD_DATA,
        loader.load_data,
        temp_data_file
    )
    
    assert len(orchestrator.step_results) == 1
    
    # Reset
    orchestrator.reset()
    
    assert orchestrator.current_step is None
    assert len(orchestrator.step_results) == 0
    assert not orchestrator.cancellation_token.is_cancelled()


def test_end_to_end_data_loading(pipeline_config, logger, temp_data_file):
    """Test complete end-to-end data loading workflow"""
    orchestrator = PipelineOrchestrator(pipeline_config, logger)
    loader = DataLoaderWrapper()
    
    progress_log = []
    
    def progress_callback(percent, message):
        progress_log.append(f"{percent:.0f}%: {message}")
    
    orchestrator.set_progress_callback(progress_callback)
    
    # Execute data loading
    result = orchestrator.execute_step(
        PipelineStep.LOAD_DATA,
        loader.load_data,
        temp_data_file,
        validate=True
    )
    
    # Verify success
    assert result.success
    assert result.data is not None
    assert isinstance(result.data, pd.DataFrame)
    
    # Verify metadata
    assert result.metadata['rows'] == 5
    assert result.metadata['columns'] == 5
    assert result.metadata['completeness'] > 0.99
    
    # Verify progress was reported
    assert len(progress_log) > 0
    
    # Verify result is cached in orchestrator
    cached_result = orchestrator.get_step_result(PipelineStep.LOAD_DATA)
    assert cached_result is not None
    assert cached_result.success
    
    # Verify execution summary
    summary = orchestrator.get_execution_summary()
    assert summary['total_steps'] == 1
    assert summary['successful_steps'] == 1
