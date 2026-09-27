# THIRD-PARTY SOFTWARE NOTICES & RESOURCE ATTRIBUTION

**Project:** Mandi Nyaay AI Core  
**Standard:** Open-Source Compliance & Anti-Fabrication Governance  
**Date:** 2026-09-25  

This document provides explicit licensing, provenance, and attribution notices for all external libraries, datasets, models, and reference repositories inspected or utilized during the build of Mandi Nyaay.

---

## 1. Primary Runtime Components

### 1.1 Microsoft ONNX Runtime
- **Repository**: [https://github.com/microsoft/onnxruntime](https://github.com/microsoft/onnxruntime)
- **License**: MIT License
- **Pinned Version**: `1.30.0` (Python runtime) / `onnxruntime-android:1.18.0+` (Android deployment target)
- **Purpose**: Primary on-device neural network inference engine for YOLO26/v7 models on mobile (Android) and desktop/edge verification.
- **Files/Functions Reused**:
  - `onnxruntime.InferenceSession`
  - `SessionOptions.graph_optimization_level`
  - Input tensor feed and raw tensor output extraction
- **Modifications**: None (used via standard binary distribution).
- **Runtime/Build Impact**: 13.6 MB runtime package; zero cloud dependency; executes fully offline on local CPU.
- **MANDI NYAAY-Owned Logic**:
  - Image preprocessing (`letterbox_image`, aspect-ratio preserving padding, BGR->RGB normalization).
  - Raw output tensor decoding (`[1, 8, 8400]` box spatial de-padding and confidence extraction).
  - Canonical semantic class remapping and confidence thresholding (`app/cv/onnx_adapter.py`).

### 1.2 OpenCV (Open Source Computer Vision Library)
- **Repository**: [https://github.com/opencv/opencv](https://github.com/opencv/opencv)
- **License**: Apache License 2.0
- **Pinned Version**: `opencv-python==5.0.0.93` (Desktop) / `opencv-mobile` or official OpenCV Android SDK
- **Purpose**: Image loading, color conversion, ArUco fiducial detection, projective planar homography, metric coordinate transformation, Non-Maximum Suppression (`cv2.dnn.NMSBoxes`), and optical quality screening (Laplacian sharpness).
- **Files/Functions Reused**:
  - `cv2.resize`, `cv2.copyMakeBorder`, `cv2.cvtColor`
  - `cv2.aruco.ArucoDetector`, `cv2.aruco.getPredefinedDictionary`
  - `cv2.getPerspectiveTransform`, `cv2.perspectiveTransform`
  - `cv2.Laplacian` (variance calculation for blur scoring)
  - `cv2.dnn.NMSBoxes`
- **Modifications**: None.
- **Runtime/Build Impact**: Primary CV foundation; deterministic execution.
- **MANDI NYAAY-Owned Logic**:
  - Homography reprojection residual auditing and drift detection (`app/cv/calibration.py`).
  - Planar vs 3D measurement limitation boundaries and legal disclaimers.
  - Exposure clipping and quality status determination (`app/cv/quality.py`).

---

## 2. Model & Baseline Dataset Provenance

### 2.1 Onion Grading Baseline Model (`onion-grading-v7.pt` / `onion-grading-v7.onnx`)
- **Repository**: [https://github.com/kanth071/Onion_grading_system](https://github.com/kanth071/Onion_grading_system)
- **License**: Unresolved / Academic Reference (Treated as uncertified research artifact under Mandi Nyaay governance).
- **Pinned Checkpoint**: `onion-grading-v7.pt` (SHA256: `0a0e62e9aa3608c75c0ccbb7870df3525dc95bd8fa532591f9f026d1a3a6a736`)
- **Exported ONNX Model**: `onion-grading-v7.onnx` (SHA256: `f8073eeed9a6becef4bb8a6949261058a57a4373ea256a8ff1b5c913eb1d4079`)
- **Architecture**: YOLO26n (120 layers, 2,375,616 parameters, 5.3 GFLOPs).
- **Semantic Class Mapping**:
  - `0`: `HEALTHY`
  - `1`: `DAMAGED`
  - `2`: `SPROUTED`
  - `3`: `ROTTEN`
- **Governance Status**:
  - Verified by Mandi Nyaay Gate 4A via source-code forensics (`evaluate_model.py`, `finetune_from_photos.py`) and visual adjudication.
  - **NON-CERTIFICATION NOTICE**: This model is a development baseline. It is NOT government-certified or certified for statutory APMC grading without formal field trials.
- **MANDI NYAAY-Owned Logic**:
  - Complete post-processing, cross-class observation reconciliation (`reconcile_detections_to_observations`), SampleUnit denominator binding, and procurement decision logic.
  - Neural detector is strictly isolated from grading policy; detector NEVER emits final grades.

---

## 3. Explicitly Excluded Components (Shipping Prohibitions)

### 3.1 Ultralytics YOLO Flutter App
- **Repository**: `https://github.com/ultralytics/yolo-flutter-app`
- **License**: AGPL-3.0
- **Status**: **STRICTLY EXCLUDED FROM SHIPPING**.
- **Reason**: AGPL-3.0 licensing constraints are incompatible with the deployment architecture. Inspected solely as high-level architectural reference; ZERO lines of code or assets imported.

---

## 4. Reference Only Resources (No Code Borrowed)

1. **Microsoft ONNX Runtime Inference Examples** (`microsoft/onnxruntime-inference-examples`)
   - License: MIT
   - Role: Android ONNX tensor passing pattern reference.

2. **Google LiteRT Samples** (`google-ai-edge/litert-samples`)
   - License: Apache-2.0
   - Role: Secondary mobile fallback reference (held in reserve; ONNX Runtime is primary).

3. **Tencent NCNN & AlertCat Android YOLO26** (`Tencent/ncnn`, `alertcat/ncnn-android-yolo26`)
   - License: BSD-3-Clause / MIT
   - Role: Tertiary mobile fallback reference only.

4. **Agricultural Tracking Reference** (`Computer-Vision-and-Robotic-Perception/ag-tracking`)
   - Role: Spatial association reference only. Mandi Nyaay uses physical tray cell indexing (`A1..D5`) rather than speculative visual tracking.

5. **VideoFruitCounting** (`imatge-upc/VideoFruitCounting`)
   - Role: Algorithmic counting reference only.

6. **Smart Produce Inspection System** (`husseinnsanzi/smart-produce-inspection-system`)
   - Role: Produce inspection UX reference only.

7. **ArUco Size & Calibration References** (`Ali619/Object-Detection-Size-Measurement`, `takuya-ki/aruco-camera-calib`)
   - Role: Fiducial geometry reference. Planar limitations explicitly enforced in Mandi Nyaay.

8. **AK SW Benchmarker** (`GRAP-UdL-AT/ak_sw_benchmarker`)
   - Role: RGB-D produce sizing literature reference.

---

## 5. Audited, Evaluated & Integrated Intelligence Stack (2026-09-26 Acceleration)

### 5.1 MAPIE (Model Agnostic Prediction Interval Estimator)
- **Repository**: [https://github.com/scikit-learn-contrib/MAPIE](https://github.com/scikit-learn-contrib/MAPIE)
- **License**: BSD 3-Clause License
- **Pinned Version**: `1.5.0`
- **Purpose**: Conformal prediction intervals for produce mass estimation; outputs certified distribution-free prediction bounds ($[W_{\text{low}}, W_{\text{high}}]$) at specified coverage (e.g. 90%).
- **Files Reused**: `mapie.regression.MapieRegressor` / split conformal nonconformity score quantile calculation.
- **Runtime Impact**: Minimal CPU overhead (<2ms); deterministic coverage guarantee.

### 5.2 statsmodels
- **Repository**: [https://github.com/statsmodels/statsmodels](https://github.com/statsmodels/statsmodels)
- **License**: BSD 3-Clause License
- **Pinned Version**: `0.15.0`
- **Purpose**: Authoritative Wilson score confidence intervals for defect proportions with finite population correction (FPC).
- **Files Reused**: `statsmodels.stats.proportion.proportion_confint(count, nobs, method='wilson')`.
- **Runtime Impact**: Zero model overhead; instant algebraic evaluation.

### 5.3 segmentation_models.pytorch
- **Repository**: [https://github.com/qubvel-org/segmentation_models.pytorch](https://github.com/qubvel-org/segmentation_models.pytorch)
- **License**: MIT License
- **Pinned Version**: `0.5.0`
- **Purpose**: High-capacity U-Net architecture exploration and backbone benchmark (MobileNetV2, ResNet) for produce silhouette and defect segmentation.
- **Runtime Comparison**: Benchmark evaluated against embedded `CompactUNet` (1.09 MB, 69 ms CPU) vs `smp.Unet` (25.29 MB, 148 ms CPU).

### 5.4 Bulb-Onion-Size-Classification-and-Mass-Estimation (marbrickaustria)
- **Repository**: [https://github.com/marbrickaustria/Bulb-Onion-Size-Classification-and-Mass-Estimation](https://github.com/marbrickaustria/Bulb-Onion-Size-Classification-and-Mass-Estimation)
- **License**: Unspecified (Empty placeholder repo)
- **Commit Audited**: `2f9fa69b88f40c334d118146f43bbc9959d5cf4a`
- **Audit Findings**: Repository contains only an initial 3-line README describing intent; contains ZERO code, ZERO model weights, ZERO datasets. No usable software artifacts exist upstream.

### 5.5 MobileSAM
- **Repository**: [https://github.com/ChaoningZhang/MobileSAM](https://github.com/ChaoningZhang/MobileSAM)
- **License**: Apache License 2.0
- **Role**: Development dataset annotation assistance pipeline (`bbox -> candidate mask -> human verification -> ground truth`). Excluded from runtime critical path.

### 5.6 License-Clean Detectors Benchmark Track
- **YOLOX** (Megvii, Apache-2.0, commit `ac58b09d`): Top candidate for edge replacement (0.91M params, 3.9MB, 11ms CPU).
- **RF-DETR** (Roboflow, Apache-2.0, commit `7e83df4`): Transformer query architecture for dense-pile resolution.
- **RTMDet** (OpenMMLab, Apache-2.0, commit `e4b51a9`): Real-time detector candidate.

