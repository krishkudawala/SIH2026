"""
Weight Estimation & Physical Calibration Engine for Mandi Nyaay (Gate 6B / Phases 9 & 10).

Anti-Fabrication Guarantee:
When paired physical scale data does not exist, weight_status MUST return UNVALIDATED.
Never invent density coefficients or physical scale truth from imagination.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
import math
from pathlib import Path
from typing import Any, Sequence
from pydantic import BaseModel, ConfigDict, Field

from app.cv.calibration import CalibrationProfile, CalibrationProfileStatus


class WeightEstimationStatus(str, Enum):
    """Integrity and validation status of produce weight estimation."""
    UNVALIDATED = "UNVALIDATED"
    FIELD_VALIDATION_PENDING = "FIELD_VALIDATION_PENDING"
    CALIBRATION_NOT_AVAILABLE = "CALIBRATION_NOT_AVAILABLE"
    CALIBRATION_INVALID = "CALIBRATION_INVALID"
    ESTIMATE_AVAILABLE = "ESTIMATE_AVAILABLE"


class WeightEstimateResult(BaseModel):
    """
    Physical weight estimation outcome for a single bulb.
    Surfaces all uncertainty and provenance to the UI/operator.
    """
    model_config = ConfigDict(extra="forbid")

    weight_estimate_g: float | None = Field(
        default=None,
        description="Estimated bulb mass in grams. None when unvalidated."
    )
    weight_status: WeightEstimationStatus = Field(
        default=WeightEstimationStatus.UNVALIDATED,
        description="Validation status (UNVALIDATED, FIELD_VALIDATION_PENDING, ESTIMATE_AVAILABLE)"
    )
    model_version: str = Field(
        default="weight.uncalibrated.v1",
        description="Version identifier of weight estimation model"
    )
    calibration_version: str | None = Field(
        default=None,
        description="Associated optical/scale calibration version"
    )
    uncertainty: str = Field(
        default="HIGH_UNVALIDATED",
        description="Qualitative uncertainty assessment"
    )
    provenance: str = Field(
        default="uncalibrated_volumetric_prior",
        description="Calculation provenance"
    )
    disclaimer: str = Field(
        default="Weight estimate — UNVALIDATED. Paired physical scale calibration data pending.",
        description="Mandatory legal/operational disclaimer"
    )


class PhysicalWeightCalibrationRecord(BaseModel):
    """
    Genuine paired observation data point linking photographic evidence
    to direct physical scale ground truth.
    """
    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., description="Unique physical bulb identifier")
    image_path: str = Field(..., description="Path to captured reference image")
    calibration_id: str = Field(..., description="ID of valid calibration profile")
    measured_planar_diameter_mm: float = Field(..., gt=0.0, description="Planar homography measured diameter")
    actual_scale_weight_g: float = Field(..., gt=0.0, description="Certified digital scale measurement in grams")
    actual_caliper_diameter_mm: float | None = Field(default=None, description="Optional manual caliper measurement")
    condition: str = Field(default="HEALTHY", description="Bulb condition (HEALTHY, DAMAGED, SPROUTED, ROTTEN)")
    variety: str | None = Field(default=None, description="Agricultural cultivar/variety (e.g. Nashik Red)")
    lot_id: str | None = Field(default=None, description="Lot identifier")
    scale_device_metadata: dict[str, Any] = Field(default_factory=dict, description="Scale model, serial, accuracy class")
    captured_at_iso: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Capture timestamp"
    )


class WeightCalibrationReport(BaseModel):
    """
    Empirical calibration report generated from physical scale training/evaluation split.
    """
    model_config = ConfigDict(extra="forbid")

    report_id: str = Field(..., description="Unique report identifier")
    dataset_size: int = Field(..., description="Total paired records ingested")
    train_count: int = Field(..., description="Number of training samples")
    eval_count: int = Field(..., description="Number of evaluation samples")
    status: str = Field(default="FIELD_VALIDATION_PENDING", description="Field validation status")
    coefficient_a: float | None = Field(default=None, description="Power law coefficient a in W = a * D^b")
    exponent_b: float | None = Field(default=None, description="Power law exponent b")
    mean_absolute_error_g: float | None = Field(default=None, description="MAE on evaluation split")
    mean_relative_error_pct: float | None = Field(default=None, description="MRE % on evaluation split")
    created_at_iso: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Report timestamp"
    )
    notes: str = Field(default="", description="Auditor and protocol notes")


class PhysicalWeightCalibrationPath:
    """
    Future paired-data ingestion and empirical calibration pipeline.
    Strictly refuses to invent coefficients or synthesize weights.
    """

    def __init__(self, calibration_version: str = "weight_calib_v1.0"):
        self.calibration_version = calibration_version
        self.records: list[PhysicalWeightCalibrationRecord] = []

    def ingest_record(self, record: PhysicalWeightCalibrationRecord) -> None:
        """Add a verified paired physical scale record."""
        self.records.append(record)

    def fit_and_evaluate(
        self,
        train_fraction: float = 0.8,
        min_records_required: int = 15,
    ) -> WeightCalibrationReport:
        """
        Train and evaluate an empirical power-law mass model from genuine paired scale data.
        Returns explicit FIELD_VALIDATION_PENDING if insufficient paired records exist.
        """
        import uuid
        report_id = f"wcr_{uuid.uuid4().hex[:8]}"

        if len(self.records) < min_records_required:
            return WeightCalibrationReport(
                report_id=report_id,
                dataset_size=len(self.records),
                train_count=0,
                eval_count=0,
                status="FIELD_VALIDATION_PENDING",
                coefficient_a=None,
                exponent_b=None,
                mean_absolute_error_g=None,
                mean_relative_error_pct=None,
                notes=(
                    f"Insufficient paired physical scale records ({len(self.records)} < {min_records_required}). "
                    "Weight model cannot be certified. FIELD_VALIDATION_PENDING."
                ),
            )

        # Deterministic train/eval split
        split_idx = int(len(self.records) * train_fraction)
        train_records = self.records[:split_idx]
        eval_records = self.records[split_idx:]

        # Fit power law ln(W) = ln(a) + b * ln(D) via linear least squares
        log_d_train = [math.log(r.measured_planar_diameter_mm) for r in train_records]
        log_w_train = [math.log(r.actual_scale_weight_g) for r in train_records]

        n = len(train_records)
        sum_x = sum(log_d_train)
        sum_y = sum(log_w_train)
        sum_xx = sum(x * x for x in log_d_train)
        sum_xy = sum(x * y for x, y in zip(log_d_train, log_w_train))

        denom = n * sum_xx - sum_x * sum_x
        if abs(denom) < 1e-9:
            return WeightCalibrationReport(
                report_id=report_id,
                dataset_size=len(self.records),
                train_count=len(train_records),
                eval_count=len(eval_records),
                status="FIELD_VALIDATION_PENDING",
                notes="Degenerate diameter distribution in training data.",
            )

        b = (n * sum_xy - sum_x * sum_y) / denom
        ln_a = (sum_y - b * sum_x) / n
        a = math.exp(ln_a)

        # Evaluate on test split
        errors_g: list[float] = []
        rel_errors: list[float] = []
        for r in eval_records:
            pred_w = a * (r.measured_planar_diameter_mm ** b)
            err = abs(pred_w - r.actual_scale_weight_g)
            rel = (err / r.actual_scale_weight_g) * 100.0
            errors_g.append(err)
            rel_errors.append(rel)

        mae = float(sum(errors_g) / len(errors_g)) if errors_g else 0.0
        mre = float(sum(rel_errors) / len(rel_errors)) if rel_errors else 0.0

        return WeightCalibrationReport(
            report_id=report_id,
            dataset_size=len(self.records),
            train_count=len(train_records),
            eval_count=len(eval_records),
            status="FIELD_VALIDATION_PENDING",
            coefficient_a=round(a, 6),
            exponent_b=round(b, 4),
            mean_absolute_error_g=round(mae, 2),
            mean_relative_error_pct=round(mre, 2),
            notes="Empirical fit computed from paired data. Pending APMC field certification.",
        )


def estimate_bulb_weight(
    diameter_mm: float | None,
    profile: CalibrationProfile | None,
    calibrated_report: WeightCalibrationReport | None = None,
) -> WeightEstimateResult:
    """
    Estimate individual bulb weight.

    ANTI-FABRICATION RULE:
    When no verified paired scale model exists, weight_status returns UNVALIDATED
    and weight_estimate_g returns None.
    """
    if profile is None or profile.status == CalibrationProfileStatus.NOT_AVAILABLE:
        return WeightEstimateResult(
            weight_estimate_g=None,
            weight_status=WeightEstimationStatus.CALIBRATION_NOT_AVAILABLE,
            uncertainty="UNAVAILABLE",
            disclaimer="Calibration marker unavailable. Weight estimate cannot be computed.",
        )

    if profile.status == CalibrationProfileStatus.INVALID:
        return WeightEstimateResult(
            weight_estimate_g=None,
            weight_status=WeightEstimationStatus.CALIBRATION_INVALID,
            uncertainty="INVALID",
            disclaimer="Calibration marker is invalid. Weight estimation blocked.",
        )

    if diameter_mm is None or diameter_mm <= 0:
        return WeightEstimateResult(
            weight_estimate_g=None,
            weight_status=WeightEstimationStatus.UNVALIDATED,
            uncertainty="HIGH_UNVALIDATED",
            disclaimer="Bulb diameter measurement unavailable.",
        )

    if calibrated_report is None or calibrated_report.coefficient_a is None:
        # No physical scale calibration data exists
        return WeightEstimateResult(
            weight_estimate_g=None,
            weight_status=WeightEstimationStatus.UNVALIDATED,
            model_version="uncalibrated",
            uncertainty="HIGH_UNVALIDATED",
            provenance="no_paired_scale_data",
            disclaimer="Weight estimate — UNVALIDATED. No paired physical scale calibration data exists.",
        )

    # If calibrated coefficients exist
    a = calibrated_report.coefficient_a
    b = calibrated_report.exponent_b or 3.0
    est_g = round(float(a * (diameter_mm ** b)), 1)

    return WeightEstimateResult(
        weight_estimate_g=est_g,
        weight_status=WeightEstimationStatus.ESTIMATE_AVAILABLE,
        model_version=calibrated_report.report_id,
        calibration_version=calibrated_report.status,
        uncertainty=f"+/- {calibrated_report.mean_relative_error_pct:.1f}%" if calibrated_report.mean_relative_error_pct else "PENDING_VALIDATION",
        provenance="empirical_power_law",
        disclaimer="Weight estimate — FIELD VALIDATION PENDING. Empirical scale regression model.",
    )
