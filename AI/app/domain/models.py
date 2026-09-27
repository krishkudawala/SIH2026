"""
Domain models and contracts for Mandi Nyaay inspection observations.

Enforces strict typing, explicit provenance, and zero data fabrication.
"""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from app.domain.status import (
    InspectionStatus,
    MarkerFailureCode,
    MeasurementStatus,
    QualityFailureCode,
)
from app.version import get_processing_version


class CaptureInput(BaseModel):
    """
    Raw capture input contract.

    Represents the genuine physical capture artifact and its acquisition context.
    """
    model_config = ConfigDict(extra="forbid")

    capture_id: str = Field(..., description="Unique deterministic or UUID identifier for the capture")
    image_path: str = Field(..., description="Filesystem path to the preserved raw image")
    captured_at: datetime = Field(..., description="Timestamp of the original photo capture")
    device_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Camera parameters, sensor model, focal length, or resolution if available"
    )
    session_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Mandi location, lot identifier, or operator session tags"
    )


class MarkerObservation(BaseModel):
    """
    Observation for physical reference marker (e.g. ArUco) detection and calibration.
    """
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    detected: bool = Field(..., alias="marker_detected", description="Whether a valid marker was detected in the frame")
    marker_id: int | None = Field(default=None, description="Decoded marker ID, if detected")
    dictionary: str | None = Field(default=None, description="ArUco dictionary identifier, e.g. DICT_4X4_50")
    corners_px: list[tuple[float, float]] | None = Field(
        default=None,
        description="Sub-pixel corner coordinates in image coordinate space [(x0, y0), (x1, y1), (x2, y2), (x3, y3)]"
    )
    marker_side_lengths_px: list[float] | None = Field(
        default=None,
        description="Observed four edge lengths in pixels [side0, side1, side2, side3]"
    )
    marker_area_px: float | None = Field(
        default=None,
        description="Enclosed quadrilateral pixel area"
    )
    physical_size_mm: float | None = Field(
        default=None,
        alias="configured_physical_size_mm",
        description="Known physical edge size in millimeters from calibration configuration"
    )
    validation_status: InspectionStatus = Field(
        ...,
        alias="marker_validation_status",
        description="Status of marker detection and geometric validity"
    )
    failure_code: MarkerFailureCode = Field(
        default=MarkerFailureCode.NONE,
        description="Primary failure reason if marker validation failed"
    )
    failure_codes: list[MarkerFailureCode] = Field(
        default_factory=list,
        description="All failure codes triggered during marker validation"
    )
    homography_matrix: list[list[float]] | None = Field(
        default=None,
        description="3x3 projective homography matrix mapping image pixels to metric plane (mm)"
    )
    reprojection_error_px: float | None = Field(
        default=None,
        description="RMS back-projection error in pixels of the 4 marker corners"
    )
    diagnostic_scale_mm_per_px: float | None = Field(
        default=None,
        description="Diagnostic simple scale factor (sanity check only, not the primary measurement architecture)"
    )
    measurement_domain: str = Field(
        default="PLANAR_METRIC_MEASUREMENT",
        description="Explicit classification of the measurement coordinate space"
    )
    limitation_disclaimer: str = Field(
        default=(
            "Measurement valid strictly on reference marker plane. "
            "Does NOT establish 3D object height or elevation-corrected dimensions."
        ),
        description="Mandatory physical measurement boundary disclaimer"
    )
    processing_version: str = Field(
        default_factory=get_processing_version,
        description="Processing version that generated this observation"
    )

    def to_validation_json(self, capture_id: str) -> dict[str, Any]:
        """Produce canonical JSON structure specified for Gate 1."""
        return {
            "capture_id": capture_id,
            "marker_detected": self.detected,
            "marker_id": self.marker_id,
            "dictionary": self.dictionary,
            "corners_px": self.corners_px,
            "marker_side_lengths_px": self.marker_side_lengths_px,
            "marker_area_px": self.marker_area_px,
            "configured_physical_size_mm": self.physical_size_mm,
            "homography_matrix": self.homography_matrix,
            "reprojection_error_px": self.reprojection_error_px,
            "diagnostic_scale_mm_per_px": self.diagnostic_scale_mm_per_px,
            "measurement_domain": self.measurement_domain,
            "limitation_disclaimer": self.limitation_disclaimer,
            "marker_validation_status": self.validation_status.value,
            "failure_codes": [fc.value for fc in self.failure_codes],
            "processing_version": self.processing_version,
        }


