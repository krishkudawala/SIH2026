"""
Gate 1 Physical Calibration & Planar Measurement Evaluation Tool.

Evaluates real photographs containing physical ArUco reference markers and known
planar reference objects. Measures projective homography, reprojection residuals,
and evaluates planar dimensional accuracy against direct caliper ground truth.

STRICT FIELD TRUTH POLICY:
- Requires operator-supplied caliper measurement of the printed marker (--caliper-marker-mm).
- Never guesses or substitutes nominal dimensions without physical verification.
- Automatic reference-object segmentation is NOT IMPLEMENTED; reference measurements
  require explicit operator pixel coordinates (--reference-points-px x1,y1,x2,y2).
"""

import argparse
import json
from pathlib import Path
import sys
import cv2
import numpy as np

from app.config import load_config
from app.cv.calibration import (
    PLANAR_LIMITATION_DISCLAIMER,
    evaluate_reference_object_measurement,
    measure_planar_distance_mm,
)
from app.cv.marker import detect_marker
from app.domain.status import InspectionStatus
from app.version import get_processing_version


def find_candidate_images(raw_dir: Path) -> list[Path]:
    """Find candidate real image files in raw directory."""
    extensions = ("*.jpg", "*.jpeg", "*.png", "*.bmp", "*.tiff")
    images = []
    for ext in extensions:
        images.extend(raw_dir.glob(ext))
    return sorted(images)


