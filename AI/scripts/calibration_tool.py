"""
Real Calibration Data Collection & Training CLI Tool for Mandi Nyaay (Feature 8).

Collects genuine paired ground-truth physical calibration records:
- Images (top, side, optional underside)
- Calibration profile (ArUco planar homography)
- Measured tri-axial dimensions (L, W, T)
- Actual caliper diameter
- Actual certified digital scale weight (grams)
- Visible condition (HEALTHY, DAMAGED, SPROUTED, ROTTEN)
- Segmented visible defect fraction
- Metadata (scale make/model, device, operator, variety)

Trains the empirical log-regression + MAPIE conformal prediction weight model.
Zero fake values. Zero mock coefficients.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from app.cv.calibration_data_collector import CalibrationDataCollector
from app.cv.real_weight_model import RealWeightEstimator
from app.engine import MandiNyaayEngine
from app.storage.sql_models import CalibrationSampleModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def add_sample(args: argparse.Namespace) -> None:
    engine = MandiNyaayEngine()
    logger.info("Recording verified physical calibration sample...")

    sample = engine.record_calibration_sample(
        sample_unit_id=args.sample_unit_id,
        lot_id=args.lot_id,
        length_mm=args.length_mm,
        width_mm=args.width_mm,
        thickness_mm=args.thickness_mm,
        actual_scale_weight_g=args.actual_weight_g,
        condition=args.condition.upper(),
        defect_fraction=args.defect_fraction,
        variety=args.variety,
        operator_id=args.operator_id,
    )

    print("\n========================================================")
    print("CALIBRATION RECORD STORED SUCCESSFULLY")
    print("========================================================")
    print(f"Sample ID       : {sample.id}")
    print(f"SampleUnit ID   : {sample.sample_unit_id}")
    print(f"Lot ID          : {sample.lot_id}")
    print(f"Dimensions L/W/T: {sample.length_mm:.1f} x {sample.width_mm:.1f} x {sample.thickness_mm:.1f} mm")
    print(f"Geometric D_g   : {sample.geometric_diameter_mm:.1f} mm")
    print(f"Ellipsoid Vol   : {sample.volume_cm3:.2f} cm³")
    print(f"Actual Weight   : {sample.actual_scale_weight_g:.1f} g")
    print(f"Condition       : {sample.condition}")
    print(f"Defect Fraction : {sample.defect_fraction * 100:.1f}%")
    print(f"Variety         : {sample.variety}")
    print(f"Operator        : {sample.operator_id}")
    print("========================================================\n")


def list_samples(args: argparse.Namespace) -> None:
    engine = MandiNyaayEngine()
    samples = engine.sql_store.list_calibration_samples()
    print("\n========================================================")
    print(f"TOTAL CERTIFIED CALIBRATION RECORDS: {len(samples)}")
    print("========================================================")
    for s in samples:
        print(f"[{s.id}] {s.sample_unit_id} ({s.lot_id}): {s.length_mm:.1f}x{s.width_mm:.1f}x{s.thickness_mm:.1f}mm | Vol: {s.volume_cm3:.1f}cm³ | Scale: {s.actual_scale_weight_g:.1f}g | {s.condition}")
    print("========================================================\n")


def train_model(args: argparse.Namespace) -> None:
    engine = MandiNyaayEngine()
    logger.info(f"Training empirical weight model with coverage target {args.coverage}...")
    try:
        artifact = engine.train_weight_model(
            coverage_target=args.coverage,
            model_version=args.version,
            artifact_save_path=args.output,
        )
        print("\n========================================================")
        print("EMPIRICAL WEIGHT MODEL TRAINED & CALIBRATED")
        print("========================================================")
        print(f"Model Version     : {artifact.model_version}")
        print(f"Coeff Version     : {artifact.coefficient_version}")
        print(f"Calibration       : {artifact.calibration_version}")
        print(f"Conformal q       : {artifact.conformal_quantile_q:.4f}")
        print(f"Coverage Target   : {artifact.coverage_target * 100:.0f}%")
        print(f"Train / Cal / Test: {artifact.train_sample_count} / {artifact.calibration_sample_count} / {artifact.holdout_sample_count}")
        print(f"Holdout MAE       : {artifact.holdout_metrics.mae_g:.2f} g")
        print(f"Holdout MAPE      : {artifact.holdout_metrics.mape_pct:.2f}%")
        print(f"Holdout RMSE      : {artifact.holdout_metrics.rmse_g:.2f} g")
        print(f"Saved to          : {args.output}")
        print("========================================================\n")
    except ValueError as e:
        print(f"\n[ERROR] {e}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Mandi Nyaay Physical Calibration Collection & Model Trainer")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: add
    p_add = subparsers.add_parser("add", help="Record physical calibration sample")
    p_add.add_argument("--sample-unit-id", required=True, help="SampleUnit ID")
    p_add.add_argument("--lot-id", default="LOT_CALIB_001", help="Lot ID")
    p_add.add_argument("--length-mm", type=float, required=True, help="Major diameter L (mm)")
    p_add.add_argument("--width-mm", type=float, required=True, help="Minor diameter W (mm)")
    p_add.add_argument("--thickness-mm", type=float, required=True, help="Polar height T (mm)")
    p_add.add_argument("--actual-weight-g", type=float, required=True, help="Direct scale weight in grams")
    p_add.add_argument("--condition", default="HEALTHY", choices=["HEALTHY", "DAMAGED", "SPROUTED", "ROTTEN"], help="Visible condition")
    p_add.add_argument("--defect-fraction", type=float, default=0.0, help="Defect area fraction (0.0 to 1.0)")
    p_add.add_argument("--variety", default="Nashik Red", help="Cultivar")
    p_add.add_argument("--operator-id", default="INSPECTOR_01", help="Inspector ID")
    p_add.set_defaults(func=add_sample)

    # Subcommand: list
    p_list = subparsers.add_parser("list", help="List stored calibration samples")
    p_list.set_defaults(func=list_samples)

    # Subcommand: train
    p_train = subparsers.add_parser("train", help="Train weight model from stored records")
    p_train.add_argument("--coverage", type=float, default=0.90, help="Target coverage (e.g. 0.90)")
    p_train.add_argument("--version", default="weight_empirical_v1.0", help="Model version tag")
    p_train.add_argument("--output", default="models/weight_model_artifact.json", help="Path to save artifact")
    p_train.set_defaults(func=train_model)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
