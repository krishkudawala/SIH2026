"""
Inspection pipeline coordinator.

Coordinates capture ingestion, image validation, marker detection, quality assessment,
and produces auditable typed InspectionObservation artifacts.
"""

from __future__ import annotations

from pathlib import Path
import cv2

from app.config.schema import InspectionConfig
from app.cv.marker import detect_marker, save_marker_debug_visualization
from app.cv.quality import assess_image_quality
from app.domain.models import (
    CaptureInput,
    ImageQualityObservation,
    InspectionObservation,
    MarkerObservation,
)
from app.domain.status import (
    InspectionStatus,
    MarkerFailureCode,
    QualityFailureCode,
)
from app.version import get_processing_version


def run_inspection(
    capture: CaptureInput,
    config: InspectionConfig,
    save_debug_artifacts: bool = False,
    debug_output_dir: str | Path = "data/processed",
) -> InspectionObservation:
    """
    Execute end-to-end inspection pipeline for a given capture.

    Returns a strongly typed InspectionObservation. Never raises exceptions for expected
    field uncertainty or missing real data; instead, assigns explicit status values.
    """
    image_path = Path(capture.image_path)

    # 1. Capture file verification
    if not image_path.is_file():
        return InspectionObservation(
            capture_id=capture.capture_id,
            marker_result=MarkerObservation(
                detected=False,
                validation_status=InspectionStatus.INVALID_CAPTURE,
                failure_code=MarkerFailureCode.MARKER_NOT_DETECTED,
            ),
            quality_result=ImageQualityObservation(
                quality_status=InspectionStatus.INVALID_CAPTURE,
                failure_codes=[QualityFailureCode.RESOLUTION_INSUFFICIENT],
            ),
            onion_observations=[],
            processing_version=get_processing_version(),
            overall_status=InspectionStatus.INVALID_CAPTURE,
        )

    # 2. Image decoding
    image = cv2.imread(str(image_path))
    if image is None or image.size == 0:
        return InspectionObservation(
            capture_id=capture.capture_id,
            marker_result=MarkerObservation(
                detected=False,
                validation_status=InspectionStatus.INVALID_CAPTURE,
                failure_code=MarkerFailureCode.MARKER_NOT_DETECTED,
            ),
            quality_result=ImageQualityObservation(
                quality_status=InspectionStatus.INVALID_CAPTURE,
                failure_codes=[QualityFailureCode.RESOLUTION_INSUFFICIENT],
            ),
            onion_observations=[],
            processing_version=get_processing_version(),
            overall_status=InspectionStatus.INVALID_CAPTURE,
        )

    # 3. Image quality assessment
    quality_obs = assess_image_quality(image, config.quality)

    # 4. Reference marker detection & calibration
    marker_obs = detect_marker(image, config.marker)

    # Optionally persist debug visualization artifact
    if save_debug_artifacts and marker_obs.corners_px is not None:
        debug_path = Path(debug_output_dir) / f"{capture.capture_id}_marker_debug.png"
        save_marker_debug_visualization(image, marker_obs, debug_path)

    # 5. Determine overall lifecycle status
    overall_status = InspectionStatus.NOT_IMPLEMENTED
    if quality_obs.quality_status == InspectionStatus.INVALID_CAPTURE:
        overall_status = InspectionStatus.INVALID_CAPTURE
    elif quality_obs.quality_status == InspectionStatus.RETRY:
        overall_status = InspectionStatus.RETRY
    elif marker_obs.validation_status == InspectionStatus.CALIBRATION_INVALID:
        overall_status = InspectionStatus.CALIBRATION_INVALID
    elif marker_obs.validation_status == InspectionStatus.MANUAL_REVIEW:
        overall_status = InspectionStatus.MANUAL_REVIEW

    return InspectionObservation(
        capture_id=capture.capture_id,
        marker_result=marker_obs,
        quality_result=quality_obs,
        onion_observations=[],  # No onions fabricated; waiting for real models/data
        processing_version=get_processing_version(),
        overall_status=overall_status,
    )
