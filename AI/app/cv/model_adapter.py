"""
Model Adapter for Ultralytics YOLO Object Detectors.

Wraps real YOLO models with domain-safe inspection contracts:
- Validates task == 'detect'
- Extracts genuine model metadata
- Maps raw class IDs to CanonicalLabel via explicit ModelClassMapping
- Guarantees zero fake detections or synthetic confidence
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any
import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from app.cv.label_mapping import (
    CanonicalLabel,
    MappingStatus,
    ModelClassMapping,
    convert_model_class_id,
)

logger = logging.getLogger(__name__)


class Detection(BaseModel):
    """Structured detection observation produced by the model adapter."""
    model_config = ConfigDict(extra="forbid")

    detection_id: str = Field(..., description="Unique deterministic identifier for this detection")
    class_id_external: int = Field(..., description="Raw integer class ID emitted by checkpoint")
    class_name_external: str = Field(..., description="Class name string registered in checkpoint")
    canonical_label: CanonicalLabel = Field(
        default=CanonicalLabel.UNKNOWN_MAPPING,
        description="Resolved semantic canonical label"
    )
    mapping_status: MappingStatus = Field(
        default=MappingStatus.UNVERIFIED,
        description="Status of mapping resolution"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Raw model confidence score")
    x1: float = Field(..., description="Bounding box top-left X coordinate in pixels")
    y1: float = Field(..., description="Bounding box top-left Y coordinate in pixels")
    x2: float = Field(..., description="Bounding box bottom-right X coordinate in pixels")
    y2: float = Field(..., description="Bounding box bottom-right Y coordinate in pixels")
    width_px: float = Field(..., description="Bounding box width in pixels")
    height_px: float = Field(..., description="Bounding box height in pixels")


class ModelMetadata(BaseModel):
    """Metadata extracted directly from the loaded model artifact."""
    model_config = ConfigDict(extra="forbid")

    checkpoint_path: str
    task: str
    architecture: str
    classes_exposed: dict[int, str]
    num_classes: int


class YOLOModelAdapter:
    """
    Adapter around Ultralytics YOLO detection models.
    """

    def __init__(
        self,
        checkpoint_path: Path | str,
        mapping: ModelClassMapping | None = None,
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.45,
    ):
        self.checkpoint_path = Path(checkpoint_path).resolve()
        self.mapping = mapping
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self._model = None
        self._metadata: ModelMetadata | None = None

        self._load_and_validate()

    def _load_and_validate(self) -> None:
        """Load model and strictly validate task compatibility."""
        if not self.checkpoint_path.exists():
            raise FileNotFoundError(f"Model checkpoint not found at: {self.checkpoint_path}")

        try:
            from ultralytics import YOLO
        except ImportError as e:
            raise ImportError(
                "Ultralytics package is not installed. Run `uv pip install ultralytics`"
            ) from e

        self._model = YOLO(str(self.checkpoint_path))

        # Validate task
        task = getattr(self._model, "task", None)
        if task != "detect":
            raise ValueError(
                f"Invalid model task: expected 'detect', found '{task}'. "
                "Only detection models are supported by this adapter."
            )

        names = getattr(self._model, "names", {})
        if isinstance(names, list):
            names_dict = {i: name for i, name in enumerate(names)}
        elif isinstance(names, dict):
            names_dict = {int(k): str(v) for k, v in names.items()}
        else:
            names_dict = {}

        arch = str(type(self._model.model).__name__) if hasattr(self._model, "model") else "Unknown"

        self._metadata = ModelMetadata(
            checkpoint_path=str(self.checkpoint_path),
            task=task,
            architecture=arch,
            classes_exposed=names_dict,
            num_classes=len(names_dict),
        )

    @property
    def metadata(self) -> ModelMetadata:
        """Return genuine metadata of the underlying checkpoint."""
        if self._metadata is None:
            self._load_and_validate()
        assert self._metadata is not None
        return self._metadata

    def predict(
        self,
        image: np.ndarray | Path | str,
        capture_id: str = "capture_0",
    ) -> list[Detection]:
        """
        Run inference on a single image and return structured detections.
        """
        if self._model is None:
            self._load_and_validate()
        assert self._model is not None

        # Execute genuine prediction
        results = self._model.predict(
            source=image,
            conf=self.conf_threshold,
            iou=self.iou_threshold,
            verbose=False,
        )

        detections: list[Detection] = []
        if not results:
            return detections

        first_res = results[0]
        boxes = first_res.boxes
        if boxes is None or len(boxes) == 0:
            return detections

        xyxy = boxes.xyxy.cpu().numpy()
        confs = boxes.conf.cpu().numpy()
        cls_ids = boxes.cls.cpu().numpy().astype(int)
        names = self.metadata.classes_exposed

        for idx, (box, conf, cid) in enumerate(zip(xyxy, confs, cls_ids)):
            x1, y1, x2, y2 = [float(v) for v in box]
            w = max(0.0, x2 - x1)
            h = max(0.0, y2 - y1)
            cname = names.get(cid, f"class_{cid}")

            # Map raw class ID to CanonicalLabel
            # If mapping is not verified or unassigned, returns UNKNOWN_MAPPING
            canonical_label, map_status = convert_model_class_id(
                class_id=cid,
                mapping=self.mapping,
                raw_class_name=cname,
            )

            detections.append(Detection(
                detection_id=f"{capture_id}_det_{idx}",
                class_id_external=int(cid),
                class_name_external=cname,
                canonical_label=canonical_label,
                mapping_status=map_status,
                confidence=round(float(conf), 4),
                x1=round(x1, 2),
                y1=round(y1, 2),
                x2=round(x2, 2),
                y2=round(y2, 2),
                width_px=round(w, 2),
                height_px=round(h, 2),
            ))

        return detections
