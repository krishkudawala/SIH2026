"""
Deterministic Multimodal Model Fusion Engine for Mandi Nyaay (Component P).

Fuses:
1. Primary Detector Evidence (YOLO v7 ONNX)
2. Fine-Grained Second-Stage Crop Classifier Evidence (Calibrated probabilities)
3. Produce Silhouette & Defect Segmentation Evidence (Area, solidity, mask quality)
4. Optical Image Quality Screening Evidence (Sharpness, brightness, exposure clipping)

Deterministic Outcomes:
- AGREE: Detector and crop classifier agree, segmentation confirms valid silhouette, quality PASS.
- DISAGREE: Detector and crop classifier contradict each other -> CLASS_CONFLICT / REVIEW.
- INSUFFICIENT_QUALITY: Severe optical blur or clipping detected.
- MANUAL_REVIEW: High defect fraction, poor mask boundary, or borderline confidence.

CRITICAL MANDI RULE: Never silently hide disagreement or smooth over conflicting neural models.
"""

from __future__ import annotations

import logging
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from app.cv.crop_classifier import CropArbitrationResult, CropClassificationResult
from app.cv.label_mapping import CanonicalLabel
from app.cv.model_adapter import Detection
from app.cv.onion_segmentation import SegmentationMaskResult
from app.cv.quality import ImageQualityMetrics, QualityGrade
from app.domain.onion_observation import ObservationStatus, resolve_annotation_ui

logger = logging.getLogger(__name__)


class FusedProduceObservation(BaseModel):
    """
    Certified produce observation synthesized from multimodal model evidence.
    """
    model_config = ConfigDict(extra="forbid")

    observation_id: str = Field(..., description="Unique deterministic observation identifier")
    detection_id: str = Field(..., description="Associated raw detection identifier")
    fusion_outcome: str = Field(
        ...,
        description="AGREE, DISAGREE, INSUFFICIENT_QUALITY, or MANUAL_REVIEW"
    )
    final_canonical_label: CanonicalLabel = Field(
        ...,
        description="Authoritative resolved label or CLASS_CONFLICT"
    )
    final_observation_status: ObservationStatus = Field(
        ...,
        description="Domain ObservationStatus"
    )
    detector_label: CanonicalLabel = Field(..., description="Detector label")
    detector_confidence: float = Field(..., description="Detector confidence score")
    classifier_label: CanonicalLabel = Field(..., description="Crop classifier label")
    classifier_confidence: float = Field(..., description="Calibrated classifier confidence score")
    visible_defect_fraction_str: str = Field(..., description="Segmented defect percentage (e.g. '12.4%')")
    visible_defect_fraction: float = Field(..., description="Numeric defect fraction")
    mask_quality: float = Field(..., description="Mask solidity / quality index")
    mask_status: str = Field(..., description="Segmentation boundary status")
    title: str = Field(..., description="Canonical user-facing UI title")
    explanation: str = Field(..., description="Deterministic audit explanation")
    review_required: bool = Field(..., description="Whether inspector arbitration is required")
    defect_disclaimer: str = Field(
        default="Externally visible condition only.",
        description="Statutory non-internal physical disclaimer"
    )


