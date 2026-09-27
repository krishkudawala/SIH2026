# Mandi Nyaay AI — Gate 1 Readiness Audit Report

**Status**: `GATE_1 = READY_FOR_FIELD_VALIDATION`  
*(NOT `GATE_1 = VALIDATED` — real field validation begins only after physical captures and physical ground truth are processed).*

---

## 1. ArUco Implementation Status

* **Source File & Functions**:
  * [`app/cv/marker.py`](file:///c:/Users/S/OneDrive/Desktop/AI/app/cv/marker.py):
    * `detect_marker(image: np.ndarray, config: MarkerConfig) -> MarkerObservation`
    * `validate_marker_geometry(pts: np.ndarray, image_shape, min_perimeter_px) -> tuple`
    * `save_marker_debug_visualization(image: np.ndarray, observation, output_path) -> Path`
  * [`scripts/run_gate1_validation.py`](file:///c:/Users/S/OneDrive/Desktop/AI/scripts/run_gate1_validation.py):
    * `main()`
* **Verification Findings**:
  * **Image Pixels Loaded**: Yes. Loaded via `cv2.imread(str(image_path))`; image array presence, non-emptiness, and shape are validated before execution.
  * **OpenCV ArUco Execution**: Yes. `cv2.aruco.ArucoDetector(dictionary, parameters).detectMarkers(image)` executes on the actual image matrix.
  * **Marker ID**: Sourced directly from detector output (`flat_ids = [int(i[0]) for i in ids]`).
  * **Corner Coordinates**: Four actual sub-pixel corners extracted directly from OpenCV detector output (`corners_list[0][0]`).
  * **Hardcoded Coordinates**: None. All corner arrays and pixel coordinates originate from the detector.
  * **Fabricated Numeric Output**: None. If no marker is detected, the system outputs `CALIBRATION_INVALID` with `failure_code: MARKER_NOT_DETECTED`.

---

## 2. Homography Implementation Status

* **Source File & Functions**:
  * [`app/cv/calibration.py`](file:///c:/Users/S/OneDrive/Desktop/AI/app/cv/calibration.py):
    * `compute_marker_homography(corners_px, physical_size_mm) -> tuple[np.ndarray, float, float]`
    * `transform_points_to_metric_plane(points_px, H) -> np.ndarray`
    * `measure_planar_distance_mm(pt1_px, pt2_px, H) -> float`
    * `measure_planar_contour_mm(contour_px, H) -> dict`
* **Verification Findings**:
  * **Homography Computation**: Projective transformation matrix $H$ ($3 \times 3$) is computed from the 4 actual detected corners to the physical marker coordinates $[(0,0), (S,0), (S,S), (0,S)]$ mm using `cv2.getPerspectiveTransform(pts_src, pts_dst)`.
  * **Reprojection Residual**: Computed directly from geometry. The metric corners are back-projected through $H^{-1}$ into image space, and the RMS Euclidean residual distance to the detected corners is calculated.
  * **Planar Measurements**: Measurements transform pixel coordinates via $H$ into metric millimetres on the reference plane.
  * **Diagnostic Scale**: Simple $\text{mm}/\text{px}$ division is strictly categorized as `diagnostic_scale_mm_per_px` for diagnostic sanity checking; it is **not** used as the primary measurement architecture.
  * **Strict Boundary Classification**: Explicitly classified as `PLANAR_METRIC_MEASUREMENT` with mandatory disclaimer: *"Measurement valid strictly on reference marker plane. Does NOT establish 3D object height or elevation-corrected dimensions."*

---

## 3. Reference Object Pipeline Status

* **Audit Finding**:
  * **Automatic Reference Object Detection**: `REFERENCE_OBJECT_DETECTION = NOT_IMPLEMENTED`.
  * **Rationale**: Automatic segmentation of an arbitrary reference object (e.g. coin or disc) under variable ambient mandi lighting and textured backgrounds without a dedicated trained localizer is brittle and unvalidated.
* **Gate 1 Workflow Correction**:
  * The fragile heuristic (`detect_circular_reference_candidate`) has been removed from the active Gate 1 verification flow.
  * If the operator supplies `--reference-ground-truth-mm` without explicit coordinate points, the pipeline reports `reference_object_detection: NOT_IMPLEMENTED`.
  * If the operator provides manual pixel endpoints via `--reference-points-px x1,y1,x2,y2`, the pipeline measures the metric distance between those points using the homography $H$ and evaluates against caliper ground truth.
  * The system makes zero false claims of automatic reference object segmentation.

---

## 4. Physical Ground-Truth Input Status

* **Caliper Marker Side Length**:
  * Parameter `--caliper-marker-mm` is **strictly required** in `run_gate1_validation.py`.
  * If omitted, the CLI aborts with exit code 1:
    `error: the following arguments are required: --caliper-marker-mm`
  * Nominal size ($50.0\text{ mm}$) is **never** silently substituted for the printed marker.
* **Reference Object Ground Truth**:
  * Parameter `--reference-ground-truth-mm` accepts the caliper-measured dimension in millimetres.
  * If absent, relative error metrics are omitted; no guessed ground truth is substituted.

---

## 5. No-Dummy Audit

Comprehensive inventory of non-dynamic values across the repository:

| File | Location | Content | Audit Classification | Action / Status |
|---|---|---|---|---|
| `configs/inspection_config.yaml` | Lines 10–27 | `physical_size_mm: 50.0`, `min_laplacian_variance: 100.0`, thresholds | **CONFIGURATION** | Valid. Tagged explicitly as `EXPERIMENTAL`. Overridden at runtime by CLI `--caliper-marker-mm`. |
| `app/version.py` | Line 10 | `PROCESSING_VERSION = "0.1.0-phase0.dev"` | **CONFIGURATION** | Valid. Immutable version string for observation provenance. |
| `app/cv/marker.py` | Line 18 | `MAX_SIDE_RATIO_THRESHOLD = 3.0` | **PRODUCTION CODE** | Valid. Mathematical geometric sanity bound to reject collapsed quadrilaterals. |
| `tests/test_domain_contracts.py` | Lines 25–95 | `capture_id="cap-001"`, `marker_id=42`, `corners_px=[(10,10)...]` | **VALID TEST FIXTURE** | Unit test fixtures for schema validation. Confined strictly to `tests/`. |
| `tests/test_serialization.py` | Lines 20–60 | `capture_id="cap-ser-1"`, synthetic corner tuples | **VALID TEST FIXTURE** | JSON roundtrip tests. Confined strictly to `tests/`. |
| `tests/test_homography_calibration.py` | Lines 18–80 | Synthetic 100px and 200px square corners, 40mm contour | **VALID TEST FIXTURE** | Mathematical verification of homography transforms and area math. Confined strictly to `tests/`. |
| `tests/test_marker_detection.py` | Lines 120–170 | Mocked detector returning ID 99 or multiple IDs | **VALID TEST FIXTURE** | Monkeypatched detector tests to verify status state machine. Confined strictly to `tests/`. |
| `scripts/generate_printable_marker.py` | Lines 1–55 | Generates printable ArUco PNG for physical printing | **UTILITY** | Header explicitly states: *For printer/reference generation only. Never use as synthetic field data.* |

**Audit Conclusion**: No production code consumes hardcoded measurements, synthetic coordinates, or mocked field evidence.

---

## 6. Test Status

* **Execution Command**: `.venv\Scripts\python -m pytest -v`
* **Test Outcome**: **28 passed, 1 skipped in 0.56s**
* **Classification**: **FOUNDATION / IMPLEMENTATION VERIFIED**.
  *(All 28 passing tests verify software contract enforcement, serialization fidelity, failure state transitions, and homography linear algebra. They do not constitute field accuracy).*

---

## 7. What Can Be Verified Without Field Data

1. Proper loading, validation, and decoding of image files via OpenCV.
2. OpenCV ArUco detector invocation and sub-pixel corner extraction.
3. Geometric rejection of non-convex, out-of-bounds, or skewed candidate quadrilaterals.
4. Correct status code emission (`INVALID_CAPTURE`, `CALIBRATION_INVALID`, `MANUAL_REVIEW`).
5. Mathematical correctness of projective homography matrix $H$ and RMS reprojection residual calculation.
6. Transformation of planar pixel coordinates to millimetres via $H$.
7. CLI argument enforcement rejecting execution when `--caliper-marker-mm` is missing.

---

## 8. What Cannot Be Verified Without Field Data

1. **Physical Marker Detectability**: True detection rate under smartphone camera optics, lens distortion, and uneven lighting.
2. **Dust & Glare Robustness**: Impact of mandi dust, surface abrasion, or paper wrinkles on corner localization.
3. **Corner Jitter**: Empirical variance of corner coordinates across repeated handheld smartphone captures.
4. **Physical Measurement Error**: Actual percentage error between homography-measured planar objects and digital calipers under real field geometry.
5. **Image Quality Degradation**: Performance of blur and exposure thresholds on genuine mandi captures.

---

## 9. Exact Physical Data Required Next

To execute the first real Gate 1 experiment, the operator must assemble:
1. **Printed ArUco Marker**: Printed from [`data/reference/printable_aruco_dict4x4_50_id0.png`](file:///c:/Users/S/OneDrive/Desktop/AI/data/reference/printable_aruco_dict4x4_50_id0.png) at 100% scale on rigid cardstock.
2. **Vernier Caliper Ground Truth**: Measured edge length of the printed marker in millimetres (e.g. $50.15\text{ mm}$).
3. **Planar Reference Object**: A flat circular object (such as an Indian 5-rupee coin or machined metal calibration disc) with its outer diameter measured by caliper (e.g. $23.00\text{ mm}$).
4. **Real Smartphone Photograph**: One or more photos taken at 45–55 cm working distance with marker and reference object placed coplanar on an inspection surface, deposited into [`data/raw/`](file:///c:/Users/S/OneDrive/Desktop/AI/data/raw) (e.g. `data/raw/tray_capture_01.jpg`).

---

## 10. Exact Command to Run After Real Photo Exists

```powershell
.venv\Scripts\python scripts/run_gate1_validation.py `
  --image "data/raw/tray_capture_01.jpg" `
  --caliper-marker-mm 50.15 `
  --reference-name "INR_5_COIN" `
  --reference-ground-truth-mm 23.00
```
*(Replace `50.15` and `23.00` with your actual caliper readings. If reference endpoints are known, add `--reference-points-px x1,y1,x2,y2`).*