class ReferenceObjectValidation(BaseModel):
    """
    Validation audit comparing planar reference object measurement against direct physical ground truth.
    """
    model_config = ConfigDict(extra="forbid")

    reference_object_name: str = Field(..., description="Name/identifier of known reference disc or coin")
    ground_truth_diameter_mm: float = Field(..., description="Direct physical caliper-measured diameter in mm")
    measured_planar_diameter_mm: float = Field(..., description="Planar homography measured diameter in mm")
    absolute_error_mm: float = Field(..., description="Absolute difference in mm")
    relative_error_pct: float = Field(..., description="Relative error percentage")
    status: InspectionStatus = Field(..., description="Validation outcome status")


class ImageQualityObservation(BaseModel):
    """
    Observation assessing environmental capture quality (blur, illumination, exposure).
    """
    model_config = ConfigDict(extra="forbid")

    blur_measure: float | None = Field(
        default=None,
        description="Computed sharpness index (e.g. Laplacian variance). Subject to experimental thresholds."
    )
    brightness_measure: float | None = Field(
        default=None,
        description="Computed mean luminance metric across image pixels"
    )
    exposure_measure: float | None = Field(
        default=None,
        description="Ratio of underexposed or overexposed clipped pixels"
    )
    quality_status: InspectionStatus = Field(
        ...,
        description="Status indicating whether image quality is sufficient for valid inference"
    )
    failure_codes: list[QualityFailureCode] = Field(
        default_factory=list,
        description="Specific failure codes when image quality is deficient"
    )


class PixelMeasurements(BaseModel):
    """Raw 2D measurements in pixel space."""
    model_config = ConfigDict(extra="forbid")

    area_px: float | None = Field(default=None, description="Enclosed boundary area in pixels")
    major_axis_px: float | None = Field(default=None, description="Major axis length in pixels")
    minor_axis_px: float | None = Field(default=None, description="Minor axis length in pixels")
    perimeter_px: float | None = Field(default=None, description="Boundary perimeter length in pixels")


class CalibratedMeasurements(BaseModel):
    """
    Physical measurements calibrated against a verified reference marker.
    Uncertain or unmodeled metrics remain None.
    """
    model_config = ConfigDict(extra="forbid")

    min_diameter_mm: float | None = Field(default=None, description="Minimum equatorial diameter in mm")
    max_diameter_mm: float | None = Field(default=None, description="Maximum equatorial diameter in mm")
    estimated_weight_g: float | None = Field(
        default=None,
        description="Physical weight estimate in grams. Never fabricated; None until volumetric models are verified."
    )


class OnionObservation(BaseModel):
    """
    Single produce (onion) observation representation.
    """
    model_config = ConfigDict(extra="forbid")

    onion_id: str = Field(..., description="Unique identifier for this segmented entity within the capture")
    boundary_px: list[tuple[float, float]] | None = Field(
        default=None,
        description="Ordered 2D polygon vertices representing the contour/mask boundary"
    )
    bbox: tuple[float, float, float, float] | None = Field(
        default=None,
        description="Bounding box in image coordinates (xmin, ymin, xmax, ymax)"
    )
    raw_pixel_measurements: PixelMeasurements | None = Field(
        default=None,
        description="Raw geometric pixel measurements before metric scale transformation"
    )
    calibrated_measurements: CalibratedMeasurements | None = Field(
        default=None,
        description="Calibrated metric measurements in mm / g"
    )
    measurement_status: MeasurementStatus = Field(
        default=MeasurementStatus.NOT_IMPLEMENTED,
        description="Status of individual onion segmentation and measurement computation"
    )


class InspectionObservation(BaseModel):
    """
    Root inspection result aggregating marker, quality, and produce observations.

    Guarantees every result identifies the software and pipeline version that produced it.
    """
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    capture_id: str = Field(..., description="Reference ID matching the input capture")
    marker_result: MarkerObservation = Field(
        ...,
        alias="marker_result",
        description="Marker observation and scale calibration result"
    )
    quality_result: ImageQualityObservation = Field(
        ...,
        alias="quality_result",
        description="Photographic quality assessment result"
    )
    onion_observations: list[OnionObservation] = Field(
        default_factory=list,
        description="List of observed and evaluated onions"
    )
    processing_version: str = Field(
        default_factory=get_processing_version,
        description="Immutable processing/model version string that produced this observation"
    )
    overall_status: InspectionStatus = Field(
        ...,
        description="High-level lifecycle status of the entire inspection slice"
    )
