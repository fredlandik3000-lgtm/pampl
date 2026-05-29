"""Configuration Management for Biomarkers Pipeline Tool"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from copy import deepcopy

from app.core.repo_paths import repo_root


class ConfigManager:
    """Manages application configuration with default values and user overrides."""
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_dir: Path to config directory. If None, uses default location.
        """
        # biomarkers_app/ (config, app package root for this project)
        self.project_root = Path(__file__).parent.parent.parent
        # Git repository root (parent of biomarkers_app/)
        self.repo_root = repo_root()

        if config_dir is None:
            self.config_dir = self.project_root / "config"
        else:
            self.config_dir = Path(config_dir)
        
        self.default_config_path = self.config_dir / "default_params.json"
        self.user_config_path = self.config_dir / "user_params.json"
        
        self._default_config: Dict[str, Any] = {}
        self._user_config: Dict[str, Any] = {}
        self._merged_config: Dict[str, Any] = {}
        
        # Load configurations
        self._load_default()
        self._load_user()
        self._merge_configs()
    
    def _load_default(self) -> None:
        """Load default configuration from file."""
        if not self.default_config_path.exists():
            raise FileNotFoundError(
                f"Default config not found: {self.default_config_path}"
            )
        
        with open(self.default_config_path, 'r') as f:
            self._default_config = json.load(f)
    
    def _load_user(self) -> None:
        """Load user configuration from file if it exists."""
        if self.user_config_path.exists():
            try:
                with open(self.user_config_path, 'r') as f:
                    self._user_config = json.load(f)
            except json.JSONDecodeError as e:
                print(f"Warning: Failed to load user config: {e}")
                self._user_config = {}
        else:
            self._user_config = {}
    
    def _merge_configs(self) -> None:
        """Merge user config with defaults (user config takes precedence)."""
        self._merged_config = deepcopy(self._default_config)
        self._deep_update(self._merged_config, self._user_config)
    
    def _deep_update(self, base: Dict, updates: Dict) -> None:
        """Recursively update nested dictionaries."""
        for key, value in updates.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-separated path.
        
        Args:
            key_path: Dot-separated path (e.g., "models.nn.learning_rate")
            default: Default value if key not found
            
        Returns:
            Configuration value or default
            
        Example:
            config.get("models.nn.learning_rate")  # Returns 0.001
        """
        keys = key_path.split('.')
        value = self._merged_config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any) -> None:
        """
        Set configuration value by dot-separated path.
        
        Args:
            key_path: Dot-separated path (e.g., "models.nn.learning_rate")
            value: Value to set
        """
        keys = key_path.split('.')
        target = self._merged_config
        
        # Navigate to the parent dict
        for key in keys[:-1]:
            if key not in target or not isinstance(target[key], dict):
                target[key] = {}
            target = target[key]
        
        # Set the final value
        target[keys[-1]] = value
        
        # Also update user config to persist changes
        target_user = self._user_config
        for key in keys[:-1]:
            if key not in target_user:
                target_user[key] = {}
            target_user = target_user[key]
        target_user[keys[-1]] = value
    
    def get_all(self) -> Dict[str, Any]:
        """Get complete merged configuration."""
        return deepcopy(self._merged_config)
    
    def save_user_config(self) -> None:
        """Save current user configuration to file."""
        os.makedirs(self.config_dir, exist_ok=True)
        
        with open(self.user_config_path, 'w') as f:
            json.dump(self._user_config, f, indent=2)
    
    def reset_to_defaults(self) -> None:
        """Reset all configuration to defaults."""
        self._user_config = {}
        self._merge_configs()
        
        # Delete user config file if it exists
        if self.user_config_path.exists():
            self.user_config_path.unlink()
    
    def validate(self) -> tuple[bool, list[str]]:
        """
        Validate current configuration.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        config = self._merged_config
        
        # Validate data path
        if 'data' in config and 'path' in config['data']:
            data_path = Path(config['data']['path'])
            if not data_path.is_absolute():
                # Make it relative to project root
                data_path = self.project_root.parent / data_path
            if not data_path.exists():
                errors.append(f"Data file not found: {data_path}")
        else:
            errors.append("Data path not specified in configuration")
        
        # Validate phases
        if 'pipeline' in config and 'phases' in config['pipeline']:
            valid_phases = ['phase_-6', 'phase_0', 'phase_15', 'phase_30']
            for phase in config['pipeline']['phases']:
                if phase not in valid_phases:
                    errors.append(f"Invalid phase: {phase}")
        
        # Validate model parameters
        if 'models' in config and 'nn' in config['models']:
            nn_config = config['models']['nn']
            if 'learning_rate' in nn_config:
                if not (0 < nn_config['learning_rate'] < 1):
                    errors.append(f"Invalid learning rate: {nn_config['learning_rate']}")
        
        # Validate split sizes
        if 'splitting' in config:
            split_config = config['splitting']
            if 'test_size' in split_config:
                test_size = split_config['test_size']
                if not (0 < test_size < 1):
                    errors.append(f"Invalid test_size: {test_size}")
            if 'val_size' in split_config:
                val_size = split_config['val_size']
                if not (0 < val_size < 1):
                    errors.append(f"Invalid val_size: {val_size}")
        
        return (len(errors) == 0, errors)
    
    def load_preset(self, preset_name: str) -> bool:
        """
        Load a preset configuration.
        
        Args:
            preset_name: Name of preset (e.g., "quick_test")
            
        Returns:
            True if loaded successfully
        """
        preset_path = self.config_dir / "presets" / f"{preset_name}.json"
        
        if not preset_path.exists():
            return False
        
        try:
            with open(preset_path, 'r') as f:
                preset_config = json.load(f)
            
            # Merge preset with defaults
            self._user_config = deepcopy(preset_config)
            self._merge_configs()
            return True
        except Exception as e:
            print(f"Failed to load preset {preset_name}: {e}")
            return False
    
    def save_preset(self, preset_name: str, description: str = "") -> bool:
        """
        Save current configuration as a preset.
        
        Args:
            preset_name: Name for the preset
            description: Optional description
            
        Returns:
            True if saved successfully
        """
        preset_path = self.config_dir / "presets" / f"{preset_name}.json"
        os.makedirs(preset_path.parent, exist_ok=True)
        
        try:
            preset_data = deepcopy(self._user_config)
            if description:
                preset_data['_description'] = description
            
            with open(preset_path, 'w') as f:
                json.dump(preset_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Failed to save preset {preset_name}: {e}")
            return False
    
    def list_presets(self) -> list[str]:
        """List available presets."""
        presets_dir = self.config_dir / "presets"
        if not presets_dir.exists():
            return []
        
        return [f.stem for f in presets_dir.glob("*.json")]
