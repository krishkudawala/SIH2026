"""
Image quality assessment interface and OpenCV evaluation engine.

Computes genuine mathematical image quality metrics:
- Image dimensions (width, height)
- Sharpness / blur via Laplacian variance (blur_score)
- Mean photometric luminance
- Exposure clipping ratio (under/over-saturated pixels)

Never fabricates metrics. Explicitly grades capture as PASS, WARN, or FAIL.
"""

from __future__ import annotations

from enum import Enum
import cv2
import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from app.config.schema import QualityConfig
from app.domain.models import ImageQualityObservation
from app.domain.status import InspectionStatus, QualityFailureCode


class QualityGrade(str, Enum):
    """Overall qualitative determination of capture admissibility."""
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


class ImageQualityMetrics(BaseModel):
    """Measured optical and photometric quality parameters."""
    model_config = ConfigDict(extra="forbid")

    width: int = Field(..., gt=0, description="Image width in pixels")
    height: int = Field(..., gt=0, description="Image height in pixels")
    mean_luminance: float = Field(..., ge=0.0, le=255.0, description="Average gray luminance (0-255)")
    blur_score: float = Field(..., ge=0.0, description="Laplacian variance sharpness index")
    exposure_clipped_ratio: float = Field(
        ..., ge=0.0, le=1.0, description="Fraction of extreme black/white clipped pixels"
    )
    grade: QualityGrade = Field(..., description="Overall qualitative judgment (PASS, WARN, FAIL)")
    reasons: list[str] = Field(default_factory=list, description="Specific triggers for WARN or FAIL")


def compute_image_quality(
    image: np.ndarray,
    config: QualityConfig | None = None,
) -> ImageQualityMetrics:
    """
    Compute genuine OpenCV metrics on an input BGR or grayscale image array.
    """
    if image is None or not isinstance(image, np.ndarray) or image.size == 0:
        raise ValueError("Invalid image: numpy array is empty, None, or unreadable.")

    height, width = image.shape[:2]

    # Convert to grayscale for optical/photometric analysis
    if len(image.shape) == 3 and image.shape[2] == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    elif len(image.shape) == 2:
        gray = image
    elif len(image.shape) == 3 and image.shape[2] == 4:
        gray = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
    else:
        gray = image.squeeze()

    # 1. Blur evaluation via variance of the Laplacian
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    blur_score = float(laplacian.var())

    # 2. Photometric luminance
    mean_luminance = float(np.mean(gray))

    # 3. Exposure clipping (pixels <= 2 or >= 253)
    total_pixels = float(gray.size)
    clipped_pixels = np.count_nonzero((gray <= 2) | (gray >= 253))
    clipped_ratio = float(clipped_pixels / total_pixels) if total_pixels > 0 else 0.0

    # Retrieve threshold parameters
    min_blur = config.blur.min_laplacian_variance if config else 100.0
    min_luma = config.brightness.min_mean_luma if config else 35.0
    max_luma = config.brightness.max_mean_luma if config else 225.0
    max_clip = config.exposure.max_clipped_ratio if config else 0.08

    reasons: list[str] = []
    grade = QualityGrade.PASS

    # Severe failure criteria
    if blur_score < (min_blur * 0.4):
        grade = QualityGrade.FAIL
        reasons.append(f"Severe motion blur: Laplacian variance {blur_score:.1f} is below critical threshold {min_blur * 0.4:.1f}")
    elif blur_score < min_blur:
        if grade != QualityGrade.FAIL:
            grade = QualityGrade.WARN
        reasons.append(f"Borderline sharpness: blur score {blur_score:.1f} < threshold {min_blur:.1f}")

    if mean_luminance < min_luma:
        if mean_luminance < (min_luma * 0.5):
            grade = QualityGrade.FAIL
            reasons.append(f"Severe underexposure: mean luma {mean_luminance:.1f} < critical {min_luma * 0.5:.1f}")
        else:
            if grade != QualityGrade.FAIL:
                grade = QualityGrade.WARN
            reasons.append(f"Low illumination: mean luma {mean_luminance:.1f} < {min_luma:.1f}")
    elif mean_luminance > max_luma:
        if grade != QualityGrade.FAIL:
            grade = QualityGrade.WARN
        reasons.append(f"High illumination / glare: mean luma {mean_luminance:.1f} > {max_luma:.1f}")

    if clipped_ratio > (max_clip * 2.0):
        grade = QualityGrade.FAIL
        reasons.append(f"Severe dynamic range clipping: {clipped_ratio * 100:.1f}% clipped pixels exceeds {max_clip * 200:.1f}%")
    elif clipped_ratio > max_clip:
        if grade != QualityGrade.FAIL:
            grade = QualityGrade.WARN
        reasons.append(f"Elevated pixel clipping: {clipped_ratio * 100:.1f}% exceeds threshold {max_clip * 100:.1f}%")

    return ImageQualityMetrics(
        width=width,
        height=height,
        mean_luminance=round(mean_luminance, 2),
        blur_score=round(blur_score, 2),
        exposure_clipped_ratio=round(clipped_ratio, 4),
        grade=grade,
        reasons=reasons,
    )


def assess_image_quality(
    image: np.ndarray | None,
    config: QualityConfig,
) -> ImageQualityObservation:
    """
    Assess photographic capture quality and populate the canonical domain observation.
    Records genuine measured metrics. If thresholds are EXPERIMENTAL, marks status
    as NOT_IMPLEMENTED until field calibration is completed.
    """
    if image is None or not isinstance(image, np.ndarray) or image.size == 0:
        return ImageQualityObservation(
            quality_status=InspectionStatus.INVALID_CAPTURE,
            failure_codes=[QualityFailureCode.RESOLUTION_INSUFFICIENT],
        )

    metrics = compute_image_quality(image, config)

    # If all thresholds are experimental, maintain Phase 0 status
    if getattr(config.blur, "threshold_status", "EXPERIMENTAL") == "EXPERIMENTAL":
        return ImageQualityObservation(
            blur_measure=metrics.blur_score,
            brightness_measure=metrics.mean_luminance,
            exposure_measure=metrics.exposure_clipped_ratio,
            quality_status=InspectionStatus.NOT_IMPLEMENTED,
            failure_codes=[QualityFailureCode.NOT_IMPLEMENTED],
        )

    failure_codes: list[QualityFailureCode] = []
    if metrics.grade == QualityGrade.FAIL:
        status = InspectionStatus.RETRY
        if any("blur" in r.lower() for r in metrics.reasons):
            failure_codes.append(QualityFailureCode.BLUR_EXCEEDED)
        if any("underexposure" in r.lower() for r in metrics.reasons):
            failure_codes.append(QualityFailureCode.UNDEREXPOSED)
        if any("illumination" in r.lower() or "clipping" in r.lower() for r in metrics.reasons):
            failure_codes.append(QualityFailureCode.OVEREXPOSED)
    elif metrics.grade == QualityGrade.WARN:
        status = InspectionStatus.MANUAL_REVIEW
        if any("blur" in r.lower() for r in metrics.reasons):
            failure_codes.append(QualityFailureCode.BLUR_EXCEEDED)
    else:
        status = InspectionStatus.VALID

    return ImageQualityObservation(
        blur_measure=metrics.blur_score,
        brightness_measure=metrics.mean_luminance,
        exposure_measure=metrics.exposure_clipped_ratio,
        quality_status=status,
        failure_codes=failure_codes,
    )