def parse_points(points_str: str) -> tuple[tuple[float, float], tuple[float, float]]:
    """Parse 'x1,y1,x2,y2' into ((x1, y1), (x2, y2))."""
    parts = [float(p.strip()) for p in points_str.split(",")]
    if len(parts) != 4:
        raise ValueError("Points must be formatted as x1,y1,x2,y2")
    return (parts[0], parts[1]), (parts[2], parts[3])


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Mandi Nyaay Gate 1 Calibration & Planar Measurement Evaluator"
    )
    parser.add_argument("--image", type=str, default=None, help="Path to input photograph in data/raw/")
    parser.add_argument("--config", type=str, default="configs/inspection_config.yaml", help="Path to config file")
    parser.add_argument(
        "--caliper-marker-mm",
        type=float,
        required=True,
        help="REQUIRED: Physical side length of printed marker measured with digital vernier caliper (mm). Never assumed.",
    )
    parser.add_argument(
        "--reference-name",
        type=str,
        default="REFERENCE_OBJECT",
        help="Name of physical reference object (e.g. INR_5_COIN, 40MM_DISC)",
    )
    parser.add_argument(
        "--reference-ground-truth-mm",
        type=float,
        default=None,
        help="Caliper-measured ground-truth diameter of reference object in mm",
    )
    parser.add_argument(
        "--reference-points-px",
        type=str,
        default=None,
        help="Diameter endpoints in pixel coordinates: x1,y1,x2,y2",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/processed",
        help="Directory to save audit JSON and debug image",
    )
    args = parser.parse_args()

    # 1. Physical ground-truth validation: caliper measurement is mandatory
    if args.caliper_marker_mm is None or args.caliper_marker_mm <= 0:
        print(
            "ERROR: INVALID_CONFIGURATION. --caliper-marker-mm must be provided with a positive value.",
            file=sys.stderr,
        )
        return 1

    # Load configuration and override nominal physical size with actual caliper measurement
    config = load_config(args.config)
    config.marker.physical_size_mm = args.caliper_marker_mm

    # 2. Resolve image path
    image_path: Path | None = None
    if args.image:
        image_path = Path(args.image)
    else:
        candidates = find_candidate_images(Path("data/raw"))
        if candidates:
            image_path = candidates[0]
            print(f"[Auto-Selected Image]: {image_path.name}", file=sys.stderr)

    if image_path is None or not image_path.is_file():
        print(
            "ERROR: INVALID_CAPTURE. No valid image file found. Please place real photographs into data/raw/ or specify --image.",
            file=sys.stderr,
        )
        return 1

    capture_id = image_path.stem
    image = cv2.imread(str(image_path))
    if image is None or image.size == 0:
        print(f"ERROR: INVALID_CAPTURE. Failed to decode image file at {image_path.resolve()}", file=sys.stderr)
        return 1

    img_h, img_w = image.shape[:2]

    # 3. Detect ArUco reference marker & compute projective homography
    obs = detect_marker(image, config.marker)

    # 4. Planar reference object evaluation
    # Automatic segmentation is explicitly NOT_IMPLEMENTED.
    # Manual coordinate endpoints may be supplied via --reference-points-px.
    reference_eval = None
    ref_pts = None

    if obs.validation_status == InspectionStatus.VALID and obs.homography_matrix is not None:
        H = np.array(obs.homography_matrix, dtype=np.float32)

        if args.reference_points_px:
            try:
                pt1, pt2 = parse_points(args.reference_points_px)
                ref_pts = (pt1, pt2)
                measured_diam_mm = measure_planar_distance_mm(pt1, pt2, H)

                if args.reference_ground_truth_mm is not None:
                    eval_data = evaluate_reference_object_measurement(
                        measured_diameter_mm=measured_diam_mm,
                        ground_truth_diameter_mm=args.reference_ground_truth_mm,
                    )
                    reference_eval = {
                        "reference_object_detection": "MANUALLY_SUPPLIED_ENDPOINTS",
                        "reference_object_name": args.reference_name,
                        "reference_points_px": [list(pt1), list(pt2)],
                        "ground_truth_diameter_mm": eval_data["ground_truth_diameter_mm"],
                        "measured_planar_diameter_mm": eval_data["measured_planar_diameter_mm"],
                        "absolute_error_mm": eval_data["absolute_error_mm"],
                        "relative_error_pct": eval_data["relative_error_pct"],
                    }
                else:
                    reference_eval = {
                        "reference_object_detection": "MANUALLY_SUPPLIED_ENDPOINTS",
                        "reference_object_name": args.reference_name,
                        "reference_points_px": [list(pt1), list(pt2)],
                        "measured_planar_diameter_mm": round(measured_diam_mm, 3),
                        "ground_truth_diameter_mm": None,
                        "note": "Ground truth diameter not supplied via --reference-ground-truth-mm; relative error omitted.",
                    }
            except Exception as e:
                reference_eval = {
                    "reference_object_detection": "ERROR",
                    "error_message": f"Failed to parse reference points: {e}",
                }
        else:
            reference_eval = {
                "reference_object_detection": "NOT_IMPLEMENTED",
                "note": (
                    "Automatic reference-object detection is NOT implemented. "
                    "Supply explicit diameter endpoints via --reference-points-px x1,y1,x2,y2 to evaluate planar accuracy."
                ),
            }

    # 5. Format comprehensive Gate 1 JSON Report
    report = {
        "gate": "GATE_1_PHYSICAL_CALIBRATION",
        "capture_id": capture_id,
        "image_file": image_path.name,
        "image_resolution_px": [img_w, img_h],
        "processing_version": get_processing_version(),
        "marker_detection": {
            "marker_detected": obs.detected,
            "detected_marker_id": obs.marker_id,
            "expected_marker_id": config.marker.expected_marker_id,
            "dictionary": obs.dictionary,
            "corners_px": obs.corners_px,
            "side_lengths_px": obs.marker_side_lengths_px,
            "quadrilateral_area_px": obs.marker_area_px,
            "physical_size_mm": obs.physical_size_mm,
            "validation_status": obs.validation_status.value,
            "failure_codes": [fc.value for fc in obs.failure_codes],
        },
        "planar_calibration": {
            "homography_matrix": obs.homography_matrix,
            "reprojection_error_px": obs.reprojection_error_px,
            "diagnostic_scale_mm_per_px": obs.diagnostic_scale_mm_per_px,
            "measurement_domain": "PLANAR_METRIC_MEASUREMENT",
            "limitation_disclaimer": PLANAR_LIMITATION_DISCLAIMER,
        },
        "reference_object_validation": reference_eval,
    }

    # 6. Save JSON and visualization
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{capture_id}_gate1_validation.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    # Save visual debug overlay
    debug_path = out_dir / f"{capture_id}_gate1_debug.png"
    debug_img = image.copy()
    if obs.corners_px is not None:
        pts = np.array(obs.corners_px, dtype=np.int32).reshape((-1, 1, 2))
        color = (0, 255, 0) if obs.validation_status == InspectionStatus.VALID else (0, 0, 255)
        cv2.polylines(debug_img, [pts], isClosed=True, color=color, thickness=3)
        c0 = (int(obs.corners_px[0][0]), int(obs.corners_px[0][1]))
        cv2.circle(debug_img, c0, radius=6, color=(0, 255, 255), thickness=-1)
        cv2.putText(
            debug_img,
            f"ID:{obs.marker_id} Reproj:{obs.reprojection_error_px}px",
            (max(10, c0[0] - 20), max(25, c0[1] - 15)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            color,
            2,
            cv2.LINE_AA,
        )

    if ref_pts is not None:
        p1 = (int(ref_pts[0][0]), int(ref_pts[0][1]))
        p2 = (int(ref_pts[1][0]), int(ref_pts[1][1]))
        cv2.line(debug_img, p1, p2, (255, 100, 0), 2)
        cv2.circle(debug_img, p1, 4, (255, 100, 0), -1)
        cv2.circle(debug_img, p2, 4, (255, 100, 0), -1)
        cv2.putText(debug_img, "REF_DIAMETER", (p1[0], p1[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 100, 0), 2)

    cv2.imwrite(str(debug_path), debug_img)

    # Print summary to stdout
    print(json.dumps(report, indent=2))
    print(f"\n[Gate 1 Audit Saved]: {json_path.resolve()}", file=sys.stderr)
    print(f"[Debug Overlay Saved]: {debug_path.resolve()}", file=sys.stderr)

    return 0 if obs.validation_status == InspectionStatus.VALID else 2


if __name__ == "__main__":
    sys.exit(main())
