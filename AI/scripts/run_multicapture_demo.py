"""
End-to-End Multi-Capture Lot Inspection Demo CLI for Mandi Nyaay (Gate 6A-10).

Executes the complete multi-capture lot inspection slice:
LOT
-> CAPTURE 1
-> CAPTURE 2
-> CAPTURE 3
-> ACCUMULATE OBSERVATIONS
-> UPDATE SAMPLING PROGRESSION
-> RECOMPUTE AGGREGATION & SIGNALS
-> LOT-LEVEL DECISION
-> TAMPER-EVIDENT EVENT LEDGER & REPLAY

Usage:
    python scripts/run_multicapture_demo.py ^
        --image path/to/image1.jpg ^
        --image path/to/image2.jpg ^
        --image path/to/image3.jpg
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.cv.label_mapping import V7_EXTERNAL_ADAPTER_MAPPING
from app.domain.session_accumulator import InspectionSessionAccumulator, replay_session
from app.pipeline.cv_pipeline import MandiNyaayCVPipeline


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run Mandi Nyaay Multi-Capture Lot Inspection Demo"
    )
    parser.add_argument(
        "--image",
        action="append",
        required=True,
        help="Path to real onion photographic image. Pass multiple --image flags for sequential captures.",
    )
    parser.add_argument(
        "--checkpoint",
        type=str,
        default=str((BASE_DIR.parent / "Onion_grading_system" / "onion-grading-v7.pt").resolve()),
        help="Path to YOLO v7 model checkpoint",
    )
    parser.add_argument(
        "--target-sample-size",
        type=int,
        default=20,
        help="Target minimum sample size for lot determination",
    )
    parser.add_argument(
        "--lot-id",
        type=str,
        default="lot_multicapture_001",
        help="Agricultural produce lot identifier",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="artifacts/gate6/multicapture_session.json",
        help="Path to save multicapture session JSON output",
    )
    parser.add_argument(
        "--replay-output",
        type=str,
        default="artifacts/gate6/replay_result.json",
        help="Path to save replay verification JSON output",
    )
    return parser.parse_args()


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    args = parse_args()

    checkpoint_path = Path(args.checkpoint).resolve()
    if not checkpoint_path.exists():
        print(f"ERROR: Model checkpoint not found: {checkpoint_path}", file=sys.stderr)
        sys.exit(1)

    image_paths: list[Path] = []
    for img_str in args.image:
        p = Path(img_str).resolve()
        if not p.exists():
            print(f"ERROR: Image file not found: {p}", file=sys.stderr)
            sys.exit(1)
        image_paths.append(p)

    print("=" * 75)
    print("MANDI NYAAY — MULTI-CAPTURE LOT INSPECTION ENGINE (GATE 6A)")
    print("=" * 75)
    print(f"Lot Identifier:      {args.lot_id}")
    print(f"Total Input Captures:{len(image_paths)}")
    print(f"Target Sample Size:  {args.target_sample_size}")
    print(f"Model Checkpoint:    {checkpoint_path.name}")
    print("-" * 75)

    # 1. Initialize CV Pipeline and Session Accumulator
    pipeline = MandiNyaayCVPipeline(
        checkpoint_path=checkpoint_path,
        mapping=V7_EXTERNAL_ADAPTER_MAPPING,
        conf_threshold=0.25,
        min_reliable_confidence=0.40,
        reconciliation_iou_threshold=0.70,
    )

    accumulator = InspectionSessionAccumulator(
        lot_id=args.lot_id,
        target_sample_size=args.target_sample_size,
    )

    # 2. Sequentially Process and Accumulate Captures
    for idx, img_path in enumerate(image_paths, 1):
        print(f"\n>>> PROCESSING CAPTURE {idx}/{len(image_paths)}: {img_path.name}")
        cap_id = f"cap_lot_{idx:03d}"
        cv_result = pipeline.process_image(img_path, capture_id=cap_id)

        session = accumulator.append_cv_result(cv_result)
        prog_step = accumulator.sampling_progression[-1]

        print(f"    Raw Detections:       {cv_result.raw_detection_count}")
        print(f"    Reconciled Bulbs:     {cv_result.reconciled_observation_count}")
        print(f"    Capture Conflicts:    {cv_result.conflict_count}")
        print(f"    Cumulative Bulbs:     {prog_step['observed_sample_size']} / {prog_step['target_sample_size']}")
        print(f"    Sampling Status:      {prog_step['status']}")
        print(f"    Sampling Rationale:   {prog_step['reason']}")
        print(f"    Lot Decision State:   {session.decision.procurement_grade.value} ({session.decision.status})")

    # Complete the session
    session = accumulator.complete_session()

    print("\n" + "=" * 75)
    print("LOT INSPECTION FINAL SUMMARY")
    print("=" * 75)
    print(f"Session ID:               {session.session_id}")
    print(f"Final Session Status:     {session.status.value}")
    print(f"Rule Pack ID:             {session.decision.rule_pack_id}")
    print(f"Rule Pack Version:        {session.decision.rule_pack_version}")
    print(f"Decision Rule Version:    {session.decision.decision_rule_version}")
    print(f"Total Captures Appended:  {len(session.captures)}")
    print(f"Certified Sample Units:   {accumulator.sample_unit_registry.unique_sample_count} (Physical bulb denominator)")
    print(f"Cumulative Observations:  {session.aggregation.total_observations}")
    print(f"Condition Breakdown (Physical Bulbs):")
    print(f"  - Healthy:              {session.aggregation.healthy_count}")
    print(f"  - Damaged:              {session.aggregation.damaged_count}")
    print(f"  - Sprouted:             {session.aggregation.sprouted_count}")
    print(f"  - Rotten:               {session.aggregation.rotten_count}")
    print(f"  - Class Conflicts:      {session.aggregation.class_conflict_count}")
    print(f"  - Unresolved Identity:  {session.aggregation.unresolved_identity_count} (No cross-view deduplication)")
    print(f"Final Procurement Grade:  {session.decision.procurement_grade.value}")
    print(f"Decision Reasons:         {session.decision.decision_reasons}")
    if session.decision.blocking_reasons:
        print(f"Blocking Reasons:         {session.decision.blocking_reasons}")
    print(f"Tamper-Evident Root Hash: {session.evidence_summary.evidence_root_hash}")
    print(f"Event Timeline Length:    {len(accumulator.timeline.events)} chained events")

    # Verify event ledger cryptographic integrity
    is_valid, err_msg = accumulator.timeline.verify_integrity()
    print(f"Ledger Hash Integrity:    {'VERIFIED (Tamper-evident chain intact)' if is_valid else f'TAMPER DETECTED: {err_msg}'}")

    # Replay verification
    print("\n--- RUNNING DETERMINISTIC REPLAY VERIFICATION ---")
    replayed_session = replay_session(accumulator.timeline.events)
    print("Replayed Session ID:     ", replayed_session.session_id)
    print("Replayed Grade:          ", replayed_session.decision.procurement_grade.value)
    print("Replayed Evidence Hash:  ", replayed_session.evidence_summary.evidence_root_hash)

    # Compare essential state
    orig_dump = session.model_dump()
    replay_dump = replayed_session.model_dump()
    state_matches = (
        orig_dump["session_id"] == replay_dump["session_id"]
        and orig_dump["status"] == replay_dump["status"]
        and orig_dump["decision"] == replay_dump["decision"]
        and orig_dump["aggregation"] == replay_dump["aggregation"]
        and orig_dump["evidence_summary"]["evidence_root_hash"] == replay_dump["evidence_summary"]["evidence_root_hash"]
    )
    print(f"Deterministic Replay:     {'SUCCESS (Original state == Replayed state)' if state_matches else 'FAILED'}")

    # 3. Save JSON Outputs
    out_dir = BASE_DIR / "artifacts" / "gate6"
    out_dir.mkdir(parents=True, exist_ok=True)

    session_payload = {
        "session": session.model_dump(),
        "captures": [c.model_dump() for c in session.captures],
        "timeline": [e.model_dump() for e in accumulator.timeline.events],
        "sampling_progression": accumulator.sampling_progression,
        "aggregation": session.aggregation.model_dump(),
        "review_signals": [s.model_dump() for s in session.review_signals],
        "decision": session.decision.model_dump(),
        "evidence": session.evidence_summary.model_dump(),
    }

    out_file = Path(args.output).resolve()
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(session_payload, f, indent=2)
    print(f"\nSaved multicapture session to: {out_file}")

    replay_payload = {
        "replayed_session": replayed_session.model_dump(),
        "ledger_verified": is_valid,
        "state_matches": state_matches,
    }
    replay_file = Path(args.replay_output).resolve()
    with open(replay_file, "w", encoding="utf-8") as f:
        json.dump(replay_payload, f, indent=2)
    print(f"Saved replay result to:        {replay_file}")
    print("=" * 75)


if __name__ == "__main__":
    main()
