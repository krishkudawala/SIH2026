# V7 Model Class-Mapping Controlled Experiment Report

**Date**: 2026-09-24  
**Evaluated Artifact**: `Onion_grading_system/onion-grading-v7.pt`  
**Dataset Evaluated**: `Onion_grading_system/training/merged_v2/valid` (241 held-out images)  
**Methodology**: Controlled A/B label hypothesis evaluation without touching source data.

---

## 1. FACT (Observed Metadata & Ground Truth)

1. **Source Dataset YAML (`merged_v2/data.yaml`)**:
   - `nc: 4`
   - `names: ['healthy', 'damaged', 'rotten', 'sprouted']`
   - ID Mapping in Dataset:
     - `0`: healthy
     - `1`: damaged
     - `2`: rotten
     - `3`: sprouted

2. **Model Checkpoint Internal Metadata (`onion-grading-v7.pt`)**:
   - `task`: detect
   - `architecture`: YOLO26n DetectionModel
   - `names`: `{0: 'healthy', 1: 'damaged', 2: 'sprouted', 3: 'rotten'}`
   - ID Mapping in Model Weights:
     - `0`: healthy
     - `1`: damaged
     - `2`: sprouted
     - `3`: rotten

3. **Discrepancy**:
   - Indices `2` and `3` are inverted between the dataset specification and model header strings.

---

## 2. EXPERIMENTAL RESULTS

Evaluations executed using unchanged `onion-grading-v7.pt` across isolated copies:
- **Variant A**: Original validation annotations (dataset canonical ordering).
- **Variant B**: Swapped validation annotations (labels for 2 and 3 swapped in validation set to align with checkpoint header).

### Aggregate Detection Metrics

| Metric | Variant A (Canonical Dataset Assumption) | Variant B (Swapped Checkpoint Name Assumption) | Absolute Difference (B - A) |
|---|---|---|---|
| **Precision (B)** | `0.459919` | `0.884580` | `+0.424661` |
| **Recall (B)** | `0.466886` | `0.796897` | `+0.330011` |
| **mAP@50 (B)** | `0.529444` | `0.896856` | `+0.367412` |
| **mAP@50-95 (B)** | `0.449757` | `0.754745` | `+0.304988` |

### Per-Class AP@50 Comparison

| Class ID | Evaluated Class Name | Variant A AP@50 | Variant B AP@50 |
|---|---|---|---|
| 0 | healthy | `0.956588` | `0.956588` |
| 1 | damaged | `0.925922` | `0.925922` |
| 2 | sprouted / rotten | `0.062386` | `0.877302` |
| 3 | rotten / sprouted | `0.172880` | `0.827614` |

---

## 3. INTERPRETATION

1. **Numerical Behavior**:
   - In Variant A: mAP@50 is `0.5294`, with individual class APs indicating whether the model was trained under dataset canonical ordering or checkpoint name ordering.
   - In Variant B: mAP@50 changed by `+0.3674`.
   
2. **Cautionary Guardrail**:
   - Higher mAP alone **does NOT mathematically prove semantic correctness**.
   - If the training dataset was generated with inverted class labels or class-imbalance artifacts (e.g. data card states: *"sprouted rests on only 3 real source photos"*), optimizing metric alignment could simply align with an inverted labeling error in the training split.

---

## 4. UNRESOLVED QUESTIONS

1. **Training Loss Origin**: Was `onion-grading-v7.pt` trained on `merged_v2` with `data.yaml` names passed directly (which mapped index 2 to rotten and 3 to sprouted), or was an custom names dict passed during training?
2. **Visual Evidence**: Individual image inspections with known visual sprouts (green shoots) vs rotten bulb textures are needed to confirm the model's actual visual associations before promoting mapping to `VERIFIED`.
3. **Current Safe Status**: In accordance with Mandi Nyaay domain contracts, the mapping status must remain:
   `MAPPING_STATUS = NEEDS_CONTROLLED_VALIDATION`
   Zero unverified labels are permitted to dictate commercial grading or farmer settlement.
