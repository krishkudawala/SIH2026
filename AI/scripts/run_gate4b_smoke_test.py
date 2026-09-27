"""
Gate 4B Smoke Test Script.

Runs the integrated CV pipeline (with image quality screening, YOLO v7 inference,
verified canonical mapping, and cross-class observation reconciliation) on real
external validation images from merged_v2/valid.

Outputs results to AI/artifacts/gate4b/.
"""

import json
from pathlib import Path
import cv2
import numpy as np

from app.cv.label_mapping import V7_EXTERNAL_ADAPTER_MAPPING
from app.pipeline.cv_pipeline import MandiNyaayCVPipeline


def main():
    base_dir = Path(__file__).resolve().parent.parent
    checkpoint_path = Path("../Onion_grading_system/onion-grading-v7.pt").resolve()
    valid_images_dir = Path("../Onion_grading_system/training/merged_v2/valid/images").resolve()
    output_dir = base_dir / "artifacts" / "gate4b"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Initializing MandiNyaayCVPipeline with model {checkpoint_path}...")
    pipeline = MandiNyaayCVPipeline(
        checkpoint_path=checkpoint_path,
        mapping=V7_EXTERNAL_ADAPTER_MAPPING,
        conf_threshold=0.25,
        min_reliable_confidence=0.40,
        reconciliation_iou_threshold=0.70,
    )

    # 1. Target Smoke Image: cropbad_20230121_084837_train_4551f94b_1.jpg
    # (Previously emitted 2 overlapping detections: damaged 0.49 vs sprouted 0.48)
    smoke_img_path = valid_images_dir / "cropbad_20230121_084837_train_4551f94b_1.jpg"
    print(f"\n--- RUNNING SMOKE TEST ON: {smoke_img_path.name} ---")

    result = pipeline.process_image(smoke_img_path, capture_id="gate4b_smoke_cropbad")

    result_dict = result.model_dump()
    out_json_path = output_dir / "smoke_test_cropbad.json"
    with open(out_json_path, "w") as f:
        json.dump(result_dict, f, indent=2)
    print(f"Saved smoke test result to {out_json_path}")

    print(f"  Quality Grade: {result.quality.grade if result.quality else 'N/A'}")
    print(f"  Raw Detections: {result.raw_detection_count}")
    print(f"  Reconciled Observations: {result.reconciled_observation_count}")
    print(f"  Conflicts: {result.conflict_count}")
    print(f"  Calibration Status: {result.calibration_status}")
    print(f"  Measurement Status: {result.measurement_status.value}")

    for idx, obs in enumerate(result.observations):
        print(f"  Observation {idx}:")
        print(f"    Status: {obs.observation_status.value}")
        print(f"    Semantic: {obs.class_semantic.value}")
        print(f"    Confidence: {obs.confidence}")
        print(f"    Candidate Classes: {[c.value for c in obs.candidate_classes]}")
        print(f"    Candidate Confidences: {obs.candidate_confidences}")
        print(f"    Source Detection IDs: {obs.source_detection_ids}")
        print(f"    IoU: {obs.reconciliation_iou}")

    # Render diagnostic image for smoke image
    img_cv = cv2.imread(str(smoke_img_path))
    if img_cv is not None:
        h, w = img_cv.shape[:2]
        canvas = np.zeros((h + 80, w * 2 + 30, 3), dtype=np.uint8)

        # Left panel: Raw detections
        left = img_cv.copy()
        colors = [(0, 165, 255), (0, 255, 0), (255, 0, 0), (0, 0, 255)]
        for idx, det in enumerate(result.detections):
            c = colors[idx % len(colors)]
            x1, y1, x2, y2 = [int(v) for v in (det.x1, det.y1, det.x2, det.y2)]
            cv2.rectangle(left, (x1, y1), (x2, y2), c, 2)
            cv2.putText(left, f"{det.class_name_external} {det.confidence:.2f}",
                        (x1 + 4, y1 + 18 + idx * 22), cv2.FONT_HERSHEY_SIMPLEX, 0.45, c, 2)

        # Right panel: Reconciled observation
        right = img_cv.copy()
        for idx, obs in enumerate(result.observations):
            x1, y1, x2, y2 = [int(v) for v in obs.bbox]
            color = (0, 0, 255) if obs.observation_status.value == "CLASS_CONFLICT" else (0, 255, 0)
            cv2.rectangle(right, (x1, y1), (x2, y2), color, 2)
            cv2.putText(right, f"Status: {obs.observation_status.value}",
                        (x1 + 4, y1 + 18), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 2)
            if obs.candidate_classes:
                classes_str = "+".join([c.value for c in obs.candidate_classes])
                cv2.putText(right, f"Candidates: {classes_str}",
                            (x1 + 4, y1 + 38), cv2.FONT_HERSHEY_SIMPLEX, 0.40, color, 1)

        canvas[60:60 + h, 10:10 + w] = left
        canvas[60:60 + h, 20 + w:20 + 2 * w] = right

        cv2.putText(canvas, f"Raw Detections ({result.raw_detection_count} boxes)", (10, 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        cv2.putText(canvas, f"Reconciled ({result.reconciled_observation_count} physical onion, {result.conflict_count} conflict)",
                    (20 + w, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)

        diag_img_path = output_dir / "smoke_cropbad_reconciled.png"
        cv2.imwrite(str(diag_img_path), canvas)
        print(f"Saved diagnostic visualization to {diag_img_path}")

    # 2. Run on Dense Validation Image: densepile_valid_0000.jpg
    dense_img_path = valid_images_dir / "densepile_valid_0000.jpg"
    if dense_img_path.exists():
        print(f"\n--- RUNNING ON DENSE IMAGE: {dense_img_path.name} ---")
        dense_res = pipeline.process_image(dense_img_path, capture_id="gate4b_dense_valid_0000")
        dense_out_path = output_dir / "smoke_test_densepile.json"
        with open(dense_out_path, "w") as f:
            json.dump(dense_res.model_dump(), f, indent=2)
        print(f"Saved dense result to {dense_out_path}")
        print(f"  Raw Detections: {dense_res.raw_detection_count}")
        print(f"  Reconciled Observations: {dense_res.reconciled_observation_count}")
        print(f"  Conflicts: {dense_res.conflict_count}")


if __name__ == "__main__":
    main()
