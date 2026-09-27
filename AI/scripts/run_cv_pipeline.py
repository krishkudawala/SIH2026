"""
CLI interface to execute the Mandi Nyaay Computer Vision Pipeline on an image.

Usage:
    python scripts/run_cv_pipeline.py --image <path_to_image> [--checkpoint <path_to_pt>] [--output <output_json>]
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.cv.label_mapping import V7_MAPPING_VARIANT_A, V7_MAPPING_VARIANT_B
from app.pipeline.cv_pipeline import MandiNyaayCVPipeline


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run Mandi Nyaay CV pipeline on a target image."
    )
    parser.add_argument(
        "--image",
        type=str,
        required=True,
        help="Path to the input image"
    )
    parser.add_argument(
        "--checkpoint",
        type=str,
        default=r"../Onion_grading_system/onion-grading-v7.pt",
        help="Path to YOLO detection model checkpoint"
    )
    parser.add_argument(
        "--mapping-variant",
        type=str,
        choices=["A", "B"],
        default="A",
        help="Class mapping variant: A (canonical assumption 0:healthy,1:damaged,2:rotten,3:sprouted), B (checkpoint strings 2:sprouted,3:rotten)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Optional path to write result JSON"
    )

    args = parser.parse_args()

    mapping = V7_MAPPING_VARIANT_A if args.mapping_variant == "A" else V7_MAPPING_VARIANT_B
    checkpoint_path = Path(args.checkpoint)

    if not checkpoint_path.exists():
        err_out = {
            "error": "Checkpoint not found",
            "checkpoint_path": str(checkpoint_path.resolve()),
            "status": "ERROR"
        }
        print(json.dumps(err_out, indent=2))
        return 1

    pipeline = MandiNyaayCVPipeline(
        checkpoint_path=checkpoint_path,
        mapping=mapping,
    )

    result = pipeline.process_image(
        image_input=args.image,
        capture_id=Path(args.image).stem,
    )

    result_json = result.model_dump_json(indent=2)
    print(result_json)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(result_json)

    return 0 if result.pipeline_status in ("SUCCESS", "QUALITY_WARN") else 1


if __name__ == "__main__":
    sys.exit(main())