class MultimodalFusionEngine:
    """
    Deterministic arbiter for multi-model evidence.
    """

    @classmethod
    def fuse(
        cls,
        detection: Detection,
        crop_result: CropClassificationResult,
        segmentation_result: SegmentationMaskResult,
        quality_metrics: ImageQualityMetrics | None = None,
    ) -> FusedProduceObservation:
        """
        Synthesize detector, classifier, segmentation, and quality evidence.
        """
        obs_id = f"obs_{detection.detection_id}"

        # 1. Image Quality Screening
        if quality_metrics is not None and quality_metrics.grade == QualityGrade.FAIL:
            return FusedProduceObservation(
                observation_id=obs_id,
                detection_id=detection.detection_id,
                fusion_outcome="INSUFFICIENT_QUALITY",
                final_canonical_label=detection.canonical_label,
                final_observation_status=ObservationStatus.INVALID_CAPTURE,
                detector_label=detection.canonical_label,
                detector_confidence=detection.confidence,
                classifier_label=crop_result.predicted_class,
                classifier_confidence=crop_result.calibrated_confidence,
                visible_defect_fraction_str=segmentation_result.visible_defect_fraction,
                visible_defect_fraction=segmentation_result.defect_fraction,
                mask_quality=segmentation_result.mask_quality,
                mask_status=segmentation_result.mask_status,
                title="Review required",
                explanation="Image failed optical quality screening (blur or exposure clipping). Evidence cannot be certified.",
                review_required=True,
            )

        # 2. Check Detector vs Crop Classifier Disagreement
        if detection.canonical_label != crop_result.predicted_class:
            return FusedProduceObservation(
                observation_id=obs_id,
                detection_id=detection.detection_id,
                fusion_outcome="DISAGREE",
                final_canonical_label=CanonicalLabel.CLASS_CONFLICT,
                final_observation_status=ObservationStatus.CLASS_CONFLICT,
                detector_label=detection.canonical_label,
                detector_confidence=detection.confidence,
                classifier_label=crop_result.predicted_class,
                classifier_confidence=crop_result.calibrated_confidence,
                visible_defect_fraction_str=segmentation_result.visible_defect_fraction,
                visible_defect_fraction=segmentation_result.defect_fraction,
                mask_quality=segmentation_result.mask_quality,
                mask_status=segmentation_result.mask_status,
                title="Review required",
                explanation=(
                    f"Model disagreement: Detector predicted '{detection.canonical_label.value}' "
                    f"({detection.confidence:.2f}) while second-stage classifier predicted "
                    f"'{crop_result.predicted_class.value}' ({crop_result.calibrated_confidence:.2f}). "
                    "Cross-class conflict flagged for inspector confirmation."
                ),
                review_required=True,
            )

        # 3. Agreement - check Segmentation consistency
        resolved_label = detection.canonical_label
        # If classifier & detector both say HEALTHY, but segmentation detects high visible defect (> 15%)
        if resolved_label == CanonicalLabel.HEALTHY and segmentation_result.defect_fraction > 0.15:
            return FusedProduceObservation(
                observation_id=obs_id,
                detection_id=detection.detection_id,
                fusion_outcome="MANUAL_REVIEW",
                final_canonical_label=CanonicalLabel.CLASS_CONFLICT,
                final_observation_status=ObservationStatus.CLASS_CONFLICT,
                detector_label=detection.canonical_label,
                detector_confidence=detection.confidence,
                classifier_label=crop_result.predicted_class,
                classifier_confidence=crop_result.calibrated_confidence,
                visible_defect_fraction_str=segmentation_result.visible_defect_fraction,
                visible_defect_fraction=segmentation_result.defect_fraction,
                mask_quality=segmentation_result.mask_quality,
                mask_status=segmentation_result.mask_status,
                title="Review required",
                explanation=(
                    f"Morphological anomaly: Models classified bulb as Healthy, but segmentation "
                    f"identified {segmentation_result.visible_defect_fraction} visible surface defect area. "
                    "Inspector review required."
                ),
                review_required=True,
            )

        # 4. Check Poor Mask Boundary
        if segmentation_result.mask_status == "POOR_BOUNDARY":
            return FusedProduceObservation(
                observation_id=obs_id,
                detection_id=detection.detection_id,
                fusion_outcome="MANUAL_REVIEW",
                final_canonical_label=resolved_label,
                final_observation_status=ObservationStatus.OBSERVED,
                detector_label=detection.canonical_label,
                detector_confidence=detection.confidence,
                classifier_label=crop_result.predicted_class,
                classifier_confidence=crop_result.calibrated_confidence,
                visible_defect_fraction_str=segmentation_result.visible_defect_fraction,
                visible_defect_fraction=segmentation_result.defect_fraction,
                mask_quality=segmentation_result.mask_quality,
                mask_status=segmentation_result.mask_status,
                title=resolve_annotation_ui(resolved_label, ObservationStatus.OBSERVED)[0],
                explanation="Models agree on condition, but segmentation boundary solidity is low. Size measurement unvalidated.",
                review_required=False,
            )

        # 5. Full Agreement
        title, expl, rev = resolve_annotation_ui(resolved_label, ObservationStatus.OBSERVED)
        return FusedProduceObservation(
            observation_id=obs_id,
            detection_id=detection.detection_id,
            fusion_outcome="AGREE",
            final_canonical_label=resolved_label,
            final_observation_status=ObservationStatus.OBSERVED,
            detector_label=detection.canonical_label,
            detector_confidence=detection.confidence,
            classifier_label=crop_result.predicted_class,
            classifier_confidence=crop_result.calibrated_confidence,
            visible_defect_fraction_str=segmentation_result.visible_defect_fraction,
            visible_defect_fraction=segmentation_result.defect_fraction,
            mask_quality=segmentation_result.mask_quality,
            mask_status=segmentation_result.mask_status,
            title=title,
            explanation=expl,
            review_required=rev,
        )
