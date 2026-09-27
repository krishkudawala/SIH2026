"""
Executable script for Phase 1 ArUco reference marker detection and validation.

Executes genuine OpenCV detection on an image, performs geometric sanity validation,
emits the canonical validation JSON, and saves a debug visualization artifact.
"""

import argparse
import json
from pathlib import Path
import sys
import cv2

from app.config import load_config
from app.cv.marker import detect_marker, save_marker_debug_visualization
from app.domain.status import InspectionStatus


def find_candidate_images(raw_dir: Path) -> list[Path]:
    """Find supported image files in raw directory."""
    extensions = ("*.jpg", "*.jpeg", "*.png", "*.bmp", "*.tiff")
    images = []
    for ext in extensions:
        images.extend(raw_dir.glob(ext))
    return sorted(images)


def main() -> int:
    parser = argparse.ArgumentParser(description="Mandi Nyaay ArUco Reference Marker Validation")
    parser.add_argument("--image", type=str, default=None, help="Path to input image")
    parser.add_argument("--config", type=str, default="configs/inspection_config.yaml", help="Path to config file")
    parser.add_argument("--output-json", type=str, default=None, help="Path to save output JSON")
    parser.add_argument("--save-debug", action="store_true", default=True, help="Save debug visualization artifact")
    args = parser.parse_args()

    # 1. Load configuration
    config = load_config(args.config)

    # 2. Resolve image path
    image_path: Path | None = None
    if args.image:
        image_path = Path(args.image)
    else:
        candidates = find_candidate_images(Path("data/raw"))
        if candidates:
            image_path = candidates[0]
            print(f"Auto-selected candidate image from data/raw/: {image_path.name}", file=sys.stderr)

    if image_path is None:
        print("ERROR: No image provided and no candidate images found in data/raw/.", file=sys.stderr)
        print("Please place a real field photograph into data/raw/ or specify --image <path>.", file=sys.stderr)
        return 1

    capture_id = image_path.stem

    # 3. Read image
    if not image_path.is_file():
        print(f"ERROR: Image file not found: {image_path.resolve()}", file=sys.stderr)
        image = None
    else:
        image = cv2.imread(str(image_path))

    # 4. Run real ArUco detection & validation
    observation = detect_marker(image, config.marker)

    # 5. Save debug visualization if corners were detected
    debug_path = None
    if args.save_debug and image is not None and observation.corners_px is not None:
        output_dir = Path("data/processed")
        output_dir.mkdir(parents=True, exist_ok=True)
        debug_path = output_dir / f"{capture_id}_marker_debug.png"
        save_marker_debug_visualization(image, observation, debug_path)

    # 6. Format canonical JSON output
    result_json = observation.to_validation_json(capture_id=capture_id)

    # Print JSON output to stdout
    print(json.dumps(result_json, indent=2))

    # Save JSON artifact
    json_dest = Path(args.output_json) if args.output_json else Path("data/processed") / f"{capture_id}_marker_validation.json"
    json_dest.parent.mkdir(parents=True, exist_ok=True)
    with open(json_dest, "w", encoding="utf-8") as f:
        json.dump(result_json, f, indent=2)

    if debug_path:
        print(f"\n[Debug Artifact] Saved visualization: {debug_path}", file=sys.stderr)
    print(f"[JSON Artifact] Saved validation output: {json_dest}", file=sys.stderr)

    return 0 if observation.validation_status == InspectionStatus.VALID else 2


if __name__ == "__main__":
    sys.exit(main())
