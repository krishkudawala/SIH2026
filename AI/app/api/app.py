"""
Mandi Nyaay FastAPI Backend Application (Feature 20 & Flutter Contract Bridge).

Provides all 14 required endpoints for the Flutter front-end:
1. POST /sessions
2. POST /sessions/{id}/captures
3. POST /sessions/{id}/inference
4. GET /sessions/{id}/observations
5. GET /sessions/{id}/sample-units
6. GET /sessions/{id}/sampling
7. GET /sessions/{id}/measurement
8. GET /sessions/{id}/weight
9. GET /sessions/{id}/review
10. POST /sessions/{id}/decision
11. POST /sessions/{id}/dispute
12. GET /sessions/{id}/evidence
13. POST /sessions/{id}/replay
14. GET /sessions/{id}/report

Plus:
- GET /sessions
- GET /sessions/{id}
- POST /sessions/{id}/dispute/resolve
- POST /calibration/samples
- GET /calibration/samples
- POST /calibration/train-weight-model
- POST /ocr/scan
- POST /ocr/confirm
- GET /health

Backed by SQLModel SQLite and MandiNyaayEngine.
Runs 100% offline. Zero mocks. Zero fake values.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.cv.offline_ocr import OCRCandidate
from app.engine import MandiNyaayEngine
from app.storage.sql_models import (
    CalibrationSampleModel,
    CaptureModel,
    DecisionModel,
    DisputeModel,
    ObservationModel,
    SampleUnitModel,
    SessionModel,
)
from app.version import get_processing_version

logger = logging.getLogger(__name__)

# Engine singleton
_engine: Optional[MandiNyaayEngine] = None


def get_engine() -> MandiNyaayEngine:
    global _engine
    if _engine is None:
        _engine = MandiNyaayEngine()
    return _engine


app = FastAPI(
    title="Mandi Nyaay AI & Inspection Backend",
    version=get_processing_version(),
    description="Offline-first AI & computer vision inspection backend for agricultural produce grading.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------------------------------------------------------
# Request / Response Schemas
# -----------------------------------------------------------------------------

class CreateSessionRequest(BaseModel):
    lot_id: str = Field(..., description="Unique agricultural lot identifier")
    source_reference: str = Field(default="BAG_INSPECTOR_SELECTED", description="Source bag/mat reference")
    target_sample_size: int = Field(default=20, ge=1, description="Minimum sample size required by rule")
    rule_pack_id: str = Field(default="AGMARK_ONION_2024_V1", description="Authoritative rule pack ID")
    declared_bag_count: Optional[int] = Field(default=None, ge=1, description="Declared total bags in lot")
    certified_lot_weight_kg: Optional[float] = Field(default=None, gt=0.0, description="Weighbridge net weight in kg")


class AddCaptureRequest(BaseModel):
    image_path: Optional[str] = Field(default=None, description="Local filesystem path to captured produce photo")
    image_base64: Optional[str] = Field(default=None, description="Base64 encoded image content for remote/mobile upload")
    filename: Optional[str] = Field(default=None, description="Optional filename for uploaded image")
    capture_role: str = Field(default="PRIMARY_SAMPLE_CAPTURE", description="PRIMARY_SAMPLE_CAPTURE or DETAIL_RECAPTURE")
    view_angle: str = Field(default="TOP", description="PRIMARY, TOP, SIDE, DETAIL, UNDERSIDE")
    target_sample_unit_id: Optional[str] = Field(default=None, description="Existing SampleUnit ID if DETAIL_RECAPTURE")
    target_cell_id: Optional[str] = Field(default=None, description="Mat grid cell ID (e.g. A1-D5)")


class RunInferenceRequest(BaseModel):
    capture_id: Optional[str] = Field(default=None, description="Optional specific capture ID to evaluate")


class DecisionRequest(BaseModel):
    rule_pack_id: Optional[str] = Field(default=None, description="RulePack to apply")
    override_grade: Optional[str] = Field(default=None, description="GRADE_A, URS, REJECT, MANUAL_REVIEW")
    override_reason: Optional[str] = Field(default=None, description="Justification for manual adjudication")


class OpenDisputeRequest(BaseModel):
    dispute_reason: str = Field(..., description="Challenger statement of grievance")
    opened_by: str = Field(default="LOT_OWNER", description="LOT_OWNER, TRADER, or SUPERVISOR")


class ResolveDisputeRequest(BaseModel):
    final_grade: str = Field(..., description="Final binding procurement grade")
    arbitrator_id: str = Field(..., description="APMC Arbitrator ID")
    arbitration_notes: str = Field(..., description="Arbitration committee ruling notes")


class CalibrationSampleRequest(BaseModel):
    sample_unit_id: str = Field(..., description="Sample unit identifier")
    lot_id: str = Field(..., description="Lot identifier")
    length_mm: float = Field(..., gt=0.0, description="Major diameter L (mm)")
    width_mm: float = Field(..., gt=0.0, description="Minor diameter W (mm)")
    thickness_mm: float = Field(..., gt=0.0, description="Polar height T (mm)")
    actual_scale_weight_g: float = Field(..., gt=0.0, description="Direct digital scale mass in grams")
    condition: str = Field(default="HEALTHY", description="HEALTHY, DAMAGED, SPROUTED, ROTTEN")
    defect_fraction: float = Field(default=0.0, ge=0.0, le=1.0, description="Defect area fraction")
    variety: str = Field(default="Nashik Red", description="Produce cultivar")
    operator_id: str = Field(default="INSPECTOR_01", description="Inspector ID")


class TrainWeightModelRequest(BaseModel):
    coverage_target: float = Field(default=0.90, ge=0.50, le=0.99, description="Target conformal coverage")
    model_version: str = Field(default="weight_empirical_v1.0", description="Model version tag")


class OCRScanRequest(BaseModel):
    image_path: str = Field(..., description="Path to label, receipt, or weighbridge slip image")


class OCRConfirmRequest(BaseModel):
    text: str = Field(..., description="Candidate raw text")
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)
    field_type: str = Field(default="GENERIC_TEXT")
    confirmed_text: str = Field(..., description="Inspector-verified text")


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------

@app.get("/health", tags=["System"])
def health_check() -> dict[str, Any]:
    """System health check and version status."""
    return {
        "status": "HEALTHY",
        "engine": "Mandi Nyaay Offline Core",
        "version": get_processing_version(),
        "offline": True,
    }


# 1. POST /sessions
@app.post("/sessions", tags=["Sessions"], response_model=SessionModel)
def create_session(
    payload: CreateSessionRequest,
    engine: MandiNyaayEngine = Depends(get_engine),
) -> SessionModel:
    """Create a new inspection session with statutory inspector source flags."""
    return engine.create_session(
        lot_id=payload.lot_id,
        source_reference=payload.source_reference,
        target_sample_size=payload.target_sample_size,
        rule_pack_id=payload.rule_pack_id,
        declared_bag_count=payload.declared_bag_count,
        certified_lot_weight_kg=payload.certified_lot_weight_kg,
    )


@app.get("/sessions", tags=["Sessions"])
def list_sessions(
    limit: int = 50,
    engine: MandiNyaayEngine = Depends(get_engine),
) -> list[SessionModel]:
    """List recent inspection sessions."""
    return engine.sql_store.list_sessions(limit=limit)


@app.get("/sessions/{id}", tags=["Sessions"], response_model=SessionModel)
def get_session(
    id: str,
    engine: MandiNyaayEngine = Depends(get_engine),
) -> SessionModel:
    """Get inspection session by ID."""
    session = engine.get_session(session_id=id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {id} not found.")
    return session


# 2. POST /sessions/{id}/captures
@app.post("/sessions/{id}/captures", tags=["Captures"], response_model=CaptureModel)
def add_capture(
    id: str,
    payload: AddCaptureRequest,
    engine: MandiNyaayEngine = Depends(get_engine),
) -> CaptureModel:
    """Add a photographic capture and execute real optical image quality screening."""
    try:
        target_path = payload.image_path
        if payload.image_base64:
            import base64
            import uuid
            captures_dir = Path("data/captures") / id
            captures_dir.mkdir(parents=True, exist_ok=True)
            fname = payload.filename or f"cap_{uuid.uuid4().hex[:8]}.jpg"
            saved_file = captures_dir / fname
            saved_file.write_bytes(base64.b64decode(payload.image_base64))
            target_path = str(saved_file.resolve())

        if not target_path:
            raise HTTPException(status_code=400, detail="Either image_path or image_base64 must be provided.")

        return engine.add_capture(
            session_id=id,
            image_path=target_path,
            capture_role=payload.capture_role,
            view_angle=payload.view_angle,
            target_sample_unit_id=payload.target_sample_unit_id,
            target_cell_id=payload.target_cell_id,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/sessions/{id}/captures", tags=["Captures"])
def get_captures(
    id: str,
    engine: MandiNyaayEngine = Depends(get_engine),
) -> list[CaptureModel]:
    """Get all captures for an inspection session."""
    return engine.sql_store.get_captures_for_session(session_id=id)


# 3. POST /sessions/{id}/inference
@app.post("/sessions/{id}/inference", tags=["Inference"])
def run_inference(
    id: str,
    payload: Optional[RunInferenceRequest] = None,
    engine: MandiNyaayEngine = Depends(get_engine),
) -> dict[str, Any]:
    """Execute complete genuine multi-stage AI inference for a session."""
    cap_id = payload.capture_id if payload else None
    try:
        return engine.run_inference(session_id=id, capture_id=cap_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("Inference failed")
        raise HTTPException(status_code=500, detail=f"Inference execution failed: {e}")


# 4. GET /sessions/{id}/observations
@app.get("/sessions/{id}/observations", tags=["Observations"])
def get_observations(
    id: str,
    engine: MandiNyaayEngine = Depends(get_engine),
) -> list[ObservationModel]:
    """Get all produce observations for an inspection session."""
    return engine.get_observations(session_id=id)


# 5. GET /sessions/{id}/sample-units
@app.get("/sessions/{id}/sample-units", tags=["SampleUnits"])
def get_sample_units(
    id: str,
    engine: MandiNyaayEngine = Depends(get_engine),
) -> list[SampleUnitModel]:
    """Get all certified physical SampleUnits for an inspection session."""
    return engine.get_sample_units(session_id=id)


# 6. GET /sessions/{id}/sampling
@app.get("/sessions/{id}/sampling", tags=["Sampling"])
def get_sampling(
    id: str,
    engine: MandiNyaayEngine = Depends(get_engine),
) -> dict[str, Any]:
    """Get real-time statistical sampling progress, Wilson CIs, and sequential state."""
    try:
        return engine.get_sampling(session_id=id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


# 7. GET /sessions/{id}/measurement
@app.get("/sessions/{id}/measurement", tags=["Measurement"])
def get_measurement(
    id: str,
    engine: MandiNyaayEngine = Depends(get_engine),
) -> dict[str, Any]:
    """Get physical size measurements, tri-axial dimensions, and size status."""
    try:
        return engine.get_measurement(session_id=id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


# 8. GET /sessions/{id}/weight
@app.get("/sessions/{id}/weight", tags=["Weight"])
def get_weight(
    id: str,
    engine: MandiNyaayEngine = Depends(get_engine),
) -> dict[str, Any]:
    """Get mass estimates, prediction intervals, and mass status."""
    try:
        return engine.get_weight(session_id=id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


# 9. GET /sessions/{id}/review
@app.get("/sessions/{id}/review", tags=["Review"])
def get_review(
    id: str,
    engine: MandiNyaayEngine = Depends(get_engine),
) -> dict[str, Any]:
    """Get prioritized Review Center queue with statutory non-fraud explanations."""
    return engine.get_review(session_id=id)


# 10. POST /sessions/{id}/decision
@app.post("/sessions/{id}/decision", tags=["Decision"], response_model=DecisionModel)
def evaluate_decision(
    id: str,
    payload: Optional[DecisionRequest] = None,
    engine: MandiNyaayEngine = Depends(get_engine),
) -> DecisionModel:
    """Evaluate procurement decision against RulePack or apply manual inspector override."""
    override_dict = None
    if payload and payload.override_grade:
        override_dict = {
            "override_grade": payload.override_grade,
            "reason": payload.override_reason or "Manual inspector override",
        }
    rule_pack_id = payload.rule_pack_id if payload else None
    try:
        return engine.evaluate_decision(
            session_id=id,
            rule_pack_id=rule_pack_id,
            manual_override=override_dict,
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


# 11. POST /sessions/{id}/dispute
@app.post("/sessions/{id}/dispute", tags=["Dispute"], response_model=DisputeModel)
def open_dispute_endpoint(
    id: str,
    payload: OpenDisputeRequest,
    engine: MandiNyaayEngine = Depends(get_engine),
) -> DisputeModel:
    """Formally open an inspection dispute and create blind secondary session."""
    try:
        return engine.open_dispute(
            session_id=id,
            dispute_reason=payload.dispute_reason,
            opened_by=payload.opened_by,
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/sessions/{id}/dispute", tags=["Dispute"])
def get_dispute(
    id: str,
    engine: MandiNyaayEngine = Depends(get_engine),
) -> DisputeModel:
    """Get active dispute details for a session."""
    dispute = engine.sql_store.get_dispute_for_session(session_id=id)
    if not dispute:
        raise HTTPException(status_code=404, detail=f"No dispute found for session {id}.")
    return dispute


@app.post("/sessions/{id}/dispute/resolve", tags=["Dispute"], response_model=DisputeModel)
def resolve_dispute_endpoint(
    id: str,
    payload: ResolveDisputeRequest,
    engine: MandiNyaayEngine = Depends(get_engine),
) -> DisputeModel:
    """Record APMC arbitrator decision and bind final procurement resolution."""
    dispute = engine.sql_store.get_dispute_for_session(session_id=id)
    if not dispute:
        raise HTTPException(status_code=404, detail=f"No dispute found for session {id}.")
    return engine.resolve_dispute(
        dispute_id=dispute.id,
        final_grade=payload.final_grade,
        arbitrator_id=payload.arbitrator_id,
        arbitration_notes=payload.arbitration_notes,
    )


# 12. GET /sessions/{id}/evidence
@app.get("/sessions/{id}/evidence", tags=["Evidence"])
def get_evidence(
    id: str,
    engine: MandiNyaayEngine = Depends(get_engine),
) -> dict[str, Any]:
    """Get SHA-256 tamper-evident chained event ledger and evidence root digest."""
    try:
        return engine.get_evidence(session_id=id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


# 13. POST /sessions/{id}/replay
@app.post("/sessions/{id}/replay", tags=["Replay"])
def replay_session(
    id: str,
    engine: MandiNyaayEngine = Depends(get_engine),
) -> dict[str, Any]:
    """Deterministically recompute session from stored inputs and verify hash parity."""
    try:
        return engine.replay_session(session_id=id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


# 14. GET /sessions/{id}/report
@app.get("/sessions/{id}/report", tags=["Report"])
def get_report(
    id: str,
    engine: MandiNyaayEngine = Depends(get_engine),
) -> dict[str, Any]:
    """Generate complete offline inspection report in JSON, Markdown, and Thermal Receipt formats."""
    try:
        return engine.get_report(session_id=id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


# -----------------------------------------------------------------------------
# Calibration & OCR Supporting Endpoints
# -----------------------------------------------------------------------------

@app.post("/calibration/samples", tags=["Calibration"], response_model=CalibrationSampleModel)
def record_calibration_sample(
    payload: CalibrationSampleRequest,
    engine: MandiNyaayEngine = Depends(get_engine),
) -> CalibrationSampleModel:
    """Record a verified physical calibration sample into SQLite and the collector dataset."""
    try:
        return engine.record_calibration_sample(
            sample_unit_id=payload.sample_unit_id,
            lot_id=payload.lot_id,
            length_mm=payload.length_mm,
            width_mm=payload.width_mm,
            thickness_mm=payload.thickness_mm,
            actual_scale_weight_g=payload.actual_scale_weight_g,
            condition=payload.condition,
            defect_fraction=payload.defect_fraction,
            variety=payload.variety,
            operator_id=payload.operator_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/calibration/samples", tags=["Calibration"])
def list_calibration_samples(
    engine: MandiNyaayEngine = Depends(get_engine),
) -> list[CalibrationSampleModel]:
    """List all stored physical calibration samples."""
    return engine.sql_store.list_calibration_samples()


@app.post("/calibration/train-weight-model", tags=["Calibration"])
def train_weight_model(
    payload: TrainWeightModelRequest,
    engine: MandiNyaayEngine = Depends(get_engine),
) -> dict[str, Any]:
    """Fit empirical weight model with MAPIE conformal uncertainty intervals."""
    try:
        artifact = engine.train_weight_model(
            coverage_target=payload.coverage_target,
            model_version=payload.model_version,
        )
        return artifact.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/ocr/scan", tags=["OCR"])
def scan_ocr(
    payload: OCRScanRequest,
    engine: MandiNyaayEngine = Depends(get_engine),
) -> dict[str, Any]:
    """Scan image for candidate Lot IDs, bag labels, and weighbridge slips."""
    try:
        res = engine.scan_ocr(payload.image_path)
        return res.model_dump()
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/ocr/confirm", tags=["OCR"])
def confirm_ocr(
    payload: OCRConfirmRequest,
    engine: MandiNyaayEngine = Depends(get_engine),
) -> dict[str, Any]:
    """Record inspector confirmation of an OCR candidate."""
    cand = OCRCandidate(
        text=payload.text,
        confidence=payload.confidence,
        field_type=payload.field_type,
    )
    confirmed = engine.confirm_ocr(cand, payload.confirmed_text)
    return confirmed.model_dump()
