"""
Production CV Inference Pipeline for Mandi Nyaay.

Connects:
1. Validated image ingestion (file path or numpy array)
2. Quality screening (Laplacian sharpness, brightness, clipped ratio)
3. Reference marker calibration evaluation (ArUco planar homography)
4. Detector execution (YOLO v7 model adapter)
5. Semantic domain mapping (CanonicalLabel)
6. Observation reconciliation (collapsing same-class duplicates and isolating cross-class conflicts)

Guarantees:
- Zero fake detections or simulated inferences
- Strong typed domain observations (OnionObservationRecord)
- Prevents double-counting physical produce items
- Explicit audit logging and error tracking
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from app.config.schema import MarkerConfig
from app.cv.label_mapping import (
    CanonicalLabel,
    MappingStatus,
    ModelClassMapping,
    V7_EXTERNAL_ADAPTER_MAPPING,
    V7_MAPPING_VARIANT_A,
    V7_MAPPING_VERIFIED,
)
from app.cv.marker import detect_marker
from app.cv.model_adapter import Detection, ModelMetadata, YOLOModelAdapter
from app.cv.observation_reconciliation import (
    DEFAULT_RECONCILIATION_IOU_THRESHOLD,
    reconcile_detections_to_observations,
)
from app.cv.quality import ImageQualityMetrics, QualityGrade, compute_image_quality
from app.domain.onion_observation import (
    ObservationProvenance,
    ObservationStatus,
    OnionObservationRecord,
    VisibilityStatus,
)
from app.domain.status import (
    CalibrationStatus,
    InspectionStatus,
    MeasurementStatus,
    OnionDiameterFeasibility,
)
from app.version import get_processing_version

logger = logging.getLogger(__name__)


class CVPipelineResult(BaseModel):
    """Unified auditable result emitted by Mandi Nyaay CV Pipeline."""
    model_config = ConfigDict(extra="forbid")

    pipeline_version: str = Field(
        default_factory=get_processing_version,
        description="Software pipeline version"
    )
    capture_id: str = Field(..., description="Unique session or capture identifier")
    image_path: str = Field(..., description="Source path of input image")
    image_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Physical file and image resolution metadata"
    )
    quality: ImageQualityMetrics | None = Field(
        default=None,
        description="Photometric and optical quality metrics"
    )
    raw_detection_count: int = Field(
        default=0,
        description="Raw bounding box detections emitted by model"
    )
    reconciled_observation_count: int = Field(
        default=0,
        description="Deduplicated physical produce observations"
    )
    conflict_count: int = Field(
        default=0,
        description="Count of cross-class conflicts detected"
    )
    detections: list[Detection] = Field(
        default_factory=list,
        description="Raw bounding box detections from underlying model"
    )
    observations: list[OnionObservationRecord] = Field(
        default_factory=list,
        description="Semantic domain observations formed from verified detections"
    )
    calibration_status: str = Field(
        default=CalibrationStatus.CALIBRATION_NOT_AVAILABLE.value,
        description="Physical reference marker calibration state"
    )
    measurement_status: MeasurementStatus = Field(
        default=MeasurementStatus.CALIBRATION_NOT_AVAILABLE,
        description="Physical metric measurement readiness"
    )
    onion_diameter_feasibility: str = Field(
        default=OnionDiameterFeasibility.ONION_DIAMETER_UNVALIDATED.value,
        description="Feasibility status of 3D bulb diameter estimation"
    )
    mapping_status: MappingStatus = Field(
        default=MappingStatus.UNVERIFIED,
        description="Overall class mapping verification state"
    )
    model_metadata: ModelMetadata | None = Field(
        default=None,
        description="Metadata of the detector checkpoint used"
    )
    pipeline_status: str = Field(
        default="SUCCESS",
        description="Execution state: SUCCESS, INVALID_CAPTURE, QUALITY_FAIL, QUALITY_WARN, ERROR"
    )
    limitations: list[str] = Field(
        default_factory=list,
        description="Explicit disclaimers regarding unverified thresholds or mapping ambiguities"
    )


class MandiNyaayCVPipeline:
    """
    Production-grade inference pipeline connecting validated image ingestion,
    quality screening, detector execution, semantic domain mapping, and
    cross-class observation reconciliation.
    """

    def __init__(
        self,
        checkpoint_path: Path | str,
        mapping: ModelClassMapping | None = None,
        conf_threshold: float = 0.25,
        min_reliable_confidence: float = 0.40,
        reconciliation_iou_threshold: float = DEFAULT_RECONCILIATION_IOU_THRESHOLD,
        marker_config: MarkerConfig | None = None,
    ):
        self.checkpoint_path = Path(checkpoint_path).resolve()
        self.mapping = mapping or V7_EXTERNAL_ADAPTER_MAPPING
        self.conf_threshold = conf_threshold
        self.min_reliable_confidence = min_reliable_confidence
        self.reconciliation_iou_threshold = reconciliation_iou_threshold
        self.marker_config = marker_config

        self._adapter: YOLOModelAdapter | None = None

    def _get_adapter(self) -> Any:
        if self._adapter is None:
            if str(self.checkpoint_path).endswith(".onnx"):
                from app.cv.onnx_adapter import ONNXModelAdapter
                self._adapter = ONNXModelAdapter(
                    model_path=self.checkpoint_path,
                    mapping=self.mapping,
                    conf_threshold=self.conf_threshold,
                )
            else:
                self._adapter = YOLOModelAdapter(
                    checkpoint_path=self.checkpoint_path,
                    mapping=self.mapping,
                    conf_threshold=self.conf_threshold,
                )
        return self._adapter

    def process_image(
        self,
        image_input: str | Path | np.ndarray,
        capture_id: str = "cap_0",
    ) -> CVPipelineResult:
        """
        Execute full pipeline over an image file path or numpy array.
        """
        limitations: list[str] = [
            "2D planar bounding boxes only; 3D height/elevation geometry is unmodeled.",
            "Defect and bulb classification subject to experimental class mapping validation.",
        ]

        # 1. Image Validation & Ingestion
        image_path_str = str(image_input) if isinstance(image_input, (str, Path)) else "in_memory_array"
        image_sha256 = "N/A"
        img: np.ndarray | None = None

        if isinstance(image_input, (str, Path)):
            p = Path(image_input).resolve()
            if not p.exists() or not p.is_file():
                return CVPipelineResult(
                    capture_id=capture_id,
                    image_path=image_path_str,
                    image_metadata={"error": "File does not exist"},
                    raw_detection_count=0,
                    reconciled_observation_count=0,
                    conflict_count=0,
                    pipeline_status="INVALID_CAPTURE",
                    limitations=limitations,
                )
            try:
                hasher = hashlib.sha256()
                with open(p, "rb") as f:
                    while chunk := f.read(65536):
                        hasher.update(chunk)
                image_sha256 = hasher.hexdigest()
            except Exception as e:
                logger.warning(f"Could not compute sha256: {e}")

            img = cv2.imread(str(p))
            if img is None:
                return CVPipelineResult(
                    capture_id=capture_id,
                    image_path=image_path_str,
                    image_metadata={"error": "Failed to decode image file"},
                    raw_detection_count=0,
                    reconciled_observation_count=0,
                    conflict_count=0,
                    pipeline_status="INVALID_CAPTURE",
                    limitations=limitations,
                )
        elif isinstance(image_input, np.ndarray):
            if image_input.size == 0:
                return CVPipelineResult(
                    capture_id=capture_id,
                    image_path=image_path_str,
                    image_metadata={"error": "Empty numpy array"},
                    raw_detection_count=0,
                    reconciled_observation_count=0,
                    conflict_count=0,
                    pipeline_status="INVALID_CAPTURE",
                    limitations=limitations,
                )
            img = image_input.copy()
            image_sha256 = hashlib.sha256(img.tobytes()).hexdigest()
        else:
            return CVPipelineResult(
                capture_id=capture_id,
                image_path=image_path_str,
                image_metadata={"error": "Unsupported input type"},
                raw_detection_count=0,
                reconciled_observation_count=0,
                conflict_count=0,
                pipeline_status="INVALID_CAPTURE",
                limitations=limitations,
            )

        height, width = img.shape[:2]
        channels = img.shape[2] if len(img.shape) > 2 else 1
        img_meta = {
            "width": width,
            "height": height,
            "channels": channels,
            "sha256": image_sha256,
        }

        # 2. Real Image Quality Assessment
        quality_metrics = compute_image_quality(img)

        pipeline_status = "SUCCESS"
        if quality_metrics.grade == QualityGrade.FAIL:
            pipeline_status = "QUALITY_FAIL"
            limitations.append("Image quality failed baseline sharpness/exposure criteria. Detections may be distorted.")
        elif quality_metrics.grade == QualityGrade.WARN:
            pipeline_status = "QUALITY_WARN"
            limitations.append("Image quality has warnings (blur or clipping). Proceed with manual inspection review.")

        # 3. Reference Marker & Calibration Check
        calib_status = CalibrationStatus.CALIBRATION_NOT_AVAILABLE.value
        meas_status = MeasurementStatus.CALIBRATION_NOT_AVAILABLE
        if self.marker_config is not None:
            marker_obs = detect_marker(img, self.marker_config)
            if marker_obs.status == InspectionStatus.VALID:
                calib_status = CalibrationStatus.PLANAR_METRIC_CALIBRATION_VALIDATED.value
                meas_status = MeasurementStatus.PLANAR_MEASUREMENT_AVAILABLE
            else:
                calib_status = CalibrationStatus.CALIBRATION_INVALID.value
                meas_status = MeasurementStatus.CALIBRATION_INVALID
        else:
            limitations.append("Physical calibration marker not configured or detected; metric millimetres unavailable.")

        # 4. Detector Execution via Adapter
        adapter = self._get_adapter()
        detections = adapter.predict(img, capture_id=capture_id)
        model_meta = adapter.metadata

        # 5. Observation Reconciliation (Prevents Double-Counting and Reconciles Conflicts)
        observations, summary = reconcile_detections_to_observations(
            detections=detections,
            capture_id=capture_id,
            iou_threshold=self.reconciliation_iou_threshold,
            min_reliable_confidence=self.min_reliable_confidence,
            model_checkpoint=str(self.checkpoint_path.name),
            measurement_status=meas_status,
        )

        if summary.conflict_count > 0:
            limitations.append(
                f"{summary.conflict_count} cross-class detection conflict(s) detected and retained as CLASS_CONFLICT for review."
            )

        current_mapping_status = self.mapping.status if self.mapping else MappingStatus.UNVERIFIED
        if current_mapping_status != MappingStatus.VERIFIED:
            limitations.append(f"Class mapping status is '{current_mapping_status.value}'. Semantic labels require controlled experimental confirmation.")

        return CVPipelineResult(
            capture_id=capture_id,
            image_path=image_path_str,
            image_metadata=img_meta,
            quality=quality_metrics,
            raw_detection_count=summary.raw_detection_count,
            reconciled_observation_count=summary.reconciled_observation_count,
            conflict_count=summary.conflict_count,
            detections=detections,
            observations=observations,
            calibration_status=calib_status,
            measurement_status=meas_status,
            onion_diameter_feasibility=OnionDiameterFeasibility.ONION_DIAMETER_UNVALIDATED.value,
            mapping_status=current_mapping_status,
            model_metadata=model_meta,
            pipeline_status=pipeline_status,
            limitations=limitations,
        )
