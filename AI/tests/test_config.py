"""
Tests for configuration loading and validation.
"""

from pathlib import Path
import pytest
from app.config import InspectionConfig, load_config


def test_load_default_inspection_config() -> None:
    config_path = Path("configs/inspection_config.yaml")
    config = load_config(config_path)

    assert isinstance(config, InspectionConfig)
    assert config.version == "0.1.0"
    assert config.marker.expected_marker_id == 0
    assert config.marker.physical_size_mm == 50.0

    # Verify that experimental flags are explicitly enforced
    assert config.quality.blur.threshold_status == "EXPERIMENTAL"
    assert config.quality.brightness.threshold_status == "EXPERIMENTAL"
    assert config.quality.exposure.threshold_status == "EXPERIMENTAL"


def test_missing_config_file_raises_error() -> None:
    with pytest.raises(FileNotFoundError):
        load_config("non_existent_config.yaml")
