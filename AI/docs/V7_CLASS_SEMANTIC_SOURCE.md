# V7 Class Semantic Source-Code Forensics Report

**Audited Repository**: `../Onion_grading_system/`  
**Target Model**: `../Onion_grading_system/onion-grading-v7.pt`  
**Date**: 2026-09-24  
**Auditor**: Mandi Nyaay AI Team  

---

## 1. FACT

1. **Canonical Dataset Specification (`training/merged_v2/data.yaml`)**:
   ```yaml
   train: train/images
   val: valid/images
   test: test/images
   nc: 4
   names: ['healthy', 'damaged', 'rotten', 'sprouted']
   ```
   Under this specification:
   - Index `0` = `healthy`
   - Index `1` = `damaged`
   - Index `2` = `rotten`
   - Index `3` = `sprouted`

2. **Checkpoint Header Metadata (`onion-grading-v7.pt`)**:
   - `model.task`: `detect`
   - `model.names`: `{0: 'healthy', 1: 'damaged', 2: 'sprouted', 3: 'rotten'}`
   Under this specification:
   - Index `0` = `healthy`
   - Index `1` = `damaged`
   - Index `2` = `sprouted`
   - Index `3` = `rotten`

3. **Observed Inversion**:
   Indices `2` and `3` are inverted between the canonical dataset YAML and the model checkpoint's internal names dictionary.

---

## 2. CODE EVIDENCE

Direct source inspection of the training and evaluation codebase in `../Onion_grading_system/` revealed documented provenance explaining this inversion.

### A. Evidence from `training/evaluate_model.py` (Lines 8–24 & 47–60)

```python
"""
WHY THIS EXISTS
----------------
Ultralytics metrics are only meaningful when the model's class ids line up
with the dataset's class ids. That silently broke during the v6/v7
fine-tunes: those models were trained on a scratch dataset that declared
the order ['healthy','damaged','sprouted','rotten'] while the canonical
dataset (training/merged_v2/data.yaml) declares ['healthy','damaged',
'rotten','sprouted']. Validating v7 straight against merged_v2/valid then
reported ~0.0 mAP for rotten/sprouted even though the model is fine --
it was just comparing every box against the wrong class id.

This harness therefore aligns class ids BY NAME before scoring, so it works
for any model regardless of its internal class order, and it reports which
mapping it used so a mismatch is visible instead of silently poisoning the
metrics.
"""

# Align the model's class ids to the canonical order by NAME. This is the
# whole point of the harness: never assume id order, always verify it.
model_names = model.names  # {id: name, ...}
model_id_for = {name: cid for cid, name in model_names.items()}
missing = [n for n in CANONICAL_NAMES if n not in model_id_for]
if missing:
    raise SystemExit(...)
mapping = {c: model_id_for[n] for c, n in enumerate(CANONICAL_NAMES)}
```

### B. Evidence from `training/finetune_from_photos.py` (Lines 26–36 & 110–120)

```python
"""
2. Builds a canonical-order dataset merged_v3/ (healthy=0, damaged=1,
   rotten=2, sprouted=3 -- the SAME order as training/merged_v2's
   data.yaml)...
3. Fine-tunes onion-grading-v7.pt on it (class ids are remapped by name
   via cls_remap, so the output model is guaranteed canonical order --
   this permanently ends the v6/v7 rotten/sprouted class-order trap),
   saves the result as onion-grading-v8.pt in the project root...
"""

# Refuse to deploy a model whose class order drifted from canonical.
names = YOLO(best).names
actual = [names[i] for i in sorted(names)]
if actual != CLASSES:
    raise SystemExit(
        f"Refusing to deploy: model names {actual} != canonical {CLASSES}. "
        "Check cls_remap / dataset class order and retrain."
    )
```

### C. Evidence from `backend/app/inference.py` (Lines 114–125)

```python
names = result.names  # Reads {0: 'healthy', 1: 'damaged', 2: 'sprouted', 3: 'rotten'} from v7
counts = {"healthy": 0, "damaged": 0, "rotten": 0, "sprouted": 0}
confidences = []
onions = []
for box in boxes:
    cls_id = int(box.cls[0].item())
    label = names.get(cls_id, str(cls_id))  # Directly resolves cls_id 2 to "sprouted" and 3 to "rotten"
```

---

## 3. INFERRED MAPPING

Based on the explicit author comments and training code:
1. `onion-grading-v7.pt` was trained on a scratch dataset whose class list had sprouted before rotten:
   - External Model ID `0` = `healthy` $\to$ Canonical `HEALTHY`
   - External Model ID `1` = `damaged` $\to$ Canonical `DAMAGED`
   - External Model ID `2` = `sprouted` $\to$ Canonical `SPROUTED`
   - External Model ID `3` = `rotten` $\to$ Canonical `ROTTEN`

2. When evaluated directly against `merged_v2/valid` without remap (Variant A in Gate 1), mAP dropped to near zero on classes 2 and 3 (`sprouted`: 0.062, `rotten`: 0.173) because ground truth had `2: rotten, 3: sprouted`.
3. When swapped (Variant B in Gate 1), mAP immediately jumped to `0.877` for sprouted and `0.828` for rotten.
4. Therefore, the internal weights of `onion-grading-v7.pt` predict:
   - ID `2` when visual sprout features (shoots/roots) are detected.
   - ID `3` when visual rot features (spoilage/mush) are detected.

---

## 4. UNRESOLVED QUESTIONS

1. **Visual Consistency of Dataset Labels**: In `merged_v2/valid`, does ground-truth ID `2` consistently represent rotten and ID `3` sprouted across all legacy source batches, or were some source datasets ingested before the canonical standardization?
2. **Visual Adjudication Requirement**: While code comments confirm the developer's intent and training script behavior, visual inspection of crops with green shoots vs dark mush is required to confirm that the training data itself was correctly labeled before granting `VERIFIED` status.
