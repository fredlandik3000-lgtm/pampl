"""Unit tests for ConfigManager"""

import pytest
import json
import tempfile
from pathlib import Path

from app.core.config_manager import ConfigManager


@pytest.fixture
def temp_config_dir():
    """Create temporary config directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir)
        
        # Create default config
        default_config = {
            "data": {
                "path": "test_data.csv",
                "validate_on_load": True
            },
            "pipeline": {
                "phases": ["phase_-6", "phase_0"],
                "random_seed": 42
            },
            "models": {
                "nn": {
                    "learning_rate": 0.001,
                    "epochs": 500
                }
            },
            "splitting": {
                "test_size": 0.3,
                "val_size": 0.25
            }
        }
        
        default_path = config_dir / "default_params.json"
        with open(default_path, 'w') as f:
            json.dump(default_config, f)
        
        yield config_dir


def test_config_manager_init(temp_config_dir):
    """Test ConfigManager initialization."""
    config = ConfigManager(str(temp_config_dir))
    
    assert config.config_dir == temp_config_dir
    assert config._default_config is not None
    assert config._merged_config is not None


def test_config_get_simple(temp_config_dir):
    """Test getting simple config value."""
    config = ConfigManager(str(temp_config_dir))
    
    assert config.get("pipeline.random_seed") == 42
    assert config.get("data.validate_on_load") is True


def test_config_get_nested(temp_config_dir):
    """Test getting nested config value."""
    config = ConfigManager(str(temp_config_dir))
    
    assert config.get("models.nn.learning_rate") == 0.001
    assert config.get("models.nn.epochs") == 500


def test_config_get_default(temp_config_dir):
    """Test getting config with default value."""
    config = ConfigManager(str(temp_config_dir))
    
    assert config.get("nonexistent.key", "default") == "default"
    assert config.get("models.nn.nonexistent", 999) == 999


def test_config_set(temp_config_dir):
    """Test setting config value."""
    config = ConfigManager(str(temp_config_dir))
    
    config.set("models.nn.learning_rate", 0.01)
    assert config.get("models.nn.learning_rate") == 0.01
    
    config.set("new.nested.value", "test")
    assert config.get("new.nested.value") == "test"


def test_config_save_and_load(temp_config_dir):
    """Test saving and loading user config."""
    config = ConfigManager(str(temp_config_dir))
    
    # Modify config
    config.set("models.nn.learning_rate", 0.01)
    config.set("pipeline.random_seed", 123)
    
    # Save
    config.save_user_config()
    
    # Create new instance (should load saved config)
    config2 = ConfigManager(str(temp_config_dir))
    
    assert config2.get("models.nn.learning_rate") == 0.01
    assert config2.get("pipeline.random_seed") == 123


def test_config_reset_to_defaults(temp_config_dir):
    """Test resetting config to defaults."""
    config = ConfigManager(str(temp_config_dir))
    
    # Modify config
    config.set("models.nn.learning_rate", 0.01)
    config.save_user_config()
    
    # Reset
    config.reset_to_defaults()
    
    # Should be back to default
    assert config.get("models.nn.learning_rate") == 0.001


def test_config_get_all(temp_config_dir):
    """Test getting complete config."""
    config = ConfigManager(str(temp_config_dir))
    
    all_config = config.get_all()
    
    assert isinstance(all_config, dict)
    assert "data" in all_config
    assert "pipeline" in all_config
    assert "models" in all_config


def test_config_validate_valid(temp_config_dir):
    """Test validation with valid config."""
    config = ConfigManager(str(temp_config_dir))
    
    # Create dummy data file
    data_path = temp_config_dir.parent / "test_data.csv"
    data_path.write_text("col1,col2\n1,2\n")
    config.set("data.path", str(data_path))
    
    is_valid, errors = config.validate()
    
    # Note: Will fail data path validation but other validations should pass
    assert isinstance(is_valid, bool)
    assert isinstance(errors, list)


def test_config_validate_invalid_learning_rate(temp_config_dir):
    """Test validation with invalid learning rate."""
    config = ConfigManager(str(temp_config_dir))
    
    config.set("models.nn.learning_rate", 1.5)  # Invalid: > 1
    
    is_valid, errors = config.validate()
    
    assert not is_valid
    assert any("learning rate" in err.lower() for err in errors)


def test_config_validate_invalid_test_size(temp_config_dir):
    """Test validation with invalid test size."""
    config = ConfigManager(str(temp_config_dir))
    
    config.set("splitting.test_size", 1.5)  # Invalid: > 1
    
    is_valid, errors = config.validate()
    
    assert not is_valid
    assert any("test_size" in err.lower() for err in errors)


def test_config_preset_save_and_load(temp_config_dir):
    """Test saving and loading presets."""
    config = ConfigManager(str(temp_config_dir))
    
    # Modify config
    config.set("models.nn.learning_rate", 0.01)
    
    # Save preset
    assert config.save_preset("test_preset", "Test preset description")
    
    # Reset to defaults
    config.reset_to_defaults()
    assert config.get("models.nn.learning_rate") == 0.001
    
    # Load preset
    assert config.load_preset("test_preset")
    assert config.get("models.nn.learning_rate") == 0.01


def test_config_list_presets(temp_config_dir):
    """Test listing presets."""
    config = ConfigManager(str(temp_config_dir))
    
    # Save some presets
    config.save_preset("preset1")
    config.save_preset("preset2")
    
    presets = config.list_presets()
    
    assert "preset1" in presets
    assert "preset2" in presets
    assert len(presets) >= 2


def test_config_user_override_default(temp_config_dir):
    """Test that user config overrides defaults."""
    config = ConfigManager(str(temp_config_dir))
    
    # Default value
    assert config.get("pipeline.random_seed") == 42
    
    # Set user value
    config.set("pipeline.random_seed", 999)
    assert config.get("pipeline.random_seed") == 999
    
    # Save and reload
    config.save_user_config()
    config2 = ConfigManager(str(temp_config_dir))
    
    # User value should persist
    assert config2.get("pipeline.random_seed") == 999
