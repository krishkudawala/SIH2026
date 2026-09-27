"""
End-to-End Inspection Demo CLI for Mandi Nyaay (Gate 5H).

Executes the complete vertical slice:
IMAGE -> CV -> RECONCILIATION -> SAMPLING -> AGGREGATION -> DECISION -> REVIEW -> EVIDENCE

Usage:
    python scripts/run_inspection_demo.py --image <path_to_real_image>
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
import sys

# Ensure repository root is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.cv.label_mapping import V7_EXTERNAL_ADAPTER_MAPPING
from app.pipeline.cv_pipeline import MandiNyaayCVPipeline
from app.pipeline.inspection_service import MandiNyaayInspectionService


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run Mandi Nyaay End-to-End Vertical Inspection Slice"
    )
    parser.add_argument(
        "--image",
        type=str,
        required=True,
        help="Path to real onion photographic image",
    )
    parser.add_argument(
        "--checkpoint",
        type=str,
        default=str((BASE_DIR.parent / "Onion_grading_system" / "onion-grading-v7.pt").resolve()),
        help="Path to YOLO v7 model checkpoint",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="inspection_result.json",
        help="Path to save output JSON inspection session result",
    )
    parser.add_argument(
        "--target-sample-size",
        type=int,
        default=20,
        help="Minimum required sample size for lot determination",
    )
    parser.add_argument(
        "--lot-id",
        type=str,
        default="lot_demo_001",
        help="Agricultural lot identifier",
    )
    parser.add_argument(
        "--conf-threshold",
        type=float,
        default=0.25,
        help="Detection confidence threshold",
    )
    parser.add_argument(
        "--iou-threshold",
        type=float,
        default=0.70,
        help="IoU threshold for same-class duplicate collapse and cross-class conflict isolation",
    )
    parser.add_argument(
        "--override-grade",
        type=str,
        default=None,
        choices=["GRADE_A", "URS", "REJECT", "MANUAL_REVIEW"],
        help="Optional manual inspector override grade",
    )
    parser.add_argument(
        "--override-reason",
        type=str,
        default=None,
        help="Inspector rationale for manual override",
    )
    return parser.parse_args()


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    args = parse_args()

    image_path = Path(args.image).resolve()
    if not image_path.exists():
        print(f"ERROR: Image file not found: {image_path}", file=sys.stderr)
        sys.exit(1)

    checkpoint_path = Path(args.checkpoint).resolve()
    if not checkpoint_path.exists():
        print(f"ERROR: Model checkpoint not found: {checkpoint_path}", file=sys.stderr)
        sys.exit(1)

    output_path = Path(args.output).resolve()

    print("=" * 70)
    print("MANDI NYAAY — VERTICAL INSPECTION SLICE (GATE 5)")
    print("=" * 70)
    print(f"Image:            {image_path.name}")
    print(f"Model Checkpoint: {checkpoint_path.name}")
    print(f"Target Sample:    {args.target_sample_size}")
    print(f"Lot Identifier:   {args.lot_id}")
    print("-" * 70)

    # 1. Initialize Pipeline and Service
    pipeline = MandiNyaayCVPipeline(
        checkpoint_path=checkpoint_path,
        mapping=V7_EXTERNAL_ADAPTER_MAPPING,
        conf_threshold=args.conf_threshold,
        min_reliable_confidence=0.40,
        reconciliation_iou_threshold=args.iou_threshold,
    )
    service = MandiNyaayInspectionService(pipeline=pipeline)

    manual_override = None
    if args.override_grade:
        manual_override = {
            "override_grade": args.override_grade,
            "reason": args.override_reason or "Operator manual adjustment",
            "inspector_id": "OP_LOCAL_CLI",
        }

    # 2. Run Complete Vertical Slice
    session = service.run_inspection(
        image_input=image_path,
        lot_id=args.lot_id,
        target_sample_size=args.target_sample_size,
        manual_override=manual_override,
    )

    # 3. Print Structured Execution Summary
    capture = session.captures[0]
    print("\n[1. CAPTURE & CV EXECUTION]")
    print(f"  Capture ID:        {capture.capture_id}")
    print(f"  Quality Status:    {capture.quality_status}")
    print(f"  Image SHA256:      {capture.image_sha256[:16]}..." if capture.image_sha256 else "  Image SHA256: None")
    print(f"  Raw Detections:    {capture.raw_detection_count}")
    print(f"  Reconciled Bulbs:  {capture.reconciled_observation_count}")
    print(f"  Conflicts:         {capture.conflict_count}")
    print(f"  Condition Counts:  {capture.visible_condition_counts}")

    print("\n[2. SAMPLING SUFFICIENCY]")
    print(f"  Sampling Status:   {session.sampling_result.status.value}")
    print(f"  Observed / Target: {session.sampling_result.observed_sample_size} / {session.sampling_result.target_sample_size}")
    print(f"  Sampling Reason:   {session.sampling_result.reason}")

    print("\n[3. COUNT DISTRIBUTION AGGREGATION]")
    print(f"  Total Count:       {session.aggregation.total_count}")
    print(f"  Distribution:      {session.aggregation.count_distribution}")
    print(f"  Mass Status:       {session.aggregation.mass_status}")
    print(f"  Disclaimer:        {session.aggregation.disclaimer}")

    print("\n[4. REVIEW SIGNALS]")
    if session.review_signals:
        for idx, sig in enumerate(session.review_signals, 1):
            action_tag = "[ACTION REQUIRED]" if sig.requires_action else "[INFO]"
            print(f"  {idx}. {action_tag} {sig.code.value} ({sig.severity.value}):")
            print(f"     \"{sig.message}\"")
    else:
        print("  None (Zero operational review signals)")

    print("\n[5. PROCUREMENT DECISION]")
    print(f"  Decision ID:       {session.decision.decision_id}")
    print(f"  Procurement Grade: {session.decision.procurement_grade.value}")
    print(f"  Decision Status:   {session.decision.status}")
    print(f"  Rule Version:      {session.decision.decision_rule_version}")
    print(f"  Reasons:           {session.decision.decision_reasons}")
    if session.decision.blocking_reasons:
        print(f"  Blocking Reasons:  {session.decision.blocking_reasons}")

    print("\n[6. TAMPER-EVIDENT REPLAYABLE EVIDENCE]")
    print(f"  Evidence ID:       {session.evidence_summary.evidence_id}")
    print(f"  Evidence Root:     {session.evidence_summary.evidence_root_hash}")
    print(f"  Integrity Term:    {session.evidence_summary.evidence_ledger_term}")

    # 4. Serialize and Save JSON Result
    output_dict = session.model_dump()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_dict, f, indent=2)

    print("-" * 70)
    print(f"Execution complete. Output saved to: {output_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
