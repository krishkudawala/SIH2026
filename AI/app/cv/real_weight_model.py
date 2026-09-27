"""
Real Weight Model & Conformal Uncertainty Estimation for Mandi Nyaay.

Implements Vertical Slice 4 (Components H & I):
L/W/T -> WEIGHT MODEL -> CONFORMAL INTERVAL -> WEIGHT STATUS

Two-Stage Estimator:
1. Physics Prior:
   mass ≈ density × volume (density ~ 0.98 - 1.02 g/cm³ for Allium cepa)
2. Empirical Data Model:
   ln(mass) = β0 + β1 ln(volume) + β2 aspect_ratio + β3 sphericity + β4 defect_fraction

Uncertainty Estimation (Component I):
Uses Conformal Prediction (MAPIE) to output calibrated prediction intervals:
- point_estimate_g
- prediction_interval_low_g
- prediction_interval_high_g
- coverage_target (e.g. 0.90)
- calibration_version

Strict Anti-Fabrication Guarantee:
Prediction intervals and point estimates are marked UNVALIDATED
and return None until genuine paired calibration data exists.
"""

from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from typing import Any, Sequence
import numpy as np
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class PairedWeightDataPoint(BaseModel):
    """
    Certified paired record linking physical dimensions and scale mass.
    """
    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., description="Unique specimen identifier")
    volume_cm3: float = Field(..., gt=0.0, description="Ellipsoid volume in cm³")
    geometric_diameter_mm: float = Field(..., gt=0.0, description="Geometric mean diameter D_g in mm")
    aspect_ratio: float = Field(default=1.0, gt=0.0, description="L / W ratio")
    sphericity: float = Field(default=0.9, ge=0.0, le=1.0, description="Sphericity index")
    defect_fraction: float = Field(default=0.0, ge=0.0, le=1.0, description="Defect area fraction")
    actual_scale_weight_g: float = Field(..., gt=0.0, description="Direct certified digital scale mass in grams")
    variety: str | None = Field(default="Nashik Red", description="Cultivar variety")
    timestamp_iso: str | None = Field(default=None, description="Measurement timestamp")


class ModelResidualMetrics(BaseModel):
    """Residual error distribution across splits."""
    model_config = ConfigDict(extra="forbid")

    mae_g: float = Field(..., description="Mean absolute error in grams")
    rmse_g: float = Field(..., description="Root mean squared error in grams")
    mape_pct: float = Field(..., description="Mean absolute percentage error %")
    max_error_g: float = Field(..., description="Maximum residual error in grams")
    residual_quantiles_g: dict[str, float] = Field(
        ...,
        description="Residual distribution percentiles (p10, p25, p50, p75, p90)"
    )


class WeightModelArtifact(BaseModel):
    """
    Persisted empirical weight calibration artifact.
    """
    model_config = ConfigDict(extra="forbid")

    model_version: str = Field(..., description="Weight model version tag")
    coefficient_version: str = Field(..., description="Fitted coefficients version")
    calibration_version: str = Field(..., description="Conformal calibration version")
    beta_coefficients: dict[str, float] = Field(
        ...,
        description="Fitted regression weights: beta_0 (intercept), beta_log_vol, beta_ar, beta_sph, beta_def"
    )
    conformal_quantile_q: float = Field(
        ...,
        description="Calibrated conformal nonconformity score quantile for prediction intervals"
    )
    coverage_target: float = Field(default=0.90, description="Target coverage probability (e.g. 0.90)")
    train_sample_count: int = Field(..., description="Number of training samples")
    calibration_sample_count: int = Field(..., description="Number of conformal calibration samples")
    holdout_sample_count: int = Field(..., description="Number of independent test samples")
    holdout_metrics: ModelResidualMetrics = Field(..., description="Holdout evaluation metrics")
    created_at_iso: str = Field(..., description="Artifact creation timestamp")


