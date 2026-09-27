"""
Controlled evaluation script for testing v7 class-mapping variants.

Compares:
Variant A: Original validation labels (ID 2 = rotten, ID 3 = sprouted according to data.yaml)
Variant B: Swapped validation labels (ID 2 and ID 3 swapped to match checkpoint string names)

Never modifies source dataset. Operates strictly in artifacts/class_mapping_audit/.
"""

import json
import shutil
import sys
from pathlib import Path
from typing import Any

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def prepare_variant_datasets(
    source_valid_dir: Path,
    audit_root: Path,
) -> tuple[Path, Path]:
    """
    Prepare isolated directory copies for Variant A (original) and Variant B (swapped 2 & 3).
    """
    source_images = source_valid_dir / "images"
    source_labels = source_valid_dir / "labels"

    if not source_images.exists() or not source_labels.exists():
        raise FileNotFoundError(f"Source validation images/labels not found under: {source_valid_dir}")

    var_a_dir = audit_root / "variant_A"
    var_b_dir = audit_root / "variant_B"

    # Clean target dirs if exist
    for vdir in (var_a_dir, var_b_dir):
        if vdir.exists():
            shutil.rmtree(vdir)
        vdir.mkdir(parents=True, exist_ok=True)

    # 1. Setup Variant A (Untouched copy)
    var_a_images = var_a_dir / "images"
    var_a_labels = var_a_dir / "labels"
    shutil.copytree(source_images, var_a_images)
    shutil.copytree(source_labels, var_a_labels)

    # 2. Setup Variant B (Images identical, labels with IDs 2 and 3 swapped)
    var_b_images = var_b_dir / "images"
    var_b_labels = var_b_dir / "labels"
    shutil.copytree(source_images, var_b_images)
    var_b_labels.mkdir(parents=True, exist_ok=True)

    for label_file in source_labels.glob("*.txt"):
        lines = label_file.read_text(encoding="utf-8").splitlines()
        swapped_lines = []
        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue
            parts = line_str.split()
            class_id = int(parts[0])
            if class_id == 2:
                swapped_class = 3
            elif class_id == 3:
                swapped_class = 2
            else:
                swapped_class = class_id

            swapped_line = " ".join([str(swapped_class)] + parts[1:])
            swapped_lines.append(swapped_line)

        (var_b_labels / label_file.name).write_text("\n".join(swapped_lines) + "\n", encoding="utf-8")

    # Create YAML configs pointing to isolated copies
    # We use model's declared names: {0: 'healthy', 1: 'damaged', 2: 'sprouted', 3: 'rotten'}
    var_a_yaml = var_a_dir / "data.yaml"
    var_a_yaml.write_text(
        f"path: {var_a_dir.resolve().as_posix()}\n"
        f"train: images\n"
        f"val: images\n"
        f"nc: 4\n"
        f"names: ['healthy', 'damaged', 'sprouted', 'rotten']\n",
        encoding="utf-8"
    )

    var_b_yaml = var_b_dir / "data.yaml"
    var_b_yaml.write_text(
        f"path: {var_b_dir.resolve().as_posix()}\n"
        f"train: images\n"
        f"val: images\n"
        f"nc: 4\n"
        f"names: ['healthy', 'damaged', 'sprouted', 'rotten']\n",
        encoding="utf-8"
    )

    return var_a_yaml, var_b_yaml


def evaluate_variant(model, yaml_path: Path) -> dict[str, Any]:
    """Run model.val on a dataset YAML and extract standard metrics."""
    metrics = model.val(
        data=str(yaml_path.resolve()),
        split="val",
        verbose=False,
        save=False,
        plots=False,
    )

    results_dict = metrics.results_dict if hasattr(metrics, "results_dict") else {}
    precision = float(results_dict.get("metrics/precision(B)", 0.0))
    recall = float(results_dict.get("metrics/recall(B)", 0.0))
    map50 = float(results_dict.get("metrics/mAP50(B)", 0.0))
    map50_95 = float(results_dict.get("metrics/mAP50-95(B)", 0.0))

    per_class = {}
    if hasattr(metrics, "box") and hasattr(metrics.box, "ap50"):
        ap50_list = metrics.box.ap50
        names = model.names
        for idx, ap in enumerate(ap50_list):
            cname = names.get(idx, f"class_{idx}")
            per_class[cname] = round(float(ap), 6)

    return {
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "mAP50": round(map50, 6),
        "mAP50-95": round(map50_95, 6),
        "per_class_ap50": per_class,
        "all_metrics": {k: round(float(v), 6) if isinstance(v, (int, float)) else str(v) for k, v in results_dict.items()},
    }


