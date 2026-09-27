"""
Pure ONNX Runtime Model Adapter for Mandi Nyaay.

Executes genuine on-device object detection using Microsoft ONNX Runtime:
- Letterbox image preprocessing (640x640, BGR->RGB, normalized to [0, 1])
- Pure onnxruntime InferenceSession execution
- Raw tensor decoding from [1, 8, 8400] (4 box coords + 4 class scores)
- De-letterbox spatial coordinate transformation
- Non-Maximum Suppression (cv2.dnn.NMSBoxes)
- Explicit canonical semantic mapping (0: HEALTHY, 1: DAMAGED, 2: SPROUTED, 3: ROTTEN)
- Zero fake metrics or invented confidence

This adapter runs in standard Python environments and represents the exact
tensor processing pipeline implemented on Android with onnxruntime-mobile.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Sequence
import cv2
import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from app.cv.label_mapping import (
    CanonicalLabel,
    MappingStatus,
    ModelClassMapping,
    convert_model_class_id,
    V7_MAPPING_VERIFIED,
)
from app.cv.model_adapter import Detection, ModelMetadata

logger = logging.getLogger(__name__)


def letterbox_image(
    image: np.ndarray,
    target_shape: tuple[int, int] = (640, 640),
    fill_color: tuple[int, int, int] = (114, 114, 114),
) -> tuple[np.ndarray, float, tuple[float, float]]:
    """
    Letterbox pad an image to target_shape while preserving aspect ratio.

    Returns:
        padded_image, scale_ratio, (pad_left, pad_top)
    """
    orig_h, orig_w = image.shape[:2]
    target_h, target_w = target_shape

    scale = min(target_h / orig_h, target_w / orig_w)
    new_w = int(round(orig_w * scale))
    new_h = int(round(orig_h * scale))

    pad_w = (target_w - new_w) / 2.0
    pad_h = (target_h - new_h) / 2.0

    top = int(round(pad_h - 0.1))
    bottom = int(round(pad_h + 0.1))
    left = int(round(pad_w - 0.1))
    right = int(round(pad_w + 0.1))

    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    padded = cv2.copyMakeBorder(
        resized, top, bottom, left, right, cv2.BORDER_CONSTANT, value=fill_color
    )
    return padded, scale, (pad_w, pad_h)


class ONNXModelAdapter:
    """
    Mobile-parity ONNX Runtime detector adapter for YOLO26/v7 models.
    """

    def __init__(
        self,
        model_path: Path | str,
        mapping: ModelClassMapping | None = None,
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.45,
        target_size: tuple[int, int] = (640, 640),
    ):
        self.model_path = Path(model_path).resolve()
        self.mapping = mapping or V7_MAPPING_VERIFIED
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self.target_size = target_size
        self._session = None
        self._metadata: ModelMetadata | None = None
        self._input_name: str = "images"
        self._output_name: str = "output0"

        self._load_session()

    def _load_session(self) -> None:
        """Initialize ONNX Runtime inference session."""
        if not self.model_path.exists():
            raise FileNotFoundError(f"ONNX model file not found at: {self.model_path}")

        import onnxruntime as ort

        # Create session with standard CPU provider
        opts = ort.SessionOptions()
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        self._session = ort.InferenceSession(str(self.model_path), sess_options=opts)

        inputs = self._session.get_inputs()
        outputs = self._session.get_outputs()

        if inputs:
            self._input_name = inputs[0].name
        if outputs:
            self._output_name = outputs[0].name

        # Standard canonical class names for v7 onion model
        names_dict = {
            0: "healthy",
            1: "damaged",
            2: "sprouted",
            3: "rotten",
        }

        self._metadata = ModelMetadata(
            checkpoint_path=str(self.model_path),
            task="detect",
            architecture="YOLO26n-ONNX",
            classes_exposed=names_dict,
            num_classes=len(names_dict),
        )

    @property
    def metadata(self) -> ModelMetadata:
        """Return model metadata."""
        if self._metadata is None:
            self._load_session()
        assert self._metadata is not None
        return self._metadata

    def predict(
        self,
        image: np.ndarray | Path | str,
        capture_id: str = "capture_0",
    ) -> list[Detection]:
        """
        Execute ONNX inference and post-processing on an image.

        Args:
            image: BGR numpy image or filesystem path
            capture_id: Identifier for source capture

        Returns:
            List of structured Detection objects
        """
        if self._session is None:
            self._load_session()
        assert self._session is not None

        if isinstance(image, (str, Path)):
            img_bgr = cv2.imread(str(image))
            if img_bgr is None:
                raise ValueError(f"Could not read image from path: {image}")
        else:
            img_bgr = image

        orig_h, orig_w = img_bgr.shape[:2]

        # 1. Letterbox preprocessing
        padded_bgr, scale, (pad_w, pad_h) = letterbox_image(
            img_bgr, target_shape=self.target_size
        )

        # 2. Color conversion & float normalization
        rgb = cv2.cvtColor(padded_bgr, cv2.COLOR_BGR2RGB)
        input_tensor = rgb.astype(np.float32) / 255.0
        # HWC -> CHW -> NCHW
        input_tensor = np.transpose(input_tensor, (2, 0, 1))[np.newaxis, ...]

        # 3. ONNX Runtime execution
        outputs = self._session.run([self._output_name], {self._input_name: input_tensor})
        raw_output = outputs[0]  # Shape: (1, 8, 8400) or similar

        # 4. Post-processing: decode boxes and scores
        # Output tensor layout: (1, 8, 8400) -> transpose to (8400, 8)
        preds = np.transpose(raw_output[0], (1, 0))

        boxes: list[list[float]] = []
        confidences: list[float] = []
        class_ids: list[int] = []

        for row in preds:
            cx, cy, w, h = row[:4]
            scores = row[4:]
            cid = int(np.argmax(scores))
            conf = float(scores[cid])

            if conf >= self.conf_threshold:
                # Convert center-xywh to top-left xywh in original unpadded image space
                x1 = (cx - w / 2.0 - pad_w) / scale
                y1 = (cy - h / 2.0 - pad_h) / scale
                bw = w / scale
                bh = h / scale

                # Clip to image boundaries
                x1 = max(0.0, min(float(orig_w), x1))
                y1 = max(0.0, min(float(orig_h), y1))
                bw = max(0.0, min(float(orig_w) - x1, bw))
                bh = max(0.0, min(float(orig_h) - y1, bh))

                if bw > 0 and bh > 0:
                    boxes.append([x1, y1, bw, bh])
                    confidences.append(conf)
                    class_ids.append(cid)

        # 5. Non-Maximum Suppression
        indices = cv2.dnn.NMSBoxes(
            boxes, confidences, self.conf_threshold, self.iou_threshold
        )

        detections: list[Detection] = []
        names = self.metadata.classes_exposed

        for det_idx, idx in enumerate(indices):
            i = int(idx if isinstance(idx, (int, np.integer)) else idx[0])
            bx = boxes[i]
            conf = confidences[i]
            cid = class_ids[i]
            cname = names.get(cid, f"class_{cid}")

            x1 = bx[0]
            y1 = bx[1]
            x2 = bx[0] + bx[2]
            y2 = bx[1] + bx[3]

            canonical_label, map_status = convert_model_class_id(
                class_id=cid,
                mapping=self.mapping,
                raw_class_name=cname,
            )

            detections.append(
                Detection(
                    detection_id=f"{capture_id}_det_{det_idx}",
                    class_id_external=cid,
                    class_name_external=cname,
                    canonical_label=canonical_label,
                    mapping_status=map_status,
                    confidence=round(float(conf), 4),
                    x1=round(float(x1), 2),
                    y1=round(float(y1), 2),
                    x2=round(float(x2), 2),
                    y2=round(float(y2), 2),
                    width_px=round(float(bx[2]), 2),
                    height_px=round(float(bx[3]), 2),
                )
            )

        return detections
