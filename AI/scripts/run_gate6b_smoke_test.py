"""
Real Validation Image Smoke Test for Gate 6B.

Runs one existing real validation image through the integrated Gate 6B pipeline:
REAL VALIDATION IMAGE
-> REAL YOLO v7 INFERENCE
-> RECONCILED OBSERVATIONS
-> PHYSICAL SAMPLE UNITS
-> SAMPLING DENOMINATOR (UNIQUE SAMPLE UNITS)
-> VALIDATED RULE PACK (AGMARK 2024 V1)
-> AUDITABLE PROCUREMENT DECISION
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.cv.label_mapping import V7_EXTERNAL_ADAPTER_MAPPING
from app.domain.rule_pack import AGMARK_ONION_STANDARD_V1
from app.domain.rule_pack_validation import validate_rule_pack
from app.domain.sample_unit import CaptureRole
from app.domain.session_accumulator import InspectionSessionAccumulator
from app.pipeline.cv_pipeline import MandiNyaayCVPipeline


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run Gate 6B Smoke Test")
    parser.add_argument(
        "--image",
        type=str,
        default="cropbad_20230121_084837_train_4551f94b_1.jpg",
        help="Image filename in valid/images/",
    )
    args = parser.parse_args()

    checkpoint_path = Path("../Onion_grading_system/onion-grading-v7.pt").resolve()
    valid_images_dir = Path("../Onion_grading_system/training/merged_v2/valid/images").resolve()
    smoke_img_path = valid_images_dir / args.image

    if not checkpoint_path.exists():
        print(f"ERROR: Model checkpoint not found at {checkpoint_path}", file=sys.stderr)
        sys.exit(1)
    if not smoke_img_path.exists():
        print(f"ERROR: Validation image not found at {smoke_img_path}", file=sys.stderr)
        sys.exit(1)

    print("=" * 80)
    print("MANDI NYAAY GATE 6B — REAL SMOKE TEST (PHYSICAL SAMPLE IDENTITY + RULE PACK)")
    print("=" * 80)
    print(f"Real Image:       {smoke_img_path.name}")
    print(f"Model Checkpoint: {checkpoint_path.name}")
    print(f"Rule Pack ID:     {AGMARK_ONION_STANDARD_V1.rule_pack_id} (v{AGMARK_ONION_STANDARD_V1.version})")
    print("-" * 80)

    # 1. Validate RulePack
    val_result = validate_rule_pack(AGMARK_ONION_STANDARD_V1)
    print(f"RulePack Validation Status: {'VALID' if val_result.is_valid else 'INVALID'}")
    print(f"RulePack Authority:         {AGMARK_ONION_STANDARD_V1.authority}")
    print(f"RulePack Source Reference:  {AGMARK_ONION_STANDARD_V1.source_reference}")
    print(f"RulePack Sampling Method:   {AGMARK_ONION_STANDARD_V1.sampling_method}")

    # 2. Run CV Pipeline on Real Validation Image
    pipeline = MandiNyaayCVPipeline(
        checkpoint_path=checkpoint_path,
        mapping=V7_EXTERNAL_ADAPTER_MAPPING,
        conf_threshold=0.25,
        min_reliable_confidence=0.40,
        reconciliation_iou_threshold=0.70,
    )
    cv_result = pipeline.process_image(smoke_img_path, capture_id="gate6b_real_cap_001")

    # 3. Ingest into Gate 6B Session Accumulator
    accumulator = InspectionSessionAccumulator(
        lot_id="lot_gate6b_real_smoke",
        target_sample_size=20,
        rule_pack=AGMARK_ONION_STANDARD_V1,
    )

    session = accumulator.append_cv_result(
        cv_result,
        capture_role=CaptureRole.PRIMARY_SAMPLE_CAPTURE,
    )
    session = accumulator.complete_session()

    # 4. Extract Pipeline Outputs
    raw_count = cv_result.raw_detection_count
    reconciled_count = cv_result.reconciled_observation_count
    sample_units = list(accumulator.sample_unit_registry.units.values())
    sampling_denom = session.sampling_result.observed_sample_size
    target_sample_size = session.sampling_result.target_sample_size
    sampling_status = session.sampling_result.status.value
    decision_grade = session.decision.procurement_grade.value
    decision_status = session.decision.status

    print("\n--- SMOKE TEST OUTPUT SUMMARY ---")
    print(f"Raw Detections:           {raw_count}")
    print(f"Reconciled Observations:  {reconciled_count}")
    print(f"Conflicts Detected:       {cv_result.conflict_count}")
    print(f"SampleUnits Created:      {len(sample_units)}")
    for idx, u in enumerate(sample_units, 1):
        print(f"  Unit #{idx}: ID={u.sample_unit_id}, Status={u.unit_status}, Semantic={u.resolved_class_semantic.value}, ObsIDs={u.observation_ids}")
    print(f"Sampling Denominator:     {sampling_denom} (Target: {target_sample_size})")
    print(f"Sampling Status:          {sampling_status} ({session.sampling_result.reason})")
    print(f"RulePack Status:          {session.decision.rule_pack_id} v{session.decision.rule_pack_version}")
    print(f"Decision Status:          {decision_grade} ({decision_status})")
    print(f"Decision Reasons:         {session.decision.decision_reasons}")
    print(f"Blocking Reasons:         {session.decision.blocking_reasons}")

    # 5. Save Artifact
    out_dir = BASE_DIR / "artifacts" / "gate6b"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"smoke_test_{smoke_img_path.stem}.json"
    alias_file = out_dir / "smoke_test_real_capture.json"
    with open(out_file, "w") as f:
        json.dump(session.model_dump(), f, indent=2)
    with open(alias_file, "w") as f:
        json.dump(session.model_dump(), f, indent=2)
    print(f"\nArtifact saved to: {out_file.relative_to(BASE_DIR)}")
    print(f"Artifact alias saved to: {alias_file.relative_to(BASE_DIR)}")


if __name__ == "__main__":
    main()
