"""
Mandi Nyaay Inspection Service (Gate 5 Vertical Slice).

Orchestrates the complete inspection slice:
REAL IMAGE
-> REAL CV PIPELINE (MandiNyaayCVPipeline)
-> RECONCILED PHYSICAL OBSERVATIONS
-> STATISTICAL SAMPLING SUFFICIENCY
-> COUNT-BASED AGGREGATION
-> REVIEW SIGNALS GENERATION
-> DETERMINISTIC PROCUREMENT DECISION
-> TAMPER-EVIDENT REPLAYABLE EVIDENCE

Guarantees:
- Zero data fabrication.
- Full provenance from detector checkpoint to audit evidence.
- Machine-readable Pydantic session contract ready for frontend consumption.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import uuid

import numpy as np

from app.cv.quality import QualityGrade
from app.domain.aggregation import aggregate_observations
from app.domain.decision_engine import evaluate_procurement_decision
from app.domain.inspection_session import (
    InspectionAggregation,
    InspectionCapture,
    InspectionDecision,
    InspectionEvidenceSummary,
    InspectionObservationSet,
    InspectionSamplingResult,
    InspectionSession,
    InspectionSessionStatus,
    ProcurementGrade,
    compute_evidence_root_hash,
)
from app.domain.review_signals import generate_review_signals
from app.domain.sampling import DEFAULT_TARGET_SAMPLE_SIZE, evaluate_sampling_sufficiency
from app.pipeline.cv_pipeline import CVPipelineResult, MandiNyaayCVPipeline
from app.version import get_processing_version


class MandiNyaayInspectionService:
    """
    Vertical slice service coordinating capture ingestion, CV inference,
    observation reconciliation, sampling, aggregation, decisioning, and evidence logging.
    """

    def __init__(self, pipeline: MandiNyaayCVPipeline):
        self.pipeline = pipeline

    def run_inspection(
        self,
        image_input: str | Path | np.ndarray,
        lot_id: str = "lot_default",
        session_id: str | None = None,
        capture_id: str | None = None,
        target_sample_size: int = DEFAULT_TARGET_SAMPLE_SIZE,
        measurement_required: bool = False,
        manual_override: dict[str, Any] | None = None,
    ) -> InspectionSession:
        """
        Execute full vertical inspection slice over an input image.
        """
        sid = session_id or f"ses_{uuid.uuid4().hex[:8]}"
        cid = capture_id or f"cap_{uuid.uuid4().hex[:8]}"
        start_time_iso = datetime.now(timezone.utc).isoformat()

        # 1. Real CV Pipeline execution
        cv_result: CVPipelineResult = self.pipeline.process_image(
            image_input=image_input,
            capture_id=cid,
        )

        # 2. Extract visible condition counts
        condition_counts: dict[str, int] = {}
        for obs in cv_result.observations:
            lbl = obs.class_semantic.value
            condition_counts[lbl] = condition_counts.get(lbl, 0) + 1

        quality_grade_str = (
            cv_result.quality.grade.value
            if cv_result.quality is not None
            else "UNKNOWN"
        )

        provenance_dict: dict[str, Any] = {
            "pipeline_version": cv_result.pipeline_version,
            "mapping_status": cv_result.mapping_status.value,
        }
        if cv_result.model_metadata is not None:
            provenance_dict.update(cv_result.model_metadata.model_dump())

        capture = InspectionCapture(
            capture_id=cid,
            status=cv_result.pipeline_status,
            image_path=cv_result.image_path,
            image_sha256=cv_result.image_metadata.get("sha256"),
            captured_at_iso=start_time_iso,
            raw_detection_count=cv_result.raw_detection_count,
            reconciled_observation_count=cv_result.reconciled_observation_count,
            conflict_count=cv_result.conflict_count,
            visible_condition_counts=condition_counts,
            quality_status=quality_grade_str,
            mapping_status=cv_result.mapping_status.value,
            measurement_status=cv_result.measurement_status.value,
            calibration_status=cv_result.calibration_status,
            provenance=provenance_dict,
        )

        # 3. Form Canonical Observation Set
        obs_set_id = f"obs_set_{uuid.uuid4().hex[:8]}"
        obs_set_status = "VALID"
        if cv_result.pipeline_status == "INVALID_CAPTURE":
            obs_set_status = "INVALID"
        elif cv_result.conflict_count > 0:
            obs_set_status = "HAS_CONFLICTS"

        observation_set = InspectionObservationSet(
            observation_set_id=obs_set_id,
            status=obs_set_status,
            capture_ids=[cid],
            total_raw_detections=cv_result.raw_detection_count,
            total_reconciled_observations=cv_result.reconciled_observation_count,
            conflict_count=cv_result.conflict_count,
            observations=cv_result.observations,
            visible_condition_counts=condition_counts,
            version=cv_result.pipeline_version,
        )

        # 4. Statistical Sampling Sufficiency
        sampling_result: InspectionSamplingResult = evaluate_sampling_sufficiency(
            observations=cv_result.observations,
            target_sample_size=target_sample_size,
            conflict_count=cv_result.conflict_count,
            quality_grade=quality_grade_str,
        )

        # 5. Count Distribution Aggregation
        aggregation: InspectionAggregation = aggregate_observations(
            observations=cv_result.observations,
        )

        # 6. Operational Review Signals
        review_signals = generate_review_signals(
            conflict_count=cv_result.conflict_count,
            quality_grade=quality_grade_str,
            sampling_status=sampling_result.status,
            observed_sample_size=sampling_result.observed_sample_size,
            target_sample_size=target_sample_size,
            calibration_status=cv_result.calibration_status,
            measurement_status=cv_result.measurement_status.value,
            mass_status=aggregation.mass_status,
            count_mass_divergence_pct=None,
            manual_override=manual_override,
            calibration_required=measurement_required,
        )

        # 7. Deterministic Procurement Decision
        decision: InspectionDecision = evaluate_procurement_decision(
            observations=cv_result.observations,
            sampling_result=sampling_result,
            aggregation=aggregation,
            review_signals=review_signals,
            measurement_status=cv_result.measurement_status,
            measurement_required=measurement_required,
            override_info=manual_override,
        )

        # 8. Replayable Evidence Summary
        image_hashes = [capture.image_sha256] if capture.image_sha256 else []
        obs_ids = [obs.observation_id for obs in cv_result.observations]
        model_version_str = (
            f"{cv_result.model_metadata.architecture}_{Path(cv_result.model_metadata.checkpoint_path).name}"
            if cv_result.model_metadata
            else "yolov7_adapter"
        )

        root_hash = compute_evidence_root_hash(
            session_id=sid,
            lot_id=lot_id,
            capture_ids=[cid],
            image_hashes=image_hashes,
            observation_ids=obs_ids,
            procurement_grade=decision.procurement_grade.value,
            rule_version=decision.decision_rule_version,
        )

        evidence_summary = InspectionEvidenceSummary(
            evidence_id=f"evi_{uuid.uuid4().hex[:8]}",
            lot_id=lot_id,
            session_id=sid,
            status="RECORDED",
            capture_ids=[cid],
            image_hashes=image_hashes,
            observation_ids=obs_ids,
            model_version=model_version_str,
            mapping_version=cv_result.mapping_status.value,
            sampling_version=sampling_result.sampling_rule_version,
            rule_version=decision.decision_rule_version,
            measurement_status=cv_result.measurement_status.value,
            calibration_status=cv_result.calibration_status,
            review_signals=review_signals,
            decision=decision,
            override_information=manual_override,
            evidence_root_hash=root_hash,
            evidence_ledger_term="tamper-evident/replayable",
        )

        # 9. Session lifecycle status
        if decision.procurement_grade == ProcurementGrade.MANUAL_REVIEW:
            session_status = InspectionSessionStatus.MANUAL_REVIEW
        elif cv_result.pipeline_status in ("INVALID_CAPTURE", "QUALITY_FAIL"):
            session_status = InspectionSessionStatus.INVALID
        else:
            session_status = InspectionSessionStatus.COMPLETED

        end_time_iso = datetime.now(timezone.utc).isoformat()

        return InspectionSession(
            session_id=sid,
            lot_id=lot_id,
            status=session_status,
            captures=[capture],
            observation_set=observation_set,
            sampling_result=sampling_result,
            aggregation=aggregation,
            review_signals=review_signals,
            decision=decision,
            evidence_summary=evidence_summary,
            created_at_iso=start_time_iso,
            updated_at_iso=end_time_iso,
            pipeline_version=get_processing_version(),
        )
