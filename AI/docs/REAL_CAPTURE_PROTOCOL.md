# Mandi Nyaay AI — Real-World Capture Protocol & Ground-Truth Procedures

## 1. Field Acquisition Principles
To ensure that computer vision algorithms are evaluated on ground reality rather than synthetic illusions:
1. **Provenance Is Immutable**: Every raw capture image file deposited into `data/raw/` must be paired with an acquisition metadata manifest (JSON or embedded EXIF/session record).
2. **Physical Measurements Must Precede Digital Inferences**: True dimensions and weights must be physically measured with verified instruments before digital processing.
3. **No Synthetic Ground Truth**: Synthetic graphics, mocked bounding boxes, or estimated values must never serve as evaluation ground truth.

---

## 2. Capture Metadata Manifest Schema

Every acquisition session must record the following metadata parameters:

```json
{
  "capture_id": "LOT42_SESSION01_TRAY01_TOP",
  "timestamp": "2026-09-24T10:15:30+05:30",
  "lot_identifier": "MAH-NAS-2026-09-4281",
  "session_identifier": "SES_20260924_01",
  "mandi_location": "Pimpalgaon Baswant, Nashik, Maharashtra",
  "onion_variety": "Nashik Red (Garwa)",
  "viewpoint": "TOP",
  "device": {
    "manufacturer": "Samsung / Xiaomi / Motorola",
    "model_name": "Galaxy M34 / Redmi Note 12",
    "camera_id": "Back Main Camera (0)",
    "lens_aperture": "f/1.8",
    "focal_length_mm": 4.2,
    "native_resolution_px": [3000, 4000],
    "capture_resolution_px": [3000, 4000]
  },
  "geometry": {
    "capture_distance_cm": 50.0,
    "camera_pitch_deg": 5.0,
    "tray_dimensions_mm": [400.0, 300.0],
    "tray_surface_type": "Matte Blue Non-Reflective Plastic",
    "marker": {
      "dictionary": "DICT_4X4_50",
      "marker_id": 0,
      "caliper_measured_side_mm": 50.12,
      "caliper_measured_thickness_mm": 0.25,
      "substrate": "Matte White 300gsm Cardstock with Lamination"
    }
  },
  "environment": {
    "lighting_condition": "INDOOR_WAREHOUSE_SHED",
    "illumination_lux": 450,
    "ambient_temperature_c": 28.5,
    "relative_humidity_pct": 65.0
  },
  "provenance": {
    "operator_name": "Field Inspector A",
    "raw_image_filename": "LOT42_SESSION01_TRAY01_TOP.jpg",
    "raw_image_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
  }
}
```

---

## 3. Ground-Truth Measurement Procedures

### Procedure A: Physical Reference Marker Verification
* **Instrument**: Mitutoyo or equivalent digital vernier caliper ($0.01\text{ mm}$ resolution).
* **Protocol**:
  1. Print the marker on rigid, non-curling cardstock.
  2. Measure all four outer edges: $L_{\text{top}}, L_{\text{right}}, L_{\text{bottom}}, L_{\text{left}}$.
  3. Record the mean measured side length in the capture manifest (e.g. $50.12\text{ mm}$).
  4. Measure diagonals to confirm square orthogonality ($|D_1 - D_2| \le 0.15\text{ mm}$).
  5. Never assume the printed size matches the digital file size without physical measurement.

### Procedure B: Produce Physical Size Ground Truth
* **Instrument**: Digital vernier caliper ($0.01\text{ mm}$ resolution).
* **Protocol**:
  1. Assign a unique tag/number to each physical onion in the sample (e.g. `ONION_01` to `ONION_20`).
  2. Measure **Maximum Equatorial Diameter** ($D_{\max}$): rotate the bulb perpendicular to polar axis to find widest diameter.
  3. Measure **Minimum Equatorial Diameter** ($D_{\min}$): measure orthogonal transverse diameter.
  4. Measure **Polar Height** ($H_{\text{polar}}$): from the root plate base to the shoulder/neck pinch point.
  5. Record all three measurements in millimetres.

