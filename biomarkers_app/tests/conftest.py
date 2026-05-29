"""Pytest configuration and fixtures"""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def project_root_path():
    """Get project root path."""
    return project_root


@pytest.fixture
def sample_config():
    """Sample configuration for testing."""
    return {
        "data": {
            "path": "data/test_data.csv",
            "validate_on_load": True
        },
        "pipeline": {
            "phases": ["phase_-6", "phase_0"],
            "random_seed": 42
        },
        "models": {
            "enable_nn": True,
            "enable_lr": True,
            "nn": {
                "hidden_dims": [128, 64, 32],
                "learning_rate": 0.001,
                "epochs": 500
            }
        }
    }
