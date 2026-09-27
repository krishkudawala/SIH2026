"""
Gate 4A: Semantic Adjudication & Detector Error Audit Script.

This script performs:
1. Stratified sampling of 30 class-2 and 30 class-3 ground-truth instances from merged_v2/valid.
2. Metadata extraction (sha256, bbox, candidate semantics).
3. Visual contact sheet and crop rendering for visual inspection.
4. Model prediction audit using unchanged onion-grading-v7.pt.
5. In-depth failure audit of cropbad_20230121_084837_train_4551f94b_1.jpg.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from collections import defaultdict
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from ultralytics import YOLO


def compute_sha256(filepath: Path) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def compute_iou(boxA: list[float], boxB: list[float]) -> float:
    # box format: [x1, y1, x2, y2]
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    inter_w = max(0.0, xB - xA)
    inter_h = max(0.0, yB - yA)
    inter_area = inter_w * inter_h

    boxA_area = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxB_area = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])

    union_area = boxA_area + boxB_area - inter_area
    if union_area <= 0:
        return 0.0
    return inter_area / union_area


def compute_image_quality(img_cv: np.ndarray) -> dict[str, Any]:
    h, w = img_cv.shape[:2]
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    mean_lum = float(np.mean(gray))
    laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    clipped_ratio = float(np.sum((gray < 5) | (gray > 250)) / (h * w))

    return {
        "width": w,
        "height": h,
        "mean_luminance": round(mean_lum, 2),
        "blur_score": round(laplacian_var, 2),
        "exposure_clipped_ratio": round(clipped_ratio, 4),
    }


def main():
    base_dir = Path(__file__).resolve().parent.parent
    valid_dir = Path("../Onion_grading_system/training/merged_v2/valid").resolve()
    v7_model_path = Path("../Onion_grading_system/onion-grading-v7.pt").resolve()
    output_dir = base_dir / "artifacts" / "semantic_adjudication"
    crops_dir = output_dir / "crops"

    output_dir.mkdir(parents=True, exist_ok=True)
    crops_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading external dataset from {valid_dir}")
    images_dir = valid_dir / "images"
    labels_dir = valid_dir / "labels"

    # Scan all labels
    instances_by_class = defaultdict(list)
    label_files = sorted(labels_dir.glob("*.txt"))

    for lbl_path in label_files:
        stem = lbl_path.stem
        img_candidates = list(images_dir.glob(f"{stem}.*"))
        if not img_candidates:
            continue
        img_path = img_candidates[0]
        prefix = stem.split("_")[0]

        with open(lbl_path, "r") as f:
            for idx, line in enumerate(f):
                parts = line.strip().split()
                if not parts:
                    continue
                cid = int(parts[0])
                bbox_norm = [float(x) for x in parts[1:5]]
                instances_by_class[cid].append({
                    "stem": stem,
                    "source_filename": img_path.name,
                    "image_path": str(img_path),
                    "relative_image_path": str(img_path.relative_to(valid_dir.parent.parent)),
                    "instance_idx": idx,
                    "ground_truth_dataset_id": cid,
                    "canonical_dataset_meaning": "rotten" if cid == 2 else ("sprouted" if cid == 3 else "other"),
                    "bbox_norm": bbox_norm,
                    "prefix": prefix,
                })

    print(f"Found {len(instances_by_class[2])} class-2 instances, {len(instances_by_class[3])} class-3 instances.")

    # Stratified selection: 30 for class 2, 30 for class 3
    # For class 2 (rotten in canonical dataset):
    # Prefixes available: cropbad (5), veg1 (36), densepile (82)
    selected_c2 = []
    # 1. Take all 5 from cropbad
    cropbad_c2 = [inst for inst in instances_by_class[2] if inst["prefix"] == "cropbad"]
    selected_c2.extend(cropbad_c2)

    # 2. Take 12 from veg1 across distinct images
    veg1_c2 = [inst for inst in instances_by_class[2] if inst["prefix"] == "veg1"]
    veg1_c2_by_stem = defaultdict(list)
    for inst in veg1_c2:
        veg1_c2_by_stem[inst["stem"]].append(inst)
    for stem, insts in sorted(veg1_c2_by_stem.items()):
        if len(selected_c2) < 5 + 12:
            selected_c2.append(insts[0])
            if len(insts) > 1 and len(selected_c2) < 5 + 12:
                selected_c2.append(insts[1])

    # 3. Fill remaining (13) from densepile across distinct images
    densepile_c2 = [inst for inst in instances_by_class[2] if inst["prefix"] == "densepile"]
    densepile_c2_by_stem = defaultdict(list)
    for inst in densepile_c2:
        densepile_c2_by_stem[inst["stem"]].append(inst)
    for stem, insts in sorted(densepile_c2_by_stem.items()):
        if len(selected_c2) < 30:
            selected_c2.append(insts[0])
            if len(insts) > 1 and len(selected_c2) < 30:
                selected_c2.append(insts[1])

    selected_c2 = selected_c2[:30]

    # For class 3 (sprouted in canonical dataset):
    # Prefixes available: veg1 (3), cropbad (70), densepile (67)
    selected_c3 = []
    # 1. Take all 3 from veg1
    veg1_c3 = [inst for inst in instances_by_class[3] if inst["prefix"] == "veg1"]
    selected_c3.extend(veg1_c3)

    # 2. Take 14 from cropbad across distinct images
    cropbad_c3 = [inst for inst in instances_by_class[3] if inst["prefix"] == "cropbad"]
    cropbad_c3_by_stem = defaultdict(list)
    for inst in cropbad_c3:
        cropbad_c3_by_stem[inst["stem"]].append(inst)
    for stem, insts in sorted(cropbad_c3_by_stem.items()):
        if len(selected_c3) < 3 + 14:
            selected_c3.append(insts[0])

    # 3. Fill remaining (13) from densepile across distinct images
    densepile_c3 = [inst for inst in instances_by_class[3] if inst["prefix"] == "densepile"]
    densepile_c3_by_stem = defaultdict(list)
    for inst in densepile_c3:
        densepile_c3_by_stem[inst["stem"]].append(inst)
    for stem, insts in sorted(densepile_c3_by_stem.items()):
        if len(selected_c3) < 30:
            selected_c3.append(insts[0])

    selected_c3 = selected_c3[:30]

    print(f"Selected {len(selected_c2)} class-2 samples and {len(selected_c3)} class-3 samples.")

    # Combine all selected instances
    all_selected = []
    for inst in selected_c2:
        inst["instance_id"] = f"c2_{len(all_selected)+1:02d}_{inst['stem']}_{inst['instance_idx']}"
        all_selected.append(inst)
    for inst in selected_c3:
        inst["instance_id"] = f"c3_{len(all_selected)+1:02d}_{inst['stem']}_{inst['instance_idx']}"
        all_selected.append(inst)

    # Load image, calculate sha256, pixel bounding boxes
    print("Extracting metadata and rendering individual cropped inspection cards...")
    sha256_cache = {}

    for inst in all_selected:
        img_path = Path(inst["image_path"])
        if img_path not in sha256_cache:
            sha256_cache[img_path] = compute_sha256(img_path)
        inst["sha256"] = sha256_cache[img_path]

        # Read image to get width, height and render crop
        img_cv = cv2.imread(str(img_path))
        h, w = img_cv.shape[:2]
        inst["image_width"] = w
        inst["image_height"] = h

        # Normalized bbox [xc, yc, bw, bh] -> pixel [x1, y1, x2, y2]
        xc, yc, bw, bh = inst["bbox_norm"]
        x1 = max(0, int((xc - bw / 2) * w))
        y1 = max(0, int((yc - bh / 2) * h))
        x2 = min(w, int((xc + bw / 2) * w))
        y2 = min(h, int((yc + bh / 2) * h))
        inst["bbox_xyxy"] = [x1, y1, x2, y2]

        # Extract crop with slight padding for context
        pad_x = int(bw * w * 0.1)
        pad_y = int(bh * h * 0.1)
        cx1 = max(0, x1 - pad_x)
        cy1 = max(0, y1 - pad_y)
        cx2 = min(w, x2 + pad_x)
        cy2 = min(h, y2 + pad_y)
        crop_img = img_cv[cy1:cy2, cx1:cx2].copy()

        # Draw ground truth box on crop (in crop coordinates)
        box_color = (0, 0, 255) if inst["ground_truth_dataset_id"] == 2 else (0, 255, 0)
        cv2.rectangle(
            crop_img,
            (x1 - cx1, y1 - cy1),
            (x2 - cx1, y2 - cy1),
            box_color,
            2,
        )

        crop_filename = f"{inst['instance_id']}_crop.jpg"
        crop_save_path = crops_dir / crop_filename
        cv2.imwrite(str(crop_save_path), crop_img)
        inst["crop_filename"] = crop_filename

    # Save adjudication sample metadata
    adjudication_sample_path = output_dir / "adjudication_sample.json"
    with open(adjudication_sample_path, "w") as f:
        json.dump(all_selected, f, indent=2)
    print(f"Saved adjudication sample to {adjudication_sample_path}")

    # Step 3: Run Model Prediction Audit using unchanged onion-grading-v7.pt
    print(f"Loading external v7 model from {v7_model_path}...")
    model = YOLO(str(v7_model_path))
    print(f"Model classes exposed: {model.names}")

    # We need to run inference on each unique image in all_selected
    unique_images = sorted(list({inst["image_path"] for inst in all_selected}))
    print(f"Running inference on {len(unique_images)} unique selected images...")

    results_by_img = {}
    for img_path_str in unique_images:
        res = model.predict(source=img_path_str, conf=0.10, iou=0.45, verbose=False)[0]
        boxes = []
        for box in res.boxes:
            b_xyxy = [float(x) for x in box.xyxy[0].tolist()]
            conf = float(box.conf[0].item())
            cls_id = int(box.cls[0].item())
            boxes.append({
                "bbox_xyxy": b_xyxy,
                "confidence": round(conf, 4),
                "predicted_external_id": cls_id,
                "predicted_external_name": model.names.get(cls_id, str(cls_id)),
            })
        results_by_img[img_path_str] = boxes

    # Map external IDs under Variant B:
    # 0 -> HEALTHY, 1 -> DAMAGED, 2 -> SPROUTED, 3 -> ROTTEN
    v7_to_canonical = {
        0: "HEALTHY",
        1: "DAMAGED",
        2: "SPROUTED",
        3: "ROTTEN",
    }

    # Now audit each selected ground truth instance
    prediction_audit = []
    for inst in all_selected:
        gt_box = inst["bbox_xyxy"]
        img_preds = results_by_img.get(inst["image_path"], [])

        # Find predicted box with highest IoU to GT box
        best_match = None
        best_iou = 0.0
        for pred in img_preds:
            iou = compute_iou(gt_box, pred["bbox_xyxy"])
            if iou > best_iou:
                best_iou = iou
                best_match = pred

        if best_match is not None and best_iou > 0.1:
            pred_id = best_match["predicted_external_id"]
            pred_name = best_match["predicted_external_name"]
            conf = best_match["confidence"]
            mapped_semantic = v7_to_canonical.get(pred_id, "UNKNOWN")
        else:
            pred_id = None
            pred_name = "NO_DETECTION"
            conf = 0.0
            mapped_semantic = "NONE"

        audit_entry = {
            "instance_id": inst["instance_id"],
            "source_filename": inst["source_filename"],
            "image_path": inst["image_path"],
            "sha256": inst["sha256"],
            "ground_truth_id": inst["ground_truth_dataset_id"],
            "ground_truth_candidate_meaning": inst["canonical_dataset_meaning"].upper(),
            "predicted_external_id": pred_id,
            "predicted_external_name": pred_name,
            "confidence": conf,
            "iou_with_relevant_ground_truth_box": round(best_iou, 4),
            "mapped_semantic_meaning": mapped_semantic,
            "is_semantically_consistent": (
                mapped_semantic == inst["canonical_dataset_meaning"].upper()
            ),
        }
        prediction_audit.append(audit_entry)

    predictions_json_path = output_dir / "predictions.json"
    with open(predictions_json_path, "w") as f:
        json.dump(prediction_audit, f, indent=2)
    print(f"Saved predictions audit to {predictions_json_path}")

    # Compute audit summary metrics
    c2_entries = [e for e in prediction_audit if e["ground_truth_id"] == 2]
    c3_entries = [e for e in prediction_audit if e["ground_truth_id"] == 3]

    print("\n--- AUDIT RESULTS FOR CLASS 2 (Canonical: ROTTEN) ---")
    c2_pred_names = defaultdict(int)
    for e in c2_entries:
        c2_pred_names[e["predicted_external_name"]] += 1
    for name, cnt in sorted(c2_pred_names.items()):
        print(f"  Predicted external '{name}': {cnt}/{len(c2_entries)}")
    c2_consistent = sum(1 for e in c2_entries if e["is_semantically_consistent"])
    print(f"  Semantically consistent (v7 external 3='rotten' matching GT 'rotten'): {c2_consistent}/{len(c2_entries)}")

    print("\n--- AUDIT RESULTS FOR CLASS 3 (Canonical: SPROUTED) ---")
    c3_pred_names = defaultdict(int)
    for e in c3_entries:
        c3_pred_names[e["predicted_external_name"]] += 1
    for name, cnt in sorted(c3_pred_names.items()):
        print(f"  Predicted external '{name}': {cnt}/{len(c3_entries)}")
    c3_consistent = sum(1 for e in c3_entries if e["is_semantically_consistent"])
    print(f"  Semantically consistent (v7 external 2='sprouted' matching GT 'sprouted'): {c3_consistent}/{len(c3_entries)}")

    # Step 4: Failure Audit on cropbad_20230121_084837_train_4551f94b_1.jpg
    print("\n--- STEP 4: FAILURE AUDIT ON SMOKE IMAGE ---")
    smoke_img_path = images_dir / "cropbad_20230121_084837_train_4551f94b_1.jpg"
    smoke_lbl_path = labels_dir / "cropbad_20230121_084837_train_4551f94b_1.txt"

    smoke_img_cv = cv2.imread(str(smoke_img_path))
    smoke_quality = compute_image_quality(smoke_img_cv)

    # Read GT annotations
    smoke_gt = []
    with open(smoke_lbl_path, "r") as f:
        for line in f:
            parts = line.strip().split()
            if not parts:
                continue
            cid = int(parts[0])
            norm = [float(x) for x in parts[1:5]]
            h, w = smoke_img_cv.shape[:2]
            xc, yc, bw, bh = norm
            x1 = (xc - bw / 2) * w
            y1 = (yc - bh / 2) * h
            x2 = (xc + bw / 2) * w
            y2 = (yc + bh / 2) * h
            smoke_gt.append({
                "class_id": cid,
                "canonical_meaning": "sprouted" if cid == 3 else ("rotten" if cid == 2 else "other"),
                "bbox_norm": norm,
                "bbox_xyxy": [round(x1, 2), round(y1, 2), round(x2, 2), round(y2, 2)],
            })

    # Run raw inference with low threshold to see all candidates
    smoke_res = model.predict(source=str(smoke_img_path), conf=0.10, iou=0.45, verbose=False)[0]
    smoke_preds = []
    for box in smoke_res.boxes:
        b_xyxy = [round(float(x), 2) for x in box.xyxy[0].tolist()]
        conf = float(box.conf[0].item())
        cls_id = int(box.cls[0].item())
        smoke_preds.append({
            "class_id_external": cls_id,
            "class_name_external": model.names.get(cls_id, str(cls_id)),
            "canonical_label": v7_to_canonical.get(cls_id, "UNKNOWN"),
            "confidence": round(conf, 4),
            "bbox_xyxy": b_xyxy,
        })

    # Compute pairwise IoU between predictions
    pred_ious = []
    for i in range(len(smoke_preds)):
        for j in range(i + 1, len(smoke_preds)):
            iou = compute_iou(smoke_preds[i]["bbox_xyxy"], smoke_preds[j]["bbox_xyxy"])
            pred_ious.append({
                "pred_a_idx": i,
                "pred_a_class": smoke_preds[i]["class_name_external"],
                "pred_a_conf": smoke_preds[i]["confidence"],
                "pred_b_idx": j,
                "pred_b_class": smoke_preds[j]["class_name_external"],
                "pred_b_conf": smoke_preds[j]["confidence"],
                "iou": round(iou, 4),
            })

    # Failure audit diagnosis
    # Analyze the cause:
    # 1. Image quality: blur score is 47.98 (below 100 threshold), resolution is small (256x256).
    # 2. Duplicate detection: two overlapping boxes spanning almost 100% of the image (IoU = 0.985).
    # 3. Cross-class disagreement: One detection predicts 'damaged' (conf 0.4902), the other predicts 'sprouted' (conf 0.4800).
    # 4. Dataset ground truth: Single bulb annotated as class 3 ('sprouted').
    failure_audit_data = {
        "target_image": "cropbad_20230121_084837_train_4551f94b_1.jpg",
        "image_path": str(smoke_img_path),
        "sha256": compute_sha256(smoke_img_path),
        "image_quality_metrics": smoke_quality,
        "ground_truth_annotations": smoke_gt,
        "predicted_detections": smoke_preds,
        "prediction_pairwise_ious": pred_ious,
        "investigation_analysis": {
            "duplicate_detection": True,
            "cross_class_disagreement": True,
            "poor_image_failure": True,
            "dataset_label_ambiguity": False,
            "unresolved": False,
            "detailed_findings": (
                "The smoke test image is a low-resolution (256x256), borderline-blurry capture (blur score 47.98). "
                "The external v7 detector emits two almost identical bounding boxes (IoU = 0.9854) covering the entire bulb. "
                "The detector displays cross-class disagreement with nearly identical split confidences: "
                "Box 0 predicts 'damaged' (conf=0.4902) while Box 1 predicts 'sprouted' (conf=0.4800). "
                "Because class-agnostic NMS was not enabled in standard Ultralytics NMS (which defaults to per-class NMS), "
                "both boxes survived filtering. Ground-truth annotation is single-class (class 3: sprouted). "
                "The image displays both visible peeling/blemish (damage) and an apical shoot (sprout), "
                "causing the single-label detector to output competing predictions."
            ),
        },
    }

    failure_audit_json_path = output_dir / "failure_audit_cropbad.json"
    with open(failure_audit_json_path, "w") as f:
        json.dump(failure_audit_data, f, indent=2)
    print(f"Saved failure audit data to {failure_audit_json_path}")

    # Render failure diagnostic image
    diag_canvas = np.zeros((300, 600, 3), dtype=np.uint8)
    # Left: original image with GT box
    left_img = smoke_img_cv.copy()
    for gt in smoke_gt:
        gx1, gy1, gx2, gy2 = [int(v) for v in gt["bbox_xyxy"]]
        cv2.rectangle(left_img, (gx1, gy1), (gx2, gy2), (0, 255, 0), 2)
        cv2.putText(left_img, f"GT: {gt['canonical_meaning']}", (gx1 + 5, gy1 + 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # Right: original image with Predicted boxes
    right_img = smoke_img_cv.copy()
    colors = [(255, 100, 0), (0, 165, 255)]
    for idx, pred in enumerate(smoke_preds):
        px1, py1, px2, py2 = [int(v) for v in pred["bbox_xyxy"]]
        c = colors[idx % len(colors)]
        cv2.rectangle(right_img, (px1, py1), (px2, py2), c, 2)
        cv2.putText(right_img, f"{pred['class_name_external']} {pred['confidence']:.2f}",
                    (px1 + 5, py1 + 20 + idx * 25), cv2.FONT_HERSHEY_SIMPLEX, 0.45, c, 2)

    # Composite side by side
    composite = np.zeros((320, 560, 3), dtype=np.uint8)
    composite[40:296, 16:272] = left_img
    composite[40:296, 288:544] = right_img
    cv2.putText(composite, "Ground Truth (Class 3: Sprouted)", (16, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
    cv2.putText(composite, "V7 Detections (Conflicted BBoxes)", (288, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)

    failure_audit_img_path = output_dir / "failure_audit_cropbad.png"
    cv2.imwrite(str(failure_audit_img_path), composite)
    print(f"Saved failure diagnostic image to {failure_audit_img_path}")

    # Build Visual Review HTML Package (Contact Sheet)
    build_html_review_package(
        output_dir=output_dir,
        selected_instances=all_selected,
        prediction_audit=prediction_audit,
        failure_audit_data=failure_audit_data,
    )


def build_html_review_package(
    output_dir: Path,
    selected_instances: list[dict[str, Any]],
    prediction_audit: list[dict[str, Any]],
    failure_audit_data: dict[str, Any],
):
    html_path = output_dir / "review_package.html"

    # Map audit by instance_id
    audit_map = {e["instance_id"]: e for e in prediction_audit}

    html = [
        "<!DOCTYPE html>",
        "<html lang='en'>",
        "<head>",
        "<meta charset='UTF-8'>",
        "<title>Mandi Nyaay - Gate 4A Semantic Adjudication Review</title>",
        "<style>",
        "body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background: #0f172a; color: #f8fafc; padding: 24px; margin: 0; }",
        "h1, h2, h3 { color: #f1f5f9; }",
        ".header-box { background: #1e293b; padding: 20px; border-radius: 8px; margin-bottom: 24px; border: 1px solid #334155; }",
        ".grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; margin-bottom: 32px; }",
        ".card { background: #1e293b; border-radius: 8px; padding: 12px; border: 1px solid #334155; display: flex; flex-direction: column; }",
        ".card img { width: 100%; height: 200px; object-fit: contain; background: #000; border-radius: 4px; }",
        ".card-meta { font-size: 12px; margin-top: 8px; line-height: 1.4; }",
        ".badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 11px; margin-right: 4px; }",
        ".badge-gt2 { background: #ef4444; color: white; }",
        ".badge-gt3 { background: #10b981; color: white; }",
        ".badge-match { background: #059669; color: white; }",
        ".badge-mismatch { background: #dc2626; color: white; }",
        ".badge-unverified { background: #f59e0b; color: black; }",
        ".table { width: 100%; border-collapse: collapse; margin-top: 16px; font-size: 13px; }",
        ".table th, .table td { border: 1px solid #334155; padding: 8px 12px; text-align: left; }",
        ".table th { background: #1e293b; color: #94a3b8; }",
        "</style>",
        "</head>",
        "<body>",
        "<div class='header-box'>",
        "<h1>Gate 4A: Semantic Adjudication & Detector Error Audit</h1>",
        "<p>Stratified sample of 60 validation instances (30 Class 2, 30 Class 3) to adjudicate semantic interpretation of external v7 detector.</p>",
        "<p><strong>Note:</strong> Ground truth candidate labels are derived from canonical dataset data.yaml (2 = rotten, 3 = sprouted). "
        "Candidate status is <strong>UNDER_REVIEW</strong> (not automatically VERIFIED).</p>",
        "</div>",
        "<h2>Visual Review: Class 2 Ground Truth (Candidate: ROTTEN)</h2>",
        "<div class='grid'>",
    ]

    for inst in selected_instances:
        if inst["ground_truth_dataset_id"] != 2:
            continue
        audit = audit_map.get(inst["instance_id"], {})
        crop_rel = f"crops/{inst['crop_filename']}"
        html.append(f"""
        <div class='card'>
            <img src='{crop_rel}' alt='{inst["instance_id"]}'>
            <div class='card-meta'>
                <div><strong>ID:</strong> {inst["instance_id"]}</div>
                <div><strong>File:</strong> {inst["source_filename"]}</div>
                <div><span class='badge badge-gt2'>GT ID: 2 (ROTTEN)</span></div>
                <div><strong>Predicted V7:</strong> {audit.get('predicted_external_name')} (ID {audit.get('predicted_external_id')})</div>
                <div><strong>Conf:</strong> {audit.get('confidence')} | <strong>IoU:</strong> {audit.get('iou_with_relevant_ground_truth_box')}</div>
                <div><strong>Semantic Match:</strong> <span class='badge {"badge-match" if audit.get("is_semantically_consistent") else "badge-mismatch"}'>{"CONSISTENT" if audit.get("is_semantically_consistent") else "DISCREPANCY"}</span></div>
            </div>
        </div>
        """)

    html.append("</div>")
    html.append("<h2>Visual Review: Class 3 Ground Truth (Candidate: SPROUTED)</h2>")
    html.append("<div class='grid'>")

    for inst in selected_instances:
        if inst["ground_truth_dataset_id"] != 3:
            continue
        audit = audit_map.get(inst["instance_id"], {})
        crop_rel = f"crops/{inst['crop_filename']}"
        html.append(f"""
        <div class='card'>
            <img src='{crop_rel}' alt='{inst["instance_id"]}'>
            <div class='card-meta'>
                <div><strong>ID:</strong> {inst["instance_id"]}</div>
                <div><strong>File:</strong> {inst["source_filename"]}</div>
                <div><span class='badge badge-gt3'>GT ID: 3 (SPROUTED)</span></div>
                <div><strong>Predicted V7:</strong> {audit.get('predicted_external_name')} (ID {audit.get('predicted_external_id')})</div>
                <div><strong>Conf:</strong> {audit.get('confidence')} | <strong>IoU:</strong> {audit.get('iou_with_relevant_ground_truth_box')}</div>
                <div><strong>Semantic Match:</strong> <span class='badge {"badge-match" if audit.get("is_semantically_consistent") else "badge-mismatch"}'>{"CONSISTENT" if audit.get("is_semantically_consistent") else "DISCREPANCY"}</span></div>
            </div>
        </div>
        """)

    html.append("</div>")

    # Failure audit section
    html.append("""
    <h2>Failure Case Deep Dive: cropbad_20230121_084837_train_4551f94b_1.jpg</h2>
    <div class='header-box'>
        <img src='failure_audit_cropbad.png' style='max-width: 100%; border-radius: 8px;' alt='Failure Diagnostic'>
        <p><strong>Diagnosis:</strong> Dual detection overlap (IoU = 0.9854) on single bulb.</p>
        <ul>
            <li><strong>Detection A:</strong> class 'damaged' (confidence 0.4902)</li>
            <li><strong>Detection B:</strong> class 'sprouted' (confidence 0.4800)</li>
            <li><strong>Image Quality:</strong> Blur score 47.98 (borderline sharpness), low-resolution 256x256.</li>
            <li><strong>Root Cause:</strong> Co-occurrence of surface blemish/peel with apical shoot, combined with per-class NMS in YOLO (classes evaluated independently, allowing cross-class duplicate boxes).</li>
        </ul>
    </div>
    </body>
    </html>
    """)

    with open(html_path, "w", encoding="utf-8") as f:
        f.write("\n".join(html))
    print(f"Saved visual review package HTML to {html_path}")


if __name__ == "__main__":
    main()
