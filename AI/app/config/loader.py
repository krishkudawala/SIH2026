"""
Configuration loader for Mandi Nyaay inspection engine.
"""

from __future__ import annotations

from pathlib import Path
import yaml

from app.config.schema import InspectionConfig


def load_config(config_path: str | Path) -> InspectionConfig:
    """
    Load and validate an InspectionConfig from a YAML file.

    Raises:
        FileNotFoundError: If the specified config file does not exist.
        ValueError: If YAML parsing fails or schema validation fails.
    """
    path = Path(config_path)
    if not path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {path.resolve()}")

    with open(path, "r", encoding="utf-8") as f:
        try:
            raw_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Failed to parse YAML from {path}: {e}") from e

    if not isinstance(raw_data, dict):
        raise ValueError(f"Configuration at {path} must be a dictionary/mapping.")

    return InspectionConfig.model_validate(raw_data)