def generate_experiment_report(
    var_a_metrics: dict[str, Any],
    var_b_metrics: dict[str, Any],
    report_path: Path,
) -> None:
    """Generate Markdown report separating FACT, EXPERIMENTAL RESULT, INTERPRETATION, and UNRESOLVED QUESTION."""
    diff_map50 = var_b_metrics["mAP50"] - var_a_metrics["mAP50"]
    diff_map50_95 = var_b_metrics["mAP50-95"] - var_a_metrics["mAP50-95"]

    content = f"""# V7 Model Class-Mapping Controlled Experiment Report

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
   - `names`: `{{0: 'healthy', 1: 'damaged', 2: 'sprouted', 3: 'rotten'}}`
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
| **Precision (B)** | `{var_a_metrics['precision']:.6f}` | `{var_b_metrics['precision']:.6f}` | `{(var_b_metrics['precision'] - var_a_metrics['precision']):+.6f}` |
| **Recall (B)** | `{var_a_metrics['recall']:.6f}` | `{var_b_metrics['recall']:.6f}` | `{(var_b_metrics['recall'] - var_a_metrics['recall']):+.6f}` |
| **mAP@50 (B)** | `{var_a_metrics['mAP50']:.6f}` | `{var_b_metrics['mAP50']:.6f}` | `{diff_map50:+.6f}` |
| **mAP@50-95 (B)** | `{var_a_metrics['mAP50-95']:.6f}` | `{var_b_metrics['mAP50-95']:.6f}` | `{diff_map50_95:+.6f}` |

### Per-Class AP@50 Comparison

| Class ID | Evaluated Class Name | Variant A AP@50 | Variant B AP@50 |
|---|---|---|---|
| 0 | healthy | `{var_a_metrics['per_class_ap50'].get('healthy', 0.0):.6f}` | `{var_b_metrics['per_class_ap50'].get('healthy', 0.0):.6f}` |
| 1 | damaged | `{var_a_metrics['per_class_ap50'].get('damaged', 0.0):.6f}` | `{var_b_metrics['per_class_ap50'].get('damaged', 0.0):.6f}` |
| 2 | sprouted / rotten | `{var_a_metrics['per_class_ap50'].get('sprouted', 0.0):.6f}` | `{var_b_metrics['per_class_ap50'].get('sprouted', 0.0):.6f}` |
| 3 | rotten / sprouted | `{var_a_metrics['per_class_ap50'].get('rotten', 0.0):.6f}` | `{var_b_metrics['per_class_ap50'].get('rotten', 0.0):.6f}` |

---

## 3. INTERPRETATION

1. **Numerical Behavior**:
   - In Variant A: mAP@50 is `{var_a_metrics['mAP50']:.4f}`, with individual class APs indicating whether the model was trained under dataset canonical ordering or checkpoint name ordering.
   - In Variant B: mAP@50 changed by `{diff_map50:+.4f}`.
   
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
"""
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(content, encoding="utf-8")


def main() -> int:
    source_valid_dir = Path(r"../Onion_grading_system/training/merged_v2/valid").resolve()
    checkpoint_path = Path(r"../Onion_grading_system/onion-grading-v7.pt").resolve()
    audit_root = Path(r"artifacts/class_mapping_audit").resolve()
    report_path = Path(r"docs/V7_MAPPING_EXPERIMENT.md").resolve()

    print("=" * 60)
    print("MANDI NYAAY — V7 CLASS MAPPING CONTROLLED EXPERIMENT")
    print("=" * 60)
    print(f"Source Validation: {source_valid_dir}")
    print(f"Model Checkpoint:  {checkpoint_path}")
    print(f"Audit Directory:   {audit_root}")

    if not source_valid_dir.exists():
        print(f"ERROR: Source validation directory not found: {source_valid_dir}")
        return 1

    if not checkpoint_path.exists():
        print(f"ERROR: Model checkpoint not found: {checkpoint_path}")
        return 1

    from ultralytics import YOLO

    print("\n1. Preparing isolated validation copies (Variant A & B)...")
    var_a_yaml, var_b_yaml = prepare_variant_datasets(source_valid_dir, audit_root)

    print("\n2. Loading model checkpoint...")
    model = YOLO(str(checkpoint_path))

    print("\n3. Evaluating Variant A (Original Canonical Dataset Labels)...")
    var_a_metrics = evaluate_variant(model, var_a_yaml)
    print(f"   Variant A Precision: {var_a_metrics['precision']:.4f}")
    print(f"   Variant A Recall:    {var_a_metrics['recall']:.4f}")
    print(f"   Variant A mAP50:     {var_a_metrics['mAP50']:.4f}")
    print(f"   Variant A mAP50-95:  {var_a_metrics['mAP50-95']:.4f}")
    print(f"   Variant A Per-class: {var_a_metrics['per_class_ap50']}")

    print("\n4. Evaluating Variant B (Swapped Labels 2 and 3)...")
    var_b_metrics = evaluate_variant(model, var_b_yaml)
    print(f"   Variant B Precision: {var_b_metrics['precision']:.4f}")
    print(f"   Variant B Recall:    {var_b_metrics['recall']:.4f}")
    print(f"   Variant B mAP50:     {var_b_metrics['mAP50']:.4f}")
    print(f"   Variant B mAP50-95:  {var_b_metrics['mAP50-95']:.4f}")
    print(f"   Variant B Per-class: {var_b_metrics['per_class_ap50']}")

    # Save metrics JSON
    raw_results = {
        "checkpoint": str(checkpoint_path),
        "source_valid_dir": str(source_valid_dir),
        "variant_A": var_a_metrics,
        "variant_B": var_b_metrics,
    }
    json_path = audit_root / "evaluation_results.json"
    json_path.write_text(json.dumps(raw_results, indent=2), encoding="utf-8")
    print(f"\nRaw results saved to: {json_path}")

    # Generate Markdown Report
    print(f"Generating report: {report_path}")
    generate_experiment_report(var_a_metrics, var_b_metrics, report_path)
    print("Report generation complete.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