### Procedure C: Produce Physical Weight Ground Truth
* **Instrument**: Precision digital balance with calibration certificate ($0.1\text{ g}$ readability).
* **Protocol**:
  1. Tare the balance.
  2. Place individual numbered onion on the center of the pan.
  3. Allow reading to stabilize (indicated by stability symbol).
  4. Record net weight in grams.
  5. For bulk verification: weigh the entire tray batch together and ensure $\sum W_i$ matches total batch weight within $\pm 0.5\text{ g}$.

### Procedure D: External Defect Ground Truth
* **Protocol**:
  1. Inspected independently by two qualified agronomists or certified mandi graders.
  2. Examine entire bulb surface under $1000\text{ lux}$ diffuse illumination.
  3. Identify canonical classes: `SPROUTING`, `SURFACE_ROT`, `MOULD`, `CUT_BRUISE`, `DEFORMITY`, `UNDERSIZED`, `NONE`.
  4. Trace defect perimeter using CVAT polygon tool.
  5. If graders disagree on classification or severity, adjudicate via joint review. Unresolved cases are flagged `AMBIGUOUS_DEFECT` and excluded from gold training sets.

### Procedure E: Multi-View Identity Ground Truth
* **Protocol**:
  1. Maintain physical onion order on indexed tray compartments (e.g. a $4 \times 5$ numbered grid tray) during initial `TOP` and `SIDE` captures.
  2. When flipping bulbs for `UNDERSIDE` capture, invert in-place within the same indexed cell.
  3. The compartment index establishes guaranteed physical identity correspondence across viewpoints.

---

## 4. Staged Dataset Collection Targets (G1 through G6)

Instead of relying on arbitrary static quotas, datasets are staged by capability gates:

1. **DATASET G1 (Marker & Planar Calibration)**:
   - *Target Size*: 30–50 captures across 3 distinct mobile phones, 3 working distances ($35, 50, 65\text{ cm}$), 3 tilt angles ($0^\circ, 15^\circ, 30^\circ$), and 3 lighting environments.
   - *Sample Size Justification*: Sufficient to estimate sub-pixel repeatability variance and verify homography planar error over all expected handheld poses.
2. **DATASET G2 (Image Quality & Degradation)**:
   - *Target Size*: 40 paired captures (sharp vs. intentional motion blur, normal vs. glare/underexposed).
   - *Sample Size Justification*: Establishes true positive/negative rejection ROC curves for blur and clipping thresholds.
3. **DATASET G3 (Instance Segmentation)**:
   - *Target Size*: 100 tray scenes ($\ge 1500$ individual onion instances) covering isolated, touching, and overlapping configurations across at least 5 distinct mandi lots.
   - *Sample Size Justification*: Captures natural morphological variance, skin peeling, and dust conditions across different procurement centres.
4. **DATASET G4 (Multi-View Correspondence)**:
   - *Target Size*: 50 multi-view tray batches (150 images total: 50 Top, 50 Side, 50 Underside) with guaranteed grid-indexed identity.
   - *Sample Size Justification*: Enables validation of Hungarian matching precision/recall and identification of ambiguous rotation failure modes.
5. **DATASET G5 (Weight & Sizing Calibration)**:
   - *Target Size*: $\ge 300$ individually numbered, vernier-measured, and scale-weighed onions spanning size grades (small, medium, large) across at least 2 seasonal varieties (Garwa and Rangada).
   - *Sample Size Justification*: Provides statistical power to detect weight prediction bias $>5\text{g}$ with $95\%$ confidence ($\alpha=0.05, 1-\beta=0.80$).
6. **DATASET G6 (External Defects)**:
   - *Target Size*: $\ge 50$ distinct specimens per canonical defect class (minimum 350 defect observations total).
   - *Sample Size Justification*: Ensures sufficient class representation to evaluate per-class precision and recall without severe imbalance skew.
