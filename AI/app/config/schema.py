"""
Configuration schema for Mandi Nyaay inspection engine.

Ensures all configuration parameters are strongly typed and validated.
"""

from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class MarkerConfig(BaseModel):
    """Configuration for physical calibration marker detection."""
    model_config = ConfigDict(extra="forbid")

    expected_marker_id: int = Field(default=0, description="Expected ArUco marker identifier")
    marker_family: str = Field(default="DICT_4X4_50", description="OpenCV ArUco dictionary specification")
    physical_size_mm: float = Field(gt=0.0, description="Physical side length of the marker in mm")
    min_corner_perimeter_px: float = Field(
        default=80.0,
        gt=0.0,
        description="EXPERIMENTAL: Minimum perimeter in pixels for acceptable detection"
    )


class BlurConfig(BaseModel):
    """Configuration for blur/sharpness evaluation."""
    model_config = ConfigDict(extra="forbid")

    threshold_status: Literal["EXPERIMENTAL", "VALIDATED"] = Field(
        default="EXPERIMENTAL",
        description="Maturity of the threshold. Must remain EXPERIMENTAL until field-validated."
    )
    min_laplacian_variance: float = Field(
        gt=0.0,
        description="Minimum acceptable variance of Laplacian"
    )


class BrightnessConfig(BaseModel):
    """Configuration for luminance/brightness evaluation."""
    model_config = ConfigDict(extra="forbid")

    threshold_status: Literal["EXPERIMENTAL", "VALIDATED"] = Field(
        default="EXPERIMENTAL",
        description="Maturity of the threshold. Must remain EXPERIMENTAL until field-validated."
    )
    min_mean_luma: float = Field(ge=0.0, le=255.0, description="Minimum acceptable mean luminance")
    max_mean_luma: float = Field(ge=0.0, le=255.0, description="Maximum acceptable mean luminance")


class ExposureConfig(BaseModel):
    """Configuration for clipping and exposure evaluation."""
    model_config = ConfigDict(extra="forbid")

    threshold_status: Literal["EXPERIMENTAL", "VALIDATED"] = Field(
        default="EXPERIMENTAL",
        description="Maturity of the threshold. Must remain EXPERIMENTAL until field-validated."
    )
    max_clipped_ratio: float = Field(
        ge=0.0,
        le=1.0,
        description="Maximum acceptable ratio of clipped pixels"
    )


class QualityConfig(BaseModel):
    """Aggregated image quality thresholds."""
    model_config = ConfigDict(extra="forbid")

    blur: BlurConfig
    brightness: BrightnessConfig
    exposure: ExposureConfig


class ProcessingConfig(BaseModel):
    """Pipeline execution parameters."""
    model_config = ConfigDict(extra="forbid")

    preserve_raw_evidence: bool = Field(default=True, description="Whether to retain raw images and capture records")
    max_dimension_px: int = Field(default=4096, gt=0, description="Max allowed image dimension before warning")


class DatasetConfig(BaseModel):
    """External training dataset configuration."""
    model_config = ConfigDict(extra="forbid")

    dataset_id: str = Field(default="external_onion_v2", description="Dataset identifier")
    external_dataset_path: str | None = Field(
        default=r"Onion_grading_system\training\merged_v2\train\images",
        description="Path to external training dataset source"
    )
    manifest_output_path: str = Field(
        default="data/processed/dataset_manifest.json",
        description="Path to save machine-readable inspection manifest"
    )


class InspectionConfig(BaseModel):
    """Root configuration for inspection pipeline execution."""
    model_config = ConfigDict(extra="forbid")

    version: str = Field(..., description="Configuration file schema version")
    marker: MarkerConfig
    quality: QualityConfig
    processing: ProcessingConfig
    dataset: DatasetConfig = Field(default_factory=DatasetConfig)