class WeightPredictionOutput(BaseModel):
    """
    User-facing weight estimate with certified prediction intervals.
    """
    model_config = ConfigDict(extra="forbid")

    point_estimate_g: float | None = Field(default=None, description="Estimated bulb weight in grams")
    prediction_interval_low_g: float | None = Field(default=None, description="Lower bound of prediction interval")
    prediction_interval_high_g: float | None = Field(default=None, description="Upper bound of prediction interval")
    coverage_target: float | None = Field(default=None, description="Confidence/coverage target (e.g. 0.90)")
    weight_status: str = Field(
        default="UNVALIDATED",
        description="ESTIMATE_AVAILABLE, UNVALIDATED, or CALIBRATION_PENDING"
    )
    model_version: str = Field(default="weight_uncalibrated_v1", description="Model version")
    coefficient_version: str = Field(default="none", description="Coefficients version")
    calibration_version: str | None = Field(default=None, description="Conformal calibration version")
    disclaimer: str = Field(
        default="Weight estimate — UNVALIDATED. Paired physical scale calibration data pending.",
        description="Mandatory operational disclaimer"
    )

    @property
    def status(self) -> str:
        if self.weight_status == "ESTIMATE_AVAILABLE":
            return "ESTIMATE_AVAILABLE"
        return "MASS_UNVALIDATED"

    @property
    def weight_estimate_g(self) -> float | None:
        return self.point_estimate_g

    @property
    def lower_bound_g(self) -> float | None:
        return self.prediction_interval_low_g

    @property
    def upper_bound_g(self) -> float | None:
        return self.prediction_interval_high_g


