# Mandi Nyaay AI — Data Strategy & Dataset Specifications

## 1. Ground Truth Principles
1. **Real Data Before Models**: No model will be selected, trained, or benchmarked without genuine field imagery.
2. **AI Proposes, Human Validates**: Automated annotation tools (e.g. SAM 2) generate label candidates only. A label becomes ground truth **only after explicit human verification and approval**.
3. **Auditability & Lineage**: Every dataset release must carry an immutable version tag, schema version, annotator/reviewer ID, and source lot/session metadata.

---

## 2. Canonical Datasets

### DATASET A — Instance Segmentation
* **Purpose**: Delineation of individual onion boundaries on inspection trays.
* **Composition**: Real captures containing:
  - Isolated onions
  - Touching onions (contact boundaries)
  - Partially overlapping onions (occlusion)
  - Mixed sizes (miniature bulblets to jumbo bulbs)
  - Varied tray backgrounds (blue, white, matte grey, stainless steel)
  - Field conditions: dust, dry outer skins, loose peels, varied ambient lighting (direct sunlight, deep shade, fluorescent shed).
* **Ground Truth**: High-precision polygon instance masks + bounding boxes + instance ID.
* **Storage Location**: `data/datasets/dataset_a_instance_seg/v1.0/`

### DATASET B — External Defects
* **Purpose**: Training and evaluation of surface defect classifiers and localizers.
* **Exact Canonical Classes**:
  1. `SPROUTING`: Visible emergence of green foliage / vegetative stem from apical neck.
  2. `SURFACE_ROT`: Soft, sunken, water-soaked, or discolored bacterial/fungal skin lesions.
  3. `MOULD`: Visible mycelium, fungal growth (e.g., black mould *Aspergillus niger*, blue mould).
  4. `CUT_BRUISE`: Mechanical damage, lacerations, skinning, impact fractures from harvest/handling.
  5. `DEFORMITY`: Double/bottleneck/split bulbs or irregular physical developmental shape.
  6. `UNDERSIZED`: Equatorial diameter strictly below procurement threshold (e.g. < 25 mm).
  7. `NONE`: Clean, intact, defect-free outer skin.
* **Mandatory Technical Disclaimer**: "Externally visible condition only. Internal rot, hollow heart, or inner core decay cannot be observed by standard RGB surface cameras."
* **Ground Truth**: Bounding box + segmentation mask + class label + severity indicator.
* **Storage Location**: `data/datasets/dataset_b_defects/v1.0/`

### DATASET C — Multi-View Correspondence
* **Purpose**: Resolving physical entity identity across sequential captures of the same inspection tray.
* **Batch Protocol**: Each physical sample is captured across three standard viewpoints:
  1. `TOP` (nadir view)
  2. `SIDE` (oblique 45-degree angle)
  3. `UNDERSIDE` (inverted / flipped view on tray)
* **Ground Truth**: Consistent global entity ID across all three viewpoints for each physical bulb.
* **Storage Location**: `data/datasets/dataset_c_multiview/v1.0/`

### DATASET D — Weight Calibration
* **Purpose**: Training and validating empirical and geometric weight prediction models.
* **Per-Onion Metadata**:
  - Multi-view high-resolution captures (Top, Side, Underside)
  - Calibrated reference scale factor (mm/px)
  - Ground-truth physical dimensions measured via calibrated digital vernier caliper:
    - Polar diameter (height from root plate to neck in mm)
    - Maximum equatorial diameter (width in mm)
    - Minimum equatorial diameter (thickness in mm)
  - Ground-truth physical weight in grams ($0.1\text{g}$ precision balance)
  - Variety/type (e.g., Nashik Red, Garwa, Rangada, White onion)
  - Environmental metadata: capture date, session, device model, relative humidity.
* **Strict Rule**: No weight model is evaluated or trusted without matching digital scale ground truth.
* **Storage Location**: `data/datasets/dataset_d_weight_calibration/v1.0/`

### DATASET E — Calibration & Reference Standards
* **Purpose**: Testing lens undistortion, perspective correction, and metric scale repeatability.
* **Contents**:
  - Calibrated ArUco reference markers (`DICT_4X4_50`, IDs 0–10) with verified side lengths (e.g., $50.0\text{ mm} \pm 0.1\text{ mm}$).
  - Precision machined metallic calibration discs (known diameter $40.0\text{ mm}$, $60.0\text{ mm}$, $80.0\text{ mm}$).
  - Multi-camera captures across different tilt angles ($0^\circ, 15^\circ, 30^\circ$) and working distances ($30\text{ cm} - 70\text{ cm}$).
* **Storage Location**: `data/datasets/dataset_e_calibration/v1.0/`

---

## 3. Data Splitting & Leakage Prevention
To ensure robust real-world generalization:
1. **Split Unit = Lot / Session**: Captures from the same physical lot, session, or mandi collection trip must **never** be split across train and validation/test sets.
2. **Multi-View Integrity**: All viewpoints (`TOP`, `SIDE`, `UNDERSIDE`) of a given physical onion must reside within the same split partition.
3. **Leave-One-Center-Out Evaluation**: When multi-center data is available, evaluation must withhold an entire mandi location to measure transferability across local lighting and camera setups.
4. **Partition Ratios**:
   - Training: 60% of lots
   - Validation (hyperparameter tuning): 20% of lots
   - Held-Out Test (benchmark reporting only): 20% of lots

---

## 4. Annotation Infrastructure & Protocol
1. **Tooling**: Use **CVAT** (Computer Vision Annotation Tool, self-hosted or managed) to handle multi-task annotations (polygons, bounding boxes, attributes).
2. **Acceleration**: Meta **SAM 2** (Segment Anything Model 2) can be used within CVAT for prompt-assisted mask generation to accelerate human annotator throughput.
3. **Quality Assurance Workflow**:
   - Level 1: Annotator generates or refines instance masks.
   - Level 2: Lead agronomist / senior inspector reviews 100% of defect labels and 20% of random instance boundaries.
   - Discrepant annotations trigger adjudication.
4. **Versioning**: Export annotations in COCO format with embedded git commit hash, taxonomy version (`TAXONOMY_V1`), and schema signature.
