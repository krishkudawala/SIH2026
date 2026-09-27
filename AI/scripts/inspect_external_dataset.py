"""
CLI script to inspect and validate external computer vision datasets for Mandi Nyaay.

Executes deterministic, non-destructive validation over external directories:
- Detects image count, label count, image integrity
- Identifies annotation type (Polygons, BBoxes, Classification, None)
- Checks boundary violations, zero-area masks, duplicates, orphans
- Generates machine-readable manifest JSON
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.cv.dataset_adapter import ExternalDatasetAdapter


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect and validate an external CV dataset without copying or modifying source files."
    )
    parser.add_argument(
        "--dataset-path",
        type=str,
        default=r"Onion_grading_system\training\merged_v2\train\images",
        help="Path to the external dataset directory"
    )
    parser.add_argument(
        "--output-manifest",
        type=str,
        default=r"data/processed/dataset_manifest.json",
        help="Path to write the output JSON manifest"
    )
    parser.add_argument(
        "--dataset-id",
        type=str,
        default="external_onion_v2",
        help="Dataset identifier string"
    )

    args = parser.parse_args()

    input_path = Path(args.dataset_path)
    output_path = Path(args.output_manifest)

    print("=" * 60)
    print("MANDI NYAAY — EXTERNAL DATASET DISCOVERY & AUDIT")
    print("=" * 60)
    print(f"Target Path: {input_path}")
    print(f"Manifest Destination: {output_path}")

    # Check if directory exists
    if not input_path.exists():
        # Check if parent or search path exists
        resolved = input_path.resolve()
        print(f"\n[CRITICAL ERROR] Target path does not exist on disk:")
        print(f"  Specified: {input_path}")
        print(f"  Resolved:  {resolved}")
        print("\nAction Required:")
        print("  Please verify the external dataset location and provide the exact path.")
        
        # Write empty/error manifest
        adapter = ExternalDatasetAdapter(dataset_id=args.dataset_id)
        manifest = adapter.inspect_and_validate(input_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(manifest.model_dump_json(indent=2))
        return 1

    adapter = ExternalDatasetAdapter(dataset_id=args.dataset_id)
    manifest = adapter.inspect_and_validate(input_path)

    # Save manifest
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(manifest.model_dump_json(indent=2))

    print("\n--- AUDIT FINDINGS ---")
    print(f"Total Images Found:      {manifest.total_images_found}")
    print(f"Total Labels Found:      {manifest.total_labels_found}")
    print(f"Valid Records:           {manifest.valid_records_count}")
    print(f"Corrupt/Unreadable:      {manifest.corrupt_images_count}")
    print(f"Missing Labels:          {manifest.missing_labels_count}")
    print(f"Orphan Labels:           {manifest.orphan_labels_count}")
    print(f"Duplicate Images:        {manifest.duplicate_images_count}")
    print(f"Detected Annotation Type:{manifest.detected_annotation_type.value}")
    print(f"Discovered Classes:      {', '.join(manifest.class_names) if manifest.class_names else 'None'}")
    print(f"Split Distribution:      {manifest.split_distribution}")

    if manifest.orphan_label_paths:
        print(f"\nSample Orphan Labels (first 5):")
        for p in manifest.orphan_label_paths[:5]:
            print(f"  - {p}")

    invalid_records = [r for r in manifest.records if not r.is_valid]
    if invalid_records:
        print(f"\nSample Invalid Records (first 5):")
        for r in invalid_records[:5]:
            print(f"  Image: {r.image_path}")
            for err in r.validation_errors:
                print(f"    Error: {err}")

    print(f"\nManifest successfully written to: {output_path.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