class RealWeightEstimator:
    """
    Two-stage weight model with conformal prediction intervals.
    Supports dataset ingestion, train/calibration/holdout splits, fitting, and inference.
    """

    def __init__(self, artifact: WeightModelArtifact | None = None):
        self.artifact = artifact

    def load_artifact(self, artifact_path: Path | str) -> None:
        """Load trained calibration artifact from file."""
        with open(artifact_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.artifact = WeightModelArtifact.model_validate(data)
        logger.info(f"Loaded weight model artifact version {self.artifact.model_version}")

    def predict(
        self,
        volume_cm3: float | None,
        geometric_diameter_mm: float | None = None,
        aspect_ratio: float = 1.0,
        sphericity: float = 0.9,
        defect_fraction: float = 0.0,
    ) -> WeightPredictionOutput:
        """
        Predict mass and prediction intervals for a bulb.
        Anti-fabrication guarantee: returns UNVALIDATED if no artifact loaded or volume is None.
        """
        if self.artifact is None:
            return WeightPredictionOutput(
                point_estimate_g=None,
                prediction_interval_low_g=None,
                prediction_interval_high_g=None,
                coverage_target=None,
                weight_status="UNVALIDATED",
                model_version="uncalibrated",
                disclaimer="Weight estimate — UNVALIDATED. No paired physical scale calibration artifact loaded.",
            )

        if volume_cm3 is None or volume_cm3 <= 0:
            return WeightPredictionOutput(
                point_estimate_g=None,
                prediction_interval_low_g=None,
                prediction_interval_high_g=None,
                coverage_target=None,
                weight_status="UNVALIDATED",
                model_version=self.artifact.model_version,
                disclaimer="Weight estimate — UNVALIDATED. Volumetric measurement unavailable.",
            )

        betas = self.artifact.beta_coefficients
        log_vol = math.log(volume_cm3)
        pred_log_mass = (
            betas["beta_0"]
            + betas.get("beta_log_vol", 1.0) * log_vol
            + betas.get("beta_ar", 0.0) * aspect_ratio
            + betas.get("beta_sph", 0.0) * sphericity
            + betas.get("beta_def", 0.0) * defect_fraction
        )
        point_est_g = math.exp(pred_log_mass)

        # Conformal interval in log space: pred_log_mass +/- q
        q = self.artifact.conformal_quantile_q
        low_g = max(1.0, math.exp(pred_log_mass - q))
        high_g = math.exp(pred_log_mass + q)

        return WeightPredictionOutput(
            point_estimate_g=round(point_est_g, 1),
            prediction_interval_low_g=round(low_g, 1),
            prediction_interval_high_g=round(high_g, 1),
            coverage_target=self.artifact.coverage_target,
            weight_status="ESTIMATE_AVAILABLE",
            model_version=self.artifact.model_version,
            coefficient_version=self.artifact.coefficient_version,
            calibration_version=self.artifact.calibration_version,
            disclaimer="Weight estimate with conformal prediction interval. Calibrated on empirical paired scale data.",
        )

    @classmethod
    def train_and_calibrate(
        cls,
        dataset: Sequence[PairedWeightDataPoint],
        model_version: str = "weight_empirical_v1.0",
        coverage_target: float = 0.90,
        train_fraction: float = 0.6,
        calib_fraction: float = 0.2,
    ) -> WeightModelArtifact:
        """
        Train multi-variable log model, calibrate prediction intervals on calibration split,
        and evaluate residual metrics on holdout test split.
        """
        from datetime import datetime, timezone
        from sklearn.linear_model import LinearRegression

        n_total = len(dataset)
        if n_total < 10:
            raise ValueError(f"Insufficient paired records for empirical training ({n_total} < 10)")

        # 1. Feature extraction
        # Features: [log(vol), aspect_ratio, sphericity, defect_fraction]
        X = np.array([
            [
                math.log(d.volume_cm3),
                d.aspect_ratio,
                d.sphericity,
                d.defect_fraction,
            ]
            for d in dataset
        ], dtype=np.float64)

        y_log = np.array([math.log(d.actual_scale_weight_g) for d in dataset], dtype=np.float64)
        y_true_g = np.array([d.actual_scale_weight_g for d in dataset], dtype=np.float64)

        # 2. Splits: Train, Calibration, Holdout
        n_train = max(4, int(n_total * train_fraction))
        n_calib = max(3, int(n_total * calib_fraction))
        n_test = n_total - n_train - n_calib

        X_train, y_train_log = X[:n_train], y_log[:n_train]
        X_calib, y_calib_log = X[n_train:n_train + n_calib], y_log[n_train:n_train + n_calib]
        X_test, y_test_log = X[n_train + n_calib:], y_log[n_train + n_calib:]
        y_test_g = y_true_g[n_train + n_calib:]

        # 3. Fit linear regression in log space
        reg = LinearRegression()
        reg.fit(X_train, y_train_log)

        betas = {
            "beta_0": round(float(reg.intercept_), 6),
            "beta_log_vol": round(float(reg.coef_[0]), 6),
            "beta_ar": round(float(reg.coef_[1]), 6),
            "beta_sph": round(float(reg.coef_[2]), 6),
            "beta_def": round(float(reg.coef_[3]), 6),
        }

        # 4. Conformal Calibration on calibration split (MAPIE / Split Conformal)
        calib_preds = reg.predict(X_calib)
        residuals_calib = np.abs(y_calib_log - calib_preds)

        # Conformal quantile: ceiling((n + 1) * alpha) / n
        alpha = coverage_target
        k = int(np.ceil((len(residuals_calib) + 1) * alpha))
        k = min(len(residuals_calib), max(1, k))
        conformal_q = float(np.sort(residuals_calib)[k - 1])

        # 5. Evaluate on Holdout Test Split
        test_preds_log = reg.predict(X_test)
        test_preds_g = np.exp(test_preds_log)

        errors_g = np.abs(y_test_g - test_preds_g)
        mae = float(np.mean(errors_g))
        rmse = float(np.sqrt(np.mean(errors_g ** 2)))
        mape = float(np.mean(errors_g / y_test_g) * 100.0)
        max_err = float(np.max(errors_g))

        quantiles = {
            "p10": round(float(np.percentile(errors_g, 10)), 2),
            "p25": round(float(np.percentile(errors_g, 25)), 2),
            "p50": round(float(np.percentile(errors_g, 50)), 2),
            "p75": round(float(np.percentile(errors_g, 75)), 2),
            "p90": round(float(np.percentile(errors_g, 90)), 2),
        }

        metrics = ModelResidualMetrics(
            mae_g=round(mae, 2),
            rmse_g=round(rmse, 2),
            mape_pct=round(mape, 2),
            max_error_g=round(max_err, 2),
            residual_quantiles_g=quantiles,
        )

        return WeightModelArtifact(
            model_version=model_version,
            coefficient_version=f"beta_v{len(dataset)}_samples",
            calibration_version=f"conformal_{int(coverage_target * 100)}cov_q{conformal_q:.4f}",
            beta_coefficients=betas,
            conformal_quantile_q=round(conformal_q, 4),
            coverage_target=coverage_target,
            train_sample_count=n_train,
            calibration_sample_count=n_calib,
            holdout_sample_count=len(y_test_g),
            holdout_metrics=metrics,
            created_at_iso=datetime.now(timezone.utc).isoformat(),
        )
