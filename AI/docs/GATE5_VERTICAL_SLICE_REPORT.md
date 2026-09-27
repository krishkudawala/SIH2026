# Mandi Nyaay — Gate 5 Readiness Report
## Vertical Inspection Slice: Observation → Decision → Evidence

---

### 1. Executive Summary

Gate 5 delivers the **first complete, real, executable Mandi Nyaay inspection vertical slice** inside `AI/`.

The system successfully implements the core product principle:
> **Mandi Nyaay is not "AI sees onion → AI gives grade."**  
> **Mandi Nyaay is an AI-assisted procurement inspection that converts observable evidence into a reviewable lot-level decision.**

Every step in the chain is executed from genuine sensor inputs, verified model inference, deterministic business rules, and tamper-evident logging:

$$\text{REAL IMAGE} \longrightarrow \text{REAL CV} \longrightarrow \text{RECONCILED OBSERVATIONS} \longrightarrow \text{SAMPLING} \longrightarrow \text{AGGREGATION} \longrightarrow \text{REVIEW SIGNALS} \longrightarrow \text{DECISION} \longrightarrow \text{EVIDENCE}$$

---

### 2. What Works End-to-End

| Component | Status | Description |
| :--- | :--- | :--- |
| **Canonical Inspection Contract** | **IMPLEMENTED** | Strict Pydantic models (`InspectionSession`, `InspectionCapture`, `InspectionObservationSet`, `InspectionSamplingResult`, `InspectionAggregation`, `InspectionDecision`, `InspectionReviewSignal`, `InspectionEvidenceSummary`) with UUIDs, ISO timestamps, and provenance tracking in [`app/domain/inspection_session.py`](file:///c:/Users/S/OneDrive/Desktop/AI/app/domain/inspection_session.py). |
| **Real CV Pipeline Integration** | **IMPLEMENTED & VALIDATED** | Integrated [`MandiNyaayCVPipeline`](file:///c:/Users/S/OneDrive/Desktop/AI/app/pipeline/cv_pipeline.py) generating canonical capture results with image SHA256 digests, optical quality screening, detector execution, and class mapping verification. |
| **Observation Reconciliation** | **IMPLEMENTED & VALIDATED** | Collapses overlapping bounding boxes into one physical bulb observation. Resolves duplicates of identical classes and isolates cross-class conflicts as `CLASS_CONFLICT` without silent double counting. |
| **Statistical Sampling Engine** | **IMPLEMENTED & VALIDATED** | Evaluates produce observation count against target sample size. Emits `SUFFICIENT`, `CONTINUE`, `MANUAL_REVIEW`, or `INVALID` with clear explanations in [`app/domain/sampling.py`](file:///c:/Users/S/OneDrive/Desktop/AI/app/domain/sampling.py). |
| **Count vs. Mass Aggregation** | **IMPLEMENTED & VALIDATED** | Computes exact condition percentages based strictly on physical bulb counts. Explicitly refuses to fabricate mass, setting `mass_status = "UNVALIDATED"` and `mass_distribution = None` in [`app/domain/aggregation.py`](file:///c:/Users/S/OneDrive/Desktop/AI/app/domain/aggregation.py). |
| **Review Signal Engine** | **IMPLEMENTED & VALIDATED** | Emits 8 explicit review signals with strict legal wording: *"This is a review signal, not proof of fraud."* Never outputs accusatory terms like *"FRAUD DETECTED"* in [`app/domain/review_signals.py`](file:///c:/Users/S/OneDrive/Desktop/AI/app/domain/review_signals.py). |
| **Procurement Decision Engine** | **IMPLEMENTED & VALIDATED** | Deterministic versioned rule pack (`MANDI_NYAAY_PROCUREMENT_RULES_V1.0`) routing to `GRADE_A`, `URS`, `REJECT`, or `MANUAL_REVIEW` based on defect percentages and blocking conditions in [`app/domain/decision_engine.py`](file:///c:/Users/S/OneDrive/Desktop/AI/app/domain/decision_engine.py). |
| **Tamper-Evident Evidence** | **IMPLEMENTED & VALIDATED** | Generates replayable evidence summary with a deterministic canonical SHA256 root hash over all capture hashes, observation IDs, decision grades, and rule versions. |
| **CLI Demo Runner** | **IMPLEMENTED & VALIDATED** | [`scripts/run_inspection_demo.py`](file:///c:/Users/S/OneDrive/Desktop/AI/scripts/run_inspection_demo.py) providing end-to-end local execution and generating machine-readable `inspection_result.json`. |

---

### 3. Real Execution Evidence

The complete vertical slice was executed against real validation images from the external dataset (`merged_v2/valid`).

#### Run A: Ambiguous Cross-Class Conflict (`cropbad`)
- **Input Image**: `merged_v2/valid/images/cropbad_20230121_084837_train_4551f94b_1.jpg`
- **Model Checkpoint**: `onion-grading-v7.pt`
- **Output Artifact**: [`artifacts/gate5/inspection_cropbad.json`](file:///c:/Users/S/OneDrive/Desktop/AI/artifacts/gate5/inspection_cropbad.json)
- **Observed Behavior**:
  - **Raw Detections**: 2 overlapping bounding boxes (damaged 0.49 vs sprouted 0.48, $\text{IoU} \approx 0.95$).
  - **Reconciled Physical Bulbs**: 1 physical bulb.
  - **Conflict Count**: 1 cross-class conflict (`CLASS_CONFLICT`).
  - **Sampling Status**: `MANUAL_REVIEW` (*"Sample contains 1 cross-class conflict(s) where overlapping detections disagree."*).
  - **Review Signals**:
    - `[ACTION REQUIRED] CLASS_CONFLICT (CRITICAL)`: *"1 cross-class detection conflict(s) detected during physical bulb reconciliation. This is a review signal, not proof of fraud."*
    - `[INFO] LOW_IMAGE_QUALITY (WARNING)`: *"Image quality screening emitted warning (borderline sharpness or illumination). This is a review signal, not proof of fraud."*
  - **Procurement Decision**:
    - **Grade**: `MANUAL_REVIEW`
    - **Status**: `REFERRED_TO_MANUAL_REVIEW`
    - **Blocking Reasons**:
      1. *"Cross-class detection conflict detected on 1 or more physical bulbs; manual adjudication required."*
      2. *"Sampling status is MANUAL_REVIEW: Sample contains 1 cross-class conflict(s) where overlapping detections disagree. Manual review required before sampling sufficiency can be affirmed."*
  - **Evidence Root Hash**: `9df7fa57101c8a79f386299a6c2814a0026ef2c62391d778df00181fa63122d0`
  - **Integrity**: **Zero double counting occurred.** The conflicting raw detections collapsed into exactly 1 physical bulb observation.

#### Run B: Dense Tray Sampling Shortfall (`densepile`, Target 20)
- **Input Image**: `merged_v2/valid/images/densepile_valid_0000.jpg`
- **Model Checkpoint**: `onion-grading-v7.pt`
- **Output Artifact**: [`artifacts/gate5/inspection_densepile.json`](file:///c:/Users/S/OneDrive/Desktop/AI/artifacts/gate5/inspection_densepile.json)
- **Observed Behavior**:
  - **Raw Detections**: 10 bounding boxes.
  - **Reconciled Physical Bulbs**: 10 separate physical bulbs (IoU between separate bulbs did not trigger collapse).
  - **Conflict Count**: 0.
  - **Condition Counts**: `{'HEALTHY': 3, 'DAMAGED': 3, 'ROTTEN': 3, 'SPROUTED': 1}`
  - **Sampling Status**: `CONTINUE` (*"Observed sample size (10) is below required target sample size (20). Additional 10 bulb observation(s) required from subsequent captures."*).
  - **Review Signals**:
    - `[ACTION REQUIRED] INSUFFICIENT_SAMPLE (WARNING)`: *"Observed sample size (10) does not satisfy target sample size (20). This is a review signal, not proof of fraud."*
  - **Procurement Decision**:
    - **Grade**: `MANUAL_REVIEW`
    - **Blocking Reason**: *"Sampling status is CONTINUE: Observed sample size (10) is below required target sample size (20). Additional 10 bulb observation(s) required from subsequent captures."*
  - **Evidence Root Hash**: `0ea96fd548693df0c202c8afe9d6ff79e9deee585685ce0600ead39ba0112d1a`

#### Run C: Deterministic Reject on Satisfied Sample (`densepile`, Target 10)
- **Input Image**: `merged_v2/valid/images/densepile_valid_0000.jpg`
- **Target Sample Size**: 10
- **Output Artifact**: [`artifacts/gate5/inspection_densepile_target10.json`](file:///c:/Users/S/OneDrive/Desktop/AI/artifacts/gate5/inspection_densepile_target10.json)
- **Observed Behavior**:
  - **Sampling Status**: `SUFFICIENT` (*"Observed sample size (10) meets or exceeds the target sample size (10) with zero unresolved cross-class conflicts."*).
  - **Aggregation**: Total count = 10; Rotten = 3 (30.0%), Damaged = 3 (30.0%), Healthy = 3 (30.0%), Sprouted = 1 (10.0%).
  - **Procurement Decision**:
    - **Grade**: `REJECT`
    - **Status**: `DECIDED`
    - **Blocking Reasons**: None (`[]`).
    - **Decision Reason**: *"Rotten proportion (30.0%) exceeds maximum allowable limit (2.0%)."*
  - **Evidence Root Hash**: `2dea1af9f0c234beef452eb36ea57612fd0c8cc2b34b280399166435421a941c`

#### Run D: Manual Inspector Override Flow (`densepile`, Target 10, Committee Override)
- **Override Specification**: Grade `URS`, Reason: *"Dispute committee settlement"*
- **Output Artifact**: [`artifacts/gate5/inspection_densepile_override.json`](file:///c:/Users/S/OneDrive/Desktop/AI/artifacts/gate5/inspection_densepile_override.json)
- **Observed Behavior**:
  - **Review Signal**: Added `[INFO] MANUAL_OVERRIDE (WARNING)`: *"Manual inspector override logged: Dispute committee settlement. This is a review signal, not proof of fraud."*
  - **Decision Grade**: `URS`
  - **Decision Reasons**: Logged both automated rule result and inspector adjustment:
    1. *"Rotten proportion (30.0%) exceeds maximum allowable limit (2.0%)."*
    2. *"Manual inspector override applied: Grade adjusted to URS. Reason: Dispute committee settlement"*
  - **Evidence Root Hash**: Deterministically updated to `70d51ec4e7e3ea7caf721ea8e49bb63a819cc4281246602061221625a8193f91`.

---

### 4. Current Decision Behavior

The Procurement Decision Engine evaluates versioned rules (`MANDI_NYAAY_PROCUREMENT_RULES_V1.0`):

1. **Mandatory Diversion to `MANUAL_REVIEW`**:
   The engine halts automated grading and diverts to `MANUAL_REVIEW` if any of the following occur:
   - Any physical produce bulb has a `CLASS_CONFLICT` (unresolved cross-class overlap).
   - Sampling sufficiency is not satisfied (`CONTINUE`, `MANUAL_REVIEW`, or `INVALID`).
   - Image quality screening triggers `CRITICAL` (quality `FAIL`).
   - Physical metric measurement was explicitly required but planar calibration is unavailable or invalid.
   - Weighbridge mass/count divergence exceeds configured review threshold ($15\%$).

2. **Automated Procurement Grades (When Sampling is Sufficient and Zero Blocking Conditions Exist)**:
   - **`REJECT`**: Rotten bulb proportion $> 2.0\%$ OR total defect proportion $> 20.0\%$.
   - **`GRADE_A`**: Total defect proportion $\le 5.0\%$ AND rotten proportion $\le 1.0\%$.
   - **`URS` (Under-grade Re-sort)**: Total defect proportion $\le 20.0\%$ (requires commercial re-sorting or utility pricing).

---

### 5. Review Signals Engine

Eight standardized signals are supported:

| Signal Code | Severity | Trigger Condition |
| :--- | :--- | :--- |
| `CLASS_CONFLICT` | `CRITICAL` | Overlapping detections with IoU $\ge 0.70$ predicting different canonical classes. |
| `LOW_IMAGE_QUALITY` | `CRITICAL` / `WARNING` | Blur (Laplacian variance), underexposure, or overexposure clipping violations. |
| `INSUFFICIENT_SAMPLE` | `WARNING` / `CRITICAL` | Observed bulb count is below lot target sample size. |
| `CALIBRATION_UNAVAILABLE` | `INFO` / `CRITICAL` | Reference ArUco marker not detected in capture tray. |
| `ONION_DIAMETER_UNVALIDATED` | `INFO` | Flags that 3D equatorial diameter from 2D bounding boxes is not field-certified. |
| `MASS_UNVALIDATED` | `INFO` | Flags that individual bulb mass is unvalidated and cannot be used for settlement. |
| `COUNT_MASS_DIVERGENCE` | `WARNING` | Aggregate weighbridge weight deviates from count-based sample distribution. |
| `MANUAL_OVERRIDE` | `WARNING` | Inspector or arbitration committee submitted a manual grade adjustment. |

**Strict Legal Policy Enforcement**: Every signal includes:
> *"This is a review signal, not proof of fraud."*  
Accusatory phrases (*"FRAUD DETECTED"*, *"theft"*, *"tampering"*) are strictly prohibited and verified by unit tests.

---

### 6. Evidence Captured

The `InspectionEvidenceSummary` contract records an immutable, replayable audit trail:
- `session_id`, `lot_id`, `capture_ids`
- Cryptographic SHA256 hashes of all input images
- List of deduplicated `observation_ids`
- Lineage versions: model checkpoint, class mapping version, sampling rule version, decision rule version
- Calibration and measurement statuses
- Emitted review signals and blocking reasons
- Automated decision and manual override metadata
- **`evidence_root_hash`**: Canonical SHA256 digest over the entire payload.
- **Classification**: Explicitly designated `tamper-evident/replayable` (never claimed as "tamper-proof").

---

### 7. Product Readiness Status Matrix

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       MANDI NYAAY STATUS MATRIX                             │
├──────────────────────────┬──────────────────────────────────────────────────┤
│ IMPLEMENTED              │ - Full Vertical Inspection Slice                 │
│                          │ - Pydantic Domain Contracts (Gate 5A)            │
│                          │ - Real CV Pipeline Integration (Gate 5B)         │
│                          │ - Statistical Sampling Engine (Gate 5C)          │
│                          │ - Count vs Mass Aggregator (Gate 5D)             │
│                          │ - Procurement Decision Engine (Gate 5E)          │
│                          │ - Operational Review Signals (Gate 5F)           │
│                          │ - Tamper-Evident Evidence Object (Gate 5G)       │
│                          │ - Local CLI Demo Runner (Gate 5H)                │
├──────────────────────────┼──────────────────────────────────────────────────┤
│ VALIDATED                │ - Same-class duplicate collapse (IoU >= 0.70)    │
│                          │ - Cross-class conflict isolation (CLASS_CONFLICT)│
│                          │ - Zero silent double-counting                    │
│                          │ - Real image execution on external valid set     │
│                          │ - Deterministic decision rule routing            │
│                          │ - JSON serialization / deserialization roundtrip │
│                          │ - 70 passing automated tests in pytest suite     │
├──────────────────────────┼──────────────────────────────────────────────────┤
│ UNVALIDATED              │ - 3D bulb equatorial diameter from 2D planar bbox│
│                          │ - Volumetric mass estimation from single camera  │
│                          │ - Empirical sharpness/exposure threshold bounds  │
│                          │   across uncontrolled Mandi lighting             │
├──────────────────────────┼──────────────────────────────────────────────────┤
│ BLOCKED                  │ - Direct mass-based procurement settlement       │
│                          │   (Blocked on physical load cell / caliper       │
│                          │   paired calibration dataset)                    │
└──────────────────────────┴──────────────────────────────────────────────────┘
```

---

### 8. Exact Frontend Contract Required Next

The vertical slice produces an immutable `InspectionSession` schema ready for consumption by the Flutter/Kotlin client:

```json
{
  "session_id": "ses_48b08875",
  "lot_id": "lot_demo_001",
  "status": "MANUAL_REVIEW",
  "captures": [
    {
      "capture_id": "cap_514bd0b2",
      "status": "SUCCESS",
      "image_path": "path/to/capture.jpg",
      "image_sha256": "a28232b50b1b177d...",
      "raw_detection_count": 2,
      "reconciled_observation_count": 1,
      "conflict_count": 1,
      "visible_condition_counts": {
        "CLASS_CONFLICT": 1
      },
      "quality_status": "WARN",
      "mapping_status": "VERIFIED",
      "measurement_status": "CALIBRATION_NOT_AVAILABLE",
      "calibration_status": "CALIBRATION_NOT_AVAILABLE",
      "provenance": {
        "pipeline_version": "0.1.0",
        "mapping_status": "VERIFIED",
        "architecture": "YOLOv7",
        "checkpoint_path": "onion-grading-v7.pt"
      }
    }
  ],
  "observation_set": {
    "observation_set_id": "obs_set_1a2b3c4d",
    "status": "HAS_CONFLICTS",
    "total_raw_detections": 2,
    "total_reconciled_observations": 1,
    "conflict_count": 1,
    "observations": [
      {
        "observation_id": "obs_0",
        "capture_id": "cap_514bd0b2",
        "bbox": [120.0, 140.0, 480.0, 510.0],
        "class_semantic": "CLASS_CONFLICT",
        "confidence": 0.49,
        "observation_status": "CLASS_CONFLICT",
        "candidate_classes": ["DAMAGED", "SPROUTED"],
        "candidate_confidences": [0.49, 0.48],
        "source_detection_ids": ["det_0", "det_1"]
      }
    ],
    "visible_condition_counts": {
      "CLASS_CONFLICT": 1
    }
  },
  "sampling_result": {
    "sampling_id": "smp_9f8e7d6c",
    "status": "MANUAL_REVIEW",
    "target_sample_size": 20,
    "observed_sample_size": 1,
    "sampling_rule_version": "MANDI_NYAAY_SAMPLING_V1.0",
    "reason": "Sample contains 1 cross-class conflict(s) where overlapping detections disagree. Manual review required before sampling sufficiency can be affirmed.",
    "limitations": [
      "Bulb mass and 3D volumetric sizing are UNVALIDATED in current field conditions.",
      "Sampling sufficiency is determined strictly from 2D physical bulb observation counts."
    ]
  },
  "aggregation": {
    "aggregation_id": "agg_11223344",
    "aggregation_mode": "COUNT_BASED",
    "total_count": 1,
    "count_distribution": {
      "CLASS_CONFLICT": {
        "count": 1,
        "percentage": 100.0
      }
    },
    "mass_status": "UNVALIDATED",
    "mass_distribution": null,
    "disclaimer": "Aggregation is based strictly on physical bulb count. Calibrated individual bulb mass is UNVALIDATED and cannot be used for procurement settlement."
  },
  "review_signals": [
    {
      "signal_id": "sig_55667788",
      "code": "CLASS_CONFLICT",
      "severity": "CRITICAL",
      "message": "1 cross-class detection conflict(s) detected during physical bulb reconciliation. This is a review signal, not proof of fraud.",
      "source": "observation_reconciliation",
      "requires_action": true
    }
  ],
  "decision": {
    "decision_id": "dec_9900aabb",
    "status": "REFERRED_TO_MANUAL_REVIEW",
    "procurement_grade": "MANUAL_REVIEW",
    "decision_rule_version": "MANDI_NYAAY_PROCUREMENT_RULES_V1.0",
    "decision_reasons": [
      "Automated procurement grading halted and diverted to MANUAL_REVIEW due to active blocking conditions."
    ],
    "blocking_reasons": [
      "Cross-class detection conflict detected on 1 or more physical bulbs; manual adjudication required.",
      "Sampling status is MANUAL_REVIEW: Sample contains 1 cross-class conflict(s) where overlapping detections disagree."
    ]
  },
  "evidence_summary": {
    "evidence_id": "evi_ccddeeff",
    "lot_id": "lot_demo_001",
    "session_id": "ses_48b08875",
    "status": "RECORDED",
    "evidence_root_hash": "9df7fa57101c8a79f386299a6c2814a0026ef2c62391d778df00181fa63122d0",
    "evidence_ledger_term": "tamper-evident/replayable"
  }
}
```

#### Frontend UI Requirements:
1. **Decision Banner**:
   - `GRADE_A` → Green badge (Accept lot at Grade A pricing).
   - `URS` → Orange badge (Under-grade Re-sort; route to utility sorting).
   - `REJECT` → Red badge (Reject lot; show defect breakdown).
   - `MANUAL_REVIEW` → Amber review badge (Display `blocking_reasons` and `review_signals` for inspector manual adjudication).
2. **Review Signal Action Center**:
   - List each active signal with severity icon.
   - For `CLASS_CONFLICT`: Show side-by-side candidate classes (`DAMAGED` vs `SPROUTED`) with confidences, allowing inspector to tap and confirm the physical condition.
3. **Sampling Progress Indicator**:
   - Show `observed_sample_size` / `target_sample_size`.
   - If status is `CONTINUE`, prompt inspector to take another tray capture for the same `lot_id`.
4. **Dispute / Manual Override Modal**:
   - Allows authorized committee members to log an override with inspector ID and formal rationale, which records directly into the replayable evidence package.

---

### 9. Next Gate: Gate 6 — Multi-Capture Tray Aggregation & Dispute Resampling

The next milestone connects multi-capture accumulation:
1. **Multi-Capture Session Progression**: Aggregating observations across multiple tray photos until sample sufficiency is satisfied.
2. **Blind Resampling Engine**: Facilitating blinded secondary inspections during farmer disputes without revealing prior inspector decisions.
3. **Ledger Event Chaining**: Cryptographic chaining of successive inspection events.
